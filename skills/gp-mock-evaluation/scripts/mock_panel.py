#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投标前模拟评审 —— 多评委打分聚合、失分排名与提分 ROI 排序
仅依赖 Python 标准库。

用法：
    python3 mock_panel.py config.json
    python3 mock_panel.py --demo        # 打印示例配置并直接跑

配置结构（JSON）：
{
  "project":   "XX区司法局2026年度法律顾问服务",
  "panel_size": 5,                同 87 号令：5 人以上单数；200万以上/技术复杂为 7 人以上单数
  "trials":     20000,            蒙特卡洛次数，默认 20000

  "items": [
    {
      "no":       "7",
      "name":     "针对采购人业务特点的风险防控方案",
      "max":      8,                 该项满分
      "type":     "subjective",      objective | subjective | price
      "scores":   {"buyer": 4.0, "experts": [4.5, 3.5, 4.0, 4.0]},
                                     模拟打分：采购人代表 1 名 + 专家若干
      "evidence": "投标文件 p32-35",  证据位置；写 "" 表示标书中找不到对应内容
      "fixable":  true,              交卷前能否补救
      "hours":    4,                 补救所需工时
      "gain":     2.5,               补救后的预期得分增量
      "certainty":0.8                补救成功的把握度 0~1
    }
  ]
}

字段说明：
  type=objective  客观分，材料齐备即满分、缺失即零分，模拟时不加扰动
  type=subjective 主观分，按评委打分的离散程度加扰动；5 人评委的经验标准差
                  约为该项满分的 8%~12%
  type=price      价格分，取决于对手报价，此处按给定值计入不加扰动；
                  报价策略请用 gp-bid-scoring-analysis 的 score_model.py
  evidence 为空   视为"未写即无"，无论 scores 填了什么，一律按 0 分计并告警
                  —— 这是对抗"作者兼评委"脑补偏差的机械防线

输出：
  1) 总分分布 P10 / P50 / P90，以及各评分项得分明细
  2) 失分排名（分结构性失分与可挽回失分）
  3) 提分 ROI 排序（期望得分增量 ÷ 工时）
  4) 可直接填入 score_model.py 的主观分区间
