#!/usr/bin/env python3
"""Enrich VAT_number (P3608) and Website (P856) from Wikidata using Wikidata_code (Qxxx)."""

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
USER_AGENT = "supraverden-wikidata-enricher/1.0 (github.com/confirmordeny/supraverden)"
QCODE_PREFIX = "Q"
VAT_PROPERTY = "P3608"  # EU VAT number
WEBSITE_PROPERTY = "P856"  # official website
DEFAULT_BATCH_SIZE = 50
DEFAULT_MAX_RETRIES = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate VAT_number and Website from Wikidata using Wikidata_code."
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
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="number of Wikidata Q-codes to fetch per API request",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help="number of retries for recoverable API failures",
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


def extract_claim_string_values(entity: dict[str, Any], property_code: str) -> list[str]:
    claims = entity.get("claims")
    if not isinstance(claims, dict):
        return []
    raw = claims.get(property_code)
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
        if isinstance(value, str):
            val = value.strip()
        elif isinstance(value, dict):
            val = str(value.get("text", "")).strip()
        else:
            continue
        if not val or val in seen:
            continue
        seen.add(val)
        values.append(val)
    return values


def chunked(values: list[str], size: int) -> list[list[str]]:
    if size < 1:
        raise ValueError("batch-size must be >= 1")
    return [values[i : i + size] for i in range(0, len(values), size)]


def get_claim_values_batch(
    qcodes: list[str], max_retries: int
) -> tuple[dict[str, dict[str, list[str]]], set[str]]:
    if not qcodes:
        return {}, set()

    params = {
        "action": "wbgetentities",
        "ids": "|".join(qcodes),
        "props": "claims",
        "format": "json",
    }
    last_exc: Exception | None = None
    for attempt in range(1, max(max_retries, 1) + 1):
        try:
            response = requests.get(
                WIKIDATA_API,
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=30,
            )
            if response.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(
                    f"HTTP {response.status_code}", response=response
                )
            response.raise_for_status()
            payload = response.json()
            entities = payload.get("entities")
            if not isinstance(entities, dict):
                return {}, set()

            out: dict[str, dict[str, list[str]]] = {}
            for qcode in qcodes:
                entity = entities.get(qcode)
                if not isinstance(entity, dict):
                    out[qcode] = {"vat_numbers": [], "websites": []}
                    continue
                out[qcode] = {
                    "vat_numbers": extract_claim_string_values(entity, VAT_PROPERTY),
                    "websites": extract_claim_string_values(entity, WEBSITE_PROPERTY),
                }
            return out, set()
        except (requests.RequestException, ValueError) as exc:
            last_exc = exc
            if attempt < max(max_retries, 1):
                time.sleep(float(attempt))
    if last_exc is not None:
        print(
            f"warn: failed to fetch batch of {len(qcodes)} Q-codes: {last_exc}",
            file=sys.stderr,
        )
    return {}, set(qcodes)


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
    updated_vat = 0
    updated_website = 0
    failed = 0

    pending: list[tuple[str, dict[str, Any], str, bool, bool]] = []
    for org_name, record in data.items():
        records += 1
        if not isinstance(record, dict):
            continue

        qcode = normalize_qcode(record.get("Wikidata_code"))
        if not qcode:
            continue
        with_qcode += 1

        needs_vat = not should_skip_existing(record.get("VAT_number"), args.overwrite)
        needs_website = not should_skip_existing(record.get("Website"), args.overwrite)
        if not needs_vat and not needs_website:
            continue

        pending.append((org_name, record, qcode, needs_vat, needs_website))

    if pending:
        qcodes = sorted({qcode for _, _, qcode, _, _ in pending})
        remote_by_qcode: dict[str, dict[str, list[str]]] = {}
        failed_qcodes: set[str] = set()
        for batch in chunked(qcodes, args.batch_size):
            remote, failed_batch = get_claim_values_batch(batch, args.max_retries)
            remote_by_qcode.update(remote)
            failed_qcodes.update(failed_batch)
            time.sleep(max(args.sleep_seconds, 0.0))

        for org_name, record, qcode, needs_vat, needs_website in pending:
            if qcode in failed_qcodes:
                failed += 1
                print(f"warn: {org_name}: failed to fetch {qcode}", file=sys.stderr)
                continue

            remote = remote_by_qcode.get(qcode, {})
            vats = remote.get("vat_numbers") if isinstance(remote, dict) else []
            websites = remote.get("websites") if isinstance(remote, dict) else []

            if needs_vat and isinstance(vats, list) and vats:
                record["VAT_number"] = vats if len(vats) > 1 else vats[0]
                updated_vat += 1
            if needs_website and isinstance(websites, list) and websites:
                record["Website"] = websites[0]
                updated_website += 1

    print(f"records: {records}")
    print(f"records with Wikidata_code: {with_qcode}")
    print(f"updated VAT_number: {updated_vat}")
    print(f"updated Website: {updated_website}")
    print(f"fetch failures: {failed}")

    if args.dry_run:
        print("dry-run: no file written")
        return 0

    if updated_vat > 0 or updated_website > 0:
        save_yaml(input_path, data)
        print(f"saved: {input_path}")
    else:
        print("no changes to write")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
