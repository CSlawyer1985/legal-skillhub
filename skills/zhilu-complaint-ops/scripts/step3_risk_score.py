#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step3 五维风险评分：对本地台账记录计算法律/金额/传播/时效/重复五维风险分（各0-20，总分0-100）。
Phase 1中本脚本只输出本地计算结果，不直接回写台账。
用法:
  Phase 1仅支持本地模式：python3 step3_risk_score.py --data data/sample_complaints.json --dry-run
  在线读取与回写已禁用；由Agent顶层通过DWS读取/写入并回读验证。
"""
import argparse
import json
import sys
from datetime import datetime

# ============ 评分规则（可按业务口径调整） ============
LEGAL_BASE_SCORES = {
    "虚假宣传": 15, "隐私泄露": 18, "自动续费": 10, "退款纠纷": 8,
    "服务质量": 5, "合同纠纷": 10, "价格欺诈": 14, "其他": 5,
}
LEGAL_KEYWORDS = ["行政处罚", "立案", "媒体曝光", "起诉", "集体诉讼", "市场监管局", "消协", "法院"]

CHANNEL_BASE_SCORES = {
    "微博": 15, "抖音": 14, "黑猫投诉": 10, "12315平台": 12, "直接投诉": 5, "其他": 8,
}
SPREAD_KEYWORDS = ["热搜", "转发", "大V", "热门", "点赞", "网红", "曝光", "爆料"]

# 常见别名归一化（OCR与台账渠道的叫法不一，不归一会静默落到默认低分）
TYPE_ALIASES = {
    "虚假广告": "虚假宣传", "误导宣传": "虚假宣传", "宣传问题": "虚假宣传",
    "个人信息": "隐私泄露", "隐私问题": "隐私泄露",
    "自动扣费": "自动续费", "续费纠纷": "自动续费",
    "质量投诉": "服务质量", "产品问题": "服务质量",
    "价格问题": "价格欺诈", "差价": "价格欺诈",
    "退费纠纷": "退款纠纷",
}
CHANNEL_ALIASES = {
    "短视频": "抖音", "快手": "抖音", "抖音平台": "抖音",
    "12315": "12315平台", "全国12315": "12315平台", "市监局转办": "12315平台",
    "黑猫": "黑猫投诉", "12345": "直接投诉", "来电": "直接投诉",
}


def normalize_type(t):
    return TYPE_ALIASES.get((t or "").strip(), (t or "").strip())


def normalize_channel(c):
    return CHANNEL_ALIASES.get((c or "").strip(), (c or "").strip())


def calculate_legal_risk(complaint_type, content):
    """法律风险分 (0-20)"""
    score = LEGAL_BASE_SCORES.get(normalize_type(complaint_type), 5)
    if content:
        for kw in LEGAL_KEYWORDS:
            if kw in content:
                score += 2
    return min(20, score)


def calculate_amount_risk(amount):
    """金额风险分 (0-20)"""
    try:
        amount = float(amount) if amount else 0
    except (ValueError, TypeError):
        amount = 0
    if amount <= 500:
        return 2
    elif amount <= 2000:
        return 6
    elif amount <= 5000:
        return 10
    elif amount <= 10000:
        return 15
    return 20


def calculate_spread_risk(channel, content):
    """传播风险分 (0-20)"""
    score = CHANNEL_BASE_SCORES.get(normalize_channel(channel), 8)
    if content:
        for kw in SPREAD_KEYWORDS:
            if kw in content:
                score += 2
    return min(20, score)


def calculate_urgency_risk(deadline_str):
    """时效风险分 (0-20)"""
    if not deadline_str:
        return 10  # 无期限，中风险
    try:
        if "T" in deadline_str:
            deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
            if deadline.tzinfo is not None:
                deadline = deadline.replace(tzinfo=None)
        else:
            deadline = datetime.strptime(str(deadline_str)[:10], "%Y-%m-%d")
        # 按自然日比较：截止日当天未过完不算逾期（避免零点日期-当前时刻误判为负数）
        days_left = (deadline.date() - datetime.now().date()).days
        if days_left < 0:
            return 20
        elif days_left <= 1:
            return 18
        elif days_left <= 3:
            return 12
        elif days_left <= 7:
            return 6
        return 3
    except Exception as e:
        print(f"⚠️ 截止日期解析失败 '{deadline_str}': {e}")
        return 10


def calculate_repeat_risk(complainant, all_records):
    """重复投诉风险分 (0-20)"""
    if not complainant:
        return 2
    count = sum(1 for r in all_records if r.get("投诉人") == complainant)
    if count <= 1:
        return 2
    elif count == 2:
        return 8
    elif count == 3:
        return 14
    return 20


def get_risk_level(total_score):
    """总分 -> 风险等级"""
    if total_score >= 80:
        return "🔴高风险"
    elif total_score >= 50:
        return "🟡中风险"
    return "🟢低风险"


def score_all(records):
    """对本地记录列表评分（记录使用中文字段名）"""
    results = []
    for rec in records:
        legal = calculate_legal_risk(rec.get("投诉类型", ""), rec.get("投诉内容", ""))
        amount = calculate_amount_risk(rec.get("诉求金额", 0))
        spread = calculate_spread_risk(rec.get("投诉渠道", ""), rec.get("投诉内容", ""))
        urgency = calculate_urgency_risk(rec.get("截止日期", ""))
        repeat = calculate_repeat_risk(rec.get("投诉人", ""), records)
        total = legal + amount + spread + urgency + repeat
        rec_out = dict(rec)
        rec_out.update({
            "法律风险分": legal, "金额风险分": amount, "传播风险分": spread,
            "时效风险分": urgency, "重复风险分": repeat,
            "风险评分": total, "风险等级": get_risk_level(total),
        })
        results.append(rec_out)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", help="本地JSON数据文件（演示/测试用）")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--dry-run", action="store_true", help="只评分不回写")
    args = parser.parse_args()

    if not args.data:
        print("在线模式已禁用：请由Agent顶层用DWS导出JSON，再传 --data 本地计算", file=sys.stderr)
        return 2
    with open(args.data, encoding="utf-8") as f:
        records = json.load(f)
    scored = score_all(records)
    cfg = None

    for rec in scored:
        print(f"{rec.get('风险等级')} {rec['风险评分']:>3}分 | {rec.get('投诉人', '?'):6} | "
              f"{rec.get('投诉类型', '?')} | 法律{rec['法律风险分']} 金额{rec['金额风险分']} "
              f"传播{rec['传播风险分']} 时效{rec['时效风险分']} 重复{rec['重复风险分']}")

    if not args.dry_run:
        print("Phase 1仅输出评分结果，不由脚本回写生产台账")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
