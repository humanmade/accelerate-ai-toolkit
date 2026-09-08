#!/usr/bin/env python3
"""Check the checked-in Accelerate contract snapshot, optionally against producer PHP."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = ROOT / "contracts" / "accelerate-abilities-92503f9.json"
REFERENCE_FILES = (
    ROOT / "docs" / "ability-reference.md",
    ROOT / "skills" / "accelerate-abilities-reference" / "SKILL.md",
)
SEMANTIC_CONTRACT = {
    "accelerate/get-site-context": {
        "input_enums": {"blocks": ["none", "styled", "all"]},
    },
    "accelerate/get-experiment-results": {
        "one_of_inputs": ["block_id", "experiment_id"],
    },
    "accelerate/create-ab-test": {
        "paired_inputs": ["expected_content_hash", "request_id"],
        "source_markers": ["expected_content_hash and request_id must be supplied together"],
    },
}


def matching_bracket(text: str, start: int) -> int:
    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(start, len(text)):
        character = text[index]
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if character in {"'", '"'}:
            quote = character
        elif character == "[":
            depth += 1
        elif character == "]":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("unclosed PHP array")


def array_for_key(block: str, key: str) -> str:
    match = re.search(rf"'{re.escape(key)}'\s*=>\s*\[", block)
    if not match:
        return ""
    start = block.index("[", match.start())
    return block[start + 1 : matching_bracket(block, start)]


def top_level_keys(array: str) -> list[str]:
    keys: list[str] = []
    depth = 0
    quote: str | None = None
    escaped = False
    line_start = True
    for index, character in enumerate(array):
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if line_start and depth == 0:
            match = re.match(r"[ \t]*'([^']+)'\s*=>", array[index:])
            if match:
                keys.append(match.group(1))
        if character in {"'", '"'}:
            quote = character
        elif character == "[":
            depth += 1
        elif character == "]":
            depth -= 1
        line_start = character == "\n"
    return keys


def top_level_arrays(array: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    depth = 0
    quote: str | None = None
    escaped = False
    line_start = True
    for index, character in enumerate(array):
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if line_start and depth == 0:
            match = re.match(r"[ \t]*'([^']+)'\s*=>\s*\[", array[index:])
            if match:
                start = index + match.end() - 1
                entries[match.group(1)] = array[start + 1 : matching_bracket(array, start)]
        if character in {"'", '"'}:
            quote = character
        elif character == "[":
            depth += 1
        elif character == "]":
            depth -= 1
        line_start = character == "\n"
    return entries


def output_field_paths(output_schema: str) -> list[str]:
    paths: list[str] = []

    def visit(properties: str, prefix: str) -> None:
        for name, definition in top_level_arrays(properties).items():
            path = f"{prefix}{name}"
            paths.append(path)
            items = array_for_key(definition, "items")
            item_properties = array_for_key(items, "properties")
            if item_properties:
                visit(item_properties, f"{path}[].")
                continue
            nested = array_for_key(definition, "properties")
            if nested:
                visit(nested, f"{path}.")

    visit(array_for_key(output_schema, "properties"), "")
    return paths


def required_inputs(input_schema: str) -> list[str]:
    required = top_level_arrays(input_schema).get("required", "")
    return re.findall(r"'([^']+)'", required)


def schema_value(definition: str, key: str) -> str | list[str] | None:
    match = re.search(rf"'{re.escape(key)}'\s*=>\s*", definition)
    if not match:
        return None
    start = match.end()
    if definition[start : start + 1] == "[":
        end = matching_bracket(definition, start)
        return re.findall(r"'([^']+)'", definition[start + 1 : end])
    scalar = re.match(r"'([^']+)'", definition[start:])
    return scalar.group(1) if scalar else None


def input_semantics(input_schema: str) -> dict[str, dict[str, str | list[str]]]:
    properties = top_level_arrays(array_for_key(input_schema, "properties"))
    semantics: dict[str, dict[str, str | list[str]]] = {}
    for name, definition in properties.items():
        field: dict[str, str | list[str]] = {}
        for key in ("type", "enum"):
            value = schema_value(definition, key)
            if value is not None:
                field[key] = value
        if field:
            semantics[name] = field
    return semantics


def extract_producer(producer: Path) -> dict[str, object]:
    abilities: dict[str, dict[str, object]] = {}
    for source in sorted((producer / "inc" / "abilities").glob("*.php")):
        text = source.read_text(encoding="utf-8")
        for match in re.finditer(r"wp_register_ability\(\s*'([^']+)'\s*,\s*\[", text):
            start = text.index("[", match.start())
            block = text[start + 1 : matching_bracket(text, start)]
            input_schema = array_for_key(block, "input_schema")
            output_schema = array_for_key(block, "output_schema")
            input_fields = top_level_keys(array_for_key(input_schema, "properties"))
            output_fields = output_field_paths(output_schema)
            permission = re.search(r"'permission_callback'\s*=>\s*([^,\n]+)", block)
            abilities[match.group(1)] = {
                "required_inputs": required_inputs(input_schema),
                "input_fields": input_fields,
                "input_semantics": input_semantics(input_schema),
                "output_fields": output_fields,
                "permission_callback": permission.group(1).strip() if permission else "",
            }
    if not abilities:
        raise ValueError(f"no Accelerate registrations found under {producer}")
    return {"abilities": dict(sorted(abilities.items()))}


def snapshot_from_producer(producer: Path, revision: str, companion_digest: str | None) -> dict[str, object]:
    snapshot = extract_producer(producer)
    snapshot["producer_base_revision"] = revision
    if companion_digest:
        snapshot["producer_companion_diff_sha256"] = companion_digest
    snapshot["semantic_contract"] = {
        name: contract for name, contract in SEMANTIC_CONTRACT.items() if name in snapshot["abilities"]
    }
    return snapshot


def differences(expected: dict[str, object], actual: dict[str, object]) -> list[str]:
    expected_abilities = expected["abilities"]
    actual_abilities = actual["abilities"]
    messages: list[str] = []
    for name in sorted(set(expected_abilities) - set(actual_abilities)):
        messages.append(f"missing registered ability: {name}")
    for name in sorted(set(actual_abilities) - set(expected_abilities)):
        messages.append(f"unexpected registered ability: {name}")
    for name in sorted(set(expected_abilities) & set(actual_abilities)):
        for field in ("required_inputs", "input_fields", "input_semantics", "output_fields", "permission_callback"):
            if field in expected_abilities[name] and expected_abilities[name][field] != actual_abilities[name][field]:
                messages.append(
                    f"{name} {field} changed: expected {expected_abilities[name][field]!r}; "
                    f"found {actual_abilities[name][field]!r}"
                )
    return messages


def semantic_differences(snapshot: dict[str, object], producer: Path) -> list[str]:
    messages: list[str] = []
    abilities = extract_producer(producer)["abilities"]
    source = "\n".join(path.read_text(encoding="utf-8") for path in (producer / "inc" / "abilities").glob("*.php"))
    for name, contract in snapshot.get("semantic_contract", {}).items():
        ability = abilities.get(name)
        if not ability:
            messages.append(f"semantic contract references missing ability: {name}")
            continue
        for field, expected_enum in contract.get("input_enums", {}).items():
            found = ability["input_semantics"].get(field, {}).get("enum")
            if found != expected_enum:
                messages.append(f"{name} {field} enum changed: expected {expected_enum!r}; found {found!r}")
        for rule in ("one_of_inputs", "paired_inputs"):
            required = contract.get(rule, [])
            missing = [field for field in required if field not in ability["input_fields"]]
            if missing:
                messages.append(f"{name} {rule} missing inputs: {', '.join(missing)}")
        for marker in contract.get("source_markers", []):
            if marker not in source:
                messages.append(f"{name} semantic source marker missing: {marker}")
    return messages


def reference_differences(snapshot: dict[str, object]) -> list[str]:
    messages: list[str] = []
    ability_names = snapshot["abilities"]
    for reference in REFERENCE_FILES:
        content = reference.read_text(encoding="utf-8")
        missing = [name for name in ability_names if name not in content]
        if missing:
            messages.append(f"{reference.relative_to(ROOT)} omits: {', '.join(missing)}")
    return messages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--producer", type=Path)
    parser.add_argument("--revision", help="producer revision recorded when refreshing a snapshot")
    parser.add_argument("--companion-digest", help="SHA-256 of local producer ability changes included in a refresh")
    parser.add_argument("--write-snapshot", action="store_true")
    args = parser.parse_args()

    try:
        if args.write_snapshot:
            if not args.producer or not args.revision:
                raise ValueError("--write-snapshot requires --producer and --revision")
            rendered = snapshot_from_producer(args.producer, args.revision, args.companion_digest)
            args.snapshot.parent.mkdir(parents=True, exist_ok=True)
            args.snapshot.write_text(json.dumps(rendered, indent=2) + "\n", encoding="utf-8")
            print(f"Wrote {args.snapshot}")
            return 0

        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
        messages = reference_differences(snapshot)
        if args.producer:
            messages.extend(differences(snapshot, extract_producer(args.producer)))
            messages.extend(semantic_differences(snapshot, args.producer))
        if messages:
            print("Accelerate contract check failed:", file=sys.stderr)
            print("\n".join(f"- {message}" for message in messages), file=sys.stderr)
            return 1
        source = f" against {args.producer}" if args.producer else " (offline snapshot)"
        print(f"Accelerate contract check passed{source}: {len(snapshot['abilities'])} abilities.")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Accelerate contract check failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
