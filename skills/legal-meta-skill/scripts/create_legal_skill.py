#!/usr/bin/env python3
"""根据完成的 intake JSON 确定性生成自包含法律 Skill；不覆盖既有目录。"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

try:
    from scripts.export_legal_skill_ir import build_ir
    from scripts.legal_meta_security import sha256_file
    from scripts.validate_legal_profile import _specific_reason, validate_profile
    from scripts.validate_legal_skill import MATURITY_LABELS, MATURITY_ORDER, _valid_review_date, check
except ModuleNotFoundError:
    from export_legal_skill_ir import build_ir
    from legal_meta_security import sha256_file
    from validate_legal_profile import _specific_reason, validate_profile
    from validate_legal_skill import MATURITY_LABELS, MATURITY_ORDER, _valid_review_date, check


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
INTAKE_SCHEMA = "legal-skill-intake/v0.3"
LEGACY_INTAKE_SCHEMAS = {"legal-skill-intake/v0.1", "legal-skill-intake/v0.2"}
META_VERSION = "1.0.0"
TRIGGER_KINDS = {
    "should-trigger": "should-trigger",
    "should-not-trigger": "should-not-trigger",
    "near-neighbor": "near-neighbor",
}
PRIOR_ART_DECISIONS = {"直接纳入", "转化后纳入", "明确不纳入", "针对缺口新增"}
SCENARIO_ARCHETYPES = {
    "dispute_resolution",
    "contract_review",
    "document_drafting",
    "legal_research",
    "compliance_regulatory",
    "legal_retrieval",
    "evidence_files",
    "document_review_redline",
    "other",
}
INTENT_CANVAS_CORE_KEYS = (
    "job",
    "users",
    "decision",
    "inputs",
    "outputs",
    "exclusions",
    "legal_profile",
    "human_control",
    "success",
)
INTENT_CANVAS_CONDITIONAL_KEYS = (
    "jurisdiction_bundle",
    "temporal_bundle",
    "actors",
    "matter",
    "evidence",
    "workspace_or_permissions",
)
INTENT_CANVAS_KEYS = INTENT_CANVAS_CORE_KEYS + INTENT_CANVAS_CONDITIONAL_KEYS
ARCHETYPE_CANVAS_RELAXED = {
    "dispute_resolution": frozenset(),
    "contract_review": frozenset(),
    "document_drafting": frozenset({"evidence"}),
    "legal_research": frozenset({"actors", "evidence"}),
    "compliance_regulatory": frozenset({"evidence"}),
    "legal_retrieval": frozenset({"actors", "evidence"}),
    "evidence_files": frozenset(),
    "other": frozenset(),
}
DOMAIN_SUPPLEMENT_SOURCES = {"builtin-archetype", "user-provided", "authorized-research"}
COPIED_REFERENCES = (
    "universal-legal-capability-model.md",
    "legal-core-rules.md",
    "legal-workspace-rules.md",
    "legal-method-core.md",
    "legal-scenario-archetypes.md",
    "legal-skill-ir.md",
    "legal-workflow-folder-design.md",
    "resource-verifier-routing.md",
    "oslaw-resource-catalog.md",
)
COPIED_SCRIPTS = (
    "validate_legal_profile.py",
    "validate_legal_skill.py",
    "evaluate_trigger_cases.py",
    "export_legal_skill_ir.py",
    "legal_meta_security.py",
    "legal_meta.py",
    "migrate_legal_skill.py",
)


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonempty_text_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(_nonempty_text(item) for item in value)


def _maturity_at_least(maturity: str, minimum: str) -> bool:
    return MATURITY_ORDER[maturity] >= MATURITY_ORDER[minimum]


def _contains_placeholder(value: object) -> bool:
    markers = ("【填写", "【替换", "replace-with", "示例仅供")
    if isinstance(value, str):
        return any(marker in value for marker in markers)
    if isinstance(value, list):
        return any(_contains_placeholder(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_placeholder(item) for item in value.values())
    return False


def _quote_yaml(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _write_text(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _write_json(root: Path, relative: str, value: object) -> None:
    _write_text(root, relative, json.dumps(value, ensure_ascii=False, indent=2))


def _specific_canvas_answer(value: object) -> bool:
    return _specific_reason(value) and not _contains_placeholder(value)


def _safe_fixture_filename(value: object) -> bool:
    """拒绝含路径分隔符、父目录段或绝对路径的 fixture 文件名（含 Windows 反斜杠逃逸）。"""
    if not _nonempty_text(value):
        return False
    name = str(value)
    if "/" in name or "\\" in name or name in {".", ".."}:
        return False
    return not Path(name).is_absolute() and Path(name).name == name


def _validate_domain_supplement(supplement: object) -> list[str]:
    """第 3 层领域问答记录；生成时必须保留为可复用规则。"""
    if supplement is None:
        return []
    if not isinstance(supplement, list):
        return ["domain_supplement 必须为对象数组"]
    errors: list[str] = []
    for index, item in enumerate(supplement, start=1):
        if not isinstance(item, dict):
            errors.append(f"domain_supplement 第 {index} 项必须为对象")
            continue
        if not all(key in item for key in ("question", "question_source")):
            errors.append(f"domain_supplement 第 {index} 项缺少 question、answer 或 question_source")
            continue
        if not _nonempty_text(item["question"]):
            errors.append(f"domain_supplement 第 {index} 项 question 不能为空")
        answer = item.get("answer_summary", item.get("answer"))
        if not _specific_canvas_answer(answer):
            errors.append(f"domain_supplement 第 {index} 项 answer 不具体（answer_summary 需为实质回答）")
        rules = item.get("internalized_rules")
        if rules is not None and not _nonempty_text_list(rules):
            errors.append(f"domain_supplement 第 {index} 项 internalized_rules 必须为非空字符串数组")
        if "id" in item and not _nonempty_text(item.get("id")):
            errors.append(f"domain_supplement 第 {index} 项 id 不能为空")
        if item["question_source"] not in DOMAIN_SUPPLEMENT_SOURCES:
            errors.append(
                f"domain_supplement 第 {index} 项 question_source 必须为 "
                + "、".join(sorted(DOMAIN_SUPPLEMENT_SOURCES))
                + " 之一"
            )
    return errors


WORKFLOW_PROFILES = {
    "case_analysis_v2": "case-analysis-v2.md",
    "due_diligence": "due-diligence.md",
    "contract_review": "contract-review.md",
    "legal_research": "legal-research.md",
}


def _inferred_workflow_profile(intake: dict) -> str | None:
    explicit = intake.get("workspace_profile")
    if isinstance(explicit, dict) and _nonempty_text(explicit.get("workflow_family")):
        return str(explicit["workflow_family"])
    return {
        "contract_review": "contract_review",
        "document_review_redline": "contract_review",
        "document_drafting": "contract_review",
        "dispute_resolution": "case_analysis_v2",
        "evidence_files": "case_analysis_v2",
        "legal_research": "legal_research",
        "legal_retrieval": "legal_research",
        "compliance_regulatory": "due_diligence",
    }.get(str(intake.get("scenario_archetype")))


def _validate_workspace_profile(intake: dict) -> list[str]:
    profile = intake.get("workspace_profile")
    family = _inferred_workflow_profile(intake)
    if family not in WORKFLOW_PROFILES:
        return ["无法确定中文法律工作流文件夹配置；请提供 workspace_profile.workflow_family"]
    if profile is None:
        return []
    if not isinstance(profile, dict):
        return ["workspace_profile 必须为对象"]
    errors: list[str] = []
    if profile.get("workflow_family") not in WORKFLOW_PROFILES:
        errors.append("workspace_profile.workflow_family 不是受支持的中文法律工作流")
    if not _nonempty_text(profile.get("display_name_zh")):
        errors.append("workspace_profile.display_name_zh 不能为空")
    if profile.get("initialization_mode", "plan_only") not in {"plan_only", "explicit_initialize"}:
        errors.append("workspace_profile.initialization_mode 必须为 plan_only 或 explicit_initialize")
    if profile.get("root_policy", "user_selected") != "user_selected":
        errors.append("workspace_profile.root_policy 必须为 user_selected")
    return errors


def _validate_intent_canvas(coverage: object, archetype: object) -> list[str]:
    """意图画布机检兜底：15 键齐全；核心键必须实质回答；条件键仅在原型放宽时允许 not_needed。"""
    if not isinstance(coverage, dict):
        return ["intent_canvas_coverage 必须为对象"]
    errors: list[str] = []
    missing = [key for key in INTENT_CANVAS_KEYS if key not in coverage]
    if missing:
        errors.append("intent_canvas_coverage 缺少字段：" + "、".join(missing))
    relaxed = ARCHETYPE_CANVAS_RELAXED.get(str(archetype), frozenset())
    for key in INTENT_CANVAS_KEYS:
        if key not in coverage:
            continue
        value = coverage[key]
        if isinstance(value, str):
            if not _specific_canvas_answer(value):
                errors.append(f"intent_canvas_coverage.{key} 的回答不具体，需说明该字段的实质内容")
            continue
        if isinstance(value, dict) and set(value) == {"not_needed"}:
            if key in INTENT_CANVAS_CORE_KEYS:
                errors.append(f"intent_canvas_coverage.{key} 是核心字段，必须实质回答，不允许 not_needed")
            elif key not in relaxed:
                errors.append(f"intent_canvas_coverage.{key} 在场景原型 {archetype} 下不允许 not_needed")
            elif not _specific_canvas_answer(value["not_needed"]):
                errors.append(f"intent_canvas_coverage.{key} 的 not_needed 需要具体理由")
            continue
        errors.append(f"intent_canvas_coverage.{key} 必须为非空字符串或 not_needed 对象")
    return errors


def _validate_trigger_groups(triggers: object, maturity: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(triggers, dict):
        return ["triggers 必须为对象"]
    minimum_counts = (
        {"should-trigger": 3, "should-not-trigger": 2, "near-neighbor": 2}
        if _maturity_at_least(maturity, "library")
        else {kind: 1 for kind in TRIGGER_KINDS}
    )
    for kind, minimum in minimum_counts.items():
        cases = triggers.get(kind)
        if not isinstance(cases, list) or len(cases) < minimum:
            errors.append(f"{kind} 至少需要 {minimum} 个自然语言用例")
            continue
        for index, case in enumerate(cases, start=1):
            if not isinstance(case, dict) or not _nonempty_text(case.get("prompt")):
                errors.append(f"{kind} 第 {index} 项缺少 prompt")
            keywords = case.get("keywords") if isinstance(case, dict) else None
            if kind == "should-trigger" and not _nonempty_text_list(keywords):
                errors.append(f"{kind} 第 {index} 项缺少非空 keywords")
    return errors


def validate_intake(intake: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(intake, dict):
        return ["intake 根必须为 JSON 对象"]
    if intake.get("template_only") is True:
        errors.append("当前文件仍是模板；请完成填写并删除 template_only 或设为 false")
    if _contains_placeholder(intake):
        errors.append("intake 仍含【填写】、【替换】或 replace-with 等占位内容")
    if intake.get("schema_version") not in {INTAKE_SCHEMA, *LEGACY_INTAKE_SCHEMAS}:
        errors.append(f"schema_version 必须为 {INTAKE_SCHEMA}（兼容读取 {', '.join(sorted(LEGACY_INTAKE_SCHEMAS))}）")
    name = intake.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        errors.append("name 必须为不超过 64 字符的小写字母、数字和单连字符组合")
    for field in ("display_name", "description", "short_description", "owner"):
        if not _nonempty_text(intake.get(field)):
            errors.append(f"{field} 不能为空")
    description = intake.get("description")
    if isinstance(description, str) and len(description) > 1024:
        errors.append("description 超过 1024 字符")
    short_description = intake.get("short_description")
    if isinstance(short_description, str) and not 25 <= len(short_description) <= 64:
        errors.append("short_description 必须为 25–64 个字符")
    maturity = intake.get("maturity")
    if maturity not in MATURITY_LABELS:
        errors.append("maturity 必须为 scaffold、production、library 或 governed")
        return errors

    contract = intake.get("skill_contract")
    if not isinstance(contract, dict):
        errors.append("skill_contract 必须为对象")
    else:
        if not _nonempty_text(contract.get("job")):
            errors.append("skill_contract.job 不能为空")
        decision = contract.get("decision")
        if not isinstance(decision, dict) or not all(
            _nonempty_text(decision.get(field)) for field in ("goal", "owner", "supported_action")
        ):
            errors.append("skill_contract.decision 缺少 goal、owner 或 supported_action")
        for field in (
            "target_users",
            "inputs",
            "outputs",
            "exclusions",
            "workflow",
            "decision_points",
            "failure_modes",
        ):
            if not _nonempty_text_list(contract.get(field)):
                errors.append(f"skill_contract.{field} 必须为非空字符串数组")

    errors.extend(_validate_trigger_groups(intake.get("triggers"), maturity))
    archetype = intake.get("scenario_archetype")
    if archetype not in SCENARIO_ARCHETYPES:
        errors.append("scenario_archetype 必须为 " + "、".join(sorted(SCENARIO_ARCHETYPES)) + " 之一")
    errors.extend(_validate_intent_canvas(intake.get("intent_canvas_coverage"), archetype))
    errors.extend(_validate_domain_supplement(intake.get("domain_supplement")))
    errors.extend(_validate_workspace_profile(intake))
    if archetype == "other" and not isinstance(intake.get("domain_supplement"), list):
        errors.append("scenario_archetype=other 必须提供非空 domain_supplement")
    if archetype == "other" and isinstance(intake.get("domain_supplement"), list) and not intake["domain_supplement"]:
        errors.append("scenario_archetype=other 的 domain_supplement 不能为空")
    profile_errors, profile_warnings = validate_profile(
        {"legal_profile": intake.get("legal_profile")}, strict=True
    )
    errors.extend(profile_errors)
    errors.extend(f"法律能力配置警告需先处理：{warning}" for warning in profile_warnings)

    for field in ("permissions", "degradation", "eval_plan", "evidence_boundary"):
        if not isinstance(intake.get(field), dict) or not intake[field]:
            errors.append(f"{field} 必须为非空对象")
    review = intake.get("review")
    if not isinstance(review, dict) or not all(
        (
            _nonempty_text(review.get("owner")),
            _nonempty_text(review.get("cadence")),
            _nonempty_text_list(review.get("reverification_triggers")),
        )
    ):
        errors.append("review 缺少 owner、cadence 或 reverification_triggers")

    if _maturity_at_least(maturity, "production"):
        evaluation_cases = intake.get("evaluation_cases")
        minimum_cases = 7 if _maturity_at_least(maturity, "library") else 1
        if not isinstance(evaluation_cases, list) or len(evaluation_cases) < minimum_cases:
            errors.append(f"{MATURITY_LABELS[maturity]}至少需要 {minimum_cases} 个法律输出评测用例")
    if _maturity_at_least(maturity, "library"):
        prior_art = intake.get("prior_art")
        if not isinstance(prior_art, list) or not prior_art:
            errors.append("基础设施级以上至少需要一项 prior_art 取舍记录")
        else:
            for index, item in enumerate(prior_art, start=1):
                if not isinstance(item, dict) or item.get("decision") not in PRIOR_ART_DECISIONS:
                    errors.append(f"prior_art 第 {index} 项缺少合法取舍决定")
                elif not all(_nonempty_text(item.get(field)) for field in ("source", "reason", "evidence")):
                    errors.append(f"prior_art 第 {index} 项缺少 source、reason 或 evidence")
    if maturity == "governed":
        governed = intake.get("governance_evidence")
        if not isinstance(governed, dict):
            errors.append("高风险治理级缺少 governance_evidence")
        else:
            fixtures = governed.get("fixture_index")
            if not isinstance(fixtures, list) or not fixtures:
                errors.append("高风险治理级缺少 file-backed fixture 索引")
            else:
                for index, fixture in enumerate(fixtures, start=1):
                    if not isinstance(fixture, dict) or not all(
                        _nonempty_text(fixture.get(field))
                        for field in ("id", "filename", "content", "authorization", "expected_boundary")
                    ):
                        errors.append(f"高风险治理级 fixture 第 {index} 项字段不完整")
                    elif not _safe_fixture_filename(fixture["filename"]):
                        errors.append(f"高风险治理级 fixture 第 {index} 项 filename 必须为单个安全文件名")
            for field in ("permission_policy", "rollback_plan"):
                if not _nonempty_text(governed.get(field)):
                    errors.append(f"高风险治理级缺少 {field}")
            records = governed.get("human_review_records")
            if not isinstance(records, list) or not records:
                errors.append("高风险治理级缺少人工复核记录")
            else:
                for index, record in enumerate(records, start=1):
                    if not isinstance(record, dict) or not all(
                        _nonempty_text(record.get(field))
                        for field in ("reviewer", "reviewed_at", "case_id", "outcome", "confidence", "reason")
                    ):
                        errors.append(f"高风险治理级人工复核记录第 {index} 项字段不完整")
                    elif not _valid_review_date(record["reviewed_at"]):
                        errors.append(f"高风险治理级人工复核记录第 {index} 项日期格式无效")
    branding = intake.get("branding_mode", "branded")
    if branding not in {"branded", "white-label"}:
        errors.append("branding_mode 只能为 branded 或 white-label")
    if branding == "white-label" and intake.get("white_label_authorized") is not True:
        errors.append("白标生成必须明确设置 white_label_authorized=true")
    return errors


def _trigger_document(intake: dict) -> dict:
    cases: list[dict] = []
    for kind in TRIGGER_KINDS:
        for index, item in enumerate(intake["triggers"][kind], start=1):
            cases.append(
                {
                    "id": f"{kind}-{index:02d}",
                    "kind": kind,
                    "prompt": item["prompt"],
                    "keywords": item.get("keywords", []),
                }
            )
    return {"schema_version": "trigger-cases/v0.1", "cases": cases}


def _normalized_domain_supplement(intake: dict) -> list[dict]:
    """把 v0.1 问答兼容转换成不会丢失的内部化规则记录。"""
    normalized: list[dict] = []
    for index, item in enumerate(intake.get("domain_supplement") or [], start=1):
        summary = item.get("answer_summary", item.get("answer", ""))
        rules = item.get("internalized_rules") or [summary]
        normalized.append(
            {
                "id": item.get("id") or f"domain-supplement-{index:02d}",
                "question": item["question"],
                "question_source": item["question_source"],
                "rules": rules,
                "sensitivity": item.get("sensitivity", "internalized-only"),
            }
        )
    return normalized


def _render_domain_supplement(intake: dict) -> str:
    lines = [
        "# 领域补充规则",
        "",
        "本文件只保留可复用的内部化规则，不复制原始访谈、客户材料或完整敏感回答。",
        "",
    ]
    for item in _normalized_domain_supplement(intake):
        lines.extend(
            [
                f"## {item['id']}",
                "",
                f"- 问题：{item['question']}",
                f"- 来源：{item['question_source']}",
                f"- 敏感性：{item['sensitivity']}",
                "- 内部化规则：",
                *[f"  - {rule}" for rule in item["rules"]],
                "",
            ]
        )
    return "\n".join(lines)


def _render_skill_md(intake: dict, branded: bool, production: bool) -> str:
    contract = intake["skill_contract"]
    workflow = "\n".join(f"{index}. {step}" for index, step in enumerate(contract["workflow"], start=1))
    exclusions = "\n".join(f"- {item}" for item in contract["exclusions"])
    outputs = "\n".join(f"- {item}" for item in contract["outputs"])
    source = (
        "\n## 作者与来源\n\n- 作者：CSlawyer\n- 主页：https://chenshi.ai\n- 生成工具：legal-meta-skill\n"
        if branded
        else ""
    )
    output_reference = (
        "按 [法律输出契约](assets/legal-skill-output-contract.md) 交付，并对十二模块逐项记录状态。"
        if production
        else "按 manifest 中的十二模块配置逐项检查；受阻时停止相应确定性结论。"
    )
    method_reference = "运行时遵守 [法律方法核心](references/legal-method-core.md) 的方法纪律"
    archetype = intake.get("scenario_archetype", "other")
    workflow_family = _inferred_workflow_profile(intake)
    if archetype != "other":
        method_reference += f"，并按 [场景检查清单](references/{archetype}.md) 逐项核对"
    supplement_reference = ""
    if intake.get("domain_supplement"):
        supplement_reference = "并按 [领域补充规则](references/domain-supplement.md) 路由专项检查"
    workspace_reference = (
        f"读取 [中文工作流配置](references/workflow-profiles/{WORKFLOW_PROFILES[workflow_family]})，"
        "先规划案件或项目目录，再生成或更新根目录下的 `文件夹使用说明.md`。"
        "新建工作区不得使用通用 `input/`、`scratch/`、`output/` 作为默认目录；旧项目只能按兼容映射处理。"
    )
    return f"""---
