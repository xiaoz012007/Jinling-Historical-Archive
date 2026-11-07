#!/usr/bin/env python3
"""Read-only Task004 consistency checks; writes reports only under --output.

Usage (a separate checkout of the frozen PR #2 tree is required):
  python scripts/validate_task004.py --baseline /path/to/v02 \
      --output /path/to/qa004_structural

This checks data propagation and arithmetic, not the historical truth of a
source, ownership of third-party text, or whether an event actually happened.
Explicit old/legacy snapshots are excluded from current source-ID checks.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


TEMP_SOURCE = re.compile(r"(?<![A-Za-z0-9])(?:T4-(?:AT|INT|TR|B)-\d+|T4-TL-0[1])(?![A-Za-z0-9])")
FINAL_SOURCE = re.compile(r"SRC-\d{4}")
SOURCE_FIELDS = {
    "source_id", "source_ids", "canonical_source_id", "canonical_source_ids",
    "evidence_ids", "new_evidence_ids", "from_source_id", "to_source_id",
    "temporary_id", "related_existing_source_ids", "reviewed_sources_this_round",
    "task004_source_ids", "source_nature_by_source_id", "来源id", "来源编号",
}
OLD_FIELD = re.compile(r"(^|_)(old|original|previous|inherited|legacy|baseline|history)(_|$)|^pre_task004")
CORE_HASHES = {
    "evacuation/recalculate.py": "8c7a6478d62f8ee9553723601b5520dc179f8ef7e6c32352a307645ab5f7f8a9",
    "evacuation/model_data.json": "5151d3fd6593e2753245004fa585a11ac10467c10be879bc872da0d7793cb3f1",
    "evacuation/evacuation_model.xlsx": "3397e10f465b62d56c96d5daac02a51297351dce73dc8aa972506506dc5b1d65",
}
KNOWN_TROOP_CORRECTIONS = {"FO-024": (2000, 6000), "FO-041": (2000, 3000), "FO-054": (2000, 11000)}
TIMELINE_FIELDS = (
    "date_start", "date_end", "time_start", "time_end", "time_text", "time_role",
    "time_precision", "actors", "event_description", "claim_status", "source_ids",
    "citation_locator", "limitations", "counterevidence", "count_value",
    "count_scope", "verified_death_count", "aggregation_allowed",
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        raw = list(csv.reader(handle))
    if not raw:
        raise ValueError(f"empty CSV: {path}")
    if len(raw[0]) != len(set(raw[0])):
        raise ValueError(f"duplicate column names: {path}")
    malformed = [(i + 1, len(row)) for i, row in enumerate(raw) if len(row) != len(raw[0])]
    if malformed:
        raise ValueError(f"CSV column-count mismatch: {path}: {malformed[:10]}")
    return [dict(zip(raw[0], row)) for row in raw[1:]]


def records(data, preferred=("records", "events", "questions", "updates", "changes")):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for name in preferred:
            if isinstance(data.get(name), list):
                return data[name]
    raise ValueError("Cannot locate a record list; schema must be mapped explicitly")


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value):
    """Normalize representation only: never guess dates, people or meanings."""
    if value is None or value == "":
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float, Decimal)):
        return str(Decimal(str(value)).normalize())
    if isinstance(value, list):
        return [normalized(item) for item in value]
    if isinstance(value, dict):
        return {key: normalized(item) for key, item in value.items()}
    value = str(value).strip()
    if value.lower() in {"true", "false"}:
        return value.lower()
    if re.fullmatch(r"-?\d+(?:\.\d+)?", value):
        return str(Decimal(value).normalize())
    if value.startswith(("[", "{")):
        try:
            return normalized(json.loads(value))
        except (ValueError, TypeError):
            pass
    return value


def source_ids(value):
    return set(FINAL_SOURCE.findall(json.dumps(value, ensure_ascii=False)))


def equal_field(left, right, field):
    if field == "source_ids":
        return source_ids(left) == source_ids(right)
    return normalized(left) == normalized(right)


def number(value):
    if isinstance(value, bool) or value is None or str(value).strip() == "":
        raise ValueError("Unknown or Boolean value cannot be used as a count")
    try:
        result = Decimal(str(value).replace(",", ""))
    except InvalidOperation as exc:
        raise ValueError(f"Non-numeric count: {value!r}") from exc
    if not result.is_finite():
        raise ValueError("Non-finite count")
    return result


def indexed(rows, key):
    if any(not row.get(key) for row in rows):
        raise ValueError(f"Missing {key}")
    counts = Counter(row[key] for row in rows)
    dupes = [identifier for identifier, count in counts.items() if count != 1]
    if dupes:
        raise ValueError(f"Duplicate {key}: {dupes}")
    return {row[key]: row for row in rows}


def current_source_values(data, location="$", historical=False):
    """Yield source-valued fields, excluding explicitly preserved old values."""
    if isinstance(data, dict):
        for key, value in data.items():
            name = str(key).lower()
            old = historical or bool(OLD_FIELD.search(name))
            here = f"{location}.{key}"
            if old:
                continue
            is_source = name in SOURCE_FIELDS or name.endswith("_source_ids")
            if is_source:
                yield here, value
            elif name in {"target", "source"} and isinstance(value, str) and (TEMP_SOURCE.search(value) or FINAL_SOURCE.fullmatch(value)):
                yield here, value
            if isinstance(value, (list, dict)):
                yield from current_source_values(value, here, old)
    elif isinstance(data, list):
        for index, value in enumerate(data):
            yield from current_source_values(value, f"{location}[{index}]", historical)


class Audit:
    def __init__(self, root, baseline, output, min_sources):
        self.root, self.baseline, self.output = root, baseline, output
        self.min_sources = min_sources
        self.results = []
        self.inputs = {}

    def csv(self, relative, baseline=False):
        path = (self.baseline if baseline else self.root) / relative
        self.inputs[str(path)] = digest(path)
        return read_csv(path)

    def json(self, relative, baseline=False):
        path = (self.baseline if baseline else self.root) / relative
        self.inputs[str(path)] = digest(path)
        return read_json(path)

    def add(self, name, errors, details=None):
        self.results.append({"check": name, "passed": not errors, "errors": errors, "details": details})

    def run(self, name, method):
        try:
            method()
        except Exception as exc:
            self.add(name, [f"{type(exc).__name__}: {exc}"], "Missing/unrecognized data is a failed check, not an automatic pass")

    def sources(self):
        registry = self.csv("sources/SOURCE_REGISTER.csv")
        by_id = indexed(registry, "source_id")
        errors = []
        if len(by_id) < self.min_sources:
            errors.append(f"Expected at least {self.min_sources} sources, got {len(by_id)}")
        invalid = [sid for sid in by_id if not FINAL_SOURCE.fullmatch(sid)]
        if invalid:
            errors.append({"nonfinal_registry_ids": invalid})
        unknown, temporary, parse_failures, scanned = [], [], [], 0
        for path in sorted(self.root.rglob("*")):
            if path.suffix.lower() not in {".csv", ".json"} or not path.is_file():
                continue
            if "fixtures" in path.parts or any(part.startswith(".") for part in path.relative_to(self.root).parts):
                continue
            scanned += 1
            self.inputs[str(path)] = digest(path)
            try:
                data = read_csv(path) if path.suffix.lower() == ".csv" else read_json(path)
            except (ValueError, UnicodeError) as exc:
                parse_failures.append({"path": str(path.relative_to(self.root)), "error": str(exc)})
                continue
            for where, value in current_source_values(data):
                text = json.dumps(value, ensure_ascii=False)
                temp = TEMP_SOURCE.findall(text)
                missing = sorted(source_ids(value) - by_id.keys())
                if temp:
                    temporary.append({"path": str(path.relative_to(self.root)), "field": where, "temporary_ids": temp})
                if missing:
                    unknown.append({"path": str(path.relative_to(self.root)), "field": where, "unregistered_ids": missing})
        if parse_failures:
            errors.append({"unparseable_current_csv_json": parse_failures})
        if temporary:
            errors.append({"temporary_source_ids": temporary})
        if unknown:
            errors.append({"unregistered_source_ids": unknown})
        self.add("source_registry_and_current_ids", errors, {"source_count": len(by_id), "files_scanned": scanned, "excluded": "fixtures and explicitly old/original/legacy/inherited/previous/baseline/history fields"})

    def questions(self):
        baseline = indexed(self.csv("unresolved/OPEN_QUESTIONS.csv", True), "original_id")
        current = indexed(self.csv("unresolved/OPEN_QUESTIONS.csv"), "original_id")
        companion = indexed(records(self.json("unresolved/OPEN_QUESTIONS.json")), "original_id")
        links = indexed(self.csv("unresolved/QUESTION_SOURCE_LINKS.csv"), "question_id")
        errors = []
        if len(baseline) != 34 or set(current) != set(baseline):
            errors.append({"original_id_set_mismatch": {"baseline": len(baseline), "current": len(current), "missing": sorted(baseline.keys()-current.keys()), "added": sorted(current.keys()-baseline.keys())}})
        if set(companion) != set(current) or set(links) != set(current):
            errors.append("Question CSV/JSON/derived link ID sets differ")
        open_ids = {qid for qid, row in baseline.items() if normalized(row.get("resolved")) != "true"}
        if len(open_ids) != 33:
            errors.append(f"Frozen baseline must have 33 open questions; found {len(open_ids)}")
        progress_ids = set()
        files = sorted((self.root / "docs/task004-research").glob("*/question_updates.json"))
        for path in files:
            self.inputs[str(path)] = digest(path)
            for row in records(read_json(path)):
                qid = row.get("original_id", row.get("question_id"))
                if qid:
                    progress_ids.add(qid)
        missing_progress = sorted(open_ids - progress_ids)
        if missing_progress:
            errors.append({"missing_task004_topic_updates": missing_progress})
        for qid, row in current.items():
            if qid in open_ids:
                if not row.get("task004_progress_status") or not row.get("task004_update_path"):
                    errors.append({"question": qid, "missing_current_progress_fields": True})
                elif not (self.root / row["task004_update_path"]).is_file():
                    errors.append({"question": qid, "missing_update_file": row["task004_update_path"]})
                if normalized(row.get("resolved")) == "true":
                    errors.append({"question": qid, "unexpected_resolution": "Task004 handoff keeps all 33 whole questions open"})
            if qid in baseline and row.get("original_question") != baseline[qid].get("original_question"):
                errors.append({"question": qid, "original_question_changed": True})
            if qid in companion:
                for field in row.keys() | companion[qid].keys():
                    if not equal_field(row.get(field), companion[qid].get(field), field):
                        errors.append({"question": qid, "csv_json_field": field})
            if qid in links and source_ids(row.get("source_ids")) != source_ids(links[qid].get("source_ids")):
                errors.append({"question": qid, "derived_source_ids": links[qid].get("source_ids"), "current_source_ids": row.get("source_ids")})
        self.add("original_questions_progress_and_source_propagation", errors, {"original_questions": len(current), "baseline_open": len(open_ids), "topic_update_ids": len(progress_ids), "topic_update_files": len(files)})

    def timeline(self):
        csv_rows = indexed(self.csv("timeline/南京保卫战统一时间线.csv"), "event_id")
        json_rows = indexed(records(self.json("timeline/NANJING_1937_TIMELINE.json")), "event_id")
        errors, comparisons = [], 0
        if set(csv_rows) != set(json_rows):
            errors.append({"csv_only": sorted(csv_rows.keys()-json_rows.keys()), "json_only": sorted(json_rows.keys()-csv_rows.keys())})
        for identifier in csv_rows.keys() & json_rows.keys():
            a, b = csv_rows[identifier], json_rows[identifier]
            for field in TIMELINE_FIELDS:
                if field not in a and field not in b:
                    continue
                comparisons += 1
                if not equal_field(a.get(field), b.get(field), field):
                    errors.append({"event_id": identifier, "field": field, "csv": a.get(field), "json": b.get(field)})
        self.add("unified_timeline_csv_json", errors, {"events": len(csv_rows), "field_comparisons": comparisons})
        schemas = [
            ("international/国际救援人员活动时间线.csv", {"date_start":"date_start", "date_end":"date_end", "time_text":"time_text", "time_role":"time_role", "people":"actors", "proposition":"event_description"}),
            ("atrocities/重要事件证据表.csv", {"date_start":"date_start", "date_end":"date_end", "time_start":"time_start", "time_end":"time_end", "time_text":"time_text", "time_role":"time_role", "actors":"actors", "event_description":"event_description"}),
        ]
        for relative, mapping in schemas:
            specialist = indexed(self.csv(relative), "event_id")
            differences, matched = [], specialist.keys() & csv_rows.keys()
            if not matched:
                differences.append("No common event IDs; propagation could not be checked")
            for identifier in matched:
                for left, right in mapping.items():
                    if left not in specialist[identifier]:
                        continue
                    if not equal_field(specialist[identifier].get(left), csv_rows[identifier].get(right), right):
                        differences.append({"event_id":identifier, "specialist_field":left, "unified_field":right, "specialist":specialist[identifier].get(left), "unified":csv_rows[identifier].get(right)})
            self.add(f"specialist_propagation:{relative}", differences, {"shared_ids_checked":len(matched), "specialist_only_ids":sorted(specialist.keys()-csv_rows.keys()), "note":"Only common IDs compared; this check does not assert every cross-year/context event belongs in the 1937 timeline"})

    def troop_revisions(self):
        old = indexed(self.csv("military/TROOP_OBSERVATIONS_81.csv", True), "observation_id")
        current = indexed(self.csv("military/TROOP_OBSERVATIONS_81.csv"), "observation_id")
        errors = []
        if set(current) != set(old) or len(current) != 81:
            errors.append("81 observation identities must be preserved")
        changed = {key for key in current.keys() & old.keys() if normalized(current[key].get("value")) != normalized(old[key].get("value"))}
        if changed != set(KNOWN_TROOP_CORRECTIONS):
            errors.append({"unexpected_changed_value_ids":sorted(changed), "expected":sorted(KNOWN_TROOP_CORRECTIONS)})
        for identifier, (previous, corrected) in KNOWN_TROOP_CORRECTIONS.items():
            row, before = current[identifier], old[identifier]
            if number(before["value"]) != previous or number(row["value"]) != corrected:
                errors.append({"observation":identifier, "wrong_old_or_new_value":True})
            if normalized(row.get("value_original_v02")) != normalized(before.get("value")) or row.get("raw_value") != before.get("raw_value"):
                errors.append({"observation":identifier, "old_value_not_preserved":True})
            if not all(row.get(field) for field in ("task004_revision_id","task004_source_ids","task004_locator","task004_review_scope")):
                errors.append({"observation":identifier, "missing_revision_provenance":True})
        for identifier,row in current.items():
            if normalized(row.get("historical_aggregate_allowed")) != "false" or normalized(row.get("historical_actual_total")) != "":
                errors.append({"observation":identifier, "historical_total_or_aggregation_enabled":True})
        self.add("three_troop_corrections_preserve_originals", errors, {"changed_observation_ids":sorted(changed)})

    def tan_arithmetic(self):
        table = self.csv("military/TAN1946_TABLE.csv")
        summary = self.json("military/TAN1946_ARITHMETIC.json")
        indexed(table,"row_id")
        columns = {key: f"{key}_printed" for key in summary["printed_column_totals"]}
        sums = {key:sum((number(row[column]) for row in table),Decimal(0)) for key,column in columns.items()}
        errors=[]
        for key,total in sums.items():
            if total != number(summary["recalculated_row_sums"][key]):
                errors.append({"column":key,"computed":str(total),"declared":summary["recalculated_row_sums"][key]})
            difference=total-number(summary["printed_column_totals"][key])
            if difference != number(summary["differences_row_sum_minus_printed"][key]):
                errors.append({"column":key,"difference_mismatch":str(difference)})
        for row in table:
            components=number(row["combat_printed"])+number(row["auxiliary_printed"])
            difference=number(row["statistics_printed"])-components
            if number(row["combat_plus_auxiliary_I"]) != components or number(row["statistics_minus_component_sum_I"]) != difference:
                errors.append({"row_id":row["row_id"],"row_arithmetic_mismatch":True})
            if normalized(row.get("historical_aggregate_allowed")) != "false":
                errors.append({"row_id":row["row_id"],"historical_aggregation_not_disabled":True})
        if number(summary["arithmetic_combat_plus_auxiliary"]) != sums["combat"]+sums["auxiliary"]:
            errors.append("Combined I arithmetic does not equal component column sums")
        if summary.get("nature_of_calculation") != "I" or normalized(summary.get("historical_actual_total")) != "":
            errors.append("Calculation must be I with historical actual total left unknown")
        if normalized(summary.get("raw_values_must_not_be_replaced_by_arithmetic")) != "true" or not summary.get("notes"):
            errors.append("Printed/arithmetic difference explanation or raw-preservation rule missing")
        audit=self.json("military/TROOPS_MODEL_AUDIT.json")
        if not audit.get("task004_scope_note") or normalized(audit.get("task004_corrections")) != normalized(summary):
            errors.append("Old workbook audit lacks scope distinction or its Task004 correction summary differs")
        self.add("tan_original_columns_and_I_arithmetic",errors,{"rows":len(table),"printed_totals":summary["printed_column_totals"],"recalculated_sums":{k:str(v) for k,v in sums.items()},"scope":"Arithmetic validates transcription structure; original printed errors are retained, not silently corrected"})

    def binary_changes(self):
        suspicious=[];existing=0
        extensions={".pdf",".png",".jpg",".jpeg",".gif",".webp",".tif",".tiff",".zip",".gz",".warc",".xlsx",".xls",".docx",".pptx",".mp4",".mp3",".djvu",".epub"}
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() or any(p.startswith(".") for p in path.relative_to(self.root).parts):
                continue
            relative=path.relative_to(self.root);payload=path.read_bytes()
            try:payload.decode("utf-8-sig");binary=False
            except UnicodeError:binary=True
            if not binary and path.suffix.lower() not in extensions:
                continue
            old=self.baseline/relative
            if old.is_file() and digest(path)==digest(old):existing+=1
            else:suspicious.append({"path":str(relative),"status":"new" if not old.exists() else "changed","sha256":digest(path)})
        self.add("no_new_third_party_binary_payloads",[{"unapproved_new_or_changed_binary":suspicious}] if suspicious else [],{"unchanged_existing_binary_files":existing,"note":"Conservative gate: all new/changed binary or archive carriers need separate explicit ownership/rights review. This does not prove copyright permission for textual material."})

    def evacuation_hashes(self):
        errors=[];actual={}
        for relative,expected in CORE_HASHES.items():
            current=digest(self.root/relative);baseline=digest(self.baseline/relative)
            actual[relative]={"current":current,"baseline":baseline,"frozen_expected":expected}
            if current!=baseline or current!=expected:errors.append({"file":relative,"hash_mismatch":actual[relative]})
        self.add("evacuation_core_frozen_hashes",errors,actual)

    def save(self):
        self.output.mkdir(parents=True,exist_ok=True)
        passed=sum(row["passed"] for row in self.results)
        report={"checked_at_utc":datetime.now(timezone.utc).isoformat(),"root":str(self.root),"baseline":str(self.baseline),"baseline_commit":"5f7377ef7c40fef9c51dab22e47c63bd47947c7e","all_passed":passed==len(self.results),"checks":len(self.results),"passed":passed,"failed":len(self.results)-passed,"results":self.results,"input_sha256":self.inputs,"scope":"结构传播、原值保留与算术；不是全史实或版权法律结论"}
        (self.output/"results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        lines=["# Task004 独立一致性检查", "", f"检查 {len(self.results)} 项：通过 {passed}，未通过 {len(self.results)-passed}。", "", "本检查仅核结构传播、原值保留和算术，不认证历史事实或第三方版权。未知、缺文件和无法识别结构不会自动判通过。", "", "| 检查 | 结果 |", "|---|---|"]
        lines += [f"| {row['check']} | {'通过' if row['passed'] else '未通过'} |" for row in self.results]
        for row in self.results:
            if row["errors"]:lines += ["", f"## {row['check']}", "", "```json",json.dumps(row["errors"],ensure_ascii=False,indent=2),"```"]
        (self.output/"REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
        print(json.dumps({k:report[k] for k in ["all_passed","checks","passed","failed"]},ensure_ascii=False))
        return 0 if report["all_passed"] else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--baseline",type=Path,required=True,help="Read-only frozen PR #2 checkout/tree")
    parser.add_argument("--output",type=Path,required=True,help="Separate QA output directory, outside the candidate root")
    parser.add_argument("--min-sources",type=int,default=175)
    args=parser.parse_args()
    root,baseline,output=args.root.resolve(),args.baseline.resolve(),args.output.resolve()
    if output==root or root in output.parents:
        parser.error("--output must be outside candidate root; validation does not mutate candidate data")
    if not root.is_dir() or not baseline.is_dir():parser.error("root and baseline must exist")
    audit=Audit(root,baseline,output,args.min_sources)
    for name,method in [("sources",audit.sources),("questions",audit.questions),("timeline",audit.timeline),("troop_revisions",audit.troop_revisions),("tan_arithmetic",audit.tan_arithmetic),("binary_changes",audit.binary_changes),("evacuation_hashes",audit.evacuation_hashes)]:
        audit.run(name,method)
    return audit.save()


if __name__=="__main__":
    sys.exit(main())
