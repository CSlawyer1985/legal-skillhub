# 引用——路由索引

先阅读本文件。它告诉您哪类问题应加载哪些引用文件，以免在不适用的文件上消耗上下文。

## 此处内容

两层 NIST 来源材料：

- **`core/`**——NIST AI 100-1（《AI 风险管理框架》1.0版，2023年1月）。通用框架。适用于任何 AI 系统。使用 `GOVERN 1.1`、`MAP 2.3` 等子类别 ID。
- **`gai-profile/`**——NIST AI 600-1（《生成式 AI 概要》，2024年7月）。GenAI 特定叠加层。增加 `GV-1.2-001`、`MS-2.7-005` 等编码的建议行动，映射回核心子类别。系统为生成式时，在 `core/` **之外**使用。

另有两个辅助文件：

- **`templates/`**——三种技能模式的输出模板（`consult.md`、`governance-plan.md`、`assessment.md`）。起草输出时加载与当前模式匹配的那一个；不要全部加载。
- **`crosswalk.md`**——将 NIST 风险名称映射到常见政策分类学别名（例如“Confabulation”↔“Hallucination”）。在衔接 NIST 语言与用户既有政策时有用。

## 按问题类型路由

| 问题 | 加载 |
|---|---|
| “AI RMF 说我对这个 AI 系统应该做什么？” | `core/functions.md`，再加载相关的 `core/<function>.md`。如为生成式，另加载对应的 `gai-profile/actions-<function>.md`。 |
| “我们应该有什么治理计划/政策？” | `core/govern.md` + `core/trustworthy-characteristics.md`。如为生成式，另加载 `gai-profile/actions-govern.md`。 |
| “应该做什么测试/评估/计量？” | `core/measure.md` +（如为生成式）`gai-profile/actions-measure.md`。 |
| “应该做什么事件响应/监测？” | `core/manage.md` +（如为生成式）`gai-profile/actions-manage.md`。 |
| “前期应做什么情境/影响分析？” | `core/map.md` +（如为生成式）`gai-profile/actions-map.md`。 |
| “NIST 识别出哪些风险？”（GenAI） | `gai-profile/risks.md` + `crosswalk.md`。 |
| “可信 AI 特征是什么？” | `core/trustworthy-characteristics.md`。 |
| “定义[术语]” | 先 `core/glossary.md`，再 `gai-profile/glossary.md`。 |
| “这个系统是 GenAI 吗？” | 由系统描述判断。如其使用基础模型或生成式架构生成文本、图像、音频、视频或其他合成内容，视为 GenAI。否则仅用 Core。 |
| 起草咨询输出 | `templates/consult.md`（仅当即将输出咨询时）。 |
| 起草治理计划 | `templates/governance-plan.md`（仅当即将输出计划时）。 |
| 起草完整评估 | `templates/assessment.md`（仅当即将输出评估时）。 |

## 按文档路由

加载前从三种模式中选一：

- **通用 AI 系统**（例如基于 XGBoost 的信用评分、分类器上的欺诈检测、需求预测）：仅加载 `core/`。引用如 `MEASURE 2.11` 的子类别。**不要引入 GAI 概要行动**——它们假设生成式行为，不会全部适用。
- **生成式 AI 系统**（例如 LLM 驱动的聊天机器人、图像生成器、RAG 应用、文本摘要器）：加载 `core/` 作为框架 + `gai-profile/` 作为 GenAI 叠加层。同时引用核心子类别和概要行动 ID。
- **混合/兼有两者的管道**（例如一个步骤用 LLM、另一个步骤用分类器的管道）：GenAI 组件按概要处理，其余按核心处理。

## 如何从这些引用中引用

输出时逐字引用：

- **核心子类别：** `**GOVERN 1.1**` —— 涉及 AI 的法律和监管要求被理解、管理和记录。（NIST AI 100-1）
- **GAI 概要行动：** `\`GV-1.2-001\`` —— 建立透明度政策和流程，记录 GAI 应用训练数据和生成数据的来源与历史……（NIST AI 600-1）

不要改写逐字文本——保留措辞。该框架的权威性来自其作为 NIST 出版物的身份；改写会剥夺这一点。

## 何时查阅 `crosswalk.md`

如用户组织已有以不同名称命名风险的政策（例如将“Confabulation”称为“Hallucination”，或将“Harmful Bias and Homogenization”拆分为“Discrimination”和“Fairness”），使用 `crosswalk.md` 在输出中将 NIST 术语转换为他们的术语。这使用户既有政策语言保持完整，而非迫使其采用 NIST 的精确词汇。

## 来源

`core/` 和 `gai-profile/` 中的逐字摘录由 NIST AI 100-1（2023年1月）和 NIST AI 600-1（2024年7月）生成。重新提取工具和冻结的源 HTML 在本发行版之外维护；本构建对应的快照版本见 `CHANGELOG.md`。
