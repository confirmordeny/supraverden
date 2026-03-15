#!/usr/bin/env python3
"""Generate dist/ORG_FAMILIES.md from YAML data files."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("error: missing dependency PyYAML (pip install pyyaml)") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate organization families markdown")
    parser.add_argument(
        "--input-files",
        nargs="+",
        default=["data/general_list.yaml", "data/united_nations.yaml"],
        help="Input YAML files",
    )
    parser.add_argument(
        "--output-file",
        default="dist/ORG_FAMILIES.md",
        help="Output markdown file",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def parse_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        print(f"Warning: file not found: {path}")
        return []

    data = load_yaml(path)
    if not isinstance(data, dict):
        print(f"Warning: YAML root is not a mapping in {path}")
        return []

    records: list[dict[str, Any]] = []
    for name, fields in data.items():
        row: dict[str, Any] = {"_main_name": str(name)}
        if isinstance(fields, dict):
            row.update(fields)
        records.append(row)
    return records


def normalize_family(value: Any) -> str:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped and stripped.lower() != "null":
            return stripped
    return "Unspecified"


def main() -> int:
    args = parse_args()
    all_records: list[dict[str, Any]] = []
    for file_path in args.input_files:
        records = parse_records(Path(file_path))
        all_records.extend(records)
        print(f"Loaded {len(records)} items from {file_path}")

    counts = Counter(normalize_family(record.get("Org_family")) for record in all_records)
    lines = ["# Organization Families Summary", ""]
    for family in sorted(counts.keys(), key=str.casefold):
        count = counts[family]
        suffix = "entity" if count == 1 else "entities"
        lines.append(f"* {family} ({count} {suffix})")

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"SUCCESS: Generated {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
