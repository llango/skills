#!/usr/bin/env python3
"""Lightweight structural validator for the mojo-reviewer skill."""

from __future__ import annotations

import json
import re
from pathlib import Path

SKILL_NAME = "mojo-reviewer"
MAX_DESCRIPTION_LEN = 420
MAX_COMPATIBILITY_LEN = 500
MAX_SKILL_LINES = 500
ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    skill_dir = Path(__file__).resolve().parent.parent
    skill_md = skill_dir / "SKILL.md"
    evals_path = skill_dir / "evals" / "evals.json"

    if not skill_md.exists():
        fail("missing SKILL.md")
    if not evals_path.exists():
        fail("missing evals/evals.json")

    skill_text = skill_md.read_text(encoding="utf-8")
    skill_lines = skill_text.splitlines()
    if len(skill_lines) > MAX_SKILL_LINES:
        fail(f"SKILL.md has {len(skill_lines)} lines; max is {MAX_SKILL_LINES}")

    frontmatter_match = re.match(r"^---\n(.*?)\n---\n", skill_text, re.DOTALL)
    if not frontmatter_match:
        fail("SKILL.md is missing YAML frontmatter")

    frontmatter = frontmatter_match.group(1)
    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
    description_match = re.search(
        r"^description:\s*(.+)$", frontmatter, re.MULTILINE
    )
    if not name_match:
        fail("SKILL.md frontmatter is missing name")
    if name_match.group(1).strip() != SKILL_NAME:
        fail(
            f"SKILL.md frontmatter name must be {SKILL_NAME!r}, "
            f"found {name_match.group(1).strip()!r}"
        )
    if not description_match:
        fail("SKILL.md frontmatter is missing description")
    description = description_match.group(1).strip()
    if len(description) > MAX_DESCRIPTION_LEN:
        fail(
            "SKILL.md description is too long: "
            f"{len(description)} chars; max is {MAX_DESCRIPTION_LEN}"
        )
    compatibility_match = re.search(
        r"^compatibility:\s*(.+)$", frontmatter, re.MULTILINE
    )
    if compatibility_match:
        compatibility = compatibility_match.group(1).strip()
        if len(compatibility) > MAX_COMPATIBILITY_LEN:
            fail(
                "SKILL.md compatibility is too long: "
                f"{len(compatibility)} chars; max is {MAX_COMPATIBILITY_LEN}"
            )
    metadata_present = re.search(r"^metadata:\s*$", frontmatter, re.MULTILINE)

    frontmatter_keys = set()
    for line in frontmatter.splitlines():
        if not line.strip():
            continue
        if not line.startswith(" ") and ":" not in line:
            fail(f"SKILL.md frontmatter line is not key/value YAML: {line!r}")
        if line.startswith(" "):
            if not metadata_present:
                fail(
                    "SKILL.md frontmatter contains an indented line without "
                    "a metadata block"
                )
            continue
        key, _ = line.split(":", 1)
        frontmatter_keys.add(key.strip())
    if "name" not in frontmatter_keys or "description" not in frontmatter_keys:
        fail("SKILL.md frontmatter must contain name and description")
    unknown_frontmatter_keys = sorted(frontmatter_keys - ALLOWED_FRONTMATTER_KEYS)
    if unknown_frontmatter_keys:
        fail(
            "SKILL.md frontmatter contains unsupported keys: "
            f"{unknown_frontmatter_keys!r}"
        )

    references = re.findall(r"`((?:references|agents|scripts)/[^`]+)`", skill_text)
    missing_refs = []
    for ref in references:
        path = skill_dir / ref
        if any(char in ref for char in "*?[]"):
            if not list(skill_dir.glob(ref)):
                missing_refs.append(ref)
        elif not path.exists():
            missing_refs.append(ref)
    if missing_refs:
        fail(f"SKILL.md references missing files: {', '.join(sorted(missing_refs))}")

    with evals_path.open(encoding="utf-8") as handle:
        evals_data = json.load(handle)

    if evals_data.get("skill_name") != SKILL_NAME:
        fail("evals/evals.json skill_name does not match folder name")

    evals = evals_data.get("evals")
    if not isinstance(evals, list) or not evals:
        fail("evals/evals.json must contain a non-empty evals list")

    ids = set()
    for entry in evals:
        if not isinstance(entry, dict):
            fail("each eval entry must be an object")
        entry_id = entry.get("id")
        if entry_id in ids:
            fail(f"duplicate eval id: {entry_id}")
        ids.add(entry_id)
        for key in ("prompt", "expected_output", "assertions", "category"):
            if key not in entry:
                fail(f"eval {entry_id} is missing {key}")
        assertions = entry["assertions"]
        if not isinstance(assertions, list) or not assertions:
            fail(f"eval {entry_id} must have a non-empty assertions list")

    suites = evals_data.get("suites")
    if not isinstance(suites, dict):
        fail("evals/evals.json must define suites")
    eval_ids = {
        entry.get("id") for entry in evals if isinstance(entry, dict) and "id" in entry
    }
    for key in ("forward_test_minimum", "trigger_boundary"):
        suite = suites.get(key)
        if not isinstance(suite, list) or not suite:
            fail(f"evals/evals.json suite {key!r} must be a non-empty list")
        unknown_ids = [value for value in suite if value not in eval_ids]
        if unknown_ids:
            fail(
                f"evals/evals.json suite {key!r} references unknown eval ids: "
                f"{unknown_ids}"
            )

    agents_yaml = skill_dir / "agents" / "openai.yaml"
    if agents_yaml.exists():
        agents_text = agents_yaml.read_text(encoding="utf-8")
        if not re.search(r"^interface:\s*$", agents_text, re.MULTILINE):
            fail("agents/openai.yaml must define interface")
        for key in ("display_name", "short_description", "default_prompt"):
            match = re.search(rf"^\s{{2}}{key}:\s*(.+)$", agents_text, re.MULTILINE)
            if not match or not match.group(1).strip():
                fail(f"agents/openai.yaml interface.{key} must be a non-empty string")
        if not re.search(r"^policy:\s*$", agents_text, re.MULTILINE):
            fail("agents/openai.yaml must define policy")
        allow_implicit = re.search(
            r"^\s{2}allow_implicit_invocation:\s*(true|false)\s*$",
            agents_text,
            re.MULTILINE,
        )
        if not allow_implicit:
            fail(
                "agents/openai.yaml policy.allow_implicit_invocation must be a boolean"
            )

    print("PASS: mojo-reviewer skill structure is valid")
    print(f"PASS: SKILL.md lines = {len(skill_lines)}")
    print(f"PASS: description chars = {len(description)}")
    print(f"PASS: eval count = {len(evals)}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover
        fail(f"unexpected error: {exc}")
