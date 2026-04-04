#!/usr/bin/env python3
"""Generate an extended English A-to-Z list from data/general_list.yaml."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("error: missing dependency PyYAML (pip install pyyaml)") from exc


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "general_list.yaml"
OUTPUT_PATH = ROOT / "dist" / "ENGLISH_EXTENDED_A_TO_Z_LIST.md"

NAME_FORMER_RE = re.compile(r"^Name_former(?:_\d+)?_en$")
NAME_OTHER_RE = re.compile(r"^Name_other(?:_\d+)?_en$")
ABBREVIATION_RE = re.compile(r"^Abbreviation_en$")
ABBREVIATION_FORMER_RE = re.compile(r"^Abbreviation_former(?:_\d+)?_en$")
ABBREVIATION_OTHER_RE = re.compile(r"^Abbreviation_other(?:_\d+)?_en$")


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"error: input file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise SystemExit("error: YAML root must be a mapping")
    return data


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() == "null":
        return ""
    return text


def first_letter(text: str) -> str:
    cleaned = text.lstrip("\"'")
    if not cleaned:
        return "#"
    char = cleaned[0].upper()
    return char if char.isalpha() else "#"


def add_entry(
    entries: list[dict[str, str]],
    seen: set[tuple[str, str, str]],
    org_name: str,
    label: str,
    entry_type: str,
) -> None:
    normalized_label = normalize_text(label)
    if not normalized_label:
        return

    dedupe_key = (org_name.casefold(), normalized_label.casefold(), entry_type)
    if dedupe_key in seen:
        return
    seen.add(dedupe_key)

    entries.append(
        {
            "label": normalized_label,
            "org_name": org_name,
            "entry_type": entry_type,
        }
    )


def collect_entries(data: dict[str, Any]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for top_level_name, props in data.items():
        org_name = normalize_text(top_level_name)
        if not org_name:
            continue

        record = props if isinstance(props, dict) else {}
        canonical_name = normalize_text(record.get("Name_en")) or org_name
        add_entry(entries, seen, canonical_name, canonical_name, "Current name")

        for key, value in record.items():
            if NAME_FORMER_RE.fullmatch(key):
                add_entry(entries, seen, canonical_name, value, "Former name")
            elif NAME_OTHER_RE.fullmatch(key):
                add_entry(entries, seen, canonical_name, value, "Other name")
            elif ABBREVIATION_RE.fullmatch(key):
                add_entry(entries, seen, canonical_name, value, "Abbreviation")
            elif ABBREVIATION_FORMER_RE.fullmatch(key):
                add_entry(entries, seen, canonical_name, value, "Former abbreviation")
            elif ABBREVIATION_OTHER_RE.fullmatch(key):
                add_entry(entries, seen, canonical_name, value, "Other abbreviation")

    return sorted(
        entries,
        key=lambda item: (
            item["label"].casefold(),
            item["org_name"].casefold(),
            item["entry_type"].casefold(),
        ),
    )


def build_content(data: dict[str, Any]) -> str:
    entries = collect_entries(data)
    groups: dict[str, list[dict[str, str]]] = {}
    for entry in entries:
        groups.setdefault(first_letter(entry["label"]), []).append(entry)

    letters = sorted(groups.keys())
    lines: list[str] = [
        "# Extended alphabetical list of English names, former names, other names and abbreviations",
        "",
        '<div id="top"></div>',
        "",
        "This list includes current English names, former English names, other English names, and English abbreviations found in `general_list.yaml`.",
        "",
    ]
    lines.append(" | ".join(f"[{letter}](#{letter.lower()})" for letter in letters))
    lines.append("")
    lines.append("---")
    lines.append("")

    for letter in letters:
        lines.append(f"## {letter}")
        lines.append("")
        for entry in groups[letter]:
            if entry["label"] == entry["org_name"] and entry["entry_type"] == "Current name":
                lines.append(f"- {entry['label']}")
            else:
                lines.append(
                    f"- {entry['label']} ({entry['entry_type']}: {entry['org_name']})"
                )
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