name: {intake['name']}
description: {_quote_yaml(intake['description'])}
license: Apache-2.0
metadata:
  author: {_quote_yaml('CSlawyer' if branded else intake['owner'])}
  version: {_quote_yaml(intake.get('version', '0.1.0'))}
---

# {intake['display_name']}

## 任务

{contract['job']}

本 Skill 支持的决定：{contract['decision']['goal']}。决定责任人：{contract['decision']['owner']}。允许支持的动作：{contract['decision']['supported_action']}。

## 工作流

{workflow}

## 输出

{outputs}

{output_reference}

## 法律能力与证据边界

运行时读取 [通用法律能力模型](references/universal-legal-capability-model.md)、[法律核心规则](references/legal-core-rules.md) 和 [法律文件规则](references/legal-workspace-rules.md)。{method_reference}{supplement_reference}。{workspace_reference} 同时按 [资源核查路由](references/resource-verifier-routing.md) 选择必要的权威来源、商业数据库或人工核验；OSLAW 仅作资源发现目录，不替代权威来源。十二模块必须全部检查、条件展开；具体法条、司法解释、案例、期限和地方口径必须结合任务法域与时点独立核验。材料、事实、法律评价和程序状态分层记录，关键依据不足时不得用模型知识补成确定结论。

## 不做事项

