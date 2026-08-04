#!/usr/bin/env python3
"""Static workflow smoke test for one platform-lite legal Skill package."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    profile = json.loads((root / "PACKAGE-PROFILE.json").read_text(encoding="utf-8"))
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    prompts = json.loads(
        (root / "tests" / "route-prompts.json").read_text(encoding="utf-8")
    )
    errors: list[str] = []

    for marker in profile.get("workflow_markers", []):
        if marker not in skill:
            errors.append(f"missing workflow marker {marker}")

    identifiers = [case.get("id") for case in prompts.get("cases", [])]
    if len(identifiers) != len(set(identifiers)):
        errors.append("duplicate route-test id")

    required_behaviors = set(profile.get("required_route_behaviors", []))
    prompt_text = json.dumps(prompts, ensure_ascii=False)
    for behavior in required_behaviors:
        if behavior not in prompt_text:
            errors.append(f"route tests do not exercise {behavior}")

    linked_paths = re.findall(r"\[[^\]]+\]\(([^)]+)\)", skill)
    missing_links: list[str] = []
    for linked in linked_paths:
        if "://" in linked or linked.startswith("#"):
            continue
        clean = linked.split("#", 1)[0]
        if clean and not (root / clean).exists():
            missing_links.append(linked)
    if missing_links:
        errors.append(f"SKILL.md has missing local links: {sorted(missing_links)}")

    python_files = sorted(root.rglob("*.py"))
    for path in python_files:
        relative = path.relative_to(root).as_posix()
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except SyntaxError as exc:
            errors.append(f"Python syntax failure {relative}: {exc}")

    result = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "checks": {
            "workflow_marker_count": len(profile.get("workflow_markers", [])),
            "route_case_count": len(prompts.get("cases", [])),
            "required_route_behavior_count": len(required_behaviors),
            "resolved_local_link_count": len(linked_paths) - len(missing_links),
            "python_syntax_file_count": len(python_files),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
