#!/usr/bin/env python3
"""Expand placeholder markers in general_list.yaml into a new entity template."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from generate_sprvd_id import collect_existing_ids, generate_unique_ids

PLACEHOLDER_RE = re.compile(r"^(?P<indent>[ \t]*)(?:\*\*New\*\*|New)\s*$", re.MULTILINE)

TEMPLATE_LINES = [
    "[Name]:",
    "  SPRVD_id: {sprvd_id}",
    "  Entity_type: International organisation",
    "  Wikidata_code:",
    "  Org_family:",
    "  Type:",
    "  Country: ZZ",
    "  Name_en:",
    "  Abbreviation_en:",
    "  Treaty_url:",
    "  Immunity_url:",
    "  Source:",
    "  OpenSanctions_id:",
    "  Assessment_against_FATF_definition:",
    "  Basis_for_assessment:",
]


def build_template(indent: str, sprvd_id: str) -> str:
    return "\n".join(f"{indent}{line.format(sprvd_id=sprvd_id)}" for line in TEMPLATE_LINES)


def expand_placeholders(text: str, sprvd_ids: list[str]) -> tuple[str, int]:
    count = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal count
        sprvd_id = sprvd_ids[count]
        count += 1
        return build_template(match.group("indent"), sprvd_id)

    return PLACEHOLDER_RE.sub(repl, text), count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replace New or **New** placeholder lines with a new entity template",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="data/general_list.yaml",
        help="path to the YAML file to update",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.path)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    original = path.read_text(encoding="utf-8")
    placeholder_count = len(PLACEHOLDER_RE.findall(original))
    if placeholder_count == 0:
        print("No New placeholders found.")
        return 0

    try:
        existing_ids = collect_existing_ids(path, "SPRVD_id")
        sprvd_ids = generate_unique_ids(placeholder_count, existing_ids)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    updated, count = expand_placeholders(original, sprvd_ids)
    if count == 0:
        print("No New placeholders found.")
        return 0

    if updated != original:
        path.write_text(updated, encoding="utf-8")

    print(f"Expanded {count} New placeholder(s) in {path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
