#!/usr/bin/env python3
"""Validate references.yaml conventions."""

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

ALLOWED_REFERENCE_TYPES = {
    "Annual Report",
    "Court Ruling",
    "International Standard",
    "Legislation",
    "Paper",
    "Structure Chart",
    "Treaty",
    "Webpage",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate references YAML conventions")
    parser.add_argument(
        "--references-file",
        default="data/references.yaml",
        help="YAML file containing references",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def main() -> int:
    args = parse_args()
    path = Path(args.references_file)

    try:
        data = load_yaml(path)
    except (FileNotFoundError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not isinstance(data, dict):
        print(f"error: root must be a mapping in {path}", file=sys.stderr)
        return 1

    violations: list[str] = []
    for record_name, record_value in data.items():
        if not isinstance(record_value, dict):
            violations.append(f"{record_name}: record must be a mapping")
            continue

        ref_type = record_value.get("Reference_type")
        if ref_type is None:
            continue
        if not isinstance(ref_type, str):
            violations.append(f"{record_name}: Reference_type must be a string")
            continue
        if ref_type not in ALLOWED_REFERENCE_TYPES:
            allowed = ", ".join(sorted(ALLOWED_REFERENCE_TYPES))
            violations.append(
                f"{record_name}: invalid Reference_type '{ref_type}' (allowed: {allowed})"
            )

    if violations:
        print("Reference validation failed:", file=sys.stderr)
        for violation in violations:
            print(f"- {violation}", file=sys.stderr)
        return 1

    print(f"Validated {len(data)} references in {path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
