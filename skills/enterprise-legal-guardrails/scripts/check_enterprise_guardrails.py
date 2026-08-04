#!/usr/bin/env python3
"""
Enterprise Legal Guardrails

Deterministic, dependency-free pre-publish risk scan for outgoing bot actions.
No external services, no network, no model calls.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Set


@dataclass
class Rule:
    id: str
    title: str
    details: str
    severity: int
    patterns: List[str]
    tags: Set[str]


RULES: List[Rule] = [
    Rule(
        id="legal_advice",
        title="Legal conclusion or legal advice",
        details="Text appears to state legal conclusions as definitive guidance.",
        severity=5,
        tags={"legal", "core"},
        patterns=[
            r"\b(under\s+the\s+law|according\s+to\s+law|legal\s+ruling)\b",
            r"\b(sue|lawsuit|litigate|litigation|court\s+filing|indict|jurisdiction)\b",
            r"\b(illegal|illegality|it\s+is\s+illegal)\b",
            r"\b(i\s+am\s+not\s+your\s+lawyer)\b",
        ],
    ),
    Rule(
        id="defamation",
        title="Potential defamation or reputational allegation",
        details="Named allegations are presented as fact without evidentiary framing.",
        severity=5,
        tags={"defamation", "social", "core"},
        patterns=[
            r"\b(scam|scammer|fraud|fraudulent|con\s+artist|imposter)\b",
            r"\b(stole|steals|stealing|stolen|embezzled|fraudulently)\b",
            r"\b(false|fake|manipulat|fraud)\s+(post|claim|thread|announcement|statement)\b",
            r"\b(the\s+fraud\b|the\s+liar\b|a\s+shill|deceptive\s+actor)\b",
        ],
    ),
    Rule(
        id="financial_promissory",
        title="Financial certainty / guaranteed outcome",
        details="Content uses guarantees or certainty around returns, results, or outcomes.",
        severity=3,
        tags={"financial", "market", "core"},
        patterns=[
            r"\b(guaranteed\s+(profit|gain|return|win)|100%\s+(win|sure|guaranteed))\b",
            r"\b(will\s+definitely|is\s+certainly|100%\s+certain|no\s+risk)\b",
            r"\b(this\s+is\s+guaranteed|you\s+cannot\s+lose|certain\s+outcome)\b",
        ],
    ),
    Rule(
        id="market_manipulation",
        title="Market manipulation framing",
        details="Language suggests coordination, manipulation, or suppression/pump instructions.",
        severity=4,
        tags={"market", "core"},
        patterns=[
            r"\b(pump\s+and\s+dump|wash\s+trade|spoof|rig\s+market|bot\s+farm)\b",
            r"\b(coordinate\s+with\s+(us|everyone|friends)|everyone\s+to\s+buy|everyone\s+to\s+sell)\b",
            r"\b(create\s+chaos\s+for\s+price|short\s+squeeze\s+trick)\b",
        ],
    ),
    Rule(
        id="antispam",
        title="Antispam / coercive urgency patterns",
        details="Appears to use manipulative urgency, repeated coercive calls to action, or non-consensual promotional pressure.",
        severity=3,
        tags={"antispam", "social"},
        patterns=[
            r"\b(act\s+now\b|last\s+chance|one\s+time\s+offer|limited\s+spots|urgent\s+action\s+required)\b",
            r"\b(click\s+here\s+now|DM\s+me|private\s+message\s+for\s+access|send\s+me\s+wallet)\b",
            r"\b(guaranteed\s+income|quick\s+cash|make\s+money\s+fast|free\s+access\s+link)\b",
        ],
    ),
    Rule(
        id="harassment",
        title="Harassment or targeted abuse",
        details="Direct threats, harassment tone, or abusive targeting.",
        severity=5,
        tags={"social", "hr", "core"},
        patterns=[
            r"\b(hack\s+their|dox|kill\s+their|report\s+them\s+to\s+laws|send\s+this\s+to\s+their\s+employer)\b",
            r"\b(you\s+all\s+are\s+cowards|idiots|scum|trash|frauds)\b",
            r"\b(whistle\s+on\s+\w+|expose\s+\w+)\b",
        ],
    ),
    Rule(
        id="privacy",
        title="Privacy / sensitive personal data",
        details="Potential disclosure of personal identifying information.",
        severity=4,
        tags={"privacy", "core"},
        patterns=[
            r"\b(personal\s+address|phone\s+number|email\s+address|social\s+security|ssn|passport)\b",
            r"\b(\b\w+@\w+\.\w+\b|\+?\d{10,15})\b",
        ],
    ),
    Rule(
        id="hr_sensitivity",
        title="HR-sensitive workplace language",
        details="Potentially discrimination, retaliation, or employee-relations allegation language.",
        severity=4,
        tags={"hr", "social", "legal"},
        patterns=[
            r"\b(discriminate|discrimination|harassed\s+at\s+work|hostile\s+workplace)\b",
            r"\b(terminated\s+without\s+cause|fired\s+for\s+complaint|retaliat)\b",
            r"\b(bias\s+against|protected\s+class|sexual\s+harassment|wage\s+discrimination)\b",
        ],
    ),
]


REWRITES = [
    (re.compile(r"\bguaranteed\b", re.IGNORECASE), "not guaranteed"),
    (re.compile(r"\bno\s+risk\b", re.IGNORECASE), "risk exists"),
    (re.compile(r"\b100%\s+certain\b", re.IGNORECASE), "highly likely"),
    (re.compile(r"\b100%\s+chance\b", re.IGNORECASE), "strong probability"),
    (re.compile(r"\blegal\s+advice\b", re.IGNORECASE), "informational analysis"),
    (re.compile(r"\babsolutely\b", re.IGNORECASE), "very likely"),
]


DEFAULT_PROFILES = {
    "post": ["social", "legal"],
    "comment": ["social", "legal"],
    "message": ["social", "legal"],
    "trade": ["market", "financial"],
    "market-analysis": ["market", "financial", "legal"],
    "generic": ["legal", "social"],
}

PROFILE_CHOICES = {"social", "antispam", "hr", "privacy", "market", "financial", "legal", "core", "defamation"}


SCOPE_CHOICES = {"all", "include", "exclude"}

DEFAULT_REVIEW_THRESHOLD = 5
DEFAULT_BLOCK_THRESHOLD = 9




def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def _get_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value
    return None


def _get_env_bool(*names: str, default: bool) -> bool:
    raw = _get_env(*names)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "off", "no"}


def _split_list(raw: str | None) -> List[str]:
    if not raw:
        return []
    return [value.strip().lower() for value in raw.split(",") if value.strip()]


def _get_env_int(*names: str, default: int) -> int:
    raw = _get_env(*names)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _normalize_thresholds(review_threshold: int, block_threshold: int) -> tuple[int, int]:
    normalized_review = max(review_threshold, 0)
    normalized_block = max(block_threshold, normalized_review + 1)

    if normalized_block <= normalized_review:
        normalized_block = normalized_review + 1

    return normalized_review, normalized_block


def _normalize_scope(value: str | None) -> str:
    normalized = _normalize(value)
    if normalized not in SCOPE_CHOICES:
        return "all"
    return normalized


def _normalize_app_targets(values: Sequence[str] | None) -> List[str]:
    if not values:
        return []
    normalized: List[str] = []
    for value in values:
        normalized.extend(_split_list(value))
    return list(dict.fromkeys([_normalize(v) for v in normalized if _normalize(v)]))


def _should_apply_for_app(action_app: str | None, scope: str, app_targets: Sequence[str]) -> bool:
    normalized_app = _normalize(action_app)
    if not normalized_app or scope == "all":
        return True

    app_set = {_normalize(app) for app in app_targets}
    if scope == "include":
        return normalized_app in app_set

    if scope == "exclude":
        return normalized_app not in app_set

    return True


def _effective_policies(raw_policies: Sequence[str] | None, action: str) -> List[str]:
    if raw_policies:
        merged = [p.lower() for p in raw_policies]
    else:
        merged = list(DEFAULT_PROFILES.get(action, ["legal", "social"]))

    merged.append("core")
    seen = []
    for profile in merged:
        if profile and profile not in seen:
            seen.append(profile)
    return seen


def _load_text(args_text: str | None, file_path: str | None) -> str:
    if args_text:
        return args_text.strip()
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def _analyze(text: str, action: str, profiles: List[str], review_threshold: int, block_threshold: int) -> Dict:
    lowered = text.lower()
    selected_profiles = set(profiles)
    score = 0
    findings = []

    for rule in RULES:
        if not (set(rule.tags) & selected_profiles):
            continue

        hits: List[str] = []
        for pattern in rule.patterns:
            for match in re.finditer(pattern, lowered, flags=0):
                hits.append(match.group(0))

        if hits:
            score += rule.severity
            findings.append(
                {
                    "rule": rule.id,
                    "title": rule.title,
                    "details": rule.details,
                    "severity": rule.severity,
                    "matches": sorted(set(hits)),
                    "tags": sorted(rule.tags),
                }
            )

    if action in {"trade", "market-analysis", "market"} and re.search(r"\bguarantee\b|\bguaranteed\b", lowered):
        score += 1
        findings.append(
            {
                "rule": "market_confidence_boost",
                "title": "Trading certainty claim",
                "details": "Market outcomes should be expressed probabilistically.",
                "severity": 2,
                "matches": ["guarantee in market context"],
                "tags": ["market", "financial"],
            }
        )

    if action in {"message", "comment", "post"} and re.search(r"\bdm\b|direct\s+message\b", lowered):
        score = max(score - 1, 0)

    if not findings:
        status = "PASS"
    elif score >= block_threshold:
        status = "BLOCK"
    elif score >= review_threshold:
        status = "REVIEW"
    else:
        status = "WATCH"

    safe_text = text
    for pattern, replacement in REWRITES:
        safe_text = pattern.sub(replacement, safe_text)

    suggestions = []
    if status in {"WATCH", "REVIEW", "BLOCK"}:
        suggestions.extend(
            [
                "Replace absolute statements with probability language (likely, probable, indicative).",
                "Avoid naming a specific person as a wrongdoer without a documented source.",
                "Do not request/encourage coordinated action for trading or manipulation outcomes.",
                "Use policy-safe workplace phrasing for HR-related content.",
                "Never include sensitive personal details (emails/phone/ID numbers).",
            ]
        )

    return {
        "status": status,
        "action": action,
        "score": score,
        "findings_count": len(findings),
        "findings": findings,
        "original_text": text,
        "safe_text": safe_text if safe_text != text else text,
        "suggestions": suggestions,
        "policy": "PASS = execute, WATCH = optional cleanup, REVIEW = manual review, BLOCK = do not execute",
        "thresholds": {
            "review": review_threshold,
            "block": block_threshold,
        },
    }


def analyze_text(
    text: str,
    action: str,
    policies: Sequence[str] | None = None,
    app: str | None = None,
    scope: str = "all",
    app_targets: Sequence[str] | None = None,
    enabled: bool = True,
    review_threshold: int | None = None,
    block_threshold: int | None = None,
) -> Dict:
    profile_list = _effective_policies(policies, action)
    normalized_scope = _normalize_scope(scope)

    normalized_review = DEFAULT_REVIEW_THRESHOLD if review_threshold is None else review_threshold
    normalized_block = DEFAULT_BLOCK_THRESHOLD if block_threshold is None else block_threshold
    review_threshold, block_threshold = _normalize_thresholds(normalized_review, normalized_block)

    if not enabled:
        return {
            "status": "PASS",
            "action": action,
            "profiles": profile_list,
            "score": 0,
            "findings_count": 0,
            "findings": [],
            "app": app,
            "scope": {
                "mode": normalized_scope,
                "apps": list(app_targets or []),
                "applied": False,
            },
            "thresholds": {
                "review": review_threshold,
                "block": block_threshold,
            },
            "original_text": text,
            "safe_text": text,
            "suggestions": [],
            "policy": "Guardrails disabled",
        }

    if not _should_apply_for_app(app, normalized_scope, list(app_targets or [])):
        return {
            "status": "PASS",
            "action": action,
            "profiles": profile_list,
            "score": 0,
            "findings_count": 0,
            "findings": [],
            "app": app,
            "scope": {
                "mode": normalized_scope,
                "apps": list(app_targets or []),
                "applied": False,
            },
            "thresholds": {
                "review": review_threshold,
                "block": block_threshold,
            },
            "original_text": text,
            "safe_text": text,
            "suggestions": ["Guardrails did not run for this app due scope settings."],
            "policy": "PASS = execute (scope excluded)",
        }

    report = _analyze(text, action, profile_list, review_threshold=review_threshold, block_threshold=block_threshold)
    report["profiles"] = profile_list
    report["app"] = app
    report["scope"] = {
        "mode": normalized_scope,
        "apps": list(app_targets or []),
        "applied": True,
    }
    return report


def render_text(report: Dict) -> str:
    lines = [
        f"status: {report['status']}",
        f"action: {report['action']}",
        f"app: {report.get('app') or 'unspecified'}",
    ]

    scope_info = report.get("scope", {})
    lines.append(f"scope: {scope_info.get('mode', 'all')}")
    if scope_info.get("mode") in {"include", "exclude"}:
        lines.append(f"scope apps: {', '.join(scope_info.get('apps', [])) or '(none)'}")

    if report.get("profiles"):
        lines.append(f"profiles: {', '.join(report['profiles'])}")

    lines.extend(
        [
            f"score: {report['score']}",
            f"findings: {report['findings_count']}",
            f"thresholds: review={report.get('thresholds', {}).get('review', 'n/a')} block={report.get('thresholds', {}).get('block', 'n/a')}",
        ]
    )

    for finding in report["findings"]:
        lines.append(f"- [{finding['rule']}] {finding['title']} (sev {finding['severity']})")
        if finding.get("tags"):
            lines.append(f"  tags: {', '.join(finding['tags'])}")
        lines.append(f"  {finding['details']}")
        lines.append(f"  matches: {', '.join(finding['matches'])}")

    if report["suggestions"]:
        lines.append("\nSuggestions:")
        for item in report["suggestions"]:
            lines.append(f"- {item}")

    if report["safe_text"] != report["original_text"]:
        lines.append(f"safe_text: {report['safe_text']}")

    lines.append(f"\n{report['policy']}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run enterprise legal guardrail checks on draft bot output.")
    parser.add_argument(
        "--action",
        default="generic",
        choices=["post", "comment", "message", "trade", "market-analysis", "generic"],
        help="Action profile",
    )
    parser.add_argument(
        "--policies",
        nargs="+",
        choices=sorted(PROFILE_CHOICES),
        help="Policy families to enforce explicitly (space-separated).",
    )
    parser.add_argument(
        "--app",
        default=_normalize(_get_env(
            "ENTERPRISE_LEGAL_GUARDRAILS_APP",
            "ELG_APP",
            "BABYLON_APP",
        )),
        help="Optional app context for outbound filtering (e.g., babylon, whatsapp, email).",
    )
    parser.add_argument(
        "--scope",
        default=_normalize(_get_env(
            "ENTERPRISE_LEGAL_GUARDRAILS_OUTBOUND_SCOPE",
            "ELG_OUTBOUND_SCOPE",
            "BABYLON_GUARDRAILS_SCOPE",
            "BABYLON_GUARDRAILS_OUTBOUND_SCOPE",
        )),
        help="Scope mode for app-level filtering: all|include|exclude. (default: all)",
    )
    parser.add_argument(
        "--apps",
        nargs="*",
        default=_split_list(_get_env(
            "ENTERPRISE_LEGAL_GUARDRAILS_OUTBOUND_APPS",
            "ENTERPRISE_LEGAL_GUARDRAILS_APPS",
            "ELG_OUTBOUND_APPS",
            "BABYLON_GUARDRAILS_APPS",
        )),
        help="App names used with scope mode when include|exclude (comma/space separated list).",
    )
    parser.add_argument(
        "--review-threshold",
        type=int,
        default=None,
        help="Override review threshold (default from env/default config).",
    )
    parser.add_argument(
        "--block-threshold",
        type=int,
        default=None,
        help="Override block threshold (default from env/default config).",
    )
    parser.add_argument("--text", default="", help="Text content to analyze")
    parser.add_argument("--file", default="", help="Optional file path for content")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument(
        "--no-guard",
        action="store_true",
        help="Skip guardrail logic regardless of scope/inputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    text = _load_text(args.text if args.text else None, args.file if args.file else None)
    if not text:
        print("No text provided. Use --text, --file, or pipe text via stdin.", file=sys.stderr)
        return 1

    enabled = _get_env_bool(
        "ENTERPRISE_LEGAL_GUARDRAILS_ENABLED",
        "ELG_ENABLED",
        "BABYLON_GUARDRAILS_ENABLED",
        default=True,
    )

    app_targets = _normalize_app_targets(args.apps)
    review_threshold = _get_env_int(
        "ENTERPRISE_LEGAL_GUARDRAILS_REVIEW_THRESHOLD",
        "ELG_REVIEW_THRESHOLD",
        "BABYLON_GUARDRAILS_REVIEW_THRESHOLD",
        default=DEFAULT_REVIEW_THRESHOLD,
    )
    block_threshold = _get_env_int(
        "ENTERPRISE_LEGAL_GUARDRAILS_BLOCK_THRESHOLD",
        "ELG_BLOCK_THRESHOLD",
        "BABYLON_GUARDRAILS_BLOCK_THRESHOLD",
        default=DEFAULT_BLOCK_THRESHOLD,
    )

    if args.review_threshold is not None:
        review_threshold = args.review_threshold
    if args.block_threshold is not None:
        block_threshold = args.block_threshold

    review_threshold, block_threshold = _normalize_thresholds(review_threshold, block_threshold)

    report = analyze_text(
        text,
        args.action,
        args.policies,
        app=args.app,
        scope=_normalize_scope(args.scope),
        app_targets=app_targets,
        enabled=enabled and not args.no_guard,
        review_threshold=review_threshold,
        block_threshold=block_threshold,
    )

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))

    return 0 if report["status"] in {"PASS", "WATCH"} else (1 if report["status"] == "REVIEW" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