{exclusions}

输入材料默认只读；外部传输、不可逆提交、正式签发和其他受限动作仅在权限契约与人工复核条件满足时进行。{source}"""


def _render_interface(intake: dict) -> str:
    return f"""interface:
  display_name: {_quote_yaml(intake['display_name'])}
  short_description: {_quote_yaml(intake['short_description'])}
  default_prompt: {_quote_yaml('使用 $' + intake['name'] + ' 完成其定义的重复法律任务；逐项检查十二模块，独立核验易变法律依据，证据不足时执行停止或降级路径。')}
compatibility:
  canonical_format: "agent-skills"
  activation:
    mode: "description"
  trust:
    generated_claims: "以证据为界"
"""


def _render_prior_art(items: list[dict]) -> str:
    lines = ["# 同类方案取舍", "", "| 来源 | 取舍 | 理由 | 证据边界 |", "|---|---|---|---|"]
    for item in items:
        clean = [str(item[field]).replace("|", "\\|").replace("\n", " ") for field in ("source", "decision", "reason", "evidence")]
        lines.append("| " + " | ".join(clean) + " |")
    return "\n".join(lines)


def _render_trust_review(intake: dict) -> str:
    boundary = intake["evidence_boundary"]
    present = "\n".join(f"- {item}" for item in boundary.get("present", [])) or "- 尚无真实运行证据"
    missing = "\n".join(f"- {item}" for item in boundary.get("missing_evidence", [])) or "- 无已登记缺口"
    return f"""# 信任与证据审查

