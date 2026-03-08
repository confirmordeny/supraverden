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


def parse_variant_policy(dict_data: dict[str, Any]) -> tuple[set[str], set[str], set[str], set[str]]:
    raw = dict_data.get("_variant_policy")
    if not isinstance(raw, dict):
        return set(), set(), set(), set()

    suffixes_raw = raw.get("language_suffixes")
    indexes_raw = raw.get("index_suffixes")
    applies_raw = raw.get("applies_to")
    required_raw = raw.get("required_variants")

    suffixes: set[str] = set()
    indexes: set[str] = set()
    bases: set[str] = set()
    required: set[str] = set()

    if isinstance(suffixes_raw, list):
        suffixes = {str(item).strip().lower() for item in suffixes_raw if str(item).strip()}
    if isinstance(indexes_raw, list):
        indexes = {str(item).strip() for item in indexes_raw if str(item).strip()}
    if isinstance(applies_raw, list):
        bases = {str(item).strip() for item in applies_raw if str(item).strip()}
    if isinstance(required_raw, list):
        required = {str(item).strip() for item in required_raw if str(item).strip()}

    return suffixes, indexes, bases, required


def parse_record_policy(dict_data: dict[str, Any]) -> tuple[set[str], set[str]]:
    raw = dict_data.get("_record_policy")
    if not isinstance(raw, dict):
        return set(), set()
    required_raw = raw.get("required_fields")
    source_required_raw = raw.get("source_required_for")

    required_fields = (
        {str(item).strip() for item in required_raw if str(item).strip()}
        if isinstance(required_raw, list)
        else set()
    )
    source_required_for = (
        {str(item).strip() for item in source_required_raw if str(item).strip()}
        if isinstance(source_required_raw, list)
        else set()
    )
    return required_fields, source_required_for


def validate_required_variants(
    record: str, record_value: dict[str, Any], required_variants: set[str]
) -> list[Violation]:
    violations: list[Violation] = []
    for key in required_variants:
        if key not in record_value:
            violations.append(Violation(record, key, "missing required key"))
            continue
        value = record_value.get(key)
        if value is None:
            violations.append(Violation(record, key, "required value is null"))
            continue
        if isinstance(value, str) and value.strip() == "":
            violations.append(Violation(record, key, "required value is blank"))
    return violations


def validate_required_fields(
    record: str, record_value: dict[str, Any], required_fields: set[str]
) -> list[Violation]:
    violations: list[Violation] = []
    for key in required_fields:
        if key not in record_value:
            violations.append(Violation(record, key, "missing required key"))
            continue
        value = record_value.get(key)
        if value is None:
            violations.append(Violation(record, key, "required value is null"))
            continue
        if isinstance(value, str) and value.strip() == "":
            violations.append(Violation(record, key, "required value is blank"))
    return violations


def has_source_reference(record_value: dict[str, Any]) -> bool:
    for key, value in record_value.items():
        if key == "Source" or re.fullmatch(r"Source_\d{1,2}", key):
            if value is None:
                continue
            if isinstance(value, str) and value.strip() == "":
                continue
            return True
    return False


def validate_source_requirements(
    record: str, record_value: dict[str, Any], source_required_for: set[str]
) -> list[Violation]:
    violations: list[Violation] = []
    has_source = has_source_reference(record_value)
    for field in source_required_for:
        value = record_value.get(field)
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue
        if not has_source:
            violations.append(
                Violation(
                    record,
                    "Source",
                    f"missing source for populated field '{field}'",
                )
            )
    return violations


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def resolve_language_variant(
    key: str,
    normalized_dict: dict[str, dict[str, Any]],
    variant_suffixes: set[str],
    variant_bases: set[str],
) -> str | None:
    if "_" not in key:
        return None

    base, suffix = key.rsplit("_", 1)
    if suffix.lower() not in variant_suffixes:
        return None
    if base not in variant_bases:
        return None
    if base not in normalized_dict:
        return None
    return base


def resolve_dict_key(
    key: str,
    normalized_dict: dict[str, dict[str, Any]],
    variant_suffixes: set[str],
    variant_indexes: set[str],
    variant_bases: set[str],
) -> str | None:
    if key in normalized_dict:
        return key

    # Language variant: <base>_<lang>
    resolved = resolve_language_variant(key, normalized_dict, variant_suffixes, variant_bases)
    if resolved is not None:
        return resolved

    if "_" not in key:
        return None

    # Numbered variant: <base>_<n> or <base>_<lang>_<n>, where n in index_suffixes.
    stem, index = key.rsplit("_", 1)
    if index not in variant_indexes:
        # Numbered+language variant: <base>_<n>_<lang>
        parts = key.split("_")
        if len(parts) >= 3:
            lang = parts[-1].lower()
            idx = parts[-2]
            base = "_".join(parts[:-2])
            if (
                lang in variant_suffixes
                and idx in variant_indexes
                and base in variant_bases
                and base in normalized_dict
            ):
                return base
        return None

    if stem in normalized_dict:
        return stem

    resolved = resolve_language_variant(stem, normalized_dict, variant_suffixes, variant_bases)
    if resolved is not None:
        return resolved

    return None


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
    return normalized == "[no code found.]"


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

    if "exactly 20 characters" in rules_lc:
        if not isinstance(value, str) or len(value) != 20:
            errors.append("must be exactly 20 characters")

    if "uppercase letters a-z and digits 0-9 only" in rules_lc:
        if not isinstance(value, str) or not re.fullmatch(r"[A-Z0-9]+", value):
            errors.append("must contain only uppercase letters A-Z and digits 0-9")

    if "either blank/null or 8 or 11 characters" in rules_lc:
        if value in (None, ""):
            pass
        elif not isinstance(value, str) or len(value) not in {8, 11}:
            errors.append("must be blank/null or have length 8 or 11")

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


