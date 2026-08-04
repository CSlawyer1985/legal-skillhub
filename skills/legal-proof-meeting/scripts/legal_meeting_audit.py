#!/usr/bin/env python3
"""Offline, transparent first-pass audit for legal-risk meeting transcripts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


VERSION = "1.0.0"
TEXT_KEYS = ("text", "content", "sentence", "paragraph_text", "transcript", "words")
SPEAKER_KEYS = ("speaker_name", "speaker", "user_name", "username", "name")
TIME_KEYS = ("timestamp", "start_time", "start", "time", "offset")

EVIDENCE_TERMS = (
    "原件", "补充协议", "签章", "签字", "邮件", "聊天记录", "录音",
    "录像", "截图", "发票", "付款记录", "订单", "日志", "报表", "工单", "通知回执",
    "证人", "鉴定", "检测报告", "考勤", "考核", "原始数据",
)
CONCLUSION_TERMS = (
    "违法", "合法", "犯罪", "诈骗", "侵权", "无效", "免责", "无责", "必胜", "肯定会输",
    "可以辞退", "直接解除", "必须赔偿", "不承担责任", "肯定没有问题",
)
PROCEDURE_TERMS = (
    "授权", "审批", "通知", "送达", "回避", "书面同意", "签署", "留痕", "催告", "补救期",
    "听证", "申诉", "复核", "保全", "版本",
)
HIGH_RISK_TERMS = (
    "人身安全", "刑事", "拘留", "逮捕", "传唤", "搜查", "重大处罚", "停业", "吊销", "冻结",
    "销毁", "删除记录", "倒签", "未成年人", "商业秘密", "身份证", "银行卡", "最后期限",
)
ACTION_TERMS = ("负责", "提供", "确认", "补齐", "提交", "核验", "导出", "保全", "暂停", "复核", "发函")
UNCERTAINTY_TERMS = ("应该", "大概", "听说", "估计", "可能", "好像", "据说")

DOMAIN_TERMS = {
    "合同/交易": ("合同", "协议", "解除", "违约", "付款", "经销", "采购", "供应商"),
    "劳动用工": ("员工", "辞退", "解除劳动", "工资", "加班", "考勤", "绩效", "工伤"),
    "数据与隐私": ("个人信息", "隐私", "数据", "手机号", "身份证", "人脸", "跨境"),
    "知识产权": ("商标", "专利", "著作权", "版权", "商业秘密", "源代码"),
    "公司治理": ("股东", "董事", "表决", "章程", "授权", "关联交易", "印章"),
    "行政/刑事": ("监管", "处罚", "刑事", "犯罪", "诈骗", "调查", "举报"),
}

NUMBER_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:%|元|万元|亿元|天|日|月|年|小时|份|次|人)?")
DATE_RE = re.compile(
    r"(?:\d{4}[-/.年]\d{1,2}[-/.月]\d{1,2}日?)|(?:\d{1,2}月\d{1,2}日)|"
    r"(?:今天|明天|后天|本周|下周|本月|月底)(?:\s*\d{1,2}(?::\d{2})?点?)?"
)
LINE_RE = re.compile(
    r"^\s*(?:\[(?P<timestamp>[^\]]+)\]\s*)?"
    r"(?:(?P<speaker>[^:：\n]{1,24})[:：])?\s*(?P<text>.+?)\s*$"
)
OWNER_WITH_DUE_RE = re.compile(
    r"(?:^|[，,。；;])(?:由|请)?\s*([\u4e00-\u9fffA-Za-z·]{2,8}?)(?="
    r"(?:今天|明天|后天|本周|下周|\d{1,2}月\d{1,2}日))"
    r"(?:今天|明天|后天|本周|下周|\d{1,2}月\d{1,2}日)(?:\d{1,2}(?::\d{2})?点?)?(?:前)?\s*"
    r"(?:负责|提供|确认|补齐|提交|核验|导出|保全|暂停|复核|发函)"
)
OWNER_DIRECT_RE = re.compile(
    r"(?:由|请)\s*([\u4e00-\u9fffA-Za-z·]{2,8})\s*"
    r"(?:负责|提供|确认|补齐|提交|核验|导出|保全|暂停|复核|发函)"
)


@dataclass(frozen=True)
class Segment:
    index: int
    speaker: str
    text: str
    timestamp: str = ""


def _first(mapping: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)) and key in TIME_KEYS:
            return str(value)
    return ""


def extract_json_segments(value: Any) -> list[Segment]:
    rows: list[tuple[str, str, str]] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            text = _first(node, TEXT_KEYS)
            if text:
                rows.append((_first(node, SPEAKER_KEYS) or "未知发言人", text, _first(node, TIME_KEYS)))
                return
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    return [Segment(i + 1, speaker, text, timestamp) for i, (speaker, text, timestamp) in enumerate(rows)]


def extract_text_segments(raw: str) -> list[Segment]:
    rows: list[Segment] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        match = LINE_RE.match(line)
        if match:
            rows.append(
                Segment(
                    len(rows) + 1,
                    (match.group("speaker") or "未知发言人").strip(),
                    match.group("text").strip(),
                    (match.group("timestamp") or "").strip(),
                )
            )
    if not rows and raw.strip():
        rows.append(Segment(1, "未知发言人", raw.strip()))
    return rows


def parse_input(path: str) -> tuple[list[Segment], str]:
    if path == "-":
        raw, source = sys.stdin.read(), "stdin"
    else:
        file = Path(path)
        raw, source = file.read_text(encoding="utf-8-sig"), file.name
    if raw.lstrip().startswith(("{", "[")):
        try:
            segments = extract_json_segments(json.loads(raw))
            if segments:
                return segments, source
        except json.JSONDecodeError:
            pass
    return extract_text_segments(raw), source


def _hits(text: str, terms: tuple[str, ...]) -> list[str]:
    return [term for term in terms if term in text]


def _owner(segment: Segment) -> str:
    for pattern in (OWNER_WITH_DUE_RE, OWNER_DIRECT_RE):
        match = pattern.search(segment.text)
        if match:
            return match.group(1)
    if segment.speaker != "未知发言人" and any(term in segment.text for term in ACTION_TERMS):
        if re.search(r"我(?:来|负责|会|可以)", segment.text):
            return segment.speaker
    return ""


def analyze(segments: list[Segment], source: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    domains: set[str] = set()
    actions: list[dict[str, Any]] = []

    for segment in segments:
        text = segment.text
        evidence = _hits(text, EVIDENCE_TERMS)
        conclusions = _hits(text, CONCLUSION_TERMS)
        procedures = _hits(text, PROCEDURE_TERMS)
        high_risk = _hits(text, HIGH_RISK_TERMS)
        uncertainty = _hits(text, UNCERTAINTY_TERMS)
        factual_anchor = bool(NUMBER_RE.search(text) or DATE_RE.search(text) or evidence)
        overreach = bool(conclusions and not (evidence or procedures))
        owner = _owner(segment)
        due_match = DATE_RE.search(text)
        action_terms = _hits(text, ACTION_TERMS)

        for domain, terms in DOMAIN_TERMS.items():
            if any(term in text for term in terms):
                domains.add(domain)

        if action_terms:
            missing = []
            if not owner:
                missing.append("责任人")
            if not due_match:
                missing.append("期限")
            actions.append(
                {
                    "segment": segment.index,
                    "owner": owner or "未明确",
                    "due": due_match.group(0) if due_match else "未明确",
                    "action_signals": action_terms,
                    "missing": missing,
                    "text": text,
                }
            )

        rows.append(
            {
                **asdict(segment),
                "factual_anchor": factual_anchor,
                "evidence_signals": evidence,
                "legal_conclusions": conclusions,
                "procedure_signals": procedures,
                "high_risk_signals": high_risk,
                "uncertainty_signals": uncertainty,
                "conclusion_overreach": overreach,
            }
        )

    relevant = [row for row in rows if row["legal_conclusions"] or row["evidence_signals"] or row["procedure_signals"]]
    supported = [row for row in relevant if row["evidence_signals"] and row["factual_anchor"]]
    evidence_completeness = round(100 * len(supported) / len(relevant)) if relevant else 0
    overreach_count = sum(1 for row in rows if row["conclusion_overreach"])

    all_text = "\n".join(segment.text for segment in segments)
    procedure_debt = []
    if relevant:
        checks = {
            "授权/审批": ("授权", "审批"),
            "通知/送达": ("通知", "送达", "回执", "催告"),
            "版本/留痕": ("版本", "留痕", "原件", "签章"),
        }
        procedure_debt = [name for name, terms in checks.items() if not any(term in all_text for term in terms)]

    high_risk_count = sum(len(row["high_risk_signals"]) for row in rows)
    if any(term in all_text for term in ("销毁", "删除记录", "倒签", "人身安全")):
        level = "红色"
    elif high_risk_count or (overreach_count and evidence_completeness < 60):
        level = "橙色"
    elif overreach_count or procedure_debt:
        level = "黄色"
    else:
        level = "绿色"

    return {
        "meta": {"version": VERSION, "source": source, "segments": len(segments)},
        "verdict": {
            "risk_level": level,
            "evidence_completeness": evidence_completeness,
            "conclusion_overreach_count": overreach_count,
            "procedure_debt_count": len(procedure_debt),
        },
        "domains": sorted(domains),
        "procedure_debt": procedure_debt,
        "actions": actions,
        "evidence_ledger": rows,
        "notice": "规则初筛不构成法律意见；所有命中须结合原文、法域和现行规则复核。",
    }


def _table(rows: list[list[Any]], headers: list[str]) -> str:
    safe = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines.extend("| " + " | ".join(safe(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def render_markdown(result: dict[str, Any]) -> str:
    verdict = result["verdict"]
    lines = [
        "# 法槌会议规则初筛",
        "",
        f"- 风险交通灯：**{verdict['risk_level']}**",
        f"- 举证完整度：**{verdict['evidence_completeness']} / 100**",
        f"- 定性越界：**{verdict['conclusion_overreach_count']} 处**",
        f"- 程序债：**{verdict['procedure_debt_count']} 类**",
        f"- 涉及领域：{('、'.join(result['domains']) or '未识别')}",
        "",
        "## 定性与证据账本",
        "",
        _table(
            [
                [
                    row["index"], row["speaker"],
                    "、".join(row["legal_conclusions"]) or "-",
                    "、".join(row["evidence_signals"]) or "-",
                    "是" if row["conclusion_overreach"] else "否",
                    row["text"],
                ]
                for row in result["evidence_ledger"]
            ],
            ["段落", "发言人", "法律定性", "证据线索", "越界", "原文"],
        ),
        "",
        "## 程序债",
        "",
        "、".join(result["procedure_debt"]) or "未发现规则级程序缺口",
        "",
        "## 行动闭环",
        "",
    ]
    if result["actions"]:
        lines.append(
            _table(
                [[item["segment"], item["owner"], item["due"], "、".join(item["missing"]) or "完整", item["text"]] for item in result["actions"]],
                ["段落", "责任人", "期限", "缺口", "原文"],
            )
        )
    else:
        lines.append("未识别到行动项。")
    lines.extend(["", f"> {result['notice']}"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline legal-risk meeting audit")
    parser.add_argument("--input", required=True, help="UTF-8 .txt/.md/.json path, or - for stdin")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", help="Optional output path")
    parser.add_argument("--version", action="version", version=VERSION)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        segments, source = parse_input(args.input)
    except (OSError, UnicodeError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2
    if not segments:
        print("input error: no usable transcript segments found", file=sys.stderr)
        return 2
    result = analyze(segments, source)
    output = json.dumps(result, ensure_ascii=False, indent=2) if args.format == "json" else render_markdown(result)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    else:
        sys.stdout.write(output + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
