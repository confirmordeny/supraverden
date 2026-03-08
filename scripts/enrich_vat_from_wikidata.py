#!/usr/bin/env python3
"""Enrich VAT_number values from Wikidata (P3608) using Wikidata_code (Qxxx)."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

try:
    import requests
    import yaml
except ImportError as exc:  # pragma: no cover
    print("error: missing dependencies (pip install requests pyyaml)", file=sys.stderr)
    raise SystemExit(2) from exc


WIKIDATA_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "supraverden-vat-enricher/1.0 (github.com/confirmordeny/supraverden)"
QCODE_PREFIX = "Q"
VAT_PROPERTY = "P3608"  # EU VAT number


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate VAT_number from Wikidata P3608 using Wikidata_code."
    )
    parser.add_argument(
        "--input-file",
        default="data/general_list.yaml",
        help="YAML file containing top-level records",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite existing VAT_number values",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="do not write changes, only report what would change",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.2,
        help="delay between API requests",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def save_yaml(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        yaml.dump(
            data,
            handle,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=1000,
        )


def normalize_qcode(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text.startswith(QCODE_PREFIX):
        return None
    if len(text) < 2 or not text[1:].isdigit():
        return None
    return text


def extract_vat_numbers(entity: dict[str, Any]) -> list[str]:
    claims = entity.get("claims")
    if not isinstance(claims, dict):
        return []
    raw = claims.get(VAT_PROPERTY)
    if not isinstance(raw, list):
        return []

    seen: set[str] = set()
    values: list[str] = []
    for statement in raw:
        if not isinstance(statement, dict):
            continue
        mainsnak = statement.get("mainsnak")
        if not isinstance(mainsnak, dict):
            continue
        datavalue = mainsnak.get("datavalue")
        if not isinstance(datavalue, dict):
            continue
        value = datavalue.get("value")
        if not isinstance(value, str):
            continue
        val = value.strip()
        if not val or val in seen:
            continue
        seen.add(val)
        values.append(val)
    return values


def get_vat_numbers(qcode: str) -> list[str]:
    params = {
        "action": "wbgetentities",
        "ids": qcode,
        "props": "claims",
        "format": "json",
    }
    response = requests.get(
        WIKIDATA_API,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    entities = payload.get("entities")
    if not isinstance(entities, dict):
        return []
    entity = entities.get(qcode)
    if not isinstance(entity, dict):
        return []
    return extract_vat_numbers(entity)


def should_skip_existing(value: Any, overwrite: bool) -> bool:
    if overwrite:
        return False
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, list):
        return any(str(v).strip() for v in value)
    return True


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_file)

    try:
        data = load_yaml(input_path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except yaml.YAMLError as exc:
        print(f"error: invalid YAML in '{input_path}': {exc}", file=sys.stderr)
        return 1

    if not isinstance(data, dict):
        print("error: YAML root must be a mapping", file=sys.stderr)
        return 1

    records = 0
    with_qcode = 0
    updated = 0
    failed = 0

    for org_name, record in data.items():
        records += 1
        if not isinstance(record, dict):
            continue

        qcode = normalize_qcode(record.get("Wikidata_code"))
        if not qcode:
            continue
        with_qcode += 1

        if should_skip_existing(record.get("VAT_number"), args.overwrite):
            continue

        try:
            vats = get_vat_numbers(qcode)
            time.sleep(max(args.sleep_seconds, 0.0))
        except requests.RequestException as exc:
            failed += 1
            print(f"warn: {org_name}: failed to fetch {qcode}: {exc}", file=sys.stderr)
            continue

        if not vats:
            continue

        record["VAT_number"] = vats if len(vats) > 1 else vats[0]
        updated += 1

    print(f"records: {records}")
    print(f"records with Wikidata_code: {with_qcode}")
    print(f"updated VAT_number: {updated}")
    print(f"fetch failures: {failed}")

    if args.dry_run:
        print("dry-run: no file written")
        return 0

    if updated > 0:
        save_yaml(input_path, data)
        print(f"saved: {input_path}")
    else:
        print("no changes to write")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
