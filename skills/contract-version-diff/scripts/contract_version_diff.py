#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


def ensure_out(path):
    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    return out


def read_text(path):
    return Path(path).read_text(encoding="utf-8-sig", errors="replace")


def write_text(path, text):
    Path(path).write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_csv(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames=None):
    rows = list(rows)
    fieldnames = fieldnames or (list(rows[0].keys()) if rows else [])
    with Path(path).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def value(row, *keys, default=""):
    for key in keys:
        if key in row and str(row[key]).strip() != "":
            return row[key]
    return default


def to_float(raw, default=0.0):
    try:
        text = str(raw).strip().replace(",", "")
        if text.endswith("%"):
            return float(text[:-1]) / 100
        return float(text)
    except (TypeError, ValueError):
        return default


def parse_date(raw):
    text = str(raw).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError(f"无法识别日期: {raw}")


def clamp(number, low=0, high=100):
    return max(low, min(high, number))


def md_table(rows, headers):
    def clean(item):
        return str(item).replace("|", "/").replace("\n", " ")
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(clean(row.get(h, "")) for h in headers) + " |")
    return "\n".join(lines)


def tokens(text):
    chinese = re.findall(r"[\u4e00-\u9fff]{2,6}", text)
    english = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.lower())
    stop = {"以及", "进行", "需要", "可以", "一个", "这个", "相关", "用户", "项目", "系统", "提供", "要求"}
    return [item for item in chinese + english if item not in stop]


def clip(text, limit=100):
    clean = re.sub(r"\s+", " ", str(text)).strip()
    return clean if len(clean) <= limit else clean[: limit - 3] + "..."

RISK_AREAS = {
    "付款": ["付款", "支付", "费用", "价款", "发票", "账期"],
    "责任赔偿": ["违约", "赔偿", "责任", "罚金", "损失", "上限"],
    "终止解除": ["终止", "解除", "到期", "续约", "单方"],
    "知识产权": ["知识产权", "著作权", "专利", "商标", "成果归属"],
    "保密": ["保密", "商业秘密", "披露"],
    "数据隐私": ["数据", "隐私", "个人信息", "跨境", "删除"],
    "争议管辖": ["管辖", "仲裁", "法院", "法律适用"],
}


def clauses(text):
    result = []
    for line in text.splitlines():
        clean = re.sub(r"^[#>*\-\s]+", "", line).strip()
        if len(clean) >= 5:
            result.append(clean)
    if len(result) < 2:
        result = [part.strip() for part in re.split(r"(?<=[。；;])", text) if len(part.strip()) >= 5]
    return result


def areas_for(text):
    return [label for label, keys in RISK_AREAS.items() if any(key in text for key in keys)] or ["一般条款"]


def severity(change_type, areas, text):
    score = 25 + len(areas) * 12
    if change_type in {"删除", "修改"}:
        score += 15
    if any(word in text for word in ["无限", "全部损失", "单方", "自动续约", "不可撤销", "立即终止"]):
        score += 30
    if "一般条款" not in areas:
        score += 15
    if set(areas) & {"责任赔偿", "终止解除", "知识产权", "数据隐私", "争议管辖"}:
        score += 15
    return "高" if score >= 70 else "中" if score >= 45 else "低"


def main():
    ap = argparse.ArgumentParser(description="对比合同版本并标记风险条款变化")
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--out", default="contract-diff-output")
    args = ap.parse_args()
    old_text = read_text(args.old)
    new_text = read_text(args.new)
    old_clauses = clauses(old_text)
    new_clauses = clauses(new_text)
    matcher = difflib.SequenceMatcher(a=old_clauses, b=new_clauses, autojunk=False)
    changes = []
    index = 1

    def add_change(change_type, old_part, new_part):
        nonlocal index
        combined = old_part + " " + new_part
        areas = areas_for(combined)
        changes.append({
            "id": f"D{index:03d}", "type": change_type, "risk": severity(change_type, areas, combined),
            "areas": ",".join(areas), "old_clause": clip(old_part, 180) or "-", "new_clause": clip(new_part, 180) or "-",
            "review_question": "该变化是否扩大我方义务、缩短履行期限或削弱救济？",
        })
        index += 1

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old_block = old_clauses[i1:i2]
        new_block = new_clauses[j1:j2]
        if tag == "replace":
            for offset in range(max(len(old_block), len(new_block))):
                old_part = old_block[offset] if offset < len(old_block) else ""
                new_part = new_block[offset] if offset < len(new_block) else ""
                add_change("修改" if old_part and new_part else "删除" if old_part else "新增", old_part, new_part)
        elif tag == "delete":
            for old_part in old_block:
                add_change("删除", old_part, "")
        else:
            for new_part in new_block:
                add_change("新增", "", new_part)
    changes.sort(key=lambda item: ({"高": 0, "中": 1, "低": 2}[item["risk"]], item["id"]))
    diff = "\n".join(difflib.unified_diff(old_text.splitlines(), new_text.splitlines(), fromfile="old_contract", tofile="new_contract", lineterm=""))
    out = ensure_out(args.out)
    write_csv(out / "clause_changes.csv", changes)
    write_text(out / "contract_diff.txt", diff or "两个文件没有文本差异。")
    summary = {"change_count": len(changes), "high_risk": sum(item["risk"] == "高" for item in changes), "changes": changes, "disclaimer": "仅用于文本差异定位，不构成法律意见。"}
    write_json(out / "contract_risk_report.json", summary)
    md = "# 合同版本差异审查报告\n\n"
    md += f"- 条款变化：{len(changes)}\n- 高风险变化：{summary['high_risk']}\n"
    md += "\n## 风险变化清单\n\n" + (md_table(changes, ["id", "type", "risk", "areas", "old_clause", "new_clause", "review_question"]) if changes else "未发现文本变化。")
    md += "\n\n> 本报告不构成法律意见，签署前请由专业法务复核。\n"
    write_text(out / "contract_risk_report.md", md)
    print(f"Compared contract versions with {len(changes)} change blocks into {out}")


if __name__ == "__main__":
    main()
