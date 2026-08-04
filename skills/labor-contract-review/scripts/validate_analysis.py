#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""劳动合同审查分析自检脚本（配套 labor-contract-review 技能）。

用于对 analysis.json 做两道"新规则"卡点校验，确保上一轮发现的漏判不再复现：

  规则A（占位符漏检防护）：任一条款原文 quote 含占位符/空白值
    （如 [起始日期]、[部门]、[发薪日]、____、待填、详见附件 等），
    其结论不得为"合规"、风险不得为"低"。否则视为必备条款缺失被误判。

  规则B（地方法规引用防护）：工资相关条款（维度含 工资/报酬/加班/
    支付/最低工资/薪酬 等）的 law 字段必须引用用人单位所在地
    工资支付/劳动合同相关地方法规（名称含 工资支付条例/规定/办法
    或 劳动合同条例）。

用法：
    python validate_analysis.py <analysis.json>
退出码：全部通过 0；存在违规 1；参数错误 2。
"""
import sys
import json
import re

PLACEHOLDER_TOKENS = [
    "起始日期", "终止日期", "部门", "岗位名称", "岗位", "发薪日", "姓名",
    "日期", "地点", "详见附件", "待填", "待定", "空白", "身份证号", "住址",
    "工资金额", "金额", "工资", "地址", "城市", "期限",
]
BRACKET_RE = re.compile(r"\[([^\[\]]*)\]")
UNDER_RE = re.compile(r"_{2,}")
WAIT_RE = re.compile(r"(待填|待定|空白|详见附件|详见附|另行约定|双方协商确定后填写)")

WAGE_DIMS = ["工资", "报酬", "加班", "支付", "最低工资", "薪酬", "薪资", "发薪"]
LOCAL_REG_KEYWORDS = ["工资支付条例", "工资支付规定", "工资支付办法", "劳动合同条例"]


def has_placeholder(quote):
    if not quote:
        return True
    q = str(quote)
    if UNDER_RE.search(q):
        return True
    if WAIT_RE.search(q):
        return True
    for m in BRACKET_RE.findall(q):
        inner = m.strip()
        if inner == "" or any(tok in inner for tok in PLACEHOLDER_TOKENS):
            return True
    return False


def is_wage_row(row):
    dim = str(row.get("dimension", ""))
    return any(k in dim for k in WAGE_DIMS)


def cites_local_reg(row):
    law = str(row.get("law", ""))
    return any(k in law for k in LOCAL_REG_KEYWORDS)


def main():
    if len(sys.argv) < 2:
        print("用法: python validate_analysis.py <analysis.json>", file=sys.stderr)
        sys.exit(2)
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = data.get("rows", [])
    violations = []

    # 规则A：占位符不得被误判为合规/低
    for r in rows:
        q = r.get("quote", "")
        if has_placeholder(q):
            risk = str(r.get("risk", ""))
            concl = str(r.get("conclusion", ""))
            if concl == "合规" or risk == "低":
                violations.append(
                    f"[规则A-占位符] 第{r.get('index', '?')}条：quote 含占位符但被判定为「{concl}/{risk}」"
                )

    # 规则B：工资相关条款必须引用地方法规
    for r in rows:
        if is_wage_row(r) and not cites_local_reg(r):
            violations.append(
                f"[规则B-地方法规] 第{r.get('index', '?')}条（{r.get('dimension', '')}）："
                f"law 未引用本地工资支付/劳动合同法规 → {r.get('law', '')}"
            )

    print(f"分析文件：{path}")
    print(f"条款总数：{len(rows)}")
    print("-" * 60)
    if not violations:
        print("✅ 校验通过：未发现占位符误判，工资相关条款均已引用地方法规。")
        sys.exit(0)
    print(f"❌ 校验未通过，发现 {len(violations)} 处违规：")
    for v in violations:
        print("  - " + v)
    sys.exit(1)


if __name__ == "__main__":
    main()
