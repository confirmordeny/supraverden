#!/usr/bin/env python3
"""Generate dist/LIST_OF_KEYS.md from selected YAML data files."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("error: missing dependency PyYAML (pip install pyyaml)") from exc

ROOT = Path(__file__).resolve().parents[1]

EXCEPTIONS = {
    "Abbreviation_other",
    "Assessment_against_FATF_definition",
    "Basis_for_assessment",
    "Legal_type",
    "Entity_type",
    "Immunity_url",
    "Name_former",
    "Name_other",
    "Name_other_2",
    "Org_family",
    "OpenSanctions_id",
    "SPRVD_id",
    "Treaty_url",
    "Wikidata_code",
}
SOURCE_INDEX_SUFFIXES = {"1", "2", "3"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate list of keys markdown")
    parser.add_argument(
        "--input-files",
        nargs="+",
        default=["data/general_list.yaml", "data/united_nations.yaml"],
        help="Input YAML files",
    )
    parser.add_argument(
        "--output-file",
        default="dist/LIST_OF_KEYS.md",
        help="Output markdown file",
    )
    parser.add_argument(
        "--supported-languages-file",
        default="data/supported_languages/supported_languages.yaml",
        help="YAML file listing supported language ISO codes",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return ROOT / path


def load_language_suffixes(path: Path) -> set[str]:
    data = load_yaml(path)
    if not isinstance(data, dict):
        raise SystemExit(f"error: supported languages file root must be a mapping ({path})")
    languages = data.get("languages")
    if not isinstance(languages, list):
        raise SystemExit(f"error: missing 'languages' list in supported languages file ({path})")

    suffixes: set[str] = set()
    for item in languages:
        if not isinstance(item, dict):
            continue
        code = str(item.get("iso_639_1", "")).strip().lower()
        if code:
            suffixes.add(code)
    return suffixes


def attach_to_tree(tree: dict[str, Any], parts: list[str]) -> None:
    head = parts[0]
    if head not in tree:
        tree[head] = {"_children": {}}

    if len(parts) > 1:
        attach_to_tree(tree[head]["_children"], parts[1:])
    else:
        tree[head]["_is_key"] = True


def split_key(key: str, language_suffixes: set[str]) -> list[str]:
    if key in EXCEPTIONS:
        return [key]

    if "_" not in key:
        return [key]

    stem, suffix = key.rsplit("_", 1)
    if stem == "Source" and suffix in SOURCE_INDEX_SUFFIXES:
        return [stem, suffix]
    if suffix in language_suffixes and stem:
        return [stem, suffix]
    return [key]


def generate_lines(tree: dict[str, Any], depth: int = 0) -> list[str]:
    lines: list[str] = []
    for node_name in sorted(tree):
        indent = "  " * depth
        lines.append(f"{indent}* {node_name}")
        children = tree[node_name].get("_children", {})
        if children:
            lines.extend(generate_lines(children, depth + 1))
    return lines


def main() -> int:
    args = parse_args()
    language_suffixes = load_language_suffixes(resolve_path(args.supported_languages_file))
    unique_keys: set[str] = set()

    for file_path in args.input_files:
        path = Path(file_path)
        if not path.exists():
            print(f"Skipping missing file: {file_path}")
            continue

        data = load_yaml(path)
        if not isinstance(data, dict):
            print(f"Skipping non-mapping YAML root in: {file_path}")
            continue

        for record in data.values():
            if isinstance(record, dict):
                unique_keys.update(record.keys())

    key_tree: dict[str, Any] = {}
    for key in unique_keys:
        attach_to_tree(key_tree, split_key(key, language_suffixes))

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(generate_lines(key_tree)) + "\n", encoding="utf-8")
    print(f"Successfully wrote {len(unique_keys)} keys to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
