#!/usr/bin/env python3
"""Generate dist/FATF_ASSESSMENTS.md from YAML sources."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("error: missing dependency PyYAML (pip install pyyaml)") from exc


ROOT = Path(__file__).resolve().parents[1]
BASIS_PATH = ROOT / "data" / "FATF_definition_analysis.yaml"
ENTITIES_PATH = ROOT / "data" / "general_list.yaml"
OUTPUT_PATH = ROOT / "dist" / "FATF_ASSESSMENTS.md"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"error: input file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise SystemExit("error: YAML root must be a mapping")
    return data


def build_content(basis_lookup: dict[str, Any], entities_data: dict[str, Any]) -> str:
    lines = [
        "# FATF Assessment Table",
        "> This file is auto-generated. Do not edit manually.",
        "",
        "| Organisation | Assessment | Basis for Assessment |",
        "| :--- | :--- | :--- |",
    ]

    for entity_name, fields in entities_data.items():
        if not isinstance(fields, dict):
            continue
        assessment = fields.get("Assessment_against_FATF_definition", "N/A")
        basis_id = fields.get("Basis_for_assessment")

        basis_text = "No basis text found."
        if isinstance(basis_id, str) and basis_id in basis_lookup:
            entry = basis_lookup[basis_id]
            if isinstance(entry, dict):
                basis_text = str(entry.get("Basis_text", entry))
            else:
                basis_text = str(entry)

        clean_basis = basis_text.replace("\n", " ").replace("\r", "").strip()
        lines.append(f"| {entity_name} | {assessment} | {clean_basis} |")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    basis_lookup = load_yaml(BASIS_PATH)
    entities_data = load_yaml(ENTITIES_PATH)
    content = build_content(basis_lookup, entities_data)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
