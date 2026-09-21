#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
TOOLS = {
    "yuandian_law_vector_zq_search",
    "yuandian_rh_ft_zq_search",
    "yuandian_rh_fg_zq_search",
    "yuandian_rh_ssgsgg_search",
    "yuandian_rh_zqcfws_search",
}


def die(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    text = SKILL.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not match:
        die("SKILL.md must begin with YAML frontmatter")
    frontmatter = yaml.safe_load(match.group(1))
    if not isinstance(frontmatter, dict):
        die("frontmatter must be a mapping")
    if frontmatter.get("name") != ROOT.name:
        die("frontmatter name must match the package directory")
    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.startswith("Use when"):
        die("description must start with 'Use when'")
    metadata = frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        die("metadata mapping is required")
    if metadata.get("version") != "1.2.0":
        die("metadata.version must be 1.2.0")
    if not metadata.get("compatibility"):
        die("metadata.compatibility is required")

    required_files = (
        "references/mcp-onboarding.md",
        "references/tool-contract.md",
        "references/deployment-notes.md",
        "tests/acceptance-cases.md",
        "scripts/yuandian_mcp_probe.py",
        "MCP_LIVE_SIGNOFF.md",
    )
    for rel in required_files:
        if not (ROOT / rel).is_file():
            die(f"missing support file: {rel}")

    contract = (ROOT / "references/tool-contract.md").read_text(encoding="utf-8")
    missing = sorted(tool for tool in TOOLS if f"`{tool}`" not in contract)
    if missing:
        die(f"missing securities tools: {', '.join(missing)}")
    docs = text + contract + (ROOT / "references/mcp-onboarding.md").read_text(encoding="utf-8")
    if "https://open.chineselaw.com/mcp/securities/stream" not in docs:
        die("public securities MCP endpoint is missing")

    print("PASS")
    print("version=1.2.0")
    print("securities_tools=5")
    print("support_files=present")


if __name__ == "__main__":
    main()
