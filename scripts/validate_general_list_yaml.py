#!/usr/bin/env python3
"""Validate a general list YAML file against a data dictionary YAML.

Checks:
- both files are valid YAML
- for each record/key in the list, if the key exists in the dictionary,
  validate value compliance against dictionary constraints
- validate SPRVD_id presence, format, check digit, and uniqueness
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    print("error: missing dependency PyYAML (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2) from exc

SPRVD_ID_RE = re.compile(r"^SPRVD0(\d{5})(\d)$")


@dataclass
class Violation:
    record: str
    key: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate general list YAML against data dictionary"
    )
    parser.add_argument(
        "--list-file",
        default="data/general_list.yaml",
        help="YAML file containing top-level records",
    )
    parser.add_argument(
        "--dict-file",
        default="data/data_dictionary.yaml",
        help="YAML data dictionary file",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def normalize_meta_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def normalize_dict_entry(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    normalized: dict[str, Any] = {}
    for key, value in raw.items():
        normalized[normalize_meta_key(str(key))] = value
    return normalized


def parse_length(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    if not text.isdigit():
        return None
    return int(text)


def parse_permissible_values(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(v).strip() for v in value if str(v).strip()}
    parts = [part.strip() for part in str(value).split(",")]
    return {part for part in parts if part}


def is_int_like(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_no_code_found(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    return normalized in {"[no code found]", "[no code found.]"}


def compute_sprvd_check_digit(payload5: str) -> int:
    total = sum(int(d) * (6 - i) for i, d in enumerate(payload5, start=1))
    return total % 10


def validate_sprvd_ids(list_data: dict[str, Any]) -> tuple[dict[str, int], list[Violation]]:
    stats = {
        "records": 0,
        "sprvd_entries": 0,
        "missing_sprvd": 0,
        "bad_format": 0,
        "bad_check_digit": 0,
        "duplicate_ids": 0,
    }
    violations: list[Violation] = []
    seen: dict[str, str] = {}

    for record_name, record_value in list_data.items():
        stats["records"] += 1
        if not isinstance(record_value, dict):
            continue

        if "SPRVD_id" not in record_value:
            stats["missing_sprvd"] += 1
            violations.append(Violation(str(record_name), "SPRVD_id", "missing required key"))
            continue

        value = record_value.get("SPRVD_id")
        stats["sprvd_entries"] += 1

        if not isinstance(value, str) or value.strip() == "":
            stats["bad_format"] += 1
            violations.append(Violation(str(record_name), "SPRVD_id", "invalid format"))
            continue

        match = SPRVD_ID_RE.fullmatch(value.strip())
        if not match:
            stats["bad_format"] += 1
            violations.append(
                Violation(
                    str(record_name),
                    "SPRVD_id",
                    "invalid format (expected SPRVD0 + 6 digits)",
                )
            )
            continue

        payload, check = match.group(1), int(match.group(2))
        expected = compute_sprvd_check_digit(payload)
        if expected != check:
            stats["bad_check_digit"] += 1
            violations.append(
                Violation(
                    str(record_name),
                    "SPRVD_id",
                    f"invalid check digit (expected {expected})",
                )
            )

        if value in seen:
            stats["duplicate_ids"] += 1
            violations.append(
                Violation(
                    str(record_name),
                    "SPRVD_id",
                    f"duplicate ID also used by '{seen[value]}'",
                )
            )
        else:
            seen[value] = str(record_name)

    return stats, violations


def apply_validation_rules(value: Any, rules: str) -> list[str]:
    errors: list[str] = []
    rules_lc = rules.lower()

    if "no spaces" in rules_lc:
        if isinstance(value, str) and (" " in value):
            errors.append("contains spaces")

    if "begins with \"http\"" in rules_lc or "starts with \"http\"" in rules_lc:
        if not isinstance(value, str) or not value.startswith("http"):
            errors.append("must start with http")

    if "must consist of two uppercase letters" in rules_lc:
        if not isinstance(value, str) or not re.fullmatch(r"[A-Z]{2}", value):
            errors.append("must be exactly two uppercase letters")

    if "must consist of two lowercase letters" in rules_lc:
        if not isinstance(value, str) or not re.fullmatch(r"[a-z]{2}", value):
            errors.append("must be exactly two lowercase letters")

    if (
        "begins with \"b\" followed by two digits" in rules_lc
        or "begins with \"b\" followed by one or two digits" in rules_lc
    ):
        if not isinstance(value, str) or not re.fullmatch(r"B\d{1,2}", value):
            errors.append("must match B followed by one or two digits")
        elif value == "B00":
            errors.append("B00 is not valid")

    if "starts with \"q\"" in rules_lc and "digits" in rules_lc:
        if not isinstance(value, str) or not re.fullmatch(r"Q\d+", value):
            errors.append("must start with Q and then digits")

    if "no earlier than 1810" in rules_lc and "no later than the current year" in rules_lc:
        current_year = datetime.now().year
        if is_int_like(value):
            year = value
        elif isinstance(value, str) and value.isdigit():
            year = int(value)
        else:
            year = None
        if year is None or year < 1810 or year > current_year:
            errors.append(f"must be between 1810 and {current_year}")

    return errors


def validate_value(record: str, key: str, value: Any, meta: dict[str, Any]) -> list[Violation]:
    violations: list[Violation] = []

    if value is None:
        return violations

    if key in {"OpenSanctions_id", "Wikidata_code"} and is_no_code_found(value):
        return violations

    data_type = str(meta.get("datatype") or meta.get("datatype") or "").strip().lower()
    min_length = parse_length(meta.get("minimumlength"))
    max_length = parse_length(meta.get("maximumlength"))
    permissible = parse_permissible_values(meta.get("permissiblevalues"))
    rules = str(meta.get("validationrules") or "").strip()

    if data_type == "integer" and not is_int_like(value):
        violations.append(Violation(record, key, "expected integer"))

    if data_type in {"text", "url", "country", "opensanctions id"} and not isinstance(value, str):
        violations.append(Violation(record, key, f"expected string for data type '{data_type}'"))

    if data_type == "url" and isinstance(value, str) and not value.startswith("http"):
        violations.append(Violation(record, key, "expected URL starting with http"))

    if min_length is not None:
        value_len = len(str(value))
        if value_len < min_length:
            violations.append(Violation(record, key, f"length {value_len} < minimum {min_length}"))

    if max_length is not None:
        value_len = len(str(value))
        if value_len > max_length:
            violations.append(Violation(record, key, f"length {value_len} > maximum {max_length}"))

    if permissible:
        if str(value) not in permissible:
            allowed = ", ".join(sorted(permissible))
            violations.append(Violation(record, key, f"value '{value}' not in permissible values [{allowed}]"))

    if rules:
        for rule_error in apply_validation_rules(value, rules):
            violations.append(Violation(record, key, rule_error))

    return violations


def main() -> int:
    args = parse_args()

    list_path = Path(args.list_file)
    dict_path = Path(args.dict_file)

    try:
        list_data = load_yaml(list_path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except yaml.YAMLError as exc:
        print(f"error: invalid YAML in list file '{list_path}': {exc}", file=sys.stderr)
        return 1

    try:
        dict_data = load_yaml(dict_path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except yaml.YAMLError as exc:
        print(f"error: invalid YAML in dictionary file '{dict_path}': {exc}", file=sys.stderr)
        return 1

    if not isinstance(list_data, dict):
        print("error: list file root must be a mapping", file=sys.stderr)
        return 1

    if not isinstance(dict_data, dict):
        print("error: dictionary file root must be a mapping", file=sys.stderr)
        return 1

    normalized_dict = {str(k): normalize_dict_entry(v) for k, v in dict_data.items()}

    violations: list[Violation] = []
    sprvd_stats, sprvd_violations = validate_sprvd_ids(list_data)
    violations.extend(sprvd_violations)
    checked_values = 0
    records = 0

    for record_name, record_value in list_data.items():
        records += 1
        if not isinstance(record_value, dict):
            violations.append(
                Violation(str(record_name), "<record>", "record value must be a mapping")
            )
            continue

        for key, value in record_value.items():
            key_str = str(key)
            if key_str not in normalized_dict:
                continue
            checked_values += 1
            violations.extend(validate_value(str(record_name), key_str, value, normalized_dict[key_str]))

    print(f"list yaml: valid ({list_path})")
    print(f"dictionary yaml: valid ({dict_path})")
    print(f"records: {records}")
    print(f"checked values (keys present in dictionary): {checked_values}")
    print("sprvd_id checks:")
    print(f"- entries: {sprvd_stats['sprvd_entries']}")
    print(f"- missing: {sprvd_stats['missing_sprvd']}")
    print(f"- bad format: {sprvd_stats['bad_format']}")
    print(f"- bad check digit: {sprvd_stats['bad_check_digit']}")
    print(f"- duplicates: {sprvd_stats['duplicate_ids']}")
    print(f"violations: {len(violations)}")

    if violations:
        print("\nViolation details:")
        for issue in violations:
            print(f"- {issue.record} :: {issue.key} -> {issue.message}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
