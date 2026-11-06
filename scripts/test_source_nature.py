#!/usr/bin/env python3
"""Adversarial closeout tests: mutate disposable copies, never project data."""
import csv
import json
import shutil
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
from validate_source_nature import validate

ROOT = Path(__file__).resolve().parents[1]


class SourceNatureCloseoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        # Only data and frozen fixtures are required; no third-party snapshots copied.
        for path in ROOT.rglob('*'):
            if path.is_file() and path.suffix in ('.csv', '.json'):
                target = self.root / path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)

    def tearDown(self):
        self.temp.cleanup()

    def mutate_csv(self, rel, mutation):
        path = self.root / rel
        with path.open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            fields, rows = reader.fieldnames, list(reader)
        mutation(rows)
        with path.open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def assertRejected(self, code):
        result = validate(self.root)
        self.assertFalse(result['passed'])
        self.assertIn(code, {error['code'] for error in result['errors']})

    def test_clean_migration_with_legacy_u_is_accepted(self):
        # U in explicit original-value cells and legacy research fields is legitimate.
        self.assertTrue(validate(self.root)['passed'])

    def test_current_csv_u_is_rejected(self):
        self.mutate_csv('sources/SOURCE_REGISTER.csv', lambda rows: rows[0].update(source_nature='U'))
        self.assertRejected('CURRENT_ENUM')

    def test_current_nested_json_u_is_rejected(self):
        path = self.root / 'sources/new_current_record.json'
        path.write_text(json.dumps({'records': [{'source_nature': 'U'}]}))
        self.assertRejected('CURRENT_ENUM')

    def test_missing_one_of_143_sources_is_rejected(self):
        self.mutate_csv('sources/SOURCE_REGISTER.csv', lambda rows: rows.pop())
        self.assertRejected('REGISTER_COMPLETENESS')

    def test_duplicate_source_cannot_hide_missing_id(self):
        self.mutate_csv('sources/SOURCE_REGISTER.csv', lambda rows: rows[-1].update(source_id=rows[0]['source_id']))
        self.assertRejected('REGISTER_COMPLETENESS')

    def test_loss_of_legacy_u_is_rejected(self):
        self.mutate_csv('sources/SOURCE_REGISTER.csv', lambda rows: rows[0].update(source_nature_original=''))
        self.assertRejected('REGISTER_ORIGINAL_VALUES')

    def test_valid_enum_but_wrong_reference_is_rejected(self):
        self.mutate_csv('sources/HISTORICAL_CLAIM_LINKS.csv', lambda rows: rows[0].update(source_nature_from_register='P' if rows[0]['source_nature_from_register'] != 'P' else 'T'))
        self.assertRejected('LINK_REGISTER_MATCH')

    def test_valid_but_upgraded_event_status_is_rejected(self):
        self.mutate_csv('timeline/EVENT_REGISTER.csv', lambda rows: rows[0].update(claim_status='contradicted' if rows[0]['claim_status'] != 'contradicted' else 'supported'))
        self.assertRejected('STATUS_UNCHANGED')

    def test_historical_link_status_change_is_rejected(self):
        self.mutate_csv('sources/HISTORICAL_CLAIM_LINKS.csv', lambda rows: rows[0].update(claim_status_repo='supported' if rows[0]['claim_status_repo'] != 'supported' else 'unverified'))
        self.assertRejected('STATUS_UNCHANGED')

    def test_rewriting_archived_metadata_is_rejected(self):
        path = self.root / 'sources/SOURCE_DETAILS.json'
        value = json.loads(path.read_text())
        value['records'][0]['claimed_metadata_unverified']['legacy_grade_not_mapped'] = 'P'
        path.write_text(json.dumps(value))
        self.assertRejected('DETAIL_ARCHIVES_UNCHANGED')

    def test_project_file_is_not_promoted_to_primary(self):
        def mutate(rows):
            row = next(row for row in rows if row['source_id'] == 'FILE-F06')
            row['source_nature_from_register'] = 'P'
        self.mutate_csv('sources/HISTORICAL_CLAIM_LINKS.csv', mutate)
        self.assertRejected('LINK_REGISTER_MATCH')

    def test_unresolved_status_change_is_rejected(self):
        self.mutate_csv('unresolved/OPEN_QUESTIONS.csv', lambda rows: rows[0].update(status='supported'))
        self.assertRejected('STATUS_UNCHANGED')


if __name__ == '__main__':
    unittest.main()
