#!/usr/bin/env python3
"""Validate the canonical Codex skill frontmatter without external packages."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ALLOWED_TOP_LEVEL = {"name", "description", "license", "allowed-tools", "metadata"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TOP_LEVEL_KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s|$)")


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("SKILL.md frontmatter is not closed")
    block = text[4:end]
    values: dict[str, str] = {}
    keys: list[str] = []
    for line in block.splitlines():
        if not line or line[0].isspace() or line.lstrip().startswith("#"):
            continue
        match = TOP_LEVEL_KEY_RE.match(line)
        if not match:
            raise ValueError(f"invalid top-level frontmatter line: {line!r}")
        key = match.group(1)
        keys.append(key)
        values[key] = line.split(":", 1)[1].strip().strip('"\'')
    return values, keys


def validate(skill: Path) -> list[str]:
    skill_md = skill / "SKILL.md" if skill.is_dir() else skill
    errors: list[str] = []
    try:
        values, keys = parse_frontmatter(skill_md)
    except (OSError, UnicodeError, ValueError) as exc:
        return [str(exc)]
    duplicate = sorted({key for key in keys if keys.count(key) > 1})
    if duplicate:
        errors.append(f"duplicate top-level key(s): {duplicate}")
    unexpected = sorted(set(keys) - ALLOWED_TOP_LEVEL)
    if unexpected:
        errors.append(f"unexpected top-level key(s): {unexpected}")
    for required in ("name", "description"):
        if not values.get(required):
            errors.append(f"missing required top-level key: {required}")
    name = values.get("name", "")
    if name and (not NAME_RE.fullmatch(name) or len(name) > 64):
        errors.append("name must be lowercase hyphen-case and no longer than 64 characters")
    description = values.get("description", "")
    if len(description) > 1024:
        errors.append("description must be no longer than 1024 characters")
    if "<" in description or ">" in description:
        errors.append("description must not contain angle brackets")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", type=Path)
    args = parser.parse_args()
    errors = validate(args.skill)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"FAILED: {len(errors)} frontmatter error(s)", file=sys.stderr)
        return 1
    print("OK: canonical Codex frontmatter validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
