#!/usr/bin/env python3
"""Generate dist/ALL_BODIES.md from data/general_list.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("error: missing dependency PyYAML (pip install pyyaml)") from exc


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "general_list.yaml"
OUTPUT_PATH = ROOT / "dist" / "ALL_BODIES.md"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"error: input file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise SystemExit("error: YAML root must be a mapping")
    return data


def escape_cell(text: str) -> str:
    return text.replace("|", "\\|")


def source_display(org: dict[str, Any]) -> str:
    treaty_url = org.get("Treaty_url")
    source = org.get("Source")

    if isinstance(treaty_url, str) and treaty_url.strip():
        return f"[Treaty]({treaty_url.strip()})"
    if not isinstance(source, str) or not source.strip():
        return "N/A"
    src = source.strip()
    if "un_system_chart" in src:
        return "[UN system chart](https://www.un.org/en/delegate/page/un-system-chart)"
    if "fao.org/unfao/govbodies" in src:
        return "[Statutory Bodies by subject matter](https://www.fao.org/unfao/govbodies/gsb-subject-matter/subject-matter/en/)"
    if src.startswith("http"):
        domain = src.split("//", 1)[-1].split("/", 1)[0]
        return f"[{domain}]({src})"
    return "N/A"


def os_display(org: dict[str, Any]) -> str:
    raw = str(org.get("OpenSanctions_id", "")).strip("'").strip('"').strip()
    if raw == "[No code found.]":
        return "[No code found.]"
    if not raw:
        return "N/A"
    return f"[{raw}](https://www.opensanctions.org/entities/{raw}/)"


def wikidata_display(org: dict[str, Any]) -> str:
    code = str(org.get("Wikidata_code", "")).strip()
    if not code.startswith("Q"):
        return "N/A"
    return f"[{code}](https://www.wikidata.org/wiki/{code})"


def build_content(data: dict[str, Any]) -> str:
    organizations: list[dict[str, Any]] = []
    for org_name, props in data.items():
        row = {"_main_name": str(org_name)}
        if isinstance(props, dict):
            row.update(props)
        organizations.append(row)

    organizations.sort(
        key=lambda x: (str(x.get("Name_en") or x.get("_main_name") or "")).lower()
    )
    count = len(organizations)

    lines = [
        "# All Supranational Bodies",
        "",
        f"There are currently {count} international organisations in the table.",
        "",
        "| English Name | Wikidata Code | OpenSanctions | Family | Source |",
        "|---|---|---|---|---|",
    ]

    for org in organizations:
        name = str(org.get("Name_en") or org.get("_main_name") or "N/A")
        family = str(org.get("Org_family") or "N/A")
        lines.append(
            "| "
            + " | ".join(
                [
                    escape_cell(name),
                    wikidata_display(org),
                    os_display(org),
                    escape_cell(family),
                    source_display(org),
                ]
            )
            + " |"
        )

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
