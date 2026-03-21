#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Add/update 'RIAD_code' in general_list.yaml from ECB mapping CSV"
    )
    p.add_argument(
        "--mapping-file",
        default="data/ECB data/AnaCredit to SupraVerden code mapping file.csv",
        help="Path to mapping CSV (repo-relative by default)",
    )
    p.add_argument(
        "--list-file",
        default="data/general_list.yaml",
        help="Path to general_list YAML (repo-relative by default)",
    )
    p.add_argument("--write", action="store_true", help="Write changes (default: dry-run)")
    return p.parse_args()


def load_mapping(path: Path) -> dict[str, str]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    header_i = next(
        i for i, r in enumerate(rows) if r and r[0].strip() == "International organisation name in AnaCredit data"
    )
    h = rows[header_i]
    idx_name = h.index("SupraVerden Name_en")
    idx_ana = h.index("AnaCredit counterparty identifier")
    idx_sprvd = h.index("SPRVD_id")
    idx_mapped = h.index("Mapped Y/N") if "Mapped Y/N" in h else None

    out: dict[str, str] = {}
    for r in rows[header_i + 1 :]:
        if not r:
            continue
        max_i = max(idx_name, idx_ana, idx_sprvd, idx_mapped or 0)
        while len(r) <= max_i:
            r.append("")
        name = r[idx_name].strip()
        ana = r[idx_ana].strip()
        sprvd = r[idx_sprvd].strip()
        mapped = r[idx_mapped].strip().upper() if idx_mapped is not None else "Y"
        if not name or not ana or not sprvd:
            continue
        if mapped != "Y":
            continue
        out.setdefault(name, ana)
    return out


def update_lines(lines: list[str], name_to_ana: dict[str, str]) -> tuple[list[str], int, int]:
    out: list[str] = []
    i = 0
    inserted = 0
    updated = 0

    while i < len(lines):
        line = lines[i]
        if line and not line.startswith(" ") and line.rstrip().endswith(":"):
            out.append(line)
            i += 1

            block: list[str] = []
            while i < len(lines):
                nxt = lines[i]
                if nxt and not nxt.startswith(" ") and nxt.rstrip().endswith(":"):
                    break
                block.append(nxt)
                i += 1

            name_idx = None
            name_val = ""
            ana_idx = None
            os_idx = None

            for bi, b in enumerate(block):
                s = b.strip()
                if s.startswith("Name_en:"):
                    name_idx = bi
                    name_val = s.split(":", 1)[1].strip()
                elif s.startswith("OpenSanctions_id:"):
                    os_idx = bi
                elif s.startswith("RIAD_code:"):
                    ana_idx = bi

            target = name_to_ana.get(name_val)
            if target:
                new_line = f"  RIAD_code: {target}\n"
                if ana_idx is not None:
                    cur = block[ana_idx].strip().split(":", 1)[1].strip()
                    if cur != target:
                        block[ana_idx] = new_line
                        updated += 1
                else:
                    if os_idx is not None:
                        block.insert(os_idx + 1, new_line)
                    elif name_idx is not None:
                        block.insert(name_idx + 1, new_line)
                    else:
                        block.append(new_line)
                    inserted += 1

            out.extend(block)
            continue

        out.append(line)
        i += 1

    return out, inserted, updated


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    mapping_file = (root / args.mapping_file).resolve()
    list_file = (root / args.list_file).resolve()

    name_to_ana = load_mapping(mapping_file)
    original = list_file.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)

    new_lines, inserted, updated = update_lines(lines, name_to_ana)
    new_text = "".join(new_lines)

    changed = new_text != original
    print(f"matched mapped names: {len(name_to_ana)}")
    print(f"inserted: {inserted}")
    print(f"updated: {updated}")
    print(f"changed: {'yes' if changed else 'no'}")

    if args.write and changed:
        list_file.write_text(new_text, encoding="utf-8")
        print(f"wrote: {list_file}")
    elif not args.write:
        print("dry-run only (use --write to apply)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
