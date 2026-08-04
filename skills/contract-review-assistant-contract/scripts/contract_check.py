#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contract_check.py — 合同结构性/确定性检查工具。

对合同文本执行可重复、确定性的检查，输出 JSON，供「合同检查智能小助手」
Skill 在生成风险审查报告时直接引用。它不做法律判断，只做文本与结构层的事实抽取。

功能：
  1. 必备条款缺失检测（基于 contract-basics.md 第二节的通用必备要素）
  2. 占位符 / 空白字段检测（XXX、____、【】、待填、TBD 等）
  3. 条款编号连续性（第X条 是否缺号 / 重复）
  4. 金额与日期抽取（供人工交叉核对前后一致性）
  5. 签名行检测 + 签名笔迹比对请求标记

用法：
  python3 contract_check.py contract.txt [--json] [--sig-img a.png b.png]
  cat contract.txt | python3 contract_check.py -

依赖：仅标准库。
"""
import sys
import re
import json
import argparse

# 通用必备要素（名称, 关键词，命中任一即视为存在）
CORE_SECTIONS = [
    ("当事人信息", ["当事人", "甲方", "乙方", "双方", "主体", "统一社会信用代码"]),
    ("标的", ["标的", "合作内容", "服务内容", "买卖", "采购", "租赁物"]),
    ("数量与质量", ["数量", "质量", "规格", "标准", "验收"]),
    ("价款/报酬", ["价款", "报酬", "金额", "费用", "服务费", "单价", "总价", "元"]),
    ("履行期限/地点/方式", ["履行", "交付", "付款期限", "交货", "期限", "地点", "方式"]),
    ("违约责任", ["违约", "违约责任", "赔偿金", "违约金"]),
    ("争议解决/管辖", ["争议", "仲裁", "诉讼", "管辖", "法院", "仲裁委员会"]),
    ("生效与终止", ["生效", "终止", "解除", "有效期", "合同期限"]),
]
COMMON_SECTIONS = [
    ("保密", ["保密"]),
    ("知识产权", ["知识产权", "著作权", "专利", "商标", "版权"]),
    ("不可抗力", ["不可抗力"]),
]

# 占位符 / 未填标记
PLACEHOLDER_PATTERNS = [
    re.compile(r"X{3,}", re.IGNORECASE),
    re.compile(r"_{3,}"),
    re.compile(r"\.{3,}"),
    re.compile(r"…{2,}"),
    re.compile(r"【\s*】"),
    re.compile(r"\[\s*\]"),
    re.compile(r"(待定|待填|待补充|待协商|待明确|TBD|todo|此处填写|空白|未填)"),
]

CN_NUM = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
          "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "百": 100, "千": 1000}
# 中文数字：简体(一二三…)与财务大写(壹贰叁…)均需覆盖，合同金额常用后者防篡改
DIGITS = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
          "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
          "壹": 1, "贰": 2, "叁": 3, "肆": 4, "伍": 5, "陆": 6,
          "柒": 7, "捌": 8, "玖": 9}
UNITS = {"十": 10, "百": 100, "千": 1000, "万": 10000, "亿": 100000000,
         "拾": 10, "佰": 100, "仟": 1000}


def cn_to_number(s: str):
    """中文数字/金额（含万、亿，兼容简体与财务大写）转 int。
    例：壹拾万->100000，贰拾->20，三万五千->35000。"""
    if s.isdigit():
        return int(s)
    total, section, num = 0, 0, 0
    for ch in s:
        if ch in UNITS:
            u = UNITS[ch]
            if u >= 10000:
                section = (section + num) * u
                total += section
                section = 0
            else:
                section += num * u
            num = 0
        elif ch in DIGITS:
            num = DIGITS[ch]
        else:
            return None
    return total + section + num


def cn_to_int(s: str) -> int:
    """将简单中文数字（如 十二、一百零三）转为 int。"""
    if s.isdigit():
        return int(s)
    total, cur, prev = 0, 0, 0
    for ch in s:
        if ch in ("十", "百", "千"):
            unit = CN_NUM[ch]
            if cur == 0:
                cur = 1
            total += cur * unit
            cur = 0
        elif ch in CN_NUM:
            cur = CN_NUM[ch]
        else:
            return None
    return total + cur


def detect_sections(text: str, sections):
    missing = []
    for name, keywords in sections:
        if not any(k in text for k in keywords):
            missing.append(name)
    return missing


def find_placeholders(text: str):
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        for pat in PLACEHOLDER_PATTERNS:
            for m in pat.finditer(line):
                out.append({"line": i, "text": m.group(0),
                            "snippet": line.strip()[:80]})
    return out


def clause_numbering(text: str):
    nums = []
    for m in re.finditer(r"第\s*([一二三四五六七八九十百零0-9]+)\s*条", text):
        v = cn_to_int(re.sub(r"\s+", "", m.group(1)))
        if v is not None:
            nums.append(v)
    dups = sorted({n for n in nums if nums.count(n) > 1})
    present = sorted(set(nums))
    missing = [n for n in range(1, (present[-1] if present else 1) + 1)
               if n not in set(nums)] if present else []
    return {"found": present, "duplicates": dups, "missing": missing}


def extract_amounts(text: str):
    pats = [
        r"(?:人民币|RMB|¥)?\s*[\d,]+(?:\.\d{1,2})?\s*元",
        r"[\d,]+(?:\.\d{1,2})?\s*(?:万|亿)\s*元",
        # 括号内的阿拉伯金额，如「（¥100,000）」「（人民币 50,000）」等
        r"¥\s*[\d,]+(?:\.\d{1,2})?",
        r"人民币\s*[\d,]+(?:\.\d{1,2})?\s*(?:万|亿)?\s*元?",
    ]
    out = []
    for p in pats:
        for m in re.finditer(p, text):
            out.append(m.group(0).strip())
    return sorted(set(out))


# 被标注为"总额/总费用"等的总金额关键词（用于一致性比对）
TOTAL_KW = ["总费用", "总额", "总价", "总价款", "合同金额",
            "合同总价", "本合同总", "总报酬", "总承包"]


def extract_amount_inconsistencies(text: str):
    """抽取被标注为总金额的数值（中文大写与阿拉伯两种），若数值不一致则标记。

    仅当某金额前的上下文出现 TOTAL_KW 时才视为"合同总额"，避免把正常的
    分期/单价款项误判为矛盾。返回 {totals, inconsistencies}。
    """
    pats = [
        (r"(?:人民币|RMB|¥)?\s*(\d[\d,]*(?:\.\d{1,2})?)\s*(万|亿)?\s*元", "arabic"),
        (r"([零〇一二三四五六七八九壹贰叁肆伍陆柒捌玖][零〇一二三四五六七八九十百千万亿壹贰叁肆伍陆柒捌玖拾佰仟]*)\s*元整?", "cn"),
    ]
    totals = []
    for pat, kind in pats:
        for m in re.finditer(pat, text):
            if kind == "arabic":
                val = float(m.group(1).replace(",", ""))
                if m.group(2) == "万":
                    val *= 10000
                elif m.group(2) == "亿":
                    val *= 100000000
            else:
                val = cn_to_number(m.group(1))
                if val is None:
                    continue
            ctx = text[max(0, m.start() - 30):m.start()]
            if any(k in ctx for k in TOTAL_KW):
                totals.append({"value": val, "raw": m.group(0).strip(),
                               "context": ctx.strip()[-30:]})
    values = {t["value"] for t in totals}
    inconsistencies = []
    if len(values) > 1:
        for i in range(len(totals)):
            for j in range(i + 1, len(totals)):
                if totals[i]["value"] != totals[j]["value"]:
                    inconsistencies.append({"a": totals[i], "b": totals[j]})
    return {"totals": totals, "inconsistencies": inconsistencies}


def extract_dates(text: str):
    pats = [
        r"\d{4}\s*[-/年]\s*\d{1,2}\s*[-/月]\s*\d{1,2}\s*日?",
        r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日",
    ]
    out = []
    for p in pats:
        for m in re.finditer(p, text):
            out.append(m.group(0).strip())
    return sorted(set(out))


def has_signature_line(text: str):
    return bool(re.search(r"(签字|盖章|签名|签章|按指印|授权代表)", text))


def main():
    ap = argparse.ArgumentParser(description="合同结构性检查工具")
    ap.add_argument("path", help="合同文本路径，或 '-' 从 stdin 读取")
    ap.add_argument("--json", action="store_true", help="仅输出 JSON")
    ap.add_argument("--sig-img", nargs="*", default=[],
                    help="传入签名图片路径，标记已请求笔迹比对")
    args = ap.parse_args()

    if args.path == "-":
        text = sys.stdin.read()
    else:
        with open(args.path, "r", encoding="utf-8") as f:
            text = f.read()

    result = {
        "missing_core_sections": detect_sections(text, CORE_SECTIONS),
        "missing_common_sections": detect_sections(text, COMMON_SECTIONS),
        "placeholders": find_placeholders(text),
        "clause_numbering": clause_numbering(text),
        "amounts": extract_amounts(text),
        "amount_inconsistencies": extract_amount_inconsistencies(text),
        "dates": extract_dates(text),
        "signature_line_present": has_signature_line(text),
        "signature_comparison_requested": bool(args.sig_img),
        "signature_images": args.sig_img,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