"""

import json
import math
import random
import sys

DEMO_CONFIG = {
    "project": "示例：XX区司法局2026年度法律顾问服务项目",
    "panel_size": 5,
    "trials": 20000,
    "items": [
        {"no": "1", "name": "律师事务所执业年限", "max": 5, "type": "objective",
         "scores": {"buyer": 5, "experts": [5, 5, 5, 5]}, "evidence": "投标文件 p8",
         "fixable": False, "hours": 0, "gain": 0, "certainty": 1.0},
        {"no": "2", "name": "近三年同类项目业绩", "max": 10, "type": "objective",
         "scores": {"buyer": 6, "experts": [6, 6, 6, 6]}, "evidence": "投标文件 p12-19",
         "fixable": True, "hours": 3, "gain": 4, "certainty": 0.6},
        {"no": "3", "name": "拟派团队人员资质", "max": 12, "type": "objective",
         "scores": {"buyer": 10, "experts": [10, 10, 10, 10]}, "evidence": "投标文件 p20-27",
         "fixable": True, "hours": 2, "gain": 2, "certainty": 0.9},
        {"no": "4", "name": "对采购需求的理解与分析", "max": 15, "type": "subjective",
         "scores": {"buyer": 9, "experts": [11, 10, 10.5, 11]}, "evidence": "投标文件 p28-31",
         "fixable": True, "hours": 6, "gain": 3.5, "certainty": 0.75},
        {"no": "5", "name": "服务实施方案的科学性与完整性", "max": 20, "type": "subjective",
         "scores": {"buyer": 13, "experts": [15, 14, 14.5, 15]}, "evidence": "投标文件 p36-52",
         "fixable": True, "hours": 8, "gain": 3, "certainty": 0.6},
        {"no": "6", "name": "服务保障与质量控制措施", "max": 10, "type": "subjective",
         "scores": {"buyer": 6, "experts": [7, 6.5, 7, 6.5]}, "evidence": "投标文件 p53-56",
         "fixable": True, "hours": 3, "gain": 2, "certainty": 0.8},
        {"no": "7", "name": "针对采购人业务特点的风险防控方案", "max": 8, "type": "subjective",
         "scores": {"buyer": 3, "experts": [4, 3.5, 4, 3.5]}, "evidence": "投标文件 p57-58",
         "fixable": True, "hours": 4, "gain": 2.5, "certainty": 0.8},
        {"no": "8", "name": "应急与突发事项处理预案", "max": 5, "type": "subjective",
         "scores": {"buyer": 0, "experts": [0, 0, 0, 0]}, "evidence": "",
         "fixable": True, "hours": 2, "gain": 3.5, "certainty": 0.85},
        {"no": "9", "name": "价格分", "max": 15, "type": "price",
         "scores": {"buyer": 13.2, "experts": [13.2, 13.2, 13.2, 13.2]},
         "evidence": "开标一览表 p60", "fixable": False, "hours": 0, "gain": 0, "certainty": 1.0},
    ],
}


def item_mean_sd(item):
    """返回该项的评委打分均值与标准差。evidence 为空则强制归零。"""
    if not item.get("evidence", "").strip():
        return 0.0, 0.0, True  # (mean, sd, zeroed_by_no_evidence)

    s = item["scores"]
    vals = [s["buyer"]] + list(s["experts"])
    mean = sum(vals) / len(vals)

    if item["type"] != "subjective":
        return mean, 0.0, False

    # 主观分：取评委实际离散度与经验下限（满分的 8%）中的较大者，
    # 避免模拟打分过于一致导致低估真实评审的波动
    if len(vals) > 1:
        var = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
        sd = math.sqrt(var)
    else:
        sd = 0.0
    return mean, max(sd, item["max"] * 0.08), False


def simulate(cfg):
    rng = random.Random(20260806)
    trials = cfg.get("trials", 20000)
    items = cfg["items"]
    totals = []
    for _ in range(trials):
        t = 0.0
        for it in items:
            mean, sd, zeroed = item_mean_sd(it)
            if zeroed:
                continue
            v = rng.gauss(mean, sd) if sd > 0 else mean
            t += max(0.0, min(v, it["max"]))
        totals.append(t)
    totals.sort()

    def pct(p):
        return totals[int(len(totals) * p)]

    return pct(0.10), pct(0.50), pct(0.90), totals


def run(cfg):
    items = cfg["items"]
    full = sum(i["max"] for i in items)

    print(f"\n项目：{cfg.get('project', '(未命名)')}")
    print(f"模拟评标委员会：{cfg.get('panel_size', 5)} 人"
          f"（采购人代表 1 名 + 评审专家 {cfg.get('panel_size', 5) - 1} 名）")
    print(f"评分表满分：{full:.0f} 分")

    # ---------- 无证据告警 ----------
    no_ev = [i for i in items if not i.get("evidence", "").strip()]
    if no_ev:
        print("\n[警告] 以下评分项在投标文件中未找到对应内容，已按 0 分计：")
        for i in no_ev:
            print(f"   第 {i['no']} 项《{i['name']}》满分 {i['max']} 分 —— 全额失分")
        print("   （评委只能看到标书里写了什么。找不到证据位置的，不允许按'应该有'给分。）")

    # ---------- 明细 ----------
    print("\n" + "=" * 84)
    print("评分项明细")
    print("=" * 84)
    print(f"{'序号':>4} {'评分项':<28} {'满分':>5} {'类别':>6} {'得分':>7} {'失分':>6} {'证据位置':<18}")
    print("-" * 84)
    rows = []
    for it in items:
        mean, sd, zeroed = item_mean_sd(it)
        loss = it["max"] - mean
        rows.append((it, mean, loss))
        name = it["name"] if len(it["name"]) <= 26 else it["name"][:25] + "…"
        tp = {"objective": "客观", "subjective": "主观", "price": "价格"}[it["type"]]
        ev = it.get("evidence", "") or "【缺失】"
        print(f"{it['no']:>4} {name:<28} {it['max']:>5} {tp:>6} {mean:>7.2f} {loss:>6.2f} {ev:<18}")

    # ---------- 分布 ----------
    p10, p50, p90, _ = simulate(cfg)
    print("\n" + "=" * 84)
    print("总分分布（主观分按评委裁量离散度模拟）")
    print("=" * 84)
    print(f"  悲观 P10：{p10:6.2f} 分")
    print(f"  中位 P50：{p50:6.2f} 分")
    print(f"  乐观 P90：{p90:6.2f} 分")
    print(f"  满分     ：{full:6.2f} 分     总失分（按中位）：{full - p50:.2f} 分")

    # ---------- 失分排名 ----------
    struct = [(i, m, l) for i, m, l in rows if not i.get("fixable") and l > 0.01]
    fixable = [(i, m, l) for i, m, l in rows if i.get("fixable") and l > 0.01]

    print("\n" + "=" * 84)
    print("失分清单")
    print("=" * 84)
    s_loss = sum(l for _, _, l in struct)
    f_loss = sum(l for _, _, l in fixable)
    print(f"\n【结构性失分】合计 {s_loss:.2f} 分 —— 客观条件不具备，本次改不了")
    for i, _, l in sorted(struct, key=lambda x: -x[2]):
        print(f"   第 {i['no']} 项《{i['name']}》失 {l:.2f} 分")
    if s_loss > 15:
        print(f"   [警告] 结构性失分 {s_loss:.1f} 分已超过 15 分。这个标很可能不是为我们准备的，")
        print(f"     建议重新评估是否投入，或核查这些条款本身是否违规（可转质疑投诉 skill）。")

    print(f"\n【可挽回失分】合计 {f_loss:.2f} 分 —— 交卷前还能补")
    for i, _, l in sorted(fixable, key=lambda x: -x[2]):
        print(f"   第 {i['no']} 项《{i['name']}》失 {l:.2f} 分，"
              f"预计可补回 {i.get('gain', 0):.1f} 分")

    # ---------- 提分 ROI ----------
    print("\n" + "=" * 84)
    print("提分优先级（按 ROI 排序，不按分值排序）")
    print("=" * 84)
    print(f"{'排序':>4} {'评分项':<28} {'工时':>5} {'期望增量':>9} {'ROI(分/时)':>11}")
    print("-" * 84)
    roi = []
    for it in items:
        h = it.get("hours", 0) or 0
        g = (it.get("gain", 0) or 0) * (it.get("certainty", 1.0) or 1.0)
        if it.get("fixable") and h > 0 and g > 0:
            roi.append((it, h, g, g / h))
    roi.sort(key=lambda x: -x[3])
    cum_h = cum_g = 0.0
    for n, (it, h, g, r) in enumerate(roi, 1):
        cum_h += h
        cum_g += g
        name = it["name"] if len(it["name"]) <= 26 else it["name"][:25] + "…"
        print(f"{n:>4} {name:<28} {h:>5.1f} {g:>9.2f} {r:>11.2f}")
    if roi:
        print("-" * 84)
        print(f"     全部执行：合计 {cum_h:.1f} 工时，期望提分 {cum_g:.2f} 分 "
              f"→ 中位分可望从 {p50:.1f} 升至约 {p50 + cum_g:.1f}")
        # 半天与一天的边际
        for budget in (4, 8, 16):
            h_acc = g_acc = 0.0
            picked = []
            for it, h, g, r in roi:
                if h_acc + h <= budget:
                    h_acc += h
                    g_acc += g
                    picked.append(it["no"])
            if picked:
                print(f"     只有 {budget:>2} 工时：做第 {'、'.join(picked)} 项，"
                      f"耗时 {h_acc:.1f} 时，期望提分 {g_acc:.2f} 分")

    # ---------- 衔接 score_model.py ----------
    subj = [i for i in items if i["type"] == "subjective"]
    if subj:
        lo = hi = 0.0
        for it in subj:
            mean, sd, zeroed = item_mean_sd(it)
            lo += max(0.0, mean - 1.28 * sd)   # 约 P10
            hi += min(it["max"], mean + 1.28 * sd)  # 约 P90
        obj = sum(item_mean_sd(i)[0] for i in items if i["type"] == "objective")
        print("\n" + "=" * 84)
        print("衔接 gp-bid-scoring-analysis 的 score_model.py")
        print("=" * 84)
        print("  把下列数值填入其配置的 self 段，中标率测算即可从估计变为有实证依据：")
        print(f'    "objective_secured": {obj:.1f},')
        print(f'    "subjective_low":    {lo:.1f},')
        print(f'    "subjective_high":   {hi:.1f}')

    print("\n【重要】以上分数是模拟，不是预测。真实评委的裁量、对手的水平、"
          "现场答辩表现都会改变结果。这份报告的价值在失分原因和提分排序，"
          "不在那个总分数字。")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        print("示例配置：")
        print(json.dumps(DEMO_CONFIG, ensure_ascii=False, indent=2)[:1200] + "\n  ...(略)")
        run(DEMO_CONFIG)
        return
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        run(json.load(f))


if __name__ == "__main__":
    main()