## 已取得证据

{present}

## 证据缺失

{missing}

静态配置、模板和计划不等于模型运行或人工复核证据；成熟度声明只覆盖已经列明的证据。
"""


def _render_handoff(intake: dict) -> str:
    supplement = intake.get("domain_supplement") or []
    supplement_line = ""
    if supplement:
        distribution = "、".join(
            f"{source} {sum(1 for item in supplement if item['question_source'] == source)} 条"
            for source in sorted(DOMAIN_SUPPLEMENT_SOURCES)
            if any(item["question_source"] == source for item in supplement)
        )
        supplement_line = f"\n- 领域补充问答：{len(supplement)} 条（{distribution}）"
    return f"""# 创建交接

- Skill：`{intake['name']}`
- 版本：`{intake.get('version', '0.1.0')}`
- 成熟度：{MATURITY_LABELS[intake['maturity']]}（`{intake['maturity']}`）
- 维护人：{intake['review']['owner']}
- 复核周期：{intake['review']['cadence']}{supplement_line}
- 生成工具：legal-meta-skill {META_VERSION}

本包由完成的 intake 确定性生成。结构通过不等于实体法律结论正确；提供方模型实跑、独立人工盲评、真实项目回归和权限原生执行，只有实际取得并记录后才算证据。
"""


def _build_manifest(intake: dict, quality_evidence: dict) -> dict:
    branded = intake.get("branding_mode", "branded") != "white-label"
    workflow_family = _inferred_workflow_profile(intake)
    return {
        "name": intake["name"],
        "version": intake.get("version", "0.1.0"),
        "owner": intake["owner"],
        "homepage": "https://chenshi.ai" if branded else intake.get("homepage", ""),
        "license": "Apache-2.0",
        "branding_mode": "branded" if branded else "white-label",
        "white_label_authorized": bool(intake.get("white_label_authorized", False)),
        "creator": {
            "identity": "CSlawyer" if branded else "",
            "homepage": "https://chenshi.ai" if branded else "",
            "created_with": "legal-meta-skill",
            "created_with_version": META_VERSION,
        },
        "maturity_tier": intake["maturity"],
        "maturity_label_zh": MATURITY_LABELS[intake["maturity"]],
        "scenario_archetype": intake["scenario_archetype"],
        "target_platforms": intake.get("target_platforms", ["openai", "generic"]),
        "skill_contract": intake["skill_contract"],
        "legal_profile": intake["legal_profile"],
        "permissions": intake["permissions"],
        "degradation": intake["degradation"],
        "eval_plan": intake["eval_plan"],
        "evidence_boundary": intake["evidence_boundary"],
        "review": intake["review"],
        "quality_evidence": quality_evidence,
        "downstream_attribution": {
            "required_on_redistribution": "保留 LICENSE、NOTICE、版权声明及修改标记",
            "business_deliverables": "不得自动注入品牌标识",
        },
        "workspace_profile": {
            "workflow_family": workflow_family,
            "profile_file": f"references/workflow-profiles/{WORKFLOW_PROFILES[workflow_family]}",
            "usage_guide": "文件夹使用说明.md",
            "plan_first": True,
            "new_workspace_default": "中文法律工作流目录；不生成 input、scratch、output",
        },
        "resource_verification": {
            "routing_reference": "references/resource-verifier-routing.md",
            "discovery_catalog": "references/oslaw-resource-catalog.md",
            "authority_required_before_conclusion": True,
        },
        "quality_evidence_digests": {},
        "self_containment": {"external_skill_dependencies": []},
    }


def create_skill(intake: dict, target_parent: Path) -> Path:
    errors = validate_intake(intake)
    if errors:
        raise ValueError("\n".join(errors))
    target_parent = target_parent.resolve()
    target = target_parent / intake["name"]
    if target.exists():
        raise FileExistsError(f"目标目录已存在，拒绝覆盖：{target}")
    staging_parent = Path(tempfile.mkdtemp(prefix=f".{intake['name']}.tmp-", dir=target_parent))
    staging = staging_parent / intake["name"]
    try:
        _generate_package(intake, staging)
    except BaseException:
        shutil.rmtree(staging_parent, ignore_errors=True)
        raise
    os.replace(staging, target)
    staging_parent.rmdir()
    return target


def _generate_package(intake: dict, target: Path) -> None:
    target.mkdir(parents=True)
    maturity = intake["maturity"]
    production = _maturity_at_least(maturity, "production")
    library = _maturity_at_least(maturity, "library")
    governed = maturity == "governed"
    branded = intake.get("branding_mode", "branded") != "white-label"

    quality_evidence: dict[str, str] = {"trigger_cases": "evals/trigger_cases.json"}
    if production:
        quality_evidence.update(
            {
                "output_contract": "assets/legal-skill-output-contract.md",
                "output_assertions": "evals/output_assertions.json",
                "universal_cases": "evals/universal_legal_cases.json",
            }
        )
    if library:
        quality_evidence.update(
            {
                "skill_ir": "reports/skill-ir.json",
                "prior_art": "reports/prior-art.md",
                "trust_review": "reports/trust-review.md",
                "creation_handoff": "reports/creation-handoff.md",
            }
        )
    if governed:
        quality_evidence.update(
            {
                "fixture_index": "evals/fixtures/index.json",
                "permission_policy": "references/permission-policy.md",
                "rollback_plan": "reports/rollback-plan.md",
                "human_review_evidence": "reports/human-review-evidence.json",
            }
        )

    _write_text(target, "SKILL.md", _render_skill_md(intake, branded, production))
    _write_json(target, "evals/trigger_cases.json", _trigger_document(intake))
    (target / "references").mkdir(parents=True, exist_ok=True)
    for filename in COPIED_REFERENCES:
        shutil.copyfile(PACKAGE_ROOT / "references" / filename, target / "references" / filename)
    workflow_family = _inferred_workflow_profile(intake)
    (target / "references" / "workflow-profiles").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        PACKAGE_ROOT / "references" / "workflow-profiles" / WORKFLOW_PROFILES[workflow_family],
        target / "references" / "workflow-profiles" / WORKFLOW_PROFILES[workflow_family],
    )
    _write_text(
        target,
        "文件夹使用说明.md",
        (PACKAGE_ROOT / "assets" / "templates" / "文件夹使用说明.md")
        .read_text(encoding="utf-8")
        .replace("{{WORKFLOW_FAMILY}}", workflow_family)
        .replace("{{PROFILE_FILE}}", f"references/workflow-profiles/{WORKFLOW_PROFILES[workflow_family]}"),
    )
    archetype = intake["scenario_archetype"]
    if archetype != "other":
        shutil.copyfile(
            PACKAGE_ROOT / "assets" / "templates" / "legal-scenario-checklists" / f"{archetype}.md",
            target / "references" / f"{archetype}.md",
        )
    if intake.get("domain_supplement"):
        _write_text(target, "references/domain-supplement.md", _render_domain_supplement(intake))
    if (PACKAGE_ROOT / "LICENSE").is_file():
        shutil.copyfile(PACKAGE_ROOT / "LICENSE", target / "LICENSE")
    if (PACKAGE_ROOT / "NOTICE").is_file():
        shutil.copyfile(PACKAGE_ROOT / "NOTICE", target / "NOTICE")
    for filename in ("ATTRIBUTION.md", "TRADEMARKS.md"):
        if (PACKAGE_ROOT / filename).is_file():
            shutil.copyfile(PACKAGE_ROOT / filename, target / filename)

    if production:
        _write_text(target, "agents/interface.yaml", _render_interface(intake))
        _write_text(target, "agents/openai.yaml", _render_interface(intake).split("compatibility:", 1)[0])
        (target / "assets").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            PACKAGE_ROOT / "assets" / "templates" / "legal-skill-output-contract.md",
            target / "assets" / "legal-skill-output-contract.md",
        )
        shutil.copyfile(
            PACKAGE_ROOT / "assets" / "templates" / "downstream-output-assertions.json",
            target / "evals" / "output_assertions.json",
        )
        _write_json(
            target,
            "evals/universal_legal_cases.json",
            {
                "schema_version": "universal-legal-eval-cases/v0.1",
                "cases": intake["evaluation_cases"],
            },
        )
        (target / "scripts").mkdir(parents=True, exist_ok=True)
        for filename in COPIED_SCRIPTS:
            shutil.copyfile(PACKAGE_ROOT / "scripts" / filename, target / "scripts" / filename)
        shutil.copyfile(PACKAGE_ROOT / "scripts" / "plan_legal_workspace.py", target / "scripts" / "plan_legal_workspace.py")

    manifest = _build_manifest(intake, quality_evidence)
    _write_json(target, "manifest.json", manifest)
    _write_text(target, "reports/creation-handoff.md", _render_handoff(intake))
    if library:
        _write_text(target, "reports/prior-art.md", _render_prior_art(intake["prior_art"]))
        _write_text(target, "reports/trust-review.md", _render_trust_review(intake))
    if governed:
        governed_input = intake["governance_evidence"]
        fixture_index = []
        for fixture in governed_input["fixture_index"]:
            relative = f"evals/fixtures/{fixture['filename']}"
            _write_text(target, relative, fixture["content"])
            fixture_index.append(
                {
                    "id": fixture["id"],
                    "input_files": [relative],
                    "authorization": fixture["authorization"],
                    "expected_boundary": fixture["expected_boundary"],
                }
            )
        _write_json(target, "evals/fixtures/index.json", fixture_index)
        _write_text(target, "references/permission-policy.md", governed_input["permission_policy"])
        _write_text(target, "reports/rollback-plan.md", governed_input["rollback_plan"])
        _write_json(target, "reports/human-review-evidence.json", governed_input["human_review_records"])
    if library:
        manifest["quality_evidence_digests"] = {
            relative: sha256_file(target / relative)
            for key, relative in quality_evidence.items()
            if key != "skill_ir" and (target / relative).is_file()
        }
        _write_json(target, "manifest.json", manifest)
        _write_json(target, "reports/skill-ir.json", build_ir(target))

    validation_errors, validation_warnings = check(target)
    if validation_errors:
        raise RuntimeError("生成包未通过校验：\n" + "\n".join(validation_errors))
    _write_text(
        target,
        "reports/generation-validation.md",
        "# 生成校验\n\n- 结构与成熟度门禁：通过\n- 警告数："
        + str(len(validation_warnings))
        + "\n- 法律实体正确性：未由静态生成校验证明",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="从完成的 intake JSON 生成自包含法律 Skill")
    parser.add_argument("--intake", required=True, help="legal-skill-intake/v0.3 JSON 文件（兼容读取 v0.1/v0.2）")
    parser.add_argument("--target-parent", required=True, help="目标 Skill 的父目录")
    args = parser.parse_args()
    try:
        intake = json.loads(Path(args.intake).read_text(encoding="utf-8"))
        target = create_skill(intake, Path(args.target_parent))
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"错误：{exc}")
        return 1
    print(f"已生成并验证法律 Skill：{target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