def apply_machine_validation_rules(value: Any, rules: Any) -> list[str]:
    if rules is None:
        return []

    if isinstance(rules, dict):
        rules_list: list[Any] = [rules]
    elif isinstance(rules, list):
        rules_list = rules
    else:
        return []

    errors: list[str] = []
    for entry in rules_list:
        if not isinstance(entry, dict):
            continue

        rule = str(entry.get("rule") or "").strip().lower()
        allow_values_raw = entry.get("allow_values")
        allow_values = (
            {str(v) for v in allow_values_raw}
            if isinstance(allow_values_raw, list)
            else set()
        )
        if str(value) in allow_values:
            continue

        allow_blank = bool(entry.get("allow_blank"))
        if allow_blank and isinstance(value, str) and value.strip() == "":
            continue

        if rule == "no_spaces":
            if isinstance(value, str) and " " in value:
                errors.append("contains spaces")
            continue

        if rule == "starts_with":
            prefix = str(entry.get("value") or "")
            if not isinstance(value, str) or not value.startswith(prefix):
                errors.append(f"must start with {prefix}")
            continue

        if rule == "regex":
            pattern = entry.get("pattern")
            if not isinstance(pattern, str) or not isinstance(value, str) or not re.fullmatch(pattern, value):
                errors.append("does not match required pattern")
            continue

        if rule == "exact_length":
            length = parse_length(entry.get("length"))
            if length is None or len(str(value)) != length:
                errors.append(f"must be exactly {length} characters")
            continue

        if rule == "disallow_values":
            disallow_raw = entry.get("values")
            disallow = {str(v) for v in disallow_raw} if isinstance(disallow_raw, list) else set()
            if str(value) in disallow:
                errors.append(f"value '{value}' is not permitted")
            continue

        if rule == "year_range":
            min_year = parse_length(entry.get("min"))
            max_year = parse_length(entry.get("max"))
            if bool(entry.get("max_current_year")):
                max_year = datetime.now().year
            if is_int_like(value):
                year = int(value)
            elif isinstance(value, str) and value.isdigit():
                year = int(value)
            else:
                year = None
            if year is None:
                errors.append("must be a valid year")
            else:
                if min_year is not None and year < min_year:
                    errors.append(f"must be >= {min_year}")
                if max_year is not None and year > max_year:
                    errors.append(f"must be <= {max_year}")
            continue

    return errors


def validate_value(record: str, key: str, value: Any, meta: dict[str, Any]) -> list[Violation]:
    violations: list[Violation] = []

    if value is None:
        return violations

    data_type = str(meta.get("datatype") or meta.get("datatype") or "").strip().lower()
    min_length = parse_length(meta.get("minimumlength"))
    max_length = parse_length(meta.get("maximumlength"))
    multi_value = parse_bool(meta.get("multivalue"))
    permissible = parse_permissible_values(meta.get("permissiblevalues"))
    rules_field = meta.get("validationrules")
    rules_summary = str(meta.get("validationsummary") or "").strip()

    if isinstance(value, list):
        if not multi_value:
            violations.append(Violation(record, key, "expected scalar value; list is not allowed"))
            return violations
        values_to_check = value
    else:
        values_to_check = [value]

    for item in values_to_check:
        if key in {"OpenSanctions_id", "Wikidata_code"} and is_no_code_found(item):
            continue

        if data_type == "integer" and not is_int_like(item):
            violations.append(Violation(record, key, "expected integer"))

        if data_type in {"text", "url", "country", "opensanctions id"} and not isinstance(item, str):
            violations.append(Violation(record, key, f"expected string for data type '{data_type}'"))
            continue

        if data_type == "url" and isinstance(item, str) and not item.startswith("http"):
            violations.append(Violation(record, key, "expected URL starting with http"))

        if min_length is not None:
            value_len = len(str(item))
            if value_len < min_length:
                violations.append(Violation(record, key, f"length {value_len} < minimum {min_length}"))

        if max_length is not None:
            value_len = len(str(item))
            if value_len > max_length:
                violations.append(Violation(record, key, f"length {value_len} > maximum {max_length}"))

        if permissible:
            if str(item) not in permissible:
                allowed = ", ".join(sorted(permissible))
                violations.append(Violation(record, key, f"value '{item}' not in permissible values [{allowed}]"))

        if isinstance(rules_field, (dict, list)):
            for rule_error in apply_machine_validation_rules(item, rules_field):
                violations.append(Violation(record, key, rule_error))
        elif isinstance(rules_field, str) and rules_field.strip():
            # Backward compatibility for legacy free-text Validation_rules entries.
            for rule_error in apply_validation_rules(item, rules_field.strip()):
                violations.append(Violation(record, key, rule_error))
        elif rules_summary:
            for rule_error in apply_validation_rules(item, rules_summary):
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
    variant_suffixes, variant_indexes, variant_bases, required_variants = parse_variant_policy(dict_data)
    required_fields, source_required_for = parse_record_policy(dict_data)

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
        violations.extend(validate_required_fields(str(record_name), record_value, required_fields))
        violations.extend(validate_source_requirements(str(record_name), record_value, source_required_for))
        violations.extend(validate_required_variants(str(record_name), record_value, required_variants))

        for key, value in record_value.items():
            key_str = str(key)
            resolved_key = resolve_dict_key(
                key_str,
                normalized_dict,
                variant_suffixes,
                variant_indexes,
                variant_bases,
            )
            if resolved_key is None:
                continue
            checked_values += 1
            violations.extend(validate_value(str(record_name), key_str, value, normalized_dict[resolved_key]))

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
