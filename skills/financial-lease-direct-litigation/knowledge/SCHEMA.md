---
title: 融资租赁普通直租公共知识库结构
created: 2026-07-13
updated: 2026-07-14
type: schema
lane: public
source_status: reviewed_methodology
privacy_status: reviewed
attribution: 李时瑀律师
---

# 融资租赁普通直租公共知识库结构

本知识库只收录普通直租型融资租赁纠纷的公开方法。它是结构化工作底稿，不是针对具体案件的法律意见，也不替代现行法律原文核验。

## 页面类型

| 目录 | 用途 | 允许内容 |
|---|---|---|
| `types/` | 交易类型识别 | 抽象主体链、合同链、物权流和资金流 |
| `playbooks/` | 办案工作流 | 合同审查、起诉材料、证据目录、代理词、法律意见书 |
| `issues/` | 争点分析 | 可复用的问题树、证据要求和风险提示 |
| `authorities/` | 法律依据门禁 | 候选法源域及核验状态，不作未经核验的结论 |
| `cases/` | 样本提炼 | 仅保留不可反向识别的聚合模式，不保存案件编号 |
| `governance/` | 发布治理 | 公私边界、署名、隐私和发布检查 |
| `integration/` | 本地检索 | GBrain 公共源的隔离检索规范 |

`playbooks/` 同时包含材料可读性、用户缺失材料清单和 DOCX 质量门禁。包根目录的 `templates/` 只保存零个案事实的可编辑空白 DOCX。

## 必备元数据

每页必须声明 `type`、`lane`、`source_status`、`privacy_status` 和 `attribution`。公共页的 `lane` 固定为 `public`，署名固定为“李时瑀律师”。

## 证据状态

- `reviewed_methodology`：来自已完成交叉审查的方法结构。
- `practice_structure`：实务写作结构，仍需结合个案调整。
- `pending_current_text_verification`：候选法源域尚待现行文本逐条核验。
- `unsupported_hold`：材料不足，不得写成结论。

## 工作流状态

- `HOLD-MATERIAL-READABILITY`：源材料无法可靠读取；
- `HOLD-ROUTE`：非普通直租或结构冲突；
- `HOLD-EVIDENCE`：关键权利基础、现余额、时效、管辖或当前事实缺证；
- `DOCX-READY`：三件套通过 OOXML 和逐页渲染检查；
- `READY`：路由、证据、法源、隐私和交付质量均通过。

## 关联入口

- [[index|知识库首页]]
- [[governance/public-private-boundary|公私边界]]
- [[authorities/legal-authority-boundary|法律依据门禁]]
