# 输出模板——模式 1（咨询）

仅在输出咨询模式结果时加载本文件。技能程序细节见 `SKILL.md`；本文件是输出骨架。

**来源纪律：**
- 下方的每个子类别 ID（如 `GOVERN 1.1`）和行动 ID（如 `GV-1.2-001`）都是从 `references/core/` 或 `references/gai-profile/` 的**逐字引用**。不得发明或转述。
- 任何**适用性判断**（“此风险在此适用”）都是模型推断，而非 NIST 陈述。首次使用时以 `[model judgment — verify against system specifics]` 行内标注。
- 如没有更多用户输入就无法评估某事，将其列在“待决问题”下，而非猜测。

---

```markdown
[工作产品页眉——见 SKILL.md“输出格式”]

# AI RMF 咨询——[系统 / 问题]

**系统类型：** [通用 AI / 生成式 AI / 混合]
**模式：** 咨询
**来源：** NIST AI 100-1（核心）[+ 适用时 NIST AI 600-1（GenAI 概况）]

## 底线
[两到四句话。框架对该系统建议做什么？什么最关键？推断性主张行内标注：`[model judgment — verify against system specifics]`。]

## 适用风险（GenAI 概况）
[非生成式 AI 则省略。否则：合理适用的 12 项风险的短表，各附一行理由。适用性判断本身是模型判断；风险*名称*是 NIST 逐字原文。]

| 风险（NIST 逐字） | 在此可能适用的原因 `[model judgment — verify]` |
|---|---|
| Confabulation | 面向客户的 LLM 摘要——错误信息到达用户。 |
| Data Privacy | 提示词可能包含用户 PII；训练数据未知。 |
| …  | … |

## 建议行动
[相关子类别/行动的 NIST 逐字文本，按职能分组。仅逐字——不要总结。]

### GOVERN
| 子类别 / 行动 | 陈述（NIST 逐字） |
|---|---|
| **GOVERN 1.1** | Legal and regulatory requirements involving AI are understood, managed, and documented. |
| `GV-1.2-001` | Establish transparency policies and processes for documenting the origin and history of training data and generated data for GAI applications… |

### MAP
[…]

### MEASURE
[…]

### MANAGE
[…]

## 待决问题
[2-4 项在没有更多用户输入时框架无法回答的事项。要具体。]
- 谁在贵组织负责 AI 事件响应？（GOVERN 4.3 / MANAGE 4.1 需要。）
- 你们对基础模型提供商是否有供应商 AI 审查流程？（GOVERN 6.1 需要。）

## 后续步骤
[2-4 项用户可从这里采取的、具体的后续步骤。从上述待决问题中提取。示例：]
- 要对该系统进行记录在案的影响评估，请以**评估**模式重新运行本技能。
- 将待决问题的答案记录在贵组织的 AI 用例登记册或系统文档中，然后重新审视受影响的子类别。
- 将本分析呈报给贵组织负责 AI 政策/供应商审查的人员。

---
*来源：NIST AI 100-1（2023 年 1 月）和 NIST AI 600-1（2024 年 7 月）。子类别和建议行动为逐字引用。标记为 `[model judgment]` 的适用性判断是对用户系统描述的推断，而非 NIST 陈述。NIST 指引无约束力——本输出是供人类决策的研究输入，不替代法律意见。*
```
