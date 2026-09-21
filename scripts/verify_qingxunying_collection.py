#!/usr/bin/env python3
"""Verify the 2026 Tianchi Juntai youth-camp collection and topic page."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
PAGE = ROOT / "docs" / "tcjtl-ai-legal-camp-2026.html"
HOME = ROOT / "docs" / "index.html"
INDEX = ROOT / "index" / "skills-index.json"

GROUPS = {
    "第一组": ("gdpr-policy-converter", "legal-research-report"),
    "第二组": ("client-background-report", "unfamiliar-business-onboarding"),
    "第三组": ("client-scope-pro", "labor-termination-cost-comparator"),
    "第四组": ("major-issue-due-diligence-checklist", "labor-law-expert"),
    "第五组": ("ad-compliance-lawyer", "client-due-diligence"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_skill(slug: str) -> None:
    folder = SKILLS / slug
    entry = folder / "SKILL.md"
    require(entry.is_file(), f"missing skill entrypoint: {slug}/SKILL.md")
    text = entry.read_text(encoding="utf-8")
    require(text.startswith("---\n"), f"missing frontmatter: {slug}")
    frontmatter = text.split("---", 2)[1]
    require(bool(re.search(rf"^name:\s*{re.escape(slug)}\s*$", frontmatter, re.M)),
            f"frontmatter name must match folder: {slug}")
    require(bool(re.search(r"^description:\s*\S|^description:\s*[>|]", frontmatter, re.M)),
            f"missing description: {slug}")
    packaging_noise = [
        path.relative_to(folder)
        for path in folder.rglob("*")
        if path.name == ".DS_Store" or path.suffix == ".pyc" or path.name.startswith(".~")
    ]
    require(not packaging_noise, f"packaging noise in {slug}: {packaging_noise}")


def main() -> None:
    slugs = tuple(slug for group in GROUPS.values() for slug in group)
    for slug in slugs:
        validate_skill(slug)

    require(PAGE.is_file(), "missing topic page")
    page = PAGE.read_text(encoding="utf-8")
    for group, group_slugs in GROUPS.items():
        require(group in page, f"topic page missing {group}")
        for slug in group_slugs:
            require(f"skill.html?f={slug}" in page, f"topic page missing link: {slug}")
    require(not re.search(r"(?<!\d)1[3-9]\d{9}(?!\d)", page),
            "topic page must not expose mobile numbers")

    records = json.loads(INDEX.read_text(encoding="utf-8"))
    indexed = {record["folder"] for record in records}
    require(len(records) >= 2086, f"expected at least 2086 indexed skills, got {len(records)}")
    require(set(slugs) <= indexed, f"collection missing from index: {set(slugs) - indexed}")

    home = HOME.read_text(encoding="utf-8")
    require('class="event-banner"' in home, "homepage missing event banner")
    require('href="./tcjtl-ai-legal-camp-2026.html"' in home,
            "homepage event banner missing topic-page link")
    require(home.index('class="event-banner"') < home.index('<section class="browse">'),
            "event banner must appear immediately before Browse Skills")

    common = (ROOT / "docs" / "assets" / "common.js").read_text(encoding="utf-8")
    require("./tcjtl-ai-legal-camp-2026.html" not in common,
            "event topic must not occupy the global navigation")
    print("PASS: 10 youth-camp skills, topic page, privacy guard, index, and homepage banner")


if __name__ == "__main__":
    main()
