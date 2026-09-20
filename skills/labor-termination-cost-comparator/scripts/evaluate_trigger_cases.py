#!/usr/bin/env python3
"""对触发用例做静态描述覆盖检查，不冒充模型触发率。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

try:
    from scripts.legal_meta_security import parse_frontmatter, resolve_regular_file, safe_relative_path
except ModuleNotFoundError:
    from legal_meta_security import parse_frontmatter, resolve_regular_file, safe_relative_path


def read_description(skill_md: Path) -> str:
    return parse_frontmatter(skill_md.read_text(encoding="utf-8"))[1]


def _resolve_within(skill_dir: Path, value: str, label: str, *, allow_external: bool = False) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() and allow_external:
        return candidate.absolute()
    resolved = candidate.resolve() if candidate.is_absolute() else (skill_dir / candidate).resolve()
    if not resolved.is_relative_to(skill_dir):
        raise ValueError(f"{label} 路径必须位于 Skill 目录内：{value}")
    if resolved.exists() and resolved.is_symlink():
        raise ValueError(f"{label} 不得指向软链接：{value}")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 Skill 触发用例的静态描述覆盖")
    parser.add_argument("skill_dir", help="Skill 根目录")
    parser.add_argument("--cases", required=True, help="触发用例 JSON")
    parser.add_argument("--output", required=True, help="输出报告 JSON")
    parser.add_argument("--observed-results", help="可选的 provider-backed 路由观测 JSON")
    parser.add_argument(
        "--audit-mode",
        action="store_true",
        help="只读审计模式：允许将报告写到 Skill 目录外，或用 --output - 输出到标准输出",
    )
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    try:
        output_path = None if args.output == "-" else _resolve_within(
            skill_dir, args.output, "--output", allow_external=args.audit_mode
        )
        observed_path = (
            _resolve_within(
                skill_dir,
                args.observed_results,
                "--observed-results",
                allow_external=args.audit_mode,
            )
            if args.observed_results
            else None
        )
        cases_path = Path(args.cases)
        if not cases_path.is_absolute():
            cases_path = skill_dir / cases_path
        cases_path = _resolve_within(
            skill_dir,
            str(cases_path),
            "--cases",
            allow_external=args.audit_mode,
        )
        raw = json.loads(cases_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"错误：{exc}")
        return 1
    cases = raw.get("cases") if isinstance(raw, dict) else raw
    if not isinstance(cases, list):
        print("错误：触发用例文件必须为数组或含 cases 数组的对象")
        return 1
    try:
        description = read_description(skill_dir / "SKILL.md")
    except (OSError, ValueError) as exc:
        print(f"错误：{exc}")
        return 1
    results = []
    errors = []
    seen = set()
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            errors.append(f"触发用例第 {index} 项必须为对象")
            continue
        case_id = case.get("id")
        kind = case.get("kind")
        prompt = case.get("prompt", "")
        keywords = case.get("keywords", [])
        if not case_id or case_id in seen:
            errors.append(f"用例 id 缺失或重复：{case_id!r}")
            continue
        seen.add(case_id)
        if kind not in {"should-trigger", "should-not-trigger", "near-neighbor"}:
            errors.append(f"{case_id} 的 kind 无效：{kind!r}")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"{case_id} 缺少 prompt")
        found = [word for word in keywords if word and word in description]
        if kind == "should-trigger" and keywords and not found:
            errors.append(f"{case_id} 的正向关键词没有出现在 description 中")
        results.append({
            "id": case_id,
            "kind": kind,
            "keyword_hits": found,
            "keyword_count": len(keywords),
            "static_coverage": bool(found) if keywords else None,
        })

    counts = {
        kind: sum(1 for case in cases if isinstance(case, dict) and case.get("kind") == kind)
        for kind in ("should-trigger", "should-not-trigger", "near-neighbor")
    }
    observed_summary = None
    provider_backed = False
    if observed_path is not None:
        try:
            observed_document = json.loads(observed_path.read_text(encoding="utf-8"))
            metadata_fields = ("provider", "model", "run_at")
            if not isinstance(observed_document, dict) or not all(
                isinstance(observed_document.get(field), str) and observed_document[field].strip()
                for field in metadata_fields
            ):
                errors.append("observed-results 缺少 provider、model 或 run_at")
                observed_cases = []
            else:
                try:
                    observed_at = datetime.fromisoformat(observed_document["run_at"].replace("Z", "+00:00"))
                    if observed_at.tzinfo is None:
                        raise ValueError("run_at 必须包含时区")
                    if observed_at.astimezone(timezone.utc) > datetime.now(timezone.utc):
                        errors.append("observed-results.run_at 不能晚于当前时间")
                except ValueError as exc:
                    errors.append(f"observed-results.run_at 无效：{exc}")
                observed_cases = observed_document.get("cases", [])
            observed_by_id = {}
            if not isinstance(observed_cases, list):
                errors.append("observed-results.cases 必须为数组")
                observed_cases = []
            for item in observed_cases:
                if not isinstance(item, dict) or not item.get("id") or not isinstance(item.get("triggered"), bool):
                    errors.append("observed-results 存在缺少 id 或 triggered 的记录")
                    continue
                if item["id"] in observed_by_id:
                    errors.append(f"observed-results 用例 id 重复：{item['id']}")
                observed_by_id[item["id"]] = item
            case_ids = {case.get("id") for case in cases if isinstance(case, dict)}
            missing_ids = case_ids - set(observed_by_id)
            unknown_ids = set(observed_by_id) - case_ids
            if missing_ids:
                errors.append("observed-results 缺少用例：" + "、".join(sorted(missing_ids)))
            if unknown_ids:
                errors.append("observed-results 含未知用例：" + "、".join(sorted(unknown_ids)))
            passed = 0
            observed_results = []
            for case in cases:
                if not isinstance(case, dict):
                    continue
                item = observed_by_id.get(case.get("id"))
                if not item:
                    continue
                expected_triggered = case.get("kind") == "should-trigger"
                route_pass = item["triggered"] is expected_triggered
                if expected_triggered and item.get("selected_skill") != skill_dir.name:
                    route_pass = False
                if route_pass:
                    passed += 1
                else:
                    errors.append(f"provider-backed 路由不符合预期：{case.get('id')}")
                observed_results.append(
                    {
                        "id": case.get("id"),
                        "expected_triggered": expected_triggered,
                        "observed_triggered": item["triggered"],
                        "selected_skill": item.get("selected_skill"),
                        "pass": route_pass,
                    }
                )
            provider_backed = not errors and passed == len(cases) and all(
                result["pass"] for result in observed_results
            )
            observed_summary = {
                "provider": observed_document.get("provider") if isinstance(observed_document, dict) else None,
                "model": observed_document.get("model") if isinstance(observed_document, dict) else None,
                "run_at": observed_document.get("run_at") if isinstance(observed_document, dict) else None,
                "passed": passed,
                "total": len(cases),
                "results": observed_results,
            }
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            errors.append(f"observed-results 无法读取：{exc}")
    report = {
        "skill": skill_dir.name,
        "evaluated_at": date.today().isoformat(),
        "evidence_kind": "provider_passed" if provider_backed else (
            "provider_failed" if observed_path is not None else "static_only"
        ),
        "provider_status": "passed" if provider_backed else ("failed" if observed_path is not None else "not_run"),
        "not_model_trigger_rate": not provider_backed,
        "counts": counts,
        "results": results,
        "observed_results": observed_summary,
        "errors": errors,
        "missing_evidence": (
            ["独立人工盲评", "跨 Skill 路由冲突实测"]
            if provider_backed
            else ["provider-backed 模型触发运行", "独立人工盲评", "跨 Skill 路由冲突实测"]
        ),
    }
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if output_path is None:
        print(serialized, end="")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized, encoding="utf-8")
        print(json.dumps({"counts": counts, "errors": len(errors), "output": str(output_path)}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
