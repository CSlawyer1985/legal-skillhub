#!/usr/bin/env python3
"""setup_wizard — 律师友好化首次配置助手（吃台账字段快照，吐 field_map 匹配报告）

架构约束：本脚本纯本地、零外部依赖、不调 dws。
用法（由 agent 顶层编排）：
  1. agent 用 `dws aitable field list --base <B> --table <T> --format json` 拉字段快照存文件
  2. python3 scripts/setup_wizard.py --fields fields.json [--config config.yaml]
  3. 脚本输出 JSON 报告：每个逻辑字段 → 匹配到的 fieldId + 置信度 + 待确认项
  4. agent 把报告里"待确认"的项逐条问律师，确认后写回 config.yaml

设计目标：律师永远不打开 config.yaml、永远看不到 fieldId。
"""
import argparse
import json
import re
import sys


# 逻辑字段名 → 台账里可能出现的中文列名（按优先级排列，第一个命中即用）
FIELD_ALIASES = {
    "case_no":         ["标题", "投诉编号", "工单编号", "编号", "案件编号"],
    "complainant":     ["投诉人", "反映人", "举报人", "联系人姓名"],
    "contact":         ["联系方式", "联系电话", "手机号", "电话"],
    "subject":         ["被投诉主体", "被投诉方", "商家名称", "被投诉对象"],
    "complaint_type":  ["投诉类型", "问题类型", "案由", "投诉分类"],
    "channel":         ["投诉渠道", "来源渠道", "投诉来源", "反映渠道"],
    "content":         ["投诉内容", "正文", "详细描述", "问题描述", "反映内容"],
    "amount":          ["诉求金额", "金额", "涉及金额", "争议金额"],
    "received_date":   ["收到日期", "登记日期", "投诉日期", "创建日期"],
    "deadline":        ["截止日期", "办理期限", "回复期限", "时限"],
    "status":          ["处理状态", "状态", "工单状态", "办理状态"],
    "handler":         ["处理人", "经办人", "负责人", "承办人"],
    "follow_up":       ["跟进记录", "处理记录", "办理情况", "进展"],
    "risk_level":      ["风险等级", "风险级别"],
    "total_score":     ["风险评分", "总分", "综合评分"],
    "legal_score":     ["法律风险分", "法律分"],
    "amount_score":    ["金额风险分", "金额分"],
    "spread_score":    ["传播风险分", "舆情风险分", "传播分"],
    "urgency_score":   ["时效风险分", "时效分"],
    "repeat_score":    ["重复风险分", "重复分"],
    "ai_suggestion":   ["AI建议答复", "AI建议", "AI初稿", "机器初稿"],
    "final_reply":     ["最终答复", "定稿答复", "答复内容", "回复内容"],
    "review_status":   ["复核状态", "审核状态"],
    "case_type":       ["工单类型", "案件类型", "来源类型"],
    "raw_12315_no":    ["12315原始编号", "12315编号", "国家平台编号"],
}


def load_fields(path):
    """兼容 dws 返回的多种结构：{data:{fields:[...]}} / {fields:[...]} / [...]"""
    raw = json.load(open(path, encoding="utf-8"))
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in (("data", "fields"), ("fields",)):
            cur = raw
            try:
                for k in key:
                    cur = cur[k]
                if isinstance(cur, list):
                    return cur
            except (KeyError, TypeError):
                continue
    raise ValueError("无法识别的字段快照结构，期望含 fields 列表")


def norm(s):
    return re.sub(r"[\s_\-/()（）\[\]]", "", (s or "").lower())


def match_fields(fields):
    """对每个逻辑字段找最佳列名匹配。
    返回 (matched, ambiguous, missing)：
      matched  : {逻辑名: {fieldId, fieldName, score}}
      ambiguous: {逻辑名: [{候选列名, fieldId, score}...]}  需人工确认
      missing  : [逻辑名]  台账里没找到，需建列或跳过
    """
    by_name = [(norm(f.get("fieldName")), f) for f in fields]
    matched, ambiguous, missing = {}, {}, []
    for logical, aliases in FIELD_ALIASES.items():
        cands = []
        for rank, alias in enumerate(aliases):
            na = norm(alias)
            for nfn, f in by_name:
                if not nfn:
                    continue
                if nfn == na:
                    score = 1.0 - rank * 0.05
                elif na in nfn or nfn in na:
                    score = 0.7 - rank * 0.05
                else:
                    continue
                cands.append({
                    "fieldId": f.get("fieldId"),
                    "fieldName": f.get("fieldName"),
                    "type": f.get("type"),
                    "score": round(max(score, 0.1), 3),
                })
                break
            if cands:
                break
        if not cands:
            missing.append(logical)
            continue
        cands.sort(key=lambda c: -c["score"])
        best = cands[0]
        # 高分且唯一 → 直接采用；否则进 ambiguous 让 agent 问律师
        if best["score"] >= 0.85 and len(cands) == 1:
            matched[logical] = best
        else:
            ambiguous[logical] = cands[:3]
    return matched, ambiguous, missing


def main():
    ap = argparse.ArgumentParser(description="律师友好化首次配置助手（field_map 匹配）")
    ap.add_argument("--fields", required=True, help="dws 拉取的字段快照 JSON 路径")
    ap.add_argument("--out", default=None, help="报告输出路径（默认 stdout）")
    ap.add_argument("--base-id", default=None, help="台账 base_id（回填进报告）")
    ap.add_argument("--table-id", default=None, help="台账 table_id（回填进报告）")
    args = ap.parse_args()

    fields = load_fields(args.fields)
    matched, ambiguous, missing = match_fields(fields)

    report = {
        "ok": True,
        "base_id": args.base_id,
        "table_id": args.table_id,
        "total_columns": len(fields),
        "matched": matched,
        "ambiguous": ambiguous,
        "missing": missing,
        "summary": {
            "matched": len(matched),
            "need_confirm": len(ambiguous),
            "missing": len(missing),
        },
        "next_step": (
            "agent 把 ambiguous 里每条候选用大白话问律师（例：'投诉人姓名在哪一列？A 投诉人 B 联系人'），"
            "把答案合入 matched，再把 matched 写成 config.yaml > ledger.field_map。"
            "missing 里的逻辑字段：可选的（如 raw_12315_no）跳过；必需的（如 content/status）"
            "问律师要不要在台账里新建列。"
        ),
    }
    out = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[setup_wizard] 报告 → {args.out}", file=sys.stderr)
        print(f"  匹配 {len(matched)} / 待确认 {len(ambiguous)} / 缺失 {len(missing)}", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
