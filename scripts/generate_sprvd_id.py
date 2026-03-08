#!/usr/bin/env python3
"""Generate unique SPRVD IDs.

Format:
- Prefix: SPRVD0
- Payload: 5 random digits
- Check digit: 1 digit, computed from payload
"""

from __future__ import annotations

import argparse
import random
import re
import sys
from pathlib import Path

PREFIX = "SPRVD0"
ID_RE = re.compile(r"^SPRVD0\d{6}$")


def compute_check_digit(payload5: str) -> int:
    if len(payload5) != 5 or not payload5.isdigit():
        raise ValueError("payload must be exactly 5 digits")
    total = sum(int(d) * (6 - i) for i, d in enumerate(payload5, start=1))
    return total % 10


def build_id(payload5: str) -> str:
    return f"{PREFIX}{payload5}{compute_check_digit(payload5)}"


def collect_existing_ids(path: Path, key: str) -> set[str]:
    if not path.exists():
        return set()

    pattern = re.compile(rf"^\s*{re.escape(key)}:\s*(\S+)\s*$")
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            value = match.group(1)
            if ID_RE.match(value):
                ids.add(value)
    return ids


def generate_unique_ids(count: int, existing: set[str]) -> list[str]:
    if count < 1:
        raise ValueError("count must be >= 1")
    if len(existing) + count > 100000:
        raise ValueError("not enough remaining ID space")

    results: set[str] = set()
    while len(results) < count:
        payload = f"{random.randrange(0, 100000):05d}"
        candidate = build_id(payload)
        if candidate not in existing and candidate not in results:
            results.add(candidate)
    return list(results)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate random SPRVD IDs with check digits")
    parser.add_argument("--count", type=int, default=1, help="number of IDs to generate")
    parser.add_argument(
        "--exclude-file",
        default="data/general_list.yaml",
        help="file to scan for existing IDs to avoid",
    )
    parser.add_argument(
        "--key",
        default="SPRVD_id",
        help="YAML key name containing IDs in --exclude-file",
    )
    parser.add_argument("--seed", type=int, default=None, help="optional random seed")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    try:
        existing = collect_existing_ids(Path(args.exclude_file), args.key)
        generated = generate_unique_ids(args.count, existing)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for value in generated:
        print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
