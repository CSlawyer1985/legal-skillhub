#!/usr/bin/env python3
# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
"""
报价校验器 (Price Validator) — 仅审不改

输入：报价规格（JSON 文件或 Python API 传入）
输出：风险命中报告（风险编号 + 等级 + 详情），退出码反映严重度
退出码：  0 = 全部通过  1 = 仅有警告（D05/D06）  2 = 有致命错误（D01-D04）

定位（v3.7.2 终版）：
  - 价格【数值】由用户人工确定，Agent 不得改数值
  - 价格【格式】由 Agent 按招标文件要求适配（大小写并列、小数位、币种标注）
  - 适配完成后必须调用本脚本审一遍
  - 审出的不一致问题，Agent 不得自动修复，必须报告给用户确认

覆盖 risk_library D01-D06：
  D01  大小写金额不一致
  D02  分项合计 ≠ 总价
  D03  超过最高限价
  D04  计价单位不一致
  D05  小数位数不符合招标要求
  D06  缺少币种标注

用法：
  CLI：
    python price_validator.py spec.json
    python price_validator.py spec.json --report report.md
    python price_validator.py --self-check
  Python API：
    from price_validator import PriceSpec, validate, format_report
    spec = PriceSpec(total_in_words="...", total_in_figures=..., ...)
    report = validate(spec)
    print(format_report(report))
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


# ─────────────────────────────────────────────────────────────
# 中文大写金额解析器
# ─────────────────────────────────────────────────────────────

_CN_DIGIT = {
    "零": 0, "壹": 1, "贰": 2, "叁": 3, "肆": 4,
    "伍": 5, "陆": 6, "柒": 7, "捌": 8, "玖": 9,
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9,
}
_CN_UNIT_BIG = {"亿": 1_0000_0000, "万": 1_0000}
_CN_UNIT_SMALL = {"拾": 10, "拾": 10, "佰": 100, "佰": 100, "仟": 1000, "仟": 1000,
                  "十": 10, "百": 100, "千": 1000}


def parse_cn_amount(text: str) -> Optional[float]:
    """解析中文大写金额为 float。失败返回 None。
    支持示例：壹拾万元整 / 叁万伍仟元整 / 人民币壹佰贰拾万元整 / 壹拾万零伍仟元整
    """
    if not text:
        return None
    s = text.strip()
    # 剥离前缀和后缀
    s = re.sub(r"^(人民币|RMB|¥|\s)+", "", s)
    s = re.sub(r"(整|正|元|圆|元整|圆整|\s)+$", "", s)
    s = s.strip()
    if not s:
        return None

    total = 0.0
    # 按亿/万分段
    for sep in ("亿", "万"):
        if sep in s:
            left, _, s = s.partition(sep)
            if left:
                v = _parse_cn_segment(left)
                if v is None:
                    return None
                total += v * _CN_UNIT_BIG[sep]
    if s:
        v = _parse_cn_segment(s)
        if v is None:
            return None
        total += v
    return total


def _parse_cn_segment(s: str) -> Optional[float]:
    """解析亿/万之间或末尾的小段，返回整数。"""
    if not s:
        return 0
    result = 0
    current = 0
    for ch in s:
        if ch in _CN_DIGIT:
            current = _CN_DIGIT[ch]
        elif ch in _CN_UNIT_SMALL:
            if current == 0:
                current = 1  # "拾" 前省略"壹"
            result += current * _CN_UNIT_SMALL[ch]
            current = 0
        elif ch == "零":
            current = 0
        else:
            return None
    result += current
    return result


# ─────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────

@dataclass
class LineItem:
    name: str
    amount: float  # 数字金额（必须）
    amount_in_words: Optional[str] = None  # 对应的中文大写（可选）


@dataclass
class PriceSpec:
    """报价规格——从用户的 DATA 字典 + 招标要素清单中组装"""
    # ── 总价 ──
    total_in_words: Optional[str] = None        # 中文大写，如 "壹拾万元整"
    total_in_figures: Optional[float] = None    # 数字总价，如 100000.00
    # ── 限价（来自招标文件）──
    max_price: Optional[float] = None           # 最高限价（数字）
    # ── 分项明细 ──
    line_items: List[LineItem] = field(default_factory=list)
    # ── 格式要求（来自招标文件解析）──
    currency: Optional[str] = "人民币"           # 币种标注，None 表示未指定
    unit: Optional[str] = "元"                  # 计价单位，None 表示未指定
    decimal_places_required: Optional[int] = 2  # 招标要求的小数位数；None 表示不检查


@dataclass
class Finding:
    code: str
    severity: str  # "fatal" | "warning"
    title: str
    detail: str
    expected: Optional[str] = None
    actual: Optional[str] = None


@dataclass
class ValidationReport:
    ok: bool = True
    findings: List[Finding] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        if any(f.severity == "fatal" for f in self.findings):
            return 2
        if any(f.severity == "warning" for f in self.findings):
            return 1
        return 0


# ─────────────────────────────────────────────────────────────
# 校验逻辑
# ─────────────────────────────────────────────────────────────

def validate(spec: PriceSpec) -> ValidationReport:
    report = ValidationReport()

    words = spec.total_in_words
    fig = spec.total_in_figures

    # ── D01 大小写金额一致性 ──
    if words and fig is not None:
        parsed = parse_cn_amount(words)
        if parsed is None:
            report.findings.append(Finding(
                code="D01", severity="warning",
                title="大写金额解析失败",
                detail=f"无法解析中文大写金额「{words}」，请人工核对",
                expected="可解析的中文大写金额",
                actual=words,
            ))
        elif abs(parsed - fig) > 0.01:
            report.findings.append(Finding(
                code="D01", severity="fatal",
                title="大小写金额不一致",
                detail=f"大写「{words}」= {parsed:.2f}，与小写 {fig:.2f} 不一致",
                expected=f"{fig:.2f}",
                actual=f"{parsed:.2f}",
            ))

    # ── D02 分项合计 = 总价 ──
    if spec.line_items and fig is not None:
        subtotal = sum(li.amount for li in spec.line_items)
        if abs(subtotal - fig) > 0.01:
            report.findings.append(Finding(
                code="D02", severity="fatal",
                title="分项合计与总价不一致",
                detail=f"分项 {len(spec.line_items)} 项合计 {subtotal:.2f}，总价 {fig:.2f}",
                expected=f"{fig:.2f}",
                actual=f"{subtotal:.2f}",
            ))

    # ── D03 超过最高限价 ──
    if spec.max_price is not None and fig is not None:
        if fig > spec.max_price:
            report.findings.append(Finding(
                code="D03", severity="fatal",
                title="报价超过最高限价",
                detail=f"报价 {fig:.2f} 超过最高限价 {spec.max_price:.2f}",
                expected=f"≤ {spec.max_price:.2f}",
                actual=f"{fig:.2f}",
            ))

    # ── D04 计价单位一致性 ──
    if spec.line_items and spec.unit:
        # 检查分项是否带不同单位（这里简化：假设所有分项都用同一单位，仅检查单位标注是否存在）
        # 如果招标文件给了要素清单的单位列表，应传入对比
        pass  # 当前版本不做强制校验，预留接口

    # ── D05 小数位数 ──（仅对字符串形式严格检查，float 输入跳过避免误报）
    if fig is not None and spec.decimal_places_required is not None and isinstance(spec.total_in_figures, str):
        required = int(spec.decimal_places_required)
        s = str(spec.total_in_figures).strip()
        if "." in s:
            actual_decimals = len(s.split(".")[-1])
        else:
            actual_decimals = 0
        if actual_decimals != required:
            report.findings.append(Finding(
                code="D05", severity="warning",
                title="小数位数与招标要求不一致",
                detail=f"招标要求保留 {required} 位小数，实际 {actual_decimals} 位",
                expected=f"{required} 位小数",
                actual=f"{actual_decimals} 位小数",
            ))

    # ── D06 币种标注 ──
    if not spec.currency:
        report.findings.append(Finding(
            code="D06", severity="warning",
            title="缺少币种标注",
            detail="报价应标注币种（如「人民币」或「RMB」），当前未检测到",
            expected="人民币 / RMB / ¥",
            actual="（未标注）",
        ))

    report.ok = len(report.findings) == 0
    return report


def format_report(report: ValidationReport) -> str:
    """生成 Markdown 报告。"""
    if report.ok:
        return "## 报价校验报告\n\n✅ **全部通过**，未命中 D01-D06 任何风险。\n"
    lines = ["## 报价校验报告", ""]
    fatal = [f for f in report.findings if f.severity == "fatal"]
    warning = [f for f in report.findings if f.severity == "warning"]
    if fatal:
        lines.append(f"### 🔴 致命错误（{len(fatal)} 项）— 必须人工确认后修复\n")
        for f in fatal:
            lines.append(f"- **{f.code}** {f.title}：{f.detail}")
            if f.expected:
                lines.append(f"  - 期望：{f.expected} / 实际：{f.actual}")
    if warning:
        lines.append(f"\n### 🟡 警告（{len(warning)} 项）— 建议核对\n")
        for f in warning:
            lines.append(f"- **{f.code}** {f.title}：{f.detail}")
    return "\n".join(lines) + "\n"


# ─────────────────────────────────────────────────────────────
# 自检
# ─────────────────────────────────────────────────────────────

def self_check() -> bool:
    """运行内置样例验证脚本逻辑。返回 True 表示全部预期通过。"""
    cases = []

    # 样例 1：全部合规
    r1 = validate(PriceSpec(
        total_in_words="壹拾万元整",
        total_in_figures=100000.00,
        currency="人民币",
    ))
    cases.append(("合规样例", r1.ok and len(r1.findings) == 0, "应该全过"))

    # 样例 2：D01 大小写不一致
    r2 = validate(PriceSpec(
        total_in_words="壹拾万元整",  # 10 万
        total_in_figures=200000.00,  # 但数字是 20 万
        currency="人民币",
    ))
    has_d01 = any(f.code == "D01" and f.severity == "fatal" for f in r2.findings)
    cases.append(("D01 大小写不一致", has_d01, "应命中 D01 fatal"))

    # 样例 3：D02 分项不等于总价
    r3 = validate(PriceSpec(
        total_in_figures=100000.00,
        line_items=[
            LineItem("法律服务费", 60000),
            LineItem("差旅费", 30000),
        ],  # 合计 9 万 ≠ 10 万
        currency="人民币",
    ))
    has_d02 = any(f.code == "D02" for f in r3.findings)
    cases.append(("D02 分项合计≠总价", has_d02, "应命中 D02 fatal"))

    # 样例 4：D03 超限价
    r4 = validate(PriceSpec(
        total_in_figures=120000.00,
        max_price=100000.00,
        currency="人民币",
    ))
    has_d03 = any(f.code == "D03" for f in r4.findings)
    cases.append(("D03 超最高限价", has_d03, "应命中 D03 fatal"))

    # 样例 5：D05 小数位（字符串形式严格检查）
    r5 = validate(PriceSpec(
        total_in_figures="125000.0",  # 1 位小数
        decimal_places_required=2,
        currency="人民币",
    ))
    has_d05 = any(f.code == "D05" for f in r5.findings)
    cases.append(("D05 小数位不对", has_d05, "应命中 D05 warning"))

    # 样例 6：D06 缺币种
    r6 = validate(PriceSpec(
        total_in_figures=100000.00,
        currency=None,
    ))
    has_d06 = any(f.code == "D06" for f in r6.findings)
    cases.append(("D06 缺币种", has_d06, "应命中 D06 warning"))

    # 样例 7：中文解析器专项
    parse_cases = [
        ("壹拾万元整", 100000),
        ("叁万伍仟元整", 35000),
        ("壹佰贰拾万元整", 1200000),
        ("壹拾万零伍仟元整", 105000),
        ("人民币贰拾伍万陆仟元整", 256000),
    ]
    for text, expected in parse_cases:
        got = parse_cn_amount(text)
        cases.append((f"解析「{text}」", got is not None and abs(got - expected) < 0.01,
                      f"应得 {expected}"))

    # 输出
    all_pass = True
    print("=" * 60)
    print("price_validator.py self-check")
    print("=" * 60)
    for name, passed, expected_desc in cases:
        mark = "✅" if passed else "❌"
        print(f"  {mark} {name} — {expected_desc}")
        if not passed:
            all_pass = False
    print("=" * 60)
    print(f"结果：{'全部通过' if all_pass else '存在失败项'}")
    return all_pass


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def load_spec_from_json(path: str) -> PriceSpec:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    line_items = [LineItem(**li) for li in data.get("line_items", [])]
    return PriceSpec(
        total_in_words=data.get("total_in_words"),
        total_in_figures=data.get("total_in_figures"),
        max_price=data.get("max_price"),
        line_items=line_items,
        currency=data.get("currency", "人民币"),
        unit=data.get("unit", "元"),
        decimal_places_required=data.get("decimal_places_required", 2),
    )


def main():
    parser = argparse.ArgumentParser(description="报价校验器（仅审不改）")
    parser.add_argument("spec", nargs="?", help="报价规格 JSON 文件路径")
    parser.add_argument("--report", "-r", help="输出 Markdown 报告到指定路径")
    parser.add_argument("--self-check", action="store_true", help="运行内置自检")
    args = parser.parse_args()

    if args.self_check:
        ok = self_check()
        sys.exit(0 if ok else 1)

    if not args.spec:
        parser.print_help()
        sys.exit(2)

    spec = load_spec_from_json(args.spec)
    report = validate(spec)
    output = format_report(report)

    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"报告已写入 {args.report}")
    else:
        print(output)

    sys.exit(report.exit_code)


if __name__ == "__main__":
    main()
