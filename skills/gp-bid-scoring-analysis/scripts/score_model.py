#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
政府采购综合评分法 —— 报价敏感性分析与中标率蒙特卡洛模拟
仅依赖 Python 标准库。

用法：
    python3 score_model.py config.json
    python3 score_model.py --demo          # 打印一份示例配置并直接跑

配置文件结构（JSON）：
{
  "project":        "XX局2026年度常年法律顾问服务",
  "budget":         600000,          必填，预算/最高限价（元）
  "price_score":    20,              必填，价格分满分
  "tech_score":     80,              必填，非价格分满分（客观分+主观分）

  "self": {
    "objective_secured":  32,        自评稳拿的客观分
    "objective_winnable": 6,         经准备可争取的客观分（模拟时按 achieve_rate 计入）
    "achieve_rate":       0.7,       可争取客观分的实现概率，默认 0.7
    "subjective_low":     22,        主观分区间下限
    "subjective_high":    32,        主观分区间上限
    "sme_discount":       0.0        中小企业价格扣除比例，如 0.10 表示评审时报价按 90% 计
  },

  "competitors": [                   对手列表；也可只给 count + 默认画像
    {"name": "本地A所", "tech_mean": 66, "tech_sd": 5, "price_ratio": 0.90},
    {"name": "本地B所", "tech_mean": 60, "tech_sd": 6, "price_ratio": 0.85},
    {"name": "外地C所", "tech_mean": 63, "tech_sd": 7, "price_ratio": 0.95}
  ],
  "competitor_count": null,          若不逐个列举，填数量，脚本用默认画像生成

  "quote_ratios": [0.75,0.80,0.85,0.90,0.95,1.00],   自己报价占预算的比例，用于敏感性分析
  "trials": 20000,                   蒙特卡洛次数，默认 20000
  "tie_break": "price"               同分排序规则: "price"(报价低者优先) | "tech" | "random"
}

字段说明：
  price_ratio  = 该对手报价 / 预算。低价优先法下，全场最低报价成为评标基准价。
  tech_sd      = 对手非价格分的标准差，反映评委裁量带来的波动。5 人评委时，
                 主观分标准差经验值约为主观分满分的 8%~12%，可据此设定。

输出：
  1) 报价敏感性表：不同报价下的价格得分、总分期望、中标概率
  2) 建议报价：中标概率与合同金额乘积最大的报价点（期望收益最优）
  3) 敏感性提示：对手数量、主观分水平变化对结论的影响
