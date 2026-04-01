#!/usr/bin/env python3
"""Generate dist/LIST_OF_KEYS.md from selected YAML data files.

Variant handling is driven primarily by _variant_policy in data_dictionary.yaml.
"""

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
    parser.add_argument(
        "--dict-file",
        default="data/data_dictionary.yaml",
        help="YAML data dictionary used for variant policy",
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


def parse_variant_policy(
    dict_data: Any, default_language_suffixes: set[str]
) -> tuple[set[str], set[str], set[str]]:
    language_suffixes = set(default_language_suffixes)
    index_suffixes: set[str] = set()
    variant_bases: set[str] = set()

    if not isinstance(dict_data, dict):
        return language_suffixes, index_suffixes, variant_bases

    raw = dict_data.get("_variant_policy")
    if not isinstance(raw, dict):
        return language_suffixes, index_suffixes, variant_bases

    language_source_file = raw.get("language_source_file")
    if isinstance(language_source_file, str) and language_source_file.strip():
        source_path = resolve_path(language_source_file.strip())
        if source_path.exists():
            language_suffixes = load_language_suffixes(source_path)

    language_suffixes_raw = raw.get("language_suffixes")
    if isinstance(language_suffixes_raw, list) and language_suffixes_raw:
        language_suffixes = {
            str(item).strip().lower()
            for item in language_suffixes_raw
            if str(item).strip()
        }

    indexes_raw = raw.get("index_suffixes")
    if isinstance(indexes_raw, list):
        index_suffixes = {str(item).strip() for item in indexes_raw if str(item).strip()}

    applies_to_raw = raw.get("applies_to")
    if isinstance(applies_to_raw, list):
        variant_bases = {str(item).strip() for item in applies_to_raw if str(item).strip()}

    return language_suffixes, index_suffixes, variant_bases


def attach_to_tree(tree: dict[str, Any], parts: list[str]) -> None:
    head = parts[0]
    if head not in tree:
        tree[head] = {"_children": {}}

    if len(parts) > 1:
        attach_to_tree(tree[head]["_children"], parts[1:])
    else:
        tree[head]["_is_key"] = True


def split_key(
    key: str,
    language_suffixes: set[str],
    index_suffixes: set[str],
    variant_bases: set[str],
) -> list[str]:
    if key in EXCEPTIONS:
        return [key]

    if "_" not in key:
        return [key]

    parts = key.split("_")

    # <base>_<n>_<lang>
    if len(parts) >= 3:
        base = "_".join(parts[:-2])
        idx = parts[-2]
        lang = parts[-1].lower()
        if (
            base in variant_bases
            and idx in index_suffixes
            and lang in language_suffixes
        ):
            return [base, idx, lang]

    # <base>_<lang>_<n>
    if len(parts) >= 3:
        base = "_".join(parts[:-2])
        lang = parts[-2].lower()
        idx = parts[-1]
        if (
            base in variant_bases
            and lang in language_suffixes
            and idx in index_suffixes
        ):
            return [base, lang, idx]

    stem, suffix = key.rsplit("_", 1)
    if stem == "Source" and suffix in SOURCE_INDEX_SUFFIXES:
        return [stem, suffix]
    if stem in variant_bases and suffix in index_suffixes:
        return [stem, suffix]
    if stem in variant_bases and suffix.lower() in language_suffixes:
        return [stem, suffix.lower()]
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
    dict_data = load_yaml(resolve_path(args.dict_file))
    language_suffixes, index_suffixes, variant_bases = parse_variant_policy(
        dict_data, language_suffixes
    )
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
        attach_to_tree(
            key_tree,
            split_key(key, language_suffixes, index_suffixes, variant_bases),
        )

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(generate_lines(key_tree)) + "\n", encoding="utf-8")
    print(f"Successfully wrote {len(unique_keys)} keys to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
