#!/usr/bin/env python3
"""AI数据合规冷启动 Skill 配置独立校验。

校验 profile JSON 的结构完整性、版本合法性、文档编号唯一性、
无代码注入和负向边界。退出码：0 通过 / 5 失败。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from common import CONFIG_SCHEMA_VERSION, GATE_FIELDS_DEFAULT, WORD_DOCS_DEFAULT, FlowError, PROFILES, read_json

REQUIRED_KEYS = ["config_version", "id", "display_name", "roles", "p0_items", "risk_themes"]
SUPPORTED_VERSIONS = {"1.0", "1.1"}

# 禁止注入的可执行模式（用词边界避免误伤中文，如"评估"）
INJECTION_PATTERNS = [
    re.compile(r"\bimport\s+[A-Za-z_]", re.IGNORECASE),
    re.compile(r"\bsubprocess\b"),
    re.compile(r"\bos\.system\b"),
    re.compile(r"\beval\s*\("),
    re.compile(r"\bexec\s*\("),
    re.compile(r"__import__"),
    re.compile(r"`[^`]+`"),
    re.compile(r"\$\{"),
    re.compile(r"os\.popen"),
    re.compile(r"compile\s*\("),
    re.compile(r"getattr\s*\("),
    re.compile(r"globals\s*\("),
    re.compile(r"locals\s*\("),
]


def scan_injection(value, path: str, findings: list[str]) -> None:
    if isinstance(value, str):
        for pattern in INJECTION_PATTERNS:
            if pattern.search(value):
                findings.append(f"{path}: 疑似代码注入 '{pattern.pattern}'")
    elif isinstance(value, dict):
        for key, item in value.items():
            scan_injection(item, f"{path}.{key}", findings)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            scan_injection(item, f"{path}[{index}]", findings)


def validate_profile(profile: dict, profile_id: str) -> dict:
    checks: dict[str, bool] = {}
    details: dict[str, object] = {}

    missing = [key for key in REQUIRED_KEYS if key not in profile]
    checks["required_keys_present"] = not missing
    details["missing_keys"] = missing

    version = profile.get("config_version")
    checks["version_supported"] = isinstance(version, str) and version in SUPPORTED_VERSIONS
    details["config_version"] = version

    checks["id_matches_filename"] = profile.get("id") == profile_id
    details["id"] = profile.get("id")

    checks["display_name_string"] = isinstance(profile.get("display_name"), str) and bool(profile.get("display_name"))
    checks["roles_list_nonempty"] = isinstance(profile.get("roles"), list) and len(profile.get("roles", [])) > 0
    checks["p0_items_list_nonempty"] = isinstance(profile.get("p0_items"), list) and len(profile.get("p0_items", [])) > 0
    checks["risk_themes_list_nonempty"] = isinstance(profile.get("risk_themes"), list) and len(profile.get("risk_themes", [])) > 0

    checks["banned_terms_strings"] = isinstance(profile.get("banned_terms", []), list) and all(isinstance(t, str) for t in profile.get("banned_terms", []))
    checks["negative_boundary_nonempty"] = isinstance(profile.get("negative_boundary", []), list) and len(profile.get("negative_boundary", [])) > 0

    gate = profile.get("fact_gate_fields")
    if isinstance(gate, dict):
        checks["gate_fields_valid"] = bool(gate) and all(isinstance(k, str) and k and isinstance(v, str) for k, v in gate.items())
        details["gate_field_count"] = len(gate)
    else:
        checks["gate_fields_valid"] = False
        details["gate_field_count"] = 0

    doc_issues = []
    word_docs = profile.get("word_docs") or {}
    for group in ("startup", "candidate"):
        docs = word_docs.get(group) or []
        if not isinstance(docs, list):
            doc_issues.append(f"{group}: 非数组")
            continue
        seen = set()
        for index, doc in enumerate(docs):
            if not isinstance(doc, dict):
                doc_issues.append(f"{group}[{index}]: 非对象")
                continue
            no = doc.get("doc_no")
            title = doc.get("title")
            if no is None or str(no) == "":
                doc_issues.append(f"{group}[{index}]: 缺 doc_no")
            elif str(no) in seen:
                doc_issues.append(f"{group}[{index}]: doc_no 重复 {no}")
            seen.add(str(no))
            if not title:
                doc_issues.append(f"{group}[{index}]: 缺 title")
    checks["word_docs_valid"] = not doc_issues
    details["word_doc_issues"] = doc_issues

    status_issues = []
    # 可选字段：缺省时由 load_profile 回退默认值，视为合法；显式提供且非法时才拒绝
    status_values = profile.get("fact_status_values")
    if status_values is not None:
        if not isinstance(status_values, list) or not status_values or not all(isinstance(s, str) and s for s in status_values):
            status_issues.append("fact_status_values: 必须为非空字符串数组")
        elif len(status_values) != len(set(status_values)):
            status_issues.append("fact_status_values: 存在重复状态")
    methods = profile.get("confirmation_methods")
    if methods is not None:
        if not isinstance(methods, list) or not methods or not all(isinstance(m, str) and m for m in methods):
            status_issues.append("confirmation_methods: 必须为非空字符串数组")
        elif len(methods) != len(set(methods)):
            status_issues.append("confirmation_methods: 存在重复方式")
    checks["fact_status_values_valid"] = not status_issues
    details["status_issues"] = status_issues

    injections: list[str] = []
    scan_injection(profile, "profile", injections)
    checks["no_code_injection"] = not injections
    details["injection_hits"] = injections

    boundary_conflicts = []
    for text in profile.get("negative_boundary", []):
        # 仅当负向边界中出现与核心边界矛盾的肯定性表述时判冲突
        # （"不自动出具正式法律意见"属合规否定表述，不冲突）
        lowered = text.replace(" ", "")
        if re.search(r"(可|允许|可以).*(正式法律意见|已确认合规|全局安装)", lowered):
            boundary_conflicts.append(text)
    checks["negative_boundary_consistent"] = not boundary_conflicts
    details["boundary_conflicts"] = boundary_conflicts

    passed = bool(checks) and all(checks.values())
    return {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "profile": profile_id,
        "passed": passed,
        "checks": checks,
        "details": details,
        "boundary": "配置校验只确认配置合同的结构与安全边界，不替代业务验收或律师复核。",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="校验 AI数据合规场景配置文件")
    parser.add_argument("--profile", required=True, help="profile 标识（如 bci-medical-ai）")
    args = parser.parse_args()
    try:
        profile = read_json(PROFILES / f"{args.profile}.json")
    except FlowError as exc:
        print(json.dumps({"schema_version": CONFIG_SCHEMA_VERSION, "profile": args.profile, "passed": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(5)
    report = validate_profile(profile, args.profile)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 5)


if __name__ == "__main__":
    main()
