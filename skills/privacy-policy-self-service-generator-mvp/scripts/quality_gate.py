#!/usr/bin/env python3
"""Quality gate for privacy-policy-drafter artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


TEXT_EXTENSIONS = {".md", ".yaml", ".yml", ".json", ".txt"}

REQUIRED_SKILL_FILES = [
    "README.md",
    "LICENSE",
    "COMMERCIAL-LICENSE.md",
    "docs/launch-post.md",
    "assets/wechat-xiarenzhimajuan.jpg",
    "assets/youdian-zhineng-shiwusuo-qrcode.jpg",
    "SKILL.md",
    "agents/openai.yaml",
    "references/privacy-policy-requirements.md",
    "references/minimum-compliance-version.md",
    "references/ai-privacy-points.md",
    "references/aigc-domain-examples.md",
    "references/legal-article-review.md",
    "references/clause-writing-requirements.md",
    "references/benchmark-policy-learning.md",
    "references/disclaimer-requirements.md",
    "references/legal-basis-boundaries.md",
    "references/app-processing-method-errors.md",
    "references/platform-channel-requirements.md",
    "references/mini-program-privacy-guide.md",
    "references/terminology.md",
    "templates/product-questionnaire.md",
    "templates/disclaimer-template.md",
    "templates/minimum-compliance-template.md",
    "templates/review-report.md",
    "scripts/quality_gate.py",
    "scripts/privacy_requirements_gate.py",
    "scripts/legal_matrix.py",
    "scripts/validate_policy_inputs.py",
    "scripts/merge_without_overwrite.py",
]

PLACEHOLDER_PATTERNS = {
    "braced token": re.compile(r"\{\{[^}\n]{1,100}\}\}"),
    "angle token": re.compile(r"<<[^>\n]{1,100}>>"),
    "editor marker": re.compile(r"\b(?:" + "TO" + "DO|TB" + "D|FIX" + "ME" + r")\b", re.IGNORECASE),
    "Chinese fill marker": re.compile("待" + "补" + "充|待" + "确" + "认|请" + "填" + "写|待" + "定"),
    "blank underline": re.compile(r"_{3,}"),
}

BANNED_TERMS = {
    "数据控制者": "个人信息处理者",
    "信息控制者": "个人信息处理者",
    "用户主体": "个人信息主体",
    "数据主体": "个人信息主体",
    "敏感信息": "敏感个人信息",
    "跨国传输": "跨境传输",
    "委外处理": "委托处理",
    "信息泄露事件": "个人信息安全事件",
}


@dataclass
class Finding:
    check: str
    path: str
    line: int
    message: str


def iter_text_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix in TEXT_EXTENSIONS else []
    files: list[Path] = []
    for path in sorted(target.rglob("*")):
        if path.is_file() and path.suffix in TEXT_EXTENSIONS:
            files.append(path)
    return files


def read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig").splitlines()


def check_placeholders(target: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_text_files(target):
        for line_no, line in enumerate(read_lines(path), start=1):
            for name, pattern in PLACEHOLDER_PATTERNS.items():
                if pattern.search(line):
                    findings.append(
                        Finding(
                            "placeholder residue scan",
                            str(path),
                            line_no,
                            f"{name} remains in text",
                        )
                    )
    return findings


def check_terms(target: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_text_files(target):
        if path.name == "terminology.md":
            continue
        for line_no, line in enumerate(read_lines(path), start=1):
            for banned, preferred in BANNED_TERMS.items():
                if banned in line:
                    findings.append(
                        Finding(
                            "terminology consistency check",
                            str(path),
                            line_no,
                            f"use '{preferred}' instead of '{banned}'",
                        )
                    )
    return findings


def check_structure(target: Path) -> list[Finding]:
    if not target.is_dir() or not (target / "SKILL.md").exists():
        return []
    findings: list[Finding] = []
    for relative in REQUIRED_SKILL_FILES:
        path = target / relative
        if not path.is_file():
            findings.append(
                Finding(
                    "file structure completeness check",
                    str(path),
                    0,
                    "required file is missing",
                )
            )
    return findings


def summarize(findings: list[Finding], target: Path) -> dict[str, object]:
    checks = {
        "placeholder residue scan": "PASS",
        "terminology consistency check": "PASS",
        "file structure completeness check": "PASS",
    }
    if not target.is_dir() or not (target / "SKILL.md").exists():
        checks["file structure completeness check"] = "NOT_APPLICABLE"
    for finding in findings:
        checks[finding.check] = "FAIL"
    return {
        "target": str(target),
        "checks": checks,
        "findings": [finding.__dict__ for finding in findings],
        "passed": not findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run privacy agreement quality gates.")
    parser.add_argument("--target", required=True, help="File or skill folder to validate.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.exists():
        print(f"Target does not exist: {target}", file=sys.stderr)
        return 2

    findings = []
    findings.extend(check_placeholders(target))
    findings.extend(check_terms(target))
    findings.extend(check_structure(target))
    result = summarize(findings, target)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for name, status in result["checks"].items():
            print(f"[{status}] {name}")
        for finding in findings:
            location = f"{finding.path}:{finding.line}" if finding.line else finding.path
            print(f"- {location}: {finding.message}")

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
