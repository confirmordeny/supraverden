#!/usr/bin/env python3
"""Generate dist/DATA_DICTIONARY.md from data/data_dictionary.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("error: missing dependency PyYAML (pip install pyyaml)") from exc


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "data_dictionary.yaml"
OUTPUT_PATH = ROOT / "dist" / "DATA_DICTIONARY.md"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise SystemExit("error: dictionary root must be a mapping")
    return data


def load_supported_language_codes(path: Path) -> list[str]:
    data = load_yaml(path)
    raw_languages = data.get("languages")
    if not isinstance(raw_languages, list):
        raise SystemExit(f"error: supported languages file must contain a 'languages' list ({path})")

    codes: list[str] = []
    for item in raw_languages:
        if not isinstance(item, dict):
            continue
        code = str(item.get("iso_639_1", "")).strip().lower()
        if code:
            codes.append(code)
    return codes


def resolve_support_file_path(source: str) -> Path:
    candidate = Path(source)
    if candidate.is_absolute():
        return candidate
    return ROOT / candidate


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return "`" + yaml.safe_dump(value, sort_keys=False).strip().replace("\n", " ") + "`"
    return str(value)


def field_anchor(name: str) -> str:
    return f"field-{name.lower()}"


def build_policy_table(title: str, data: dict[str, Any]) -> list[str]:
    lines = [f"## {title}", "", "| Key | Value |", "| --- | --- |"]
    for key, value in data.items():
        lines.append(f"| `{key}` | {format_value(value)} |")
    lines.append("")
    return lines


def build_field_section(field_name: str, meta: dict[str, Any]) -> list[str]:
    lines: list[str] = [f'<a id="{field_anchor(field_name)}"></a>', f"## `{field_name}`", ""]
    lines.extend(["| Attribute | Value |", "| --- | --- |"])

    ordered_keys = [
        "Title",
        "Data_type",
        "Minimum_length",
        "Maximum_length",
        "Requirement",
        "Description",
        "Multi_value",
        "Permissible values",
        "Validation_summary",
        "Example_source",
        "Examples",
    ]

    seen: set[str] = set()
    for key in ordered_keys:
        if key in meta:
            lines.append(f"| `{key}` | {format_value(meta.get(key))} |")
            seen.add(key)

    for key, value in meta.items():
        if key in seen or key == "Validation_rules":
            continue
        lines.append(f"| `{key}` | {format_value(value)} |")

    if "Validation_rules" in meta:
        lines.append(
            f"| `Validation_rules` | `{yaml.safe_dump(meta['Validation_rules'], sort_keys=False).strip().replace(chr(10), ' ')}` |"
        )

    lines.append("")
    return lines


def main() -> int:
    data = load_yaml(INPUT_PATH)

    record_policy = data.get("_record_policy", {})
    variant_policy = data.get("_variant_policy", {})
    if isinstance(variant_policy, dict):
        source = variant_policy.get("language_source_file")
        if isinstance(source, str) and source.strip():
            source_path = resolve_support_file_path(source.strip())
            variant_policy = {
                **variant_policy,
                "language_suffixes": load_supported_language_codes(source_path),
            }

    field_names = [k for k in data.keys() if not k.startswith("_")]

    lines: list[str] = [
        "# Data Dictionary",
        "",
        "## Field Index",
        "",
    ]

    for name in field_names:
        lines.append(f"- [`{name}`](#{field_anchor(name)})")
    lines.append("")

    if isinstance(record_policy, dict) and record_policy:
        lines.extend(build_policy_table("Record Policy", record_policy))
    if isinstance(variant_policy, dict) and variant_policy:
        lines.extend(build_policy_table("Variant Policy", variant_policy))

    for field_name in field_names:
        meta = data.get(field_name)
        if not isinstance(meta, dict):
            continue
        lines.extend(build_field_section(field_name, meta))

    OUTPUT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
