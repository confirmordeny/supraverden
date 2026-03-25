#!/usr/bin/env python3
"""Enrich selected YAML files with fields fetched from Wikidata."""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path
from typing import Any

try:
    import requests
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("error: missing dependency (pip install pyyaml requests)") from exc

ROOT = Path(__file__).resolve().parents[1]
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "SupraverdenBot/1.0 (github.com/confirmordeny/supraverden)"
QCODE_RE = re.compile(r"^Q\d+$")
ISO_CODE_RE = re.compile(r"^[a-z]{2}$")
HEADER_RE = re.compile(r"^(\s*#.*|\s*\n)*")
BATCH_SIZE = 150
MAX_RETRIES = 3
BATCH_DELAY_SECONDS = 0.2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich local YAML with Wikidata fields")
    parser.add_argument(
        "--files",
        nargs="+",
        default=["data/general_list.yaml", "data/united_nations.yaml"],
        help="YAML files to enrich",
    )
    parser.add_argument(
        "--supported-languages-file",
        default="data/supported_languages/supported_languages.yaml",
        help="YAML file listing supported language ISO codes",
    )
    return parser.parse_args()


def batched(values: list[str], size: int) -> list[str]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return ROOT / path


def load_supported_language_codes(path: Path) -> list[str]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit(f"error: supported languages file root must be a mapping ({path})")

    languages = raw.get("languages")
    if not isinstance(languages, list):
        raise SystemExit(f"error: missing 'languages' list in supported languages file ({path})")

    codes: list[str] = []
    for index, item in enumerate(languages, start=1):
        if not isinstance(item, dict):
            raise SystemExit(f"error: languages[{index}] must be a mapping ({path})")
        code = str(item.get("iso_639_1", "")).strip().lower()
        if not ISO_CODE_RE.fullmatch(code):
            raise SystemExit(
                f"error: languages[{index}].iso_639_1 must be a two-letter lowercase code ({path})"
            )
        codes.append(code)
    return codes


def build_name_field_map(language_codes: list[str]) -> dict[str, str]:
    # Name_en remains curated in-repo; enrich only non-English language labels from Wikidata.
    return {f"Name_{code}": code for code in language_codes if code != "en"}


def fetch_wikidata_batch(
    q_codes: list[str], name_field_to_wikidata_lang: dict[str, str]
) -> dict[str, dict[str, str | None]]:
    values_clause = " ".join(f"wd:{code}" for code in q_codes)
    name_select = "\n".join(
        f'           (SAMPLE(?{field.lower()}) AS ?{field.lower()})'
        for field in name_field_to_wikidata_lang
    )
    name_optional = "\n".join(
        f'      OPTIONAL {{ ?item rdfs:label ?{field.lower()} . FILTER(LANG(?{field.lower()}) = "{lang}") }}'
        for field, lang in name_field_to_wikidata_lang.items()
    )
    query = f"""
    SELECT ?item
           (SAMPLE(?id) AS ?id)
{name_select}
           (SAMPLE(?website) AS ?website)
    WHERE {{
      VALUES ?item {{ {values_clause} }}
      OPTIONAL {{ ?item wdt:P10632 ?id . }}
{name_optional}
      OPTIONAL {{ ?item wdt:P856 ?website . }}
    }}
    GROUP BY ?item
    """

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                WIKIDATA_ENDPOINT,
                params={"format": "json", "query": query},
                headers={"User-Agent": USER_AGENT},
                timeout=60,
            )
            if response.status_code == 200:
                rows = response.json().get("results", {}).get("bindings", [])
                results: dict[str, dict[str, str | None]] = {}
                for row in rows:
                    item_uri = row.get("item", {}).get("value", "")
                    q_code = item_uri.rsplit("/", 1)[-1]
                    if not QCODE_RE.match(q_code):
                        continue
                    row_result: dict[str, str | None] = {
                        "os_id": row.get("id", {}).get("value"),
                        "website": row.get("website", {}).get("value"),
                    }
                    for field in name_field_to_wikidata_lang:
                        variable = field.lower()
                        row_result[variable] = row.get(variable, {}).get("value")
                    results[q_code] = row_result
                return results
            if response.status_code in (429, 500, 502, 503, 504):
                time.sleep(attempt * 2.0)
                continue
            return {}
        except requests.RequestException:
            time.sleep(attempt * 2.0)
    return {}


def process_single_file(path: Path, name_field_to_wikidata_lang: dict[str, str]) -> bool:
    print(f"Checking {path}...")
    if not path.exists():
        print(f"Skipping missing file: {path}")
        return False

    original_content = path.read_text(encoding="utf-8")
    header_match = HEADER_RE.match(original_content)
    header_block = header_match.group(0) if header_match else ""

    try:
        data = yaml.safe_load(original_content)
    except yaml.YAMLError as exc:
        print(f"Failed to parse {path}: {exc}")
        return False

    if not isinstance(data, dict):
        print(f"Skipping non-mapping YAML root in {path}")
        return False

    pending: list[tuple[dict[str, Any], str, dict[str, bool]]] = []
    for info in data.values():
        if not isinstance(info, dict) or "Wikidata_code" not in info:
            continue

        w_code = str(info["Wikidata_code"]).replace("[", "").replace("]", "").strip()
        if not QCODE_RE.match(w_code):
            continue

        needs = {
            "OpenSanctions_id": "OpenSanctions_id" not in info,
            "Website": "Website" not in info,
        }
        for field in name_field_to_wikidata_lang:
            needs[field] = field not in info

        if any(needs.values()):
            pending.append((info, w_code, needs))

    if not pending:
        return False

    q_codes = sorted({item[1] for item in pending})
    remote_by_qcode: dict[str, dict[str, str | None]] = {}
    for batch in batched(q_codes, BATCH_SIZE):
        remote_by_qcode.update(fetch_wikidata_batch(batch, name_field_to_wikidata_lang))
        time.sleep(BATCH_DELAY_SECONDS)

    updates_count = 0
    for info, w_code, needs in pending:
        remote = remote_by_qcode.get(w_code, {})
        if not remote:
            continue

        changed = False
        if needs["OpenSanctions_id"] and remote.get("os_id"):
            info["OpenSanctions_id"] = remote["os_id"]
            changed = True
        for field in name_field_to_wikidata_lang:
            if needs[field]:
                value = remote.get(field.lower())
                if value:
                    info[field] = value
                    changed = True
        if needs["Website"] and remote.get("website"):
            info["Website"] = remote["website"]
            changed = True

        if changed:
            updates_count += 1

    if updates_count == 0:
        return False

    print(f"Saving {updates_count} updates to {path}...")
    with path.open("w", encoding="utf-8") as handle:
        handle.write(header_block)
        yaml.dump(
            data,
            handle,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=1000,
        )
    return True


def main() -> int:
    args = parse_args()
    language_codes = load_supported_language_codes(resolve_path(args.supported_languages_file))
    name_field_to_wikidata_lang = build_name_field_map(language_codes)

    any_updated = False
    for file_name in args.files:
        if process_single_file(Path(file_name), name_field_to_wikidata_lang):
            any_updated = True

    if not any_updated:
        print("No changes found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
