#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
条款推荐引擎 (Clause Recommender)

根据合同类型、已识别风险、关键词，智能推荐条款库中的替代条款。

用法：
    python3 scripts/clause_recommender.py --type house-sale
    python3 scripts/clause_recommender.py --type tech-service --risks 违约金约定偏高,收款账户空白
    python3 scripts/clause_recommender.py --keywords 违约金,定金,过户 --type house-sale
    python3 scripts/clause_recommender.py --all
"""

import json
import os
import sys
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

# ── 类型别名 ────────────────────────────────────────────────────────────────
ClauseMatch   = dict    # 单条推荐结果
ResultBundle  = dict    # 完整推荐报告

# ── 风险 → 条款类别映射 ────────────────────────────────
RISK_TO_CATEGORY: dict[str, list[str]] = {
    # 风险描述（中文关键词） → 推荐条款类别
    "违约金":            ["penalty"],
    "违约金偏高":        ["penalty"],
    "违约金过高":        ["penalty"],
    "违约金不对等":      ["penalty"],
    "违约金缺失":        ["penalty"],
    "付款":              ["payment"],
    "付款方式":          ["payment"],
    "付款时间":          ["payment"],
    "付款条件":          ["payment"],
    "收款账户空白":      ["payment"],
    "收款账户未指定":    ["payment"],
    "分期付款":          ["payment", "milestone"],
    "预付款":            ["payment", "prepaid"],
    "尾款":              ["payment", "milestone"],
    "交割":              ["delivery"],
    "交付":              ["delivery"],
    "验收":              ["delivery"],
    "交付时间":          ["delivery"],
    "知识产权":          ["ip"],
    "IP归属":            ["ip"],
    "权属":              ["ip"],
    "工作成果归属":      ["ip", "work-for-hire"],
    "保密":              ["confidentiality"],
    "竞业":              ["confidentiality"],
    "保密期限":          ["confidentiality"],
    "竞业限制":          ["confidentiality"],
    "解除":              ["termination"],
    "解除权":            ["termination"],
    "终止":              ["termination"],
    "提前解除":          ["termination", "convenience"],
    "不可抗力":          ["force-majeure"],
    "不可抗力缺失":      ["force-majeure"],
    "争议":              ["dispute"],
    "争议解决":          ["dispute"],
    "仲裁":              ["dispute", "arbitration"],
    "诉讼":              ["dispute", "court"],
    "管辖":              ["dispute", "court"],
    "适用法律":          ["general", "governing"],
    "变更":              ["general", "amendment"],
    "书面":              ["general", "amendment"],
    "完整协议":           ["general", "entire"],
}

# ── 合同类型 → 推荐优先类别 ────────────────────────────
TYPE_DEFAULT_CATEGORIES: dict[str, list[str]] = {
    "house-sale":     ["payment", "penalty", "delivery", "termination", "dispute", "force-majeure"],
    "tech-service":   ["payment", "delivery", "ip", "confidentiality", "termination", "dispute"],
    "consulting":     ["payment", "ip", "confidentiality", "termination", "dispute"],
    "construction":   ["payment", "delivery", "ip", "penalty", "termination", "force-majeure"],
    "labor-contract": ["payment", "penalty", "termination", "confidentiality", "dispute"],
    "lease":          ["payment", "delivery", "penalty", "termination", "dispute", "force-majeure"],
    "nda":            ["confidentiality", "dispute", "general"],
    "sales":          ["payment", "delivery", "penalty", "dispute"],
    "loan":           ["payment", "penalty", "dispute", "ip"],
    "ip-license":     ["ip", "payment", "confidentiality", "dispute", "termination"],
    "saas":           ["payment", "delivery", "ip", "confidentiality", "dispute", "termination"],
    "joint-venture":  ["ip", "payment", "termination", "dispute"],
    "ppp":            ["payment", "ip", "penalty", "dispute", "force-majeure"],
    "default":        ["payment", "penalty", "dispute", "termination", "force-majeure", "confidentiality", "ip", "delivery"],
}


# ── 数据结构 ────────────────────────────────────────────────────────────────
@dataclass
class ClauseEntry:
    """单条条款条目"""
    id:          str
    file:        str
    category:    str
    name:        str
    text:        str
    position:    dict = field(default_factory=dict)  # buyer/seller tips
    legal_ref:   str = ""
    applicable:  list = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict, file_path: str) -> "ClauseEntry":
        return cls(
            id         = Path(file_path).stem,
            file       = file_path,
            category   = d.get("category", ""),
            name       = d.get("name", ""),
            text       = d.get("clause_text", ""),
            position   = d.get("position_tips", {}),
            legal_ref  = d.get("legal_reference", ""),
            applicable = d.get("applicable_types", []),
        )


# ── 加载条款库 ─────────────────────────────────────────────────────────────
def _get_skill_base() -> Path:
    script_dir = Path(__file__).parent.resolve()
    return script_dir.parent


def load_clause_library(base_dir: Optional[Path] = None) -> dict[str, ClauseEntry]:
    """加载所有条款，返回 {文件名: ClauseEntry}"""
    if base_dir is None:
        base_dir = _get_skill_base()
    lib_dir = base_dir / "references" / "clause-library"

    clauses: dict[str, ClauseEntry] = {}
    if not lib_dir.exists():
        return clauses

    for cat_dir in lib_dir.iterdir():
        if cat_dir.is_dir():
            for fpath in cat_dir.glob("*.json"):
                try:
                    data = json.loads(fpath.read_text(encoding="utf-8"))
                    entry = ClauseEntry.from_dict(data, str(fpath))
                    clauses[entry.id] = entry
                except Exception:
                    pass
    return clauses


# ── 推荐逻辑 ────────────────────────────────────────────────────────────────
def _score_clause_for_risk(entry: ClauseEntry, risk_keywords: list[str]) -> float:
    """计算条款与风险的匹配得分"""
    score = 0.0
    combined = (entry.name + " " + entry.text + " " + entry.category).lower()
    for kw in risk_keywords:
        kw_l = kw.lower()
        if kw_l in combined:
            score += 2.0
        # 部分匹配
        for word in combined.split():
            if kw_l[:2] in word or word[:2] in kw_l:
                score += 0.5
    return score


def _score_clause_for_type(entry: ClauseEntry, contract_type: str) -> float:
    """计算条款与合同类型的匹配得分"""
    score = 0.0
    if contract_type in entry.applicable:
        score += 5.0
    if contract_type in entry.id:
        score += 3.0
    if contract_type in entry.category:
        score += 1.0
    # 检查是否有通用的
    if "all" in entry.applicable:
        score += 1.0
    return score


def recommend_clauses(
    contract_type: Optional[str] = None,
    risks:          Optional[list[str]] = None,
    keywords:       Optional[list[str]] = None,
    top_k:          int = 5,
    base_dir:       Optional[Path] = None,
) -> ResultBundle:
    """
    智能推荐条款。

    参数:
        contract_type: 合同类型英文名（如 "house-sale"）
        risks:         已识别的风险关键词列表（如 ["违约金偏高", "收款账户空白"]）
        keywords:      合同中的关键词（如 ["定金", "过户", "违约金"]）
        top_k:         每个类别最多返回几条
        base_dir:      skill 根目录

    返回:
        推荐报告 dict，含 categories/risks/clauses 三个键
    """
    if risks is None:
        risks = []
    if keywords is None:
        keywords = []

    all_clauses = load_clause_library(base_dir)
    if not all_clauses:
        return {
            "status": "error",
            "error": "条款库目录不存在或为空",
        }

    # 收集需要查询的类别
    target_categories: set[str] = set()
    if contract_type:
        target_categories.update(TYPE_DEFAULT_CATEGORIES.get(contract_type, TYPE_DEFAULT_CATEGORIES["default"]))

    for risk in risks:
        for risk_kw, cats in RISK_TO_CATEGORY.items():
            if risk_kw in risk or risk in risk_kw:
                target_categories.update(cats)

    # 也从 keywords 推断类别
    for kw in keywords:
        for risk_kw, cats in RISK_TO_CATEGORY.items():
            if risk_kw in kw or kw in risk_kw:
                target_categories.add(cats[0])

    # 如果没有找到任何类别，使用通用
    if not target_categories:
        target_categories = set(TYPE_DEFAULT_CATEGORIES.get("default", []))

    # 按类别分组选择条款
    chosen: dict[str, list] = {}
    for cat in target_categories:
        cat_clauses = [
            (cid, c) for cid, c in all_clauses.items()
            if c.category == cat
        ]
        # 综合排序
        scored = []
        for cid, c in cat_clauses:
            s_type  = _score_clause_for_type(c, contract_type or "")
            s_risk  = _score_clause_for_risk(c, risks + keywords)
            s_total = s_type + s_risk
            scored.append((s_total, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        chosen[cat] = scored[:top_k]

    # 构建报告
    categories_out = []
    for cat, scored_list in chosen.items():
        cat_entries = []
        for score, entry in scored_list:
            cat_entries.append({
                "id":          entry.id,
                "file":        entry.file,
                "name":        entry.name,
                "text":        entry.text,
                "position":    entry.position,
                "legal_ref":   entry.legal_ref,
                "applicable":  entry.applicable,
                "match_score": round(score, 2),
            })
        if cat_entries:
            categories_out.append({
                "category_id": cat,
                "category_name": _CATEGORY_NAMES.get(cat, cat),
                "entries":     cat_entries,
            })

    return {
        "status":        "ok",
        "contract_type": contract_type,
        "input_risks":   risks,
        "input_keywords": keywords,
        "categories":     categories_out,
        "total_clauses": sum(len(c["entries"]) for c in categories_out),
    }


# ── CLI ─────────────────────────────────────────────────────────────────────
def _print_report(bundle: ResultBundle):
    if bundle.get("status") == "error":
        print(f"[ERROR] {bundle['error']}")
        return

    print("\n" + "=" * 70)
    print(f"  条款推荐报告  |  合同类型: {bundle.get('contract_type') or '未指定'}")
    print("=" * 70)

    if bundle.get("input_risks"):
        print(f"  关联风险: {', '.join(bundle['input_risks'])}")
    if bundle.get("input_keywords"):
        print(f"  关联关键词: {', '.join(bundle['input_keywords'])}")

    print(f"\n  共推荐 {bundle['total_clauses']} 条条款，覆盖 {len(bundle['categories'])} 个类别\n")
    print("-" * 70)

    for cat in bundle["categories"]:
        print(f"\n【{cat['category_name']}】")
        for e in cat["entries"]:
            stars = "★" * min(int(e["match_score"]), 5)
            print(f"  {stars} {e['name']} ({e['id']})")
            print(f"     📋 {e['text'][:120]}...")
            if e["position"]:
                tips = e["position"]
                if "buyer" in tips:
                    print(f"     📌 甲方版建议: {tips['buyer'][:60]}")
                if "seller" in tips:
                    print(f"     📌 乙方版建议: {tips['seller'][:60]}")
                if "both" in tips:
                    print(f"     📌 双方注意: {tips['both'][:60]}")
                if "employer" in tips:
                    print(f"     📌 用人单位: {tips['employer'][:60]}")
                if "employee" in tips:
                    print(f"     📌 劳动者: {tips['employee'][:60]}")
                if "owner" in tips:
                    print(f"     📌 建设单位: {tips['owner'][:60]}")
                if "contractor" in tips:
                    print(f"     📌 施工单位: {tips['contractor'][:60]}")
            if e["legal_ref"]:
                print(f"     ⚖️  {e['legal_ref']}")
            print()


# ── 常量：类别名称映射 ───────────────────────────────────────────────────────
_CATEGORY_NAMES: dict[str, str] = {
    "payment":    "付款/结算条款",
    "penalty":    "违约金条款",
    "dispute":    "争议解决条款",
    "force-majeure": "不可抗力条款",
    "ip":         "知识产权条款",
    "delivery":   "交付/验收条款",
    "confidentiality": "保密条款",
    "termination":    "解除/终止条款",
    "general":    "综合类条款",
}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="条款推荐引擎")
    parser.add_argument("--type", "-t", help="合同类型（如 house-sale）")
    parser.add_argument("--risks", "-r", nargs="*", help="已识别风险关键词")
    parser.add_argument("--keywords", "-k", nargs="*", help="合同关键词")
    parser.add_argument("--all", "-a", action="store_true", help="显示所有类别条款")
    parser.add_argument("--top-k", type=int, default=3, help="每类别最多返回条数（默认3）")
    parser.add_argument("--output-json", "-o", help="输出 JSON 路径")
    args = parser.parse_args()

    if args.all:
        result = recommend_clauses(top_k=2)
    else:
        result = recommend_clauses(
            contract_type = args.type,
            risks         = args.risks or [],
            keywords      = args.keywords or [],
            top_k         = args.top_k,
        )

    if args.output_json:
        Path(args.output_json).write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"已输出: {args.output_json}")

    _print_report(result)


if __name__ == "__main__":
    main()
