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

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "SupraverdenBot/1.0 (github.com/confirmordeny/supraverden)"
QCODE_RE = re.compile(r"^Q\d+$")
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
    return parser.parse_args()


def batched(values: list[str], size: int) -> list[str]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def fetch_wikidata_batch(q_codes: list[str]) -> dict[str, dict[str, str | None]]:
    values_clause = " ".join(f"wd:{code}" for code in q_codes)
    query = f"""
    SELECT ?item
           (SAMPLE(?id) AS ?id)
           (SAMPLE(?name_fr) AS ?name_fr)
           (SAMPLE(?name_es) AS ?name_es)
           (SAMPLE(?name_de) AS ?name_de)
           (SAMPLE(?name_pt) AS ?name_pt)
           (SAMPLE(?name_ru) AS ?name_ru)
           (SAMPLE(?name_uk) AS ?name_uk)
           (SAMPLE(?name_zh) AS ?name_zh)
           (SAMPLE(?website) AS ?website)
    WHERE {{
      VALUES ?item {{ {values_clause} }}
      OPTIONAL {{ ?item wdt:P10632 ?id . }}
      OPTIONAL {{ ?item rdfs:label ?name_fr . FILTER(LANG(?name_fr) = "fr") }}
      OPTIONAL {{ ?item rdfs:label ?name_es . FILTER(LANG(?name_es) = "es") }}
      OPTIONAL {{ ?item rdfs:label ?name_de . FILTER(LANG(?name_de) = "de") }}
      OPTIONAL {{ ?item rdfs:label ?name_pt . FILTER(LANG(?name_pt) = "pt") }}
      OPTIONAL {{ ?item rdfs:label ?name_ru . FILTER(LANG(?name_ru) = "ru") }}
      OPTIONAL {{ ?item rdfs:label ?name_uk . FILTER(LANG(?name_uk) = "uk") }}
      OPTIONAL {{ ?item rdfs:label ?name_zh . FILTER(LANG(?name_zh) = "zh") }}
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
                    results[q_code] = {
                        "os_id": row.get("id", {}).get("value"),
                        "name_fr": row.get("name_fr", {}).get("value"),
                        "name_es": row.get("name_es", {}).get("value"),
                        "name_de": row.get("name_de", {}).get("value"),
                        "name_pt": row.get("name_pt", {}).get("value"),
                        "name_ru": row.get("name_ru", {}).get("value"),
                        "name_uk": row.get("name_uk", {}).get("value"),
                        "name_zh": row.get("name_zh", {}).get("value"),
                        "website": row.get("website", {}).get("value"),
                    }
                return results
            if response.status_code in (429, 500, 502, 503, 504):
                time.sleep(attempt * 2.0)
                continue
            return {}
        except requests.RequestException:
            time.sleep(attempt * 2.0)
    return {}


def process_single_file(path: Path) -> bool:
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
            "Name_fr": "Name_fr" not in info,
            "Name_es": "Name_es" not in info,
            "Name_de": "Name_de" not in info,
            "Name_pt": "Name_pt" not in info,
            "Name_ru": "Name_ru" not in info,
            "Name_uk": "Name_uk" not in info,
            "Name_zh": "Name_zh" not in info,
            "Website": "Website" not in info,
        }

        if any(needs.values()):
            pending.append((info, w_code, needs))

    if not pending:
        return False

    q_codes = sorted({item[1] for item in pending})
    remote_by_qcode: dict[str, dict[str, str | None]] = {}
    for batch in batched(q_codes, BATCH_SIZE):
        remote_by_qcode.update(fetch_wikidata_batch(batch))
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
        if needs["Name_fr"] and remote.get("name_fr"):
            info["Name_fr"] = remote["name_fr"]
            changed = True
        if needs["Name_es"] and remote.get("name_es"):
            info["Name_es"] = remote["name_es"]
            changed = True
        if needs["Name_de"] and remote.get("name_de"):
            info["Name_de"] = remote["name_de"]
            changed = True
        if needs["Name_pt"] and remote.get("name_pt"):
            info["Name_pt"] = remote["name_pt"]
            changed = True
        if needs["Name_ru"] and remote.get("name_ru"):
            info["Name_ru"] = remote["name_ru"]
            changed = True
        if needs["Name_uk"] and remote.get("name_uk"):
            info["Name_uk"] = remote["name_uk"]
            changed = True
        if needs["Name_zh"] and remote.get("name_zh"):
            info["Name_zh"] = remote["name_zh"]
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
    any_updated = False
    for file_name in args.files:
        if process_single_file(Path(file_name)):
            any_updated = True

    if not any_updated:
        print("No changes found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
