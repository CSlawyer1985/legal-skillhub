#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Logic Doctor — 输出品质核验脚本

对 Agent 生成的 Markdown 输出做「十一维核验」，返回核验报告与可信等级。
用法:
    python3 scripts/logic_doctor.py <output.md>
    cat output.md | python3 scripts/logic_doctor.py -

十一维维度（与 01-一审阶段辩护 等专家技能中定义的核验口径一致）:
    1. 事实与证据一致   2. 请求权与事实一致   3. 法律依据与请求权一致
    4. 程序与请求一致   5. 诉讼策略与事实一致   6. 攻防逻辑一致
    7. 文书结构与策略一致 8. 代理意见与庭审表现一致 9. 主体适格与管辖
    10. 脱敏与隐私合规  11. 风险提示完整性

说明: 第 1-9、11 维为「结构/一致性」启发式检查（脚本能自动判定的给 PASS/WARN，
需人工/AI 语义判断的给 WARN 并附自查提示）；第 10 维做 PII 硬扫描（发现疑似
身份证号/手机号等真实敏感信息直接 FAIL）。最终可信等级 = 高 / 中 / 低。
"""

import os
import re
import sys


def _load(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---- 单维检查：返回 (status, note) status ∈ PASS/WARN/FAIL ----
def _has(t, *kw):
    return any(k in t for k in kw)


def d_fact_evidence(t):
    if _has(t, "证据", "书证", "证言", "物证", "鉴定意见") and _has(t, "事实"):
        return "PASS", "存在事实主张且配套证据表述"
    return "WARN", "建议补充「事实—证据」对应表述，便于核验"


def d_claim_fact(t):
    if _has(t, "请求权", "诉请", "诉讼请求", "请求") and _has(t, "事实"):
        return "PASS", "请求权/诉请与事实均有呈现"
    return "WARN", "请求权基础与事实对应不明显"


def d_law_claim(t):
    if _has(t, "法条", "法律依据", "民法典", "刑法", "民事诉讼法", "刑事诉讼法", "条例", "司法解释"):
        return "PASS", "已引用法律/法条依据"
    return "FAIL", "未发现任何法条/法律依据引用，必须补充"


def d_procedure(t):
    if _has(t, "管辖", "时效", "程序", "送达", "举证期限"):
        return "PASS", "已涉及程序/管辖/时效要素"
    return "WARN", "建议补充管辖、时效或程序合规说明"


def d_strategy_fact(t):
    if _has(t, "策略") and _has(t, "事实"):
        return "PASS", "策略基于事实展开"
    return "WARN", "诉讼策略与事实关联不显，建议点明"


def d_attack_defense(t):
    if _has(t, "我方", "己方") and _has(t, "对方", "抗辩", "反驳", "质证"):
        return "PASS", "攻防两端均有呈现，推理链较完整"
    return "WARN", "建议同时呈现我方主张与对方可能的抗辩/质证"


def d_doc_structure(t):
    if _has(t, "文书", "起诉状", "答辩状", "申请书", "代理词", "法律意见书"):
        return "PASS", "已生成对应文书结构"
    return "WARN", "建议明确产出文书及其结构"


def d_opinion_court(t):
    if _has(t, "代理意见", "庭审", "陈述", "法庭"):
        return "PASS", "含代理意见/庭审陈述维度"
    return "WARN", "建议补充庭审表现与书面意见的一致性说明"


def d_standing(t):
    if _has(t, "原告", "被告", "申请人", "被申请人", "当事人", "委托人") and _has(t, "管辖", "法院", "仲裁"):
        return "PASS", "主体与管辖/受理机关均有标识"
    return "WARN", "建议明确当事人主体资格与管辖/受理机关"


def d_pii(t):
    notes = []
    # 18 位身份证
    if re.search(r"\b\d{17}[\dXx]\b", t):
        notes.append("疑似身份证号")
    # 11 位手机号
    if re.search(r"\b1[3-9]\d{9}\b", t):
        notes.append("疑似手机号")
    #  bank card
    if re.search(r"\b\d{16,19}\b", t):
        notes.append("疑似长数字账号(银行/证件)")
    if notes:
        return "FAIL", "发现可能泄露的敏感信息：" + "、".join(notes) + "，请脱敏后输出"
    if _has(t, "脱敏", "化名", "张三", "李四", "某甲", "某某"):
        return "PASS", "已做脱敏/化名处理"
    return "WARN", "未发现明显 PII，但仍请确认无真实姓名/证件泄露"


def d_risk(t):
    if _has(t, "风险", "时效", "执行风险", "败诉", "举证不能"):
        return "PASS", "已包含风险提示"
    return "WARN", "建议补充诉讼时效、证据与执行风险提醒"


def d_disclaimer(t):
    """免责声明核验：交付物必须声明 AI 初稿属性与律师审查义务。"""
    if _has(t, "初稿", "AI生成", "AI 生成", "不得直接使用", "实质审查", "以法院", "以裁判"):
        return "PASS", "已声明初稿属性与审查义务"
    return "FAIL", "未发现免责声明（须标注「AI生成初稿，不得直接使用，须经主办律师实质审查」）"


DIMENSIONS = [
    ("事实与证据一致", d_fact_evidence),
    ("请求权与事实一致", d_claim_fact),
    ("法律依据与请求权一致", d_law_claim),
    ("程序与请求一致", d_procedure),
    ("诉讼策略与事实一致", d_strategy_fact),
    ("攻防逻辑一致", d_attack_defense),
    ("文书结构与策略一致", d_doc_structure),
    ("代理意见与庭审表现一致", d_opinion_court),
    ("主体适格与管辖", d_standing),
    ("脱敏与隐私合规", d_pii),
    ("风险提示完整性", d_risk),
    ("免责声明", d_disclaimer),
]


def verify(text):
    rows = []
    fails = warns = 0
    for name, fn in DIMENSIONS:
        status, note = fn(text)
        if status == "FAIL":
            fails += 1
        elif status == "WARN":
            warns += 1
        rows.append((name, status, note))
    if fails >= 2:
        conf = "低"
    elif fails == 1:
        conf = "中"
    else:
        conf = "高" if warns <= 3 else "中"
    return rows, conf


def report(path, text):
    rows, conf = verify(text)
    print(f"# Logic Doctor 十一维核验报告")
    print(f"- 目标文件: {path}")
    print(f"- 维度总数: {len(rows)}")
    print()
    print("| # | 维度 | 结果 | 说明 |")
    print("|:--:|:-----|:----:|:-----|")
    for i, (name, status, note) in enumerate(rows, 1):
        print(f"| {i} | {name} | **{status}** | {note} |")
    print()
    print(f"**最终可信等级: {conf}** （FAIL={sum(1 for _,s,_ in rows if s=='FAIL')}, WARN={sum(1 for _,s,_ in rows if s=='WARN')}）")
    print()
    print("> 注：结构/一致性维度为启发式检查，WARN 项需主办律师或 AI 复核；")
    print("> 仅 PII 维度做硬扫描，FAIL 必须脱敏后重新生成。所有文书均为初稿，须经执业律师实质审查。")


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/logic_doctor.py <output.md|->", file=sys.stderr)
        sys.exit(2)
    path = sys.argv[1]
    try:
        text = _load(path)
    except Exception as e:
        print(f"读取失败: {e}", file=sys.stderr)
        sys.exit(1)
    report(path, text)


if __name__ == "__main__":
    main()
