#!/usr/bin/env python3
"""将结构化审查计划批量应用到 DOCX，并生成配套审查报告。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from defusedxml import minidom


def _bootstrap_runtime_isolation() -> None:
    """把运行态配置默认隔离到本轮归档目录，而不是写进 Skill 副本。

    运行态配置（审查人自述、审查记忆）默认落在 Skill 的 `config/` 下；
    实测中首跑没设 `CONTRACT_COPILOT_CONFIG_DIR`，审查人配置就被写进了**冻结的 Skill 副本**。
    文档里写了隔离办法，但"文档写了"不等于"默认安全"——这里把默认改成隔离。

    位置取自命令行（`--log` / `--archive-dir` / `--quality-dir` / `--output`）的目录；
    **显式设置的环境变量一律尊重，不覆盖**。
    """
    if os.environ.get("CONTRACT_COPILOT_CONFIG_DIR"):
        return
    argv = sys.argv[1:]
    candidate: Path | None = None
    for flag in ("--log", "--archive-dir", "--quality-dir", "--output", "--report"):
        if flag in argv:
            index = argv.index(flag)
            if index + 1 < len(argv):
                value = argv[index + 1]
                if value.startswith("-"):
                    continue
                candidate = Path(value).expanduser()
                break
    if candidate is None:
        return
    base = candidate if candidate.suffix == "" else candidate.parent
    config_dir = base / "runtime-config"
    os.environ["CONTRACT_COPILOT_CONFIG_DIR"] = str(config_dir)
    print(
        f"[one-contract] 运行态配置已隔离到：{config_dir}"
        "（如需固定位置，请显式设置 CONTRACT_COPILOT_CONFIG_DIR）",
        file=sys.stderr,
    )


_bootstrap_runtime_isolation()

if __package__ in (None, ""):
    skill_root = Path(__file__).resolve().parents[2]
    if str(skill_root) not in sys.path:
        sys.path.insert(0, str(skill_root))

try:
    from .action_executor import apply_finding
    from .archive_service import (
        DEFAULT_ARCHIVE_DIR,
        archive_run,
        create_archive_run_dir,
    )
    from ..docx_engine.pack import pack_document
    from ..docx_engine.quality_gate import (
        inspect_docx,
        render_docx_evidence,
        run_quality_gate,
    )
    from ..docx_engine.revision_views import resolve_unpacked_revisions
    from .plan_loader import (
        enrich_plan,
        get_findings,
        get_plan_meta,
        load_plan,
        normalize_edit_policy,
        validate_plan,
    )
    from ..report.report_docx import write_review_report_docx
    from ..report.reporting import collect_legal_citations, render_review_report
    from .review_runtime import (
        ReviewTimeline,
        build_comment_author_display,
        resolve_review_context,
        resolve_reviewer_profile,
    )
    from ..docx_engine.reviewer import ContractReviewer
    from .comment_hygiene import resolve_orphan_comments
    from .comment_targets import (
        RESPONSE_STANCES,
        SourceComment,
        find_comment,
        load_source_comments,
    )
except ImportError:
    from action_executor import apply_finding
    from archive_service import DEFAULT_ARCHIVE_DIR, archive_run, create_archive_run_dir
    from scripts.docx_engine.pack import pack_document
    from scripts.docx_engine.quality_gate import (
        inspect_docx,
        render_docx_evidence,
        run_quality_gate,
    )
    from scripts.docx_engine.revision_views import resolve_unpacked_revisions
    from plan_loader import (
        enrich_plan,
        get_findings,
        get_plan_meta,
        load_plan,
        normalize_edit_policy,
        validate_plan,
    )
    from scripts.report.report_docx import write_review_report_docx
    from scripts.report.reporting import collect_legal_citations, render_review_report
    from review_runtime import (
        ReviewTimeline,
        build_comment_author_display,
        resolve_review_context,
        resolve_reviewer_profile,
    )
    from scripts.docx_engine.reviewer import ContractReviewer
    from comment_hygiene import resolve_orphan_comments
    from comment_targets import (
        RESPONSE_STANCES,
        SourceComment,
        find_comment,
        load_source_comments,
    )



#: GOV-008：本地操作者 / 审查人身份为自述留痕的统一表述。任何在 UI 或报告中
#: 呈现该身份的位置都必须带上它，不得宣称身份认证、电子签名或不可抵赖。
OPERATOR_IDENTITY_NOTE = (
    "本机操作者 / 审查人身份为单用户自述留痕，"
    "不构成身份认证、电子签名或不可抵赖证明。"
)

def unpack_docx(input_docx: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(input_docx) as archive:
        root = output_dir.resolve()
        for member in archive.infolist():
            target = (output_dir / member.filename).resolve()
            if target != root and root not in target.parents:
                raise ValueError(f"DOCX 包含不安全路径: {member.filename}")
        archive.extractall(output_dir)

    xml_files = list(output_dir.rglob("*.xml")) + list(output_dir.rglob("*.rels"))
    for xml_file in xml_files:
        dom = minidom.parseString(xml_file.read_bytes())
        xml_file.write_bytes(dom.toxml(encoding="utf-8"))


#: 金额识别：用于「填数三条线」的软检查（**只提示，不阻断**）。
#: 规则见 `references/redline-comment-policy.md` 1.6：天数与比例可填；
#: **具体金额应留 `【待填：金额】`**，能写成比例的（日万分之五）就不写成金额（每日 200 元）。
AMOUNT_RE = re.compile(r"(?:人民币\s*)?\d[\d,，]*(?:\.\d+)?\s*(?:万元|亿元|元)")
AMOUNT_PLACEHOLDER_HINTS = ("【待填", "【需填", "待定", "另行确认", "以实际发生为准")


def audit_replacement_amounts(findings: list[Any]) -> list[dict[str, Any]]:
    """挑出「本轮新增文本里带了具体金额、又没有标待填」的 finding。

    只报不改：这是**写作者自己的护栏**，不是发布门。引用原文里既有的金额（如附件一的报价）
    不视为新引入；写了比例（万分之五）不会被误报。
    """
    flagged: list[dict[str, Any]] = []
    for item in findings:
        if not isinstance(item, dict):
            continue
        action = str(item.get("action") or "")
        if action not in {"replace", "insert", "auto"}:
            continue
        text = str(item.get("replacement_text") or item.get("insert_text") or "")
        if not text:
            continue
        baseline = str(item.get("target_text") or item.get("search") or "")
        for match in AMOUNT_RE.finditer(text):
            snippet = match.group(0).strip()
            if snippet in baseline:
                continue
            window = text[max(0, match.start() - 16) : match.end() + 16]
            if any(hint in window for hint in AMOUNT_PLACEHOLDER_HINTS):
                continue
            flagged.append(
                {
                    "id": item.get("id"),
                    "amount": snippet,
                    "context": window.replace("\n", " "),
                    "hint": "具体金额建议改为【待填：金额】，或改写为比例（如按日万分之五）",
                }
            )
            break
    return flagged


#: 主体与资信核查的识别词（`redline-comment-policy` 四之二：**只进报告，不落批注**）。
#: 审阅件是给对方看的文本工作件——在批注里替客户表达"我不信任你的资信"，
#: 既无助于谈判，也不产生任何法律效果。
SUBJECT_CHECK_HINTS = (
    "主体资格",
    "资信",
    "履约能力",
    "营业执照",
    "失信被执行",
    "经营异常",
    "实际控制人",
    "偿付能力",
)

#: 与上表**同时命中**才报警：说明这条 finding 是在要求"去核对"，
#: 而不是把主体状态写成合同条款的触发条件（后者是正当的正文修订）。
SUBJECT_CHECK_ACTION_HINTS = ("核查", "核验", "核实", "尽调", "资信调查", "留档")

#: 保险义务方位：`common-clause-doctrine` 3.5.2 要求**只加对方义务**，
#: 不为我方创设投保义务（写成"双方各自投保"等于给自己加一项持续花钱的义务）。
INSURANCE_BURDEN_RE = re.compile(r"(甲方|我方|双方)[^。；\n]{0,24}投保")


def audit_subject_check(findings: list[Any]) -> list[dict[str, Any]]:
    """挑出「主体／资信核查却落在修订稿里」的 finding（软检查，只提示不阻断）。

    **必须同时命中"主体词"与"核对动作词"才报**：合同条款本身完全可能以
    「乙方被吊销营业执照」「列入严重违法失信名单」作为**解除或违约的触发条件**——
    那是要写进正文的内容（如 OC-SL-018 的即时解除权），不是要客户去做尽调。
    只按主体词报会把这类正确修订误判为违规（实测踩过：第一次运行时误报 1 条）。
    """
    flagged: list[dict[str, Any]] = []
    for item in findings:
        if not isinstance(item, dict):
            continue
        action = str(item.get("action") or "")
        if action not in {"comment", "replace", "insert", "auto"}:
            continue
        # 只扫「意见正文」字段：**不含 legal_basis**——那里有「经元典核验现行有效」这类固定表述，
        # "核验"二字会把正确修订误判成核查要求（实测第二次误报的根因）。
        blob = " ".join(
            str(item.get(key) or "")
            for key in ("title", "clause", "risk", "comment", "target_text")
        )
        hits = [word for word in SUBJECT_CHECK_HINTS if word in blob]
        asks_to_verify = any(word in blob for word in SUBJECT_CHECK_ACTION_HINTS)
        if hits and asks_to_verify:
            flagged.append(
                {
                    "id": item.get("id"),
                    "action": action,
                    "hits": hits,
                    "hint": (
                        "主体与资信核查应只进审查报告、不落批注/修订"
                        "（redline-comment-policy 四之二）："
                        "把 action 改为 report-only；如确属合同文本问题，请在风险说明里写明理由"
                    ),
                }
            )
    return flagged


def audit_insurance_burden(findings: list[Any]) -> list[dict[str, Any]]:
    """挑出「把投保义务加到我方或双方」的改文（软检查，只提示不阻断）。"""
    flagged: list[dict[str, Any]] = []
    for item in findings:
        if not isinstance(item, dict):
            continue
        if str(item.get("action") or "") not in {"replace", "insert", "auto"}:
            continue
        text = str(item.get("replacement_text") or item.get("insert_text") or "")
        for match in INSURANCE_BURDEN_RE.finditer(text):
            window = text[max(0, match.start() - 10) : match.end() + 12].replace("\n", " ")
            if "投保" not in window:
                continue
            flagged.append(
                {
                    "id": item.get("id"),
                    "context": window,
                    "hint": (
                        "保险义务宜只加对方（common-clause-doctrine 3.5.2）："
                        "我方为采购/委托/服务方时，让实际控制标的与作业的一方投保；"
                        "写成「双方各自投保」等于给我方加一项持续成本"
                    ),
                }
            )
            break
    return flagged


#: review plan 的 `responses[].stance` 取值与报告中显示的处理口径。
#: 定义在 `comment_targets` 里，报告侧共用同一份，避免两处漂移。
def apply_responses(
    reviewer,
    responses,
    *,
    source_comments: list[SourceComment],
) -> list[dict[str, Any]]:
    """按 `plan.responses` 对源文档批注形成**线程化回复**。

    门禁（来自实测教训，见 `references/redline-comment-policy.md`「审查人回复口径」）：

    1. `stance` 必须是四值之一；`text` 不得为空；
    2. **`stance=already_present` 必须带 `evidence`（条文号或落点）**——
       没有证据就不得声称"现稿已体现"，更不得把现稿本就有的内容写成"本轮采纳"；
    3. 源批注**在正文中无锚点**时，Word 里无法形成回复 → 记 `skipped`（由报告另行列出），
       **不得当作已回复**。

    审查人是审查人，不是当事人：回复文本用"经核对／本轮已补充／仍需填写"口径，
    不得出现"采纳、同意、接受、认可"这类**当事人表态**。
    """
    results: list[dict[str, Any]] = []
    items = responses if isinstance(responses, list) else []
    for index, item in enumerate(items, start=1):
        rid = f"RESP-{index:03d}"
        if not isinstance(item, dict):
            results.append({"id": rid, "status": "failed", "message": "response 不是对象"})
            continue
        rid = str(item.get("id") or rid)
        stance = str(item.get("stance") or "").strip()
        text = str(item.get("text") or "").strip()
        entry: dict[str, Any] = {"id": rid, "stance": stance, "status": "applied", "message": ""}

        if stance not in RESPONSE_STANCES:
            entry.update(
                status="failed",
                message=f"stance 非法：{stance!r}（允许：{'/'.join(sorted(RESPONSE_STANCES))}）",
            )
            results.append(entry)
            continue
        if not text:
            entry.update(status="failed", message="缺少回复文本")
            results.append(entry)
            continue
        evidence = str(item.get("evidence") or "").strip()
        if stance == "already_present" and not evidence:
            entry.update(
                status="failed",
                message=(
                    "「现稿已体现」类回复必须提供 evidence（条文号或其他落点）："
                    "没有证据不得声称现稿已覆盖"
                ),
            )
            results.append(entry)
            continue

        target = item.get("target") if isinstance(item.get("target"), dict) else {}
        try:
            occurrence = int(target.get("occurrence") or 1)
        except (TypeError, ValueError):
            occurrence = 1
        found = find_comment(
            source_comments,
            comment_id=target.get("comment_id"),
            anchor_text=target.get("anchor_text"),
            occurrence=occurrence,
        )
        if found is None:
            entry.update(
                status="failed",
                message="未定位到源批注（comment_id 与 anchor_text 均未命中）",
            )
            results.append(entry)
            continue

        entry["source_comment_id"] = found.comment_id
        entry["source_author"] = found.author
        entry["evidence"] = evidence
        if not found.anchored:
            entry.update(
                status="skipped",
                message="源批注在正文中无锚点，Word 中无法回复；请在报告中作为未落地意见列出",
            )
            results.append(entry)
            continue
        try:
            reply_id = reviewer.reply_to_comment(found.comment_id, text)
        except Exception as exc:  # noqa: BLE001 - 逐条降级，不影响其他回复
            entry.update(status="failed", message=f"回复失败：{exc}")
            results.append(entry)
            continue

        entry["reply_comment_id"] = reply_id
        entry["message"] = "已形成线程化回复"
        results.append(entry)
    return results


def build_execution_summary(
    applied_results: list[dict[str, Any]],
    source_docx: Path,
    plan_path: Path,
    plan_meta: dict[str, Any],
    reviewer_profile: dict[str, Any],
    review_context: dict[str, Any],
    output_docx: Path,
    report_path: Path,
    report_docx_path: Path,
    existing_revisions: str,
    existing_revision_resolution: dict[str, Any] | None,
    source_inspection: dict[str, Any],
    source_sha256: str,
    quality_gate: dict[str, Any],
) -> dict[str, Any]:
    applied = sum(1 for item in applied_results if item["status"] == "applied")
    failed = sum(1 for item in applied_results if item["status"] == "failed")
    skipped = sum(1 for item in applied_results if item["status"] == "skipped")
    report_only = sum(1 for item in applied_results if item["status"] == "report_only")
    directed_blocked = sum(
        1 for item in applied_results if item["status"] == "directed_blocked"
    )

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_docx": str(source_docx),
        "plan_path": str(plan_path),
        "plan_meta": plan_meta,
        "reviewer_profile": reviewer_profile,
        "review_context": review_context,
        "edit_policy": plan_meta.get("edit_policy"),
        "output_docx": str(output_docx),
        "report_path": str(report_path),
        "report_docx_path": str(report_docx_path),
        "existing_revisions": existing_revisions,
        "existing_revision_resolution": existing_revision_resolution,
        "source_inspection": source_inspection,
        "source_sha256": source_sha256,
        "quality_gate": quality_gate,
        "applied": applied,
        "failed": failed,
        "skipped": skipped,
        "report_only": report_only,
        "directed_blocked": directed_blocked,
        "results": applied_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="批量执行审查计划（批注/修订），并生成审查报告"
    )
    parser.add_argument("--input", required=True, help="输入 DOCX 路径")
    parser.add_argument("--plan", required=True, help="审查计划 JSON 路径")
    parser.add_argument(
        "--output",
        help="输出修订版 DOCX 路径；不传时默认生成 <原文件名>-修订版.docx（与输入同目录）",
    )
    parser.add_argument("--report", help="输出 Markdown 报告路径")
    parser.add_argument(
        "--report-docx",
        help="输出 Word 审查报告路径；不传时默认生成 <原文件名>-审查报告.docx（与输入同目录）",
    )
    parser.add_argument("--log", help="输出执行日志 JSON 路径")
    parser.add_argument(
        "--archive-dir",
        default=str(DEFAULT_ARCHIVE_DIR),
        help="归档目录（默认: one-contract/archive）",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="关闭归档功能（默认开启）",
    )
    parser.add_argument(
        "--archive-no-input",
        action="store_true",
        help="归档时不复制原始输入 DOCX",
    )
    parser.add_argument("--author", help="批注/修订作者；未提供时优先读取本地配置")
    parser.add_argument("--initials", help="批注/修订作者缩写；未提供时按姓名推导")
    parser.add_argument("--organization", help="审查报告署名中的律所/公司名称")
    parser.add_argument("--department", help="审查报告署名中的部门名称（可选）")
    parser.add_argument("--client-name", help="客户名称；未提供时优先读取历史记录或从合同主体推断")
    parser.add_argument("--party-role", help="审查立场：甲方 / 乙方 / 中立 / 其他")
    parser.add_argument(
        "--review-intensity",
        help="审查口径：克制 / 常规 / 强势（影响风险识别与表达强度，不直接决定正文落痕）",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="跳过 DOCX 校验（默认会校验）",
    )
    parser.add_argument(
        "--no-enrich-plan",
        action="store_true",
        help="关闭审查计划策略字段自动补全（默认开启）",
    )
    parser.add_argument(
        "--edit-policy",
        choices=["revise-first", "balanced", "comment-first"],
        default=None,
        help="自动分流策略；与审查口径独立，默认 revise-first（能直接改就优先修订）",
    )
    parser.add_argument(
        "--existing-revisions",
        choices=["reject", "accept-existing"],
        default="reject",
        help="既有修订策略：默认拒绝在含历史修订的段落上改写；明确选择 accept-existing 时先接受历史修订再审查",
    )
    parser.add_argument(
        "--orphan-comments",
        choices=["reject", "quarantine", "strip"],
        default="quarantine",
        help=(
            "悬空批注（comments.xml 里有、正文里无锚点）策略："
            "quarantine（默认）导出到 orphan-comments.json 后从工作副本移除；"
            "strip 仅移除并记入日志；reject 保留原样，交由质量门报错"
        ),
    )
    parser.add_argument(
        "--quality-dir",
        help="严格质量门输出目录；默认与输出 DOCX 同目录并以 _quality 结尾",
    )
    parser.add_argument(
        "--visual-policy",
        choices=["require", "allow-structural", "structural-only"],
        default="allow-structural",
        help="渲染门：require 要求 PDF/PNG；allow-structural 在无渲染环境时允许结构验证版",
    )
    args = parser.parse_args()

    input_docx = Path(args.input).expanduser().resolve()
    plan_path = Path(args.plan).expanduser().resolve()
    if args.output:
        output_docx = Path(args.output).expanduser().resolve()
    else:
        output_docx = input_docx.with_name(f"{input_docx.stem}-修订版.docx")
    quality_dir = (
        Path(args.quality_dir).expanduser().resolve()
        if args.quality_dir
        else output_docx.with_name(f"{output_docx.stem}_quality")
    )
    archive_dir = Path(args.archive_dir).expanduser().resolve()

    if not input_docx.exists():
        raise FileNotFoundError(f"输入 DOCX 不存在: {input_docx}")
    if not plan_path.exists():
        raise FileNotFoundError(f"审查计划文件不存在: {plan_path}")
    if output_docx.exists():
        raise FileExistsError(f"拒绝覆盖既有输出 DOCX: {output_docx}")
    source_sha256 = hashlib.sha256(input_docx.read_bytes()).hexdigest()
    source_inspection = inspect_docx(input_docx)

    plan = load_plan(plan_path)
    plan_meta = get_plan_meta(plan)
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    review_context = resolve_review_context(
        input_docx=input_docx,
        plan_meta=plan_meta,
        summary=summary,
        client_name=args.client_name,
        party_role=args.party_role,
        review_intensity=args.review_intensity,
        edit_policy=args.edit_policy,
    )
    edit_policy = normalize_edit_policy(
        args.edit_policy or plan_meta.get("edit_policy") or review_context.get("edit_policy"),
        default=str(review_context.get("edit_policy") or "revise-first"),
    )
    if not args.no_enrich_plan:
        plan = enrich_plan(plan, edit_policy=edit_policy)
    findings = get_findings(plan)
    plan_meta = get_plan_meta(plan)
    plan_meta["client_name"] = review_context["client_name"]
    plan_meta["party_role"] = review_context["party_role"]
    plan_meta["review_intensity"] = review_context["review_intensity"]
    plan_meta["edit_policy"] = edit_policy
    plan["meta"] = plan_meta
    validate_plan(plan)
    reviewer_profile = resolve_reviewer_profile(
        args.author,
        args.initials,
        args.organization,
        args.department,
    )
    author = str(reviewer_profile["author"])
    comment_author = build_comment_author_display(reviewer_profile)
    initials = str(reviewer_profile["initials"])
    plan_meta["reviewer"] = author
    plan_meta["reviewer_organization"] = str(
        reviewer_profile.get("organization") or ""
    )
    plan_meta["reviewer_department"] = str(
        reviewer_profile.get("department") or ""
    )
    # GOV-008：审查人身份属**单用户自述留痕**，报告记录必须写明，
    # 不得被当作身份认证、电子签名或不可抵赖证明。此前 plan meta 只写
    # reviewer/organization/department，无任何此类声明。
    plan_meta["reviewer_identity_note"] = OPERATOR_IDENTITY_NOTE
    plan["meta"] = plan_meta
    archive_path = None
    if not args.no_archive:
        archive_path = create_archive_run_dir(
            archive_dir=archive_dir,
            plan_meta=plan_meta,
            output_docx=output_docx,
        )
    input_stem = input_docx.stem
    if not args.quality_dir and archive_path is not None:
        quality_dir = archive_path / "quality"
    report_path = (
        Path(args.report).expanduser().resolve()
        if args.report
        else (
            archive_path / f"{input_stem}-审查报告.md"
            if archive_path
            else output_docx.with_name(f"{input_stem}-审查报告.md")
        )
    )
    report_docx_path = (
        Path(args.report_docx).expanduser().resolve()
        if args.report_docx
        else output_docx.with_name(f"{input_stem}-审查报告.docx")
    )
    log_path = (
        Path(args.log).expanduser().resolve()
        if args.log
        else (
            archive_path / f"{input_stem}_执行日志.json"
            if archive_path
            else output_docx.with_name(f"{input_stem}_执行日志.json")
        )
    )
    for path in (report_path, report_docx_path, log_path):
        if path.exists():
            raise FileExistsError(f"拒绝覆盖既有审查产物: {path}")
    review_timeline = ReviewTimeline(
        gap_min_minutes=int(reviewer_profile["time_gap_min_minutes"]),
        gap_max_minutes=int(reviewer_profile["time_gap_max_minutes"]),
    )

    output_docx.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_docx_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    applied_results: list[dict[str, Any]] = []
    existing_revision_resolution: dict[str, Any] | None = None

    with tempfile.TemporaryDirectory(prefix="contract-review-") as temp_dir:
        unpacked_path = Path(temp_dir) / "unpacked"
        unpack_docx(input_docx, unpacked_path)
        if args.existing_revisions == "accept-existing":
            existing_revision_resolution = resolve_unpacked_revisions(
                unpacked_path, "accept"
            )

        # 悬空批注先处置、再构造 reviewer：`Document` 会把拆包目录复制进自己的临时目录，
        # 保存时再整体写回——顺序反了，这里的清理会被 reviewer.save() 覆盖掉。
        orphan_resolution = resolve_orphan_comments(
            unpacked_path,
            policy=args.orphan_comments,
            export_path=log_path.with_name("orphan-comments.json"),
        )
        source_comments = load_source_comments(unpacked_path)

        reviewer = ContractReviewer(
            unpacked_dir=unpacked_path,
            author=comment_author,
            initials=initials,
        )

        for index, finding in enumerate(findings, start=1):
            if not isinstance(finding, dict):
                applied_results.append(
                    {
                        "id": f"R{index:03d}",
                        "action": "none",
                        "status": "failed",
                        "message": "finding 不是对象",
                    }
                )
                continue

            finding = dict(finding)
            finding.setdefault("id", f"R{index:03d}")

            try:
                reviewer.set_operation_timestamp(review_timeline.start_finding())
                result = apply_finding(reviewer, finding, edit_policy=edit_policy)
            except Exception as exc:
                result = {
                    "id": finding.get("id"),
                    "action": finding.get("action"),
                    "status": "failed",
                    "message": str(exc),
                }
            finally:
                reviewer.clear_operation_timestamp()
                review_timeline.complete_finding()
            applied_results.append(result)

        response_results = apply_responses(
            reviewer,
            plan.get("responses"),
            source_comments=source_comments,
        )

        reviewer.save(validate=not args.no_validate)
        packed = pack_document(unpacked_path, output_docx, validate=not args.no_validate)
        if not packed:
            raise ValueError("DOCX 打包校验失败，请检查计划中的 XML 变更")

    direct_applied = any(
        item.get("status") == "applied"
        and item.get("action") in {"replace", "insert", "delete"}
        for item in applied_results
    )
    try:
        quality_gate = run_quality_gate(
            output_docx,
            original_docx=input_docx,
            output_dir=quality_dir,
            baseline_view=(
                "accept" if args.existing_revisions == "accept-existing" else "reject"
            ),
            require_revisions=direct_applied,
            visual_policy=args.visual_policy,
        )
    except Exception as exc:
        quality_gate = {
            "status": "FAIL",
            "errors": [f"质量门执行异常: {exc}"],
            "output_dir": str(quality_dir),
        }
        quality_dir.mkdir(parents=True, exist_ok=True)
        failure_path = quality_dir / "quality-gate-failure.json"
        if not failure_path.exists():
            failure_path.write_text(
                json.dumps(quality_gate, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    execution_summary = build_execution_summary(
        applied_results=applied_results,
        source_docx=input_docx,
        plan_path=plan_path,
        plan_meta=plan_meta,
        reviewer_profile=reviewer_profile,
        review_context=review_context,
        output_docx=output_docx,
        report_path=report_path,
        report_docx_path=report_docx_path,
        existing_revisions=args.existing_revisions,
        existing_revision_resolution=existing_revision_resolution,
        source_inspection=source_inspection,
        source_sha256=source_sha256,
        quality_gate=quality_gate,
    )
    # 源批注的两类处置结果：对源意见的回复、悬空批注的处置（供报告与日志使用）
    execution_summary["responses"] = response_results
    execution_summary["orphan_comments"] = orphan_resolution

    # 待复核法条清单：本库条文经建库时核验，但是**冻结时点**的结论；
    # 具备法律数据库的使用方可据此逐条复核现行有效性。
    legal_citations = collect_legal_citations(findings)
    citation_path = log_path.with_name("legal-citations.json")
    citation_path.parent.mkdir(parents=True, exist_ok=True)
    citation_path.write_text(
        json.dumps(
            {
                "description": (
                    "本次审查意见书引用到的法条（取自各 finding 的 legal_basis）。"
                    "本库条文于建库时经元典核验并随文标注日期；如具备法律数据库，"
                    "建议在正式出具前逐条复核现行有效性。"
                ),
                "count": len(legal_citations),
                "citations": legal_citations,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    execution_summary["legal_citations"] = {
        "count": len(legal_citations),
        "path": str(citation_path),
    }

    # 填数三条线的软检查（只提示，不阻断）：本轮新增文本里是否带了具体金额
    amount_flags = audit_replacement_amounts(findings)
    execution_summary["amount_guard"] = {"count": len(amount_flags), "flagged": amount_flags}
    if amount_flags:
        print(
            f"提示：{len(amount_flags)} 处新增文本写入了具体金额（"
            + "、".join(f"{item['id']} {item['amount']}" for item in amount_flags[:5])
            + "）。按 redline-comment-policy 1.6，具体金额宜留【待填：金额】或改写为比例。",
            file=sys.stderr,
        )

    # 另两条口径的软检查（同样只提示）：主体核查不得落在修订稿；保险义务只加对方
    subject_flags = audit_subject_check(findings)
    insurance_flags = audit_insurance_burden(findings)
    execution_summary["subject_check_guard"] = {
        "count": len(subject_flags),
        "flagged": subject_flags,
    }
    execution_summary["insurance_burden_guard"] = {
        "count": len(insurance_flags),
        "flagged": insurance_flags,
    }
    if subject_flags:
        print(
            "提示："
            + "、".join(f"{item['id']}" for item in subject_flags[:5])
            + " 涉及主体／资信核查，却带了批注或修订动作。按 redline-comment-policy 四之二，"
            "这类核对应只进审查报告（action=report-only）。",
            file=sys.stderr,
        )
    if insurance_flags:
        print(
            "提示："
            + "、".join(f"{item['id']}" for item in insurance_flags[:5])
            + " 的改文里出现了「甲方／我方／双方…投保」。按 common-clause-doctrine 3.5.2，"
            "保险义务宜只加对方。",
            file=sys.stderr,
        )

    report_content = render_review_report(plan=plan, execution=execution_summary)
    report_path.write_text(report_content, encoding="utf-8")
    write_review_report_docx(
        markdown_content=report_content,
        output_path=report_docx_path,
        title=(
            f"{plan_meta.get('contract_name')}审查意见书"
            if plan_meta.get("contract_name")
            else "合同审查意见书"
        ),
        author=author,
        generated_at=execution_summary["generated_at"][:16],
        validate=not args.no_validate,
    )
    try:
        report_visual = render_docx_evidence(
            report_docx_path,
            output_dir=quality_dir / "render" / "report",
            visual_policy=args.visual_policy,
        )
    except Exception as exc:
        report_visual = {
            "status": "FAIL",
            "delivery_level": "blocked",
            "visual_final_eligible": False,
            "visual_inspection_status": "blocked",
            "errors": [f"审查报告渲染门异常: {exc}"],
        }
    quality_gate["report_visual_validation"] = report_visual
    if report_visual.get("status") == "FAIL":
        quality_gate["status"] = "FAIL"
        quality_gate.setdefault("errors", []).extend(
            f"report visual: {error}" for error in report_visual.get("errors", [])
        )
        quality_gate["delivery_level"] = "blocked"
    elif report_visual.get("status") == "STRUCTURAL_ONLY" and quality_gate.get("status") == "PASS":
        quality_gate["delivery_level"] = "structural_validation"
    quality_gate["visual_final_eligible"] = False
    quality_gate["visual_inspection_status"] = (
        "blocked"
        if quality_gate.get("status") != "PASS"
        else "not_performed"
        if quality_gate.get("delivery_level") == "structural_validation"
        else "required"
    )
    execution_summary["quality_gate"] = quality_gate
    quality_report_path = quality_dir / "quality-gate.json"
    quality_report_path.write_text(
        json.dumps(quality_gate, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    log_path.write_text(
        json.dumps(execution_summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if archive_path:
        archive_path = archive_run(
            archive_dir=archive_dir,
            input_docx=input_docx,
            plan_path=plan_path,
            output_docx=output_docx,
            report_path=report_path,
            report_docx_path=report_docx_path,
            log_path=log_path,
            execution_summary=execution_summary,
            include_input=not args.archive_no_input,
            run_dir=archive_path,
        )

    print(f"输出 DOCX: {output_docx}")
    print(f"输出报告 DOCX: {report_docx_path}")
    if args.report or args.no_archive:
        print(f"输出报告: {report_path}")
    if args.log or args.no_archive:
        print(f"执行日志: {log_path}")
    if archive_path:
        print(f"归档目录: {archive_path}")
    print(
        "审查上下文: "
        f"客户={review_context['client_name']}，"
        f"立场={review_context['party_role']}，"
        f"口径={review_context['review_intensity']}"
    )
    print(
        "执行统计: "
        f"成功={execution_summary['applied']}，"
        f"失败={execution_summary['failed']}，"
        f"跳过={execution_summary['skipped']}，"
        f"仅意见书={execution_summary['report_only']}"
    )
    print(f"定向阻断项: {execution_summary['directed_blocked']}")
    print(
        f"DOCX 质量门: {quality_gate['status']} / "
        f"{quality_gate.get('delivery_level', 'unknown')}（证据目录: {quality_dir}）"
    )
    if quality_gate.get("visual_inspection_status") == "required":
        print("视觉状态: 已生成逐页证据，仍须逐页检查缺字、裁切、重叠和字体替代；不得直接称为视觉终版。")
    elif quality_gate.get("visual_inspection_status") == "not_performed":
        print("视觉状态: 未完成渲染复核，仅可标注为结构验证版。")
    if execution_summary["failed"] > 0 or quality_gate["status"] != "PASS":
        if archive_path:
            print("存在失败项或质量门失败，请检查归档、执行日志与质量证据。", file=sys.stderr)
        else:
            print("存在失败项或质量门失败，请检查执行日志、报告与质量证据。", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
