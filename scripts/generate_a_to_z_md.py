#!/usr/bin/env python3
"""Generate dist/ENGLISH_A_TO_Z_LIST.md from data/general_list.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("error: missing dependency PyYAML (pip install pyyaml)") from exc


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "general_list.yaml"
OUTPUT_PATH = ROOT / "dist" / "ENGLISH_A_TO_Z_LIST.md"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"error: input file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise SystemExit("error: YAML root must be a mapping")
    return data


def build_content(data: dict[str, Any]) -> str:
    organizations: list[dict[str, Any]] = []
    for org_name, props in data.items():
        row = {"_main_name": str(org_name)}
        if isinstance(props, dict):
            row.update(props)
        organizations.append(row)

    sorted_orgs = sorted(
        organizations,
        key=lambda x: (str(x.get("Name_en") or x.get("_main_name") or "")).strip().lower(),
    )

    groups: dict[str, list[str]] = {}
    for org in sorted_orgs:
        name = str(org.get("Name_en") or org.get("_main_name") or "").strip()
        if not name:
            continue
        first_char = name.lstrip("\"'")[0].upper()
        if not first_char.isalpha():
            first_char = "#"
        groups.setdefault(first_char, []).append(name)

    letters = sorted(groups.keys())
    lines: list[str] = ["# Alphabetical list of names of international organisations in English", "", '<div id="top"></div>', ""]
    lines.append(" | ".join(f"[{letter}](#{letter.lower()})" for letter in letters))
    lines.append("")
    lines.append("---")
    lines.append("")

    for letter in letters:
        lines.append(f"## {letter}")
        lines.append("")
        for name in groups[letter]:
            lines.append(f"- {name}")
        lines.append("")
        lines.append("[↑ Back to Top](#top)")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    data = load_yaml(INPUT_PATH)
    content = build_content(data)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