"""

import json
import math
import random
import sys

DEMO_CONFIG = {
    "project": "示例：XX区司法局2026年度法律顾问服务项目",
    "budget": 600000,
    "price_score": 20,
    "tech_score": 80,
    "self": {
        "objective_secured": 32,
        "objective_winnable": 6,
        "achieve_rate": 0.7,
        "subjective_low": 22,
        "subjective_high": 32,
        "sme_discount": 0.0,
    },
    "competitors": [
        {"name": "本地A所", "tech_mean": 66, "tech_sd": 5, "price_ratio": 0.90},
        {"name": "本地B所", "tech_mean": 60, "tech_sd": 6, "price_ratio": 0.85},
        {"name": "外地C所", "tech_mean": 63, "tech_sd": 7, "price_ratio": 0.95},
        {"name": "综合D所", "tech_mean": 58, "tech_sd": 6, "price_ratio": 0.92},
    ],
    "competitor_count": None,
    "quote_ratios": [0.75, 0.80, 0.85, 0.90, 0.95, 1.00],
    "trials": 20000,
    "tie_break": "price",
}


def build_competitors(cfg):
    """返回对手画像列表。显式列举优先；否则按数量生成默认画像。"""
    comps = cfg.get("competitors")
    if comps:
        return [dict(c) for c in comps]

    n = cfg.get("competitor_count") or 4
    tech_full = cfg["tech_score"]
    out = []
    for i in range(n):
        # 默认画像：非价格分均值落在满分的 70%~82% 之间，报价落在预算的 82%~96%
        out.append(
            {
                "name": f"对手{i + 1}",
                "tech_mean": tech_full * (0.70 + 0.12 * (i + 0.5) / n),
                "tech_sd": tech_full * 0.08,
                "price_ratio": 0.82 + 0.14 * (i + 0.5) / n,
            }
        )
    return out


def self_tech_sample(s, tech_full, rng):
    """抽样自己的非价格分：稳拿客观分 + 可争取客观分(按概率) + 主观分(区间内三角分布)"""
    score = s.get("objective_secured", 0.0)
    winnable = s.get("objective_winnable", 0.0)
    if winnable and rng.random() < s.get("achieve_rate", 0.7):
        score += winnable
    lo = s.get("subjective_low", 0.0)
    hi = s.get("subjective_high", lo)
    if hi > lo:
        # 三角分布，众数取区间中值偏下（保守），避免自评过于乐观
        mode = lo + (hi - lo) * 0.45
        score += rng.triangular(lo, hi, mode)
    else:
        score += lo
    return min(score, tech_full)


def price_scores(quotes, price_full):
    """低价优先法：得分 = (最低报价 / 本方报价) × 价格分满分。
    quotes 为评审用报价（已扣除中小企业优惠）。"""
    base = min(quotes)
    return [(base / q) * price_full if q > 0 else 0.0 for q in quotes]


def simulate(cfg, my_quote, comps, rng):
    """给定本方报价，跑一轮蒙特卡洛，返回 (中标概率, 本方总分均值, 本方总分标准差)"""
    s = cfg["self"]
    tech_full = cfg["tech_score"]
    price_full = cfg["price_score"]
    trials = cfg.get("trials", 20000)
    tie_break = cfg.get("tie_break", "price")

    discount = s.get("sme_discount", 0.0)
    my_eval_quote = my_quote * (1.0 - discount)
    comp_quotes = [c["price_ratio"] * cfg["budget"] for c in comps]

    all_quotes = [my_eval_quote] + comp_quotes
    p_scores = price_scores(all_quotes, price_full)
    my_price_score = p_scores[0]
    comp_price_scores = p_scores[1:]

    wins = 0
    totals = []
    for _ in range(trials):
        my_total = self_tech_sample(s, tech_full, rng) + my_price_score
        totals.append(my_total)

        best = my_total
        best_is_me = True
        best_quote = my_eval_quote
        for c, ps in zip(comps, comp_price_scores):
            t = rng.gauss(c["tech_mean"], c["tech_sd"])
            t = max(0.0, min(t, tech_full))
            total = t + ps
            q = c["price_ratio"] * cfg["budget"]
            if total > best + 1e-9:
                best, best_is_me, best_quote = total, False, q
            elif abs(total - best) <= 1e-9:
                # 同分排序
                if tie_break == "price" and q < best_quote:
                    best_is_me, best_quote = False, q
                elif tie_break == "random" and rng.random() < 0.5:
                    best_is_me, best_quote = False, q
        if best_is_me:
            wins += 1

    mean = sum(totals) / len(totals)
    var = sum((t - mean) ** 2 for t in totals) / len(totals)
    return wins / trials, mean, math.sqrt(var)


def run(cfg):
    rng = random.Random(20260805)
    comps = build_competitors(cfg)
    budget = cfg["budget"]
    ratios = cfg.get("quote_ratios") or [0.75, 0.80, 0.85, 0.90, 0.95, 1.00]

    print(f"\n项目：{cfg.get('project', '(未命名)')}")
    print(f"预算/最高限价：{budget:,.0f} 元")
    print(f"评分构成：非价格分 {cfg['tech_score']} 分 + 价格分 {cfg['price_score']} 分")
    print(f"假设对手数量：{len(comps)} 家")
    disc = cfg["self"].get("sme_discount", 0.0)
    if disc:
        print(f"中小企业价格扣除：{disc:.0%}（评审报价按 {1 - disc:.0%} 计）")
    print("\n对手画像：")
    for c in comps:
        print(
            f"  {c['name']:<10} 非价格分均值 {c['tech_mean']:.1f} (σ={c['tech_sd']:.1f})，"
            f"报价 {c['price_ratio'] * budget:,.0f} 元（预算的 {c['price_ratio']:.0%}）"
        )

    print("\n" + "=" * 78)
    print("报价敏感性分析")
    print("=" * 78)
    print(
        f"{'报价比例':>8} {'报价(元)':>12} {'价格得分':>9} {'总分均值':>9} "
        f"{'总分σ':>7} {'中标概率':>9} {'期望收益(元)':>14}"
    )
    print("-" * 78)

    rows = []
    for r in ratios:
        q = budget * r
        p_win, mean, sd = simulate(cfg, q, comps, rng)
        # 本方价格得分（相对全场最低价）
        disc_q = q * (1.0 - disc)
        allq = [disc_q] + [c["price_ratio"] * budget for c in comps]
        my_ps = price_scores(allq, cfg["price_score"])[0]
        expected = p_win * q
        rows.append((r, q, my_ps, mean, sd, p_win, expected))
        print(
            f"{r:>7.0%} {q:>12,.0f} {my_ps:>9.2f} {mean:>9.2f} "
            f"{sd:>7.2f} {p_win:>8.1%} {expected:>14,.0f}"
        )

    best_ev = max(rows, key=lambda x: x[6])
    best_win = max(rows, key=lambda x: x[5])

    print("\n" + "=" * 78)
    print("结论")
    print("=" * 78)
    print(
        f"期望收益最优报价：{best_ev[1]:,.0f} 元（预算的 {best_ev[0]:.0%}），"
        f"中标概率约 {best_ev[5]:.0%}，期望收益 {best_ev[6]:,.0f} 元"
    )
    print(
        f"中标概率最高报价：{best_win[1]:,.0f} 元（预算的 {best_win[0]:.0%}），"
        f"中标概率约 {best_win[5]:.0%}"
    )
    if best_ev[0] != best_win[0]:
        print(
            "  提示：两者不一致说明继续降价虽能提高胜率，但收入损失更快。"
            f"若以盈利为目标取 {best_ev[0]:.0%}，若以中标业绩为目标取 {best_win[0]:.0%}。"
        )

    # 边界告警：最优点落在测试区间端点，说明区间没覆盖真实拐点
    lo_r, hi_r = min(ratios), max(ratios)
    if abs(best_ev[0] - lo_r) < 1e-9:
        print(
            f"  [警告] 最优点落在测试区间下端（{lo_r:.0%}），真实拐点可能更低。"
            "建议在 quote_ratios 中补充更低的比例重跑。"
        )
    if abs(best_ev[0] - hi_r) < 1e-9:
        print(
            f"  [警告] 最优点落在测试区间上端（{hi_r:.0%}），说明降价无收益，"
            "本项目应把全部精力投向非价格分。"
        )

    # 低价风险提示（87号令第60条）
    lowest_comp = min(c["price_ratio"] for c in comps) * budget
    if best_ev[1] < lowest_comp * 0.8:
        print(
            f"  [警告] 建议报价（{best_ev[1]:,.0f} 元）低于最低对手报价的 80%，"
            "可能触发 87 号令第 60 条的低价说明程序：报价明显低于其他通过符合性"
            "审查投标人的报价、可能影响履约的，评标委员会可要求现场作出书面说明，"
            "不能证明其报价合理性的将作无效投标处理。压价前务必核算真实履约成本。"
        )

    # 敏感性提示：非价格分提升 5 分的效果
    cfg2 = json.loads(json.dumps(cfg))
    cfg2["self"]["subjective_low"] += 5
    cfg2["self"]["subjective_high"] += 5
    p2, _, _ = simulate(cfg2, best_ev[1], comps, random.Random(20260805))
    print(
        f"\n若服务方案质量提升、主观分上浮 5 分：同等报价下中标概率 "
        f"{best_ev[5]:.0%} → {p2:.0%}（提升 {p2 - best_ev[5]:+.1%}）"
    )

    # 敏感性提示：多一家对手
    comps3 = comps + [
        {
            "name": "新增对手",
            "tech_mean": sum(c["tech_mean"] for c in comps) / len(comps),
            "tech_sd": sum(c["tech_sd"] for c in comps) / len(comps),
            "price_ratio": min(c["price_ratio"] for c in comps) - 0.03,
        }
    ]
    p3, _, _ = simulate(cfg, best_ev[1], comps3, random.Random(20260805))
    print(
        f"若多出 1 家低价对手：同等报价下中标概率 "
        f"{best_ev[5]:.0%} → {p3:.0%}（变动 {p3 - best_ev[5]:+.1%}）"
    )

    print(
        "\n【重要】以上为基于假设参数的估算，不是对结果的预测。主观分和对手画像"
        "都是估计值，参数变化会显著改变结论。使用时应同时列明假设，并把该概率"
        "用于多个项目之间的横向比较和资源分配，而非作为单一项目的成败判断。"
    )


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        print("示例配置：")
        print(json.dumps(DEMO_CONFIG, ensure_ascii=False, indent=2))
        run(DEMO_CONFIG)
        return
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        cfg = json.load(f)
    run(cfg)


if __name__ == "__main__":
    main()
