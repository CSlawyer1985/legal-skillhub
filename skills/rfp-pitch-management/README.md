# rfp-pitch-management

**OCM Skills 插件**——8 个技能中的第 3 个
**状态：** 已完成——第一阶段和第二阶段已测试

---

## 本技能的用途

运行结构化的招标书（RFP）流程以选择外部法律顾问——从起草初始文件，到评估律所回应，再到产出经得起推敲的遴选建议供 GC 签批。

一家普通律所平均花费 47 小时准备 RFP 回应。该成本被计入法律服务价格。结构不佳的 RFP 产生的回应不可比较，且会默认选择包装最精美的提案，而非最佳律所。本技能固化了运行能产生真正可比性和经得起推敲决策的流程的方法论。

---

## 模式

| 模式 | 触发 | 输出 |
|------|---------|--------|
| 1——起草 RFP | "起草一份 RFP" / "撰写法律 RFP" / "我们需要进入市场" | RFP 文件 + 评估标准框架 |
| 2——评估回应 | "评估律所回应" / "给 RFP 提交打分" / "比较各提案" | 评分评估矩阵 + 评估摘要说明 |
| 3——入围与遴选简报 | "我们应该入围哪些律所" / "遴选建议" / "我们希望委托[律所]" | 遴选简报 + 反馈函（成功与未成功） |
| 4——RFP 流程设计 | "我们如何运行律师库 RFP" / "设计 RFP 流程" / "我们如何设定标准权重" | RFP 流程计划 + 评估标准框架 |

---

## 关键设计决策

**内部文件中使用具体律所名称。** 评估文件（模式 2 评分矩阵、模式 3 遴选简报）使用实际律所名称——这些是内部治理记录。反馈函（模式 3）在模板中使用[律所]占位符，发送时填充。

**定价结构要求。** RFP 模板包含结构化的定价章节，要求提供 AFA 选项、AI 折扣披露和费率透明度。PERSUIT 上 83% 的提案现采用基于价值的定价。不处理定价结构的 RFP 会白白浪费金钱。

**OCG 作为委托条件。** 模式 1 将 OCG 确认作为委托条件。如果 OCG 不存在，本技能提示应并行运行 engagement-terms-billing-guidelines（技能 1），以便委托函发出时文件已就绪。

**经得起推敲的流程文档。** 每种模式都产出足以经受 GC 对流程公平性挑战的文档。评估标准在收到回应之前定义。评分锚定于描述性评分标准，而非主观印象。

---

## 在 OCM 生命周期中的位置

| 阶段 | 技能 |
|-------|-------|
| 计费规则 | engagement-terms-billing-guidelines（技能 1） |
| 律师库设计 | panel-design-selection（技能 2） |
| **律所选择** | **rfp-pitch-management（技能 3）← 本技能** |
| 收费安排 | fee-arrangement-structuring（技能 4） |
| 案件委托 | matter-allocation-instruction（技能 5） |
| 发票审查 | invoice-review-compliance（技能 6） |
| 绩效管理 | performance-scorecard（技能 7） |
| 律师库审查 | panel-review-rationalisation（技能 8） |

---

## 跨技能关联

| 技能 | 关联 |
|-------|-----------|
| panel-design-selection（技能 2） | 律师库设计中的遴选标准矩阵为 RFP 评估标准和权重提供输入。 |
| engagement-terms-billing-guidelines（技能 1） | 通过 RFP 委托的律所必须在工作开始前收到并签署 OCG。 |
| fee-arrangement-structuring（技能 4） | RFP 谈判中商定的商业条款成为案件层面收费安排的基础。 |
| matter-allocation-instruction（技能 5） | 通过 RFP 委托的律所在其首个案件上通过技能 5 获得委托。 |
| performance-scorecard（技能 7） | RFP 遴选标准应成为持续评估标准。 |
| panel-review-rationalisation（技能 8） | 律师库审查可触发更新 RFP。技能 8 的模式 4 产出的律师库更新简报（Panel Refresh Brief）输入本技能。 |

---

## 测试

第一阶段和第二阶段测试提示与断言集在构建日志中。

---

## 文件

- `rfp-pitch-management/SKILL.md`——技能指令
- `rfp-pitch-management-README.md`——本文档

---

## 许可证

Apache 2.0——LegalOps Consulting Limited
