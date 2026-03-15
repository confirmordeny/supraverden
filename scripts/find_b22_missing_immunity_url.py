#!/usr/bin/env python3
"""List B22 entities that do not have Immunity_url populated."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    print("error: missing dependency PyYAML (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find records with Basis_for_assessment=B22 missing Immunity_url"
    )
    parser.add_argument(
        "--list-file",
        default="data/general_list.yaml",
        help="Path to general list YAML file",
    )
    parser.add_argument(
        "--show-count-only",
        action="store_true",
        help="Print only the number of matching records",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def is_populated(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return True


def has_immunity_url(fields: dict[str, Any]) -> bool:
    # Support both canonical and lower-case key variants.
    if "Immunity_url" in fields:
        return is_populated(fields.get("Immunity_url"))
    if "immunity_url" in fields:
        return is_populated(fields.get("immunity_url"))
    return False


def main() -> int:
    args = parse_args()
    list_path = Path(args.list_file)

    try:
        records = load_yaml(list_path)
    except (FileNotFoundError, OSError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not isinstance(records, dict):
        print("error: expected top-level mapping of entities", file=sys.stderr)
        return 2

    missing: list[str] = []
    for entity_name, fields in records.items():
        if not isinstance(fields, dict):
            continue
        if fields.get("Basis_for_assessment") != "B22":
            continue
        if not has_immunity_url(fields):
            missing.append(str(entity_name))

    if args.show_count_only:
        print(len(missing))
    else:
        for name in missing:
            print(name)
        print(f"\nTotal: {len(missing)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
