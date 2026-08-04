---
name: cue-equity-incentive
description: 用 Cue 查询和分析上市公司股权激励计划——基于市面上最全的股权激励数据库（2015年至今10年+历史覆盖），独家特有数据源，查询历史方案要素、实施效果、同行竞品对比，用真实数据评估激励方案的竞争力与合理性。
description_zh: Cue 股权激励查询：独家最全股权激励数据库，覆盖2015年至今10年+历史，查询方案要素、实施效果与同行对比。
version: 1.0.0
author: sensedeal
tags: [cue, equity-incentive, ESOP, 股权激励, 激励方案, 市值管理, 高管激励]
---

# 股权激励查询

> 查询上市公司历史股权激励计划，分析方案设计与效果，拉取同行竞品方案对比，用真实数据告诉你什么才有竞争力。

## Agent 执行摘要

| 顺序 | 做什么 | 禁止 |
|------|--------|------|
| 1 | 确认 Cue runner 就绪 | 禁止跳过 |
| 2 | 告知用户耗时 2-15 分钟 | 禁止中途取消 |
| 3 | 一条命令，`--template-id template__xWp8N`，传入目标公司 | 禁止连发多条 |
| 4 | `[cue-research] RESULT ok` = 完成 | 禁止编造 |
| 5 | 原样交付 | 禁止概括 |

## 适用场景

| 场景 | 解决的问题 |
|------|-----------|
| 激励方案设计 | 参考同行方案要素，设计有竞争力的激励计划 |
| 方案合理性评估 | 判断某公司激励方案的考核条件是否合理 |
| 投资者尽调 | 了解公司激励对管理层的绑定效果 |
| 竞品对标 | 同行业激励方案的横向对比 |

## 核心能力

1. **历史方案查询** — 公司历次股权激励计划全文要素
2. **方案要素拆解** — 激励对象、份额、行权价、考核条件、锁定期
3. **实施效果评估** — 激励后的业绩达成率、股价表现、核心人员留存
4. **同行对比分析** — 同行业公司的激励方案横向对标

## 试试这样问

- "查一下宁德时代的股权激励方案"
- "比亚迪的股权激励和宁德比怎么样？"
- "半导体行业典型的激励方案长什么样？"
- "这家公司的激励考核条件合理吗？"

## 输出形式

结构化报告：公司激励概览 → 历次方案要素 → 实施效果 → 同行对比 → 竞争力评估 → 来源链接。

---

## 环境要求

```bash
if [ -d ~/.cue/cue-skills/.git ]; then
  git -C ~/.cue/cue-skills pull --ff-only
else
  git clone https://github.com/sensedeal/cue-skills ~/.cue/cue-skills
fi
```

Cue API Key：[cuecue.cn](https://cuecue.cn) 注册获取。

---

## 调用说明

```bash
python3 ~/.cue/cue-skills/cue-research/scripts/research_run.py \
  --query "宁德时代 股权激励计划：历史方案、设计要素、实施效果、同行对比" \
  --template-id template__xWp8N \
  --output ~/cue-reports/$(date +%Y-%m-%d-%H%M)-equity-incentive.md
```

| 参数 | 说明 |
|------|------|
| `--query` | 目标公司名称，**必填**；可选加行业对比范围 |
| `--template-id` | 固定为 `template__xWp8N` |
| `--output` | 落盘路径 |

---

## 输出示例

[查看完整报告](https://cuecue.cn/share/TIxQDFYs)

## FAQ

**Q: 数据来源是什么？**
A: 上市公司公告、交易所披露、公开工商数据。

**Q: 含非上市公司吗？**
A: 非上市公司激励方案为非公开信息，仅覆盖上市公司。
