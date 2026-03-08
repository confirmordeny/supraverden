#!/usr/bin/env python3
"""Compatibility wrapper for SPRVD_id validation.

This script delegates SPRVD checks to scripts/validate_general_list_yaml.py
so SPRVD validation logic has a single implementation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from validate_general_list_yaml import load_yaml, validate_sprvd_ids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate SPRVD_id values (delegates to main validator logic)"
    )
    parser.add_argument(
        "--file",
        default="data/general_list.yaml",
        help="file containing top-level org mappings",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.file)
    try:
        list_data = load_yaml(path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except yaml.YAMLError as exc:
        print(f"error: invalid YAML in list file '{path}': {exc}", file=sys.stderr)
        return 1

    if not isinstance(list_data, dict):
        print("error: list file root must be a mapping", file=sys.stderr)
        return 1

    stats, violations = validate_sprvd_ids(list_data)

    print(f"records: {stats['records']}")
    print(f"SPRVD_id entries: {stats['sprvd_entries']}")
    print(f"missing SPRVD_id: {stats['missing_sprvd']}")
    print(f"bad format: {stats['bad_format']}")
    print(f"bad check digit: {stats['bad_check_digit']}")
    print(f"duplicate IDs: {stats['duplicate_ids']}")

    if violations:
        print("\nViolation details:")
        for issue in violations:
            print(f"- {issue.record} :: {issue.key} -> {issue.message}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
