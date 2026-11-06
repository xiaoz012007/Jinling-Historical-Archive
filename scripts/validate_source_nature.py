#!/usr/bin/env python3
"""Validate the PR #1 source-nature migration without rewriting data.

This is a closeout guard against the frozen 975725c input, not a claim-verification
tool. Later research additions require a separately reviewed baseline change.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ALLOWED = frozenset(('P', 'S', 'T', 'unknown'))
CURRENT_FIELDS = frozenset(('source_nature', 'source_nature_from_register'))
ARCHIVE_CONTAINERS = frozenset(('claimed_metadata_unverified', 'prior_access', 'original_values'))
REG = 'sources/SOURCE_REGISTER.csv'
DETAIL = 'sources/SOURCE_DETAILS.json'
LINK = 'sources/HISTORICAL_CLAIM_LINKS.csv'


def digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest()


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def validate(root, baseline_path=None):
    root = Path(root).resolve()
    baseline_path = baseline_path or root / 'scripts/fixtures/source_nature_closeout_baseline.json'
    errors, checks = [], []

    def check(ok, code, message):
        checks.append(dict(code=code, passed=bool(ok), detail=message))
        if not ok:
            errors.append(dict(code=code, detail=message))

    try:
        baseline = json.loads(Path(baseline_path).read_text(encoding='utf-8-sig'))
        _, register = read_csv(root / REG)
        details = json.loads((root / DETAIL).read_text(encoding='utf-8-sig'))
        _, links = read_csv(root / LINK)
    except (OSError, ValueError, csv.Error) as exc:
        return dict(passed=False, errors=[dict(code='INPUT_READ', detail=str(exc))], checks=[])

    old = baseline['original_source_nature']
    expected = {sid: ('unknown' if nature == 'U' else nature) for sid, nature in old.items()}
    check(len(old) == 143 and Counter(old.values()) == {'U': 69, 'P': 17, 'S': 8, 'T': 49},
          'BASELINE_IDENTITY', 'Frozen input must contain 143 sources, including precisely 69 legacy U values.')
    reg_ids = [row.get('source_id') for row in register]
    check(len(reg_ids) == 143 and len(set(reg_ids)) == 143 and set(reg_ids) == set(old),
          'REGISTER_COMPLETENESS', 'All 143 original stable source IDs must occur exactly once.')
    current = {row.get('source_id'): row.get('source_nature') for row in register}
    check(current == expected, 'ONLY_U_TO_UNKNOWN', 'P/S/T values stay unchanged; each old U becomes unknown.')
    check(all(row.get('source_nature_original') == ('U' if old.get(row.get('source_id')) == 'U' else '') for row in register),
          'REGISTER_ORIGINAL_VALUES', 'Exactly the 69 changed source records retain original U; other original-value cells stay blank.')

    detail_rows = details.get('records', [])
    detail_ids = [row.get('source_id') for row in detail_rows]
    check(details.get('count') == 143 and len(detail_ids) == 143 and len(set(detail_ids)) == 143 and set(detail_ids) == set(old),
          'DETAIL_COMPLETENESS', 'SOURCE_DETAILS must contain the same 143 sources exactly once.')
    check({row.get('source_id'): row.get('source_nature') for row in detail_rows} == expected,
          'DETAIL_REGISTER_MATCH', 'Current detail nature values must agree with the register.')
    check(all(row.get('source_nature_original') == ('U' if old.get(row.get('source_id')) == 'U' else '') for row in detail_rows),
          'DETAIL_ORIGINAL_VALUES', 'SOURCE_DETAILS preserves the same 69 legacy U values.')
    detail_projection = [{k: v for k, v in row.items() if k not in ('source_nature', 'source_nature_original', 'notes')} for row in detail_rows]
    check(digest(detail_projection) == baseline['source_details_protected_sha256'],
          'DETAIL_ARCHIVES_UNCHANGED', 'Acquisition, archived metadata, limitations, research labels and all other detail fields are unchanged.')
    check({k: v for k, v in details.items() if k != 'records'} == baseline['source_details_original_top_level'],
          'DETAIL_METADATA_UNCHANGED', 'Top-level detail metadata remains unchanged.')

    file_links = 0
    for row in links:
        sid = row.get('source_id')
        label = row.get('evidence_link_id')
        if sid in expected:
            wanted = expected[sid]
            original = 'U' if old[sid] == 'U' else ''
        elif sid in ('FILE-F06', 'FILE-F07') and row.get('source_object_role') == 'project_file_only_not_primary_evidence':
            # These 61 inherited file-location references are not SRC sources.
            wanted, original = 'unknown', 'U'
            file_links += 1
        else:
            check(False, 'LINK_SOURCE_ID', f'{label}: unregistered source/file identity {sid!r}')
            continue
        check(row.get('source_nature_from_register') == wanted, 'LINK_REGISTER_MATCH', f'{label}: {sid} current nature matches its authoritative record or retained FILE role.')
        check(row.get('source_nature_from_register_original') == original, 'LINK_ORIGINAL_VALUES', f'{label}: original linked nature is preserved correctly.')
    check(file_links == 61, 'PROJECT_FILE_COUNT', 'The 61 FILE-F06/F07 links remain project-file locators, not registered primary evidence.')
    check(sum(row.get('source_nature_from_register_original') == 'U' for row in links) == 145,
          'LINK_MIGRATION_COUNT', '145 linked U values are preserved: 84 SRC links and 61 project-file links.')

    for rel, spec in baseline['protected_csv'].items():
        try:
            fields, rows = read_csv(root / rel)
        except (OSError, ValueError, csv.Error) as exc:
            check(False, 'PROTECTED_INPUT_READ', f'{rel}: {exc}')
            continue
        omitted = set(spec['omitted_fields']) | {'source_nature_original', 'source_nature_from_register_original'}
        projection = [{k: v for k, v in row.items() if k not in omitted} for row in rows]
        check(len(rows) == spec['row_count'] and digest(projection) == spec['protected_sha256'],
              'OTHER_FIELDS_UNCHANGED', f'{rel}: every pre-existing field outside current nature/notes is unchanged.')
        statuses = [{key: row.get(key) for key in spec['status_fields']} for row in rows]
        check(digest(statuses) == spec['status_sha256'], 'STATUS_UNCHANGED', f'{rel}: frozen status and evidence-limit projection is unchanged.')

    try:
        _, migration = read_csv(root / 'sources/SOURCE_NATURE_MIGRATION.csv')
        mids = [row.get('source_id') for row in migration]
        check(len(mids) == 69 and len(set(mids)) == 69 and set(mids) == {sid for sid, val in old.items() if val == 'U'},
              'MIGRATION_LOG_COVERAGE', 'The source-level migration log covers exactly the 69 converted source IDs.')
        check(all(row.get('field') == 'source_nature' and row.get('original_value') == 'U' and row.get('current_value') == 'unknown' and row.get('claim_status_changed') == 'false' and row.get('baseline_commit') == baseline['baseline_commit'] for row in migration),
              'MIGRATION_LOG_VALUES', 'Migration entries retain old/new values, unchanged claim status and input commit.')
    except (OSError, ValueError, csv.Error) as exc:
        check(False, 'MIGRATION_LOG_READ', str(exc))

    # Scan actual current fields in all live CSV/JSON, including future nested records.
    # Test fixtures contain intentional legacy/invalid examples and are not live data.
    def walk(obj, path, archived=False):
        if isinstance(obj, dict):
            for key, value in obj.items():
                is_archive = archived or key in ARCHIVE_CONTAINERS
                if key in CURRENT_FIELDS and not is_archive:
                    check(isinstance(value, str) and value in ALLOWED, 'CURRENT_ENUM', f'{path}/{key}: {value!r}')
                walk(value, f'{path}/{key}', is_archive)
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                walk(value, f'{path}/{i}', archived)

    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix not in ('.csv', '.json'):
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith('scripts/fixtures/'):
            continue
        try:
            if path.suffix == '.json':
                walk(json.loads(path.read_text(encoding='utf-8-sig')), rel)
            else:
                fields, rows = read_csv(path)
                for index, row in enumerate(rows, 2):
                    for field in CURRENT_FIELDS.intersection(fields):
                        check(row.get(field) in ALLOWED, 'CURRENT_ENUM', f'{rel}:{index}:{field}={row.get(field)!r}')
                        if field == 'source_nature' and rel != REG and row.get('source_id') in expected:
                            check(row[field] == expected[row['source_id']], 'CURRENT_REFERENCE_MATCH', f'{rel}:{index}: current source nature matches register.')
        except (OSError, ValueError, csv.Error) as exc:
            check(False, 'CURRENT_DATA_READ', f'{rel}: {exc}')
    return dict(passed=not errors, baseline_commit=baseline['baseline_commit'], source_count=len(register),
                source_nature_counts=dict(Counter(current.values())), checks_run=len(checks), errors=errors, checks=checks,
                limitations='Field/schema migration validation only; not historical re-verification, copyright clearance or source independence assessment.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--baseline', type=Path, help='Explicit frozen input baseline; never generated by this command.')
    parser.add_argument('--json', action='store_true', help='Print full machine-readable diagnostics to stdout.')
    args = parser.parse_args()
    result = validate(args.root, args.baseline)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{'PASS' if result['passed'] else 'FAIL'}: {result.get('checks_run', 0)} field/invariant checks; {len(result['errors'])} errors")
        for error in result['errors']:
            print(f"{error['code']}: {error['detail']}")
        print(result.get('limitations', 'Input could not be read.'))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
