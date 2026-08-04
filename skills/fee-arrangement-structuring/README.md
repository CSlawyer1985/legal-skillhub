# fee-arrangement-structuring

**OCM 技能插件**——8 个技能中的第 4 个
**状态：** 完成——第 1 阶段和第 2 阶段已测试

---

## 本技能做什么

在公司内部法务团队与外部律师之间设计商业费用安排。设计 AFA（固定、上限、区间、混合、分阶段、成功费），评估范围是否支持所提议的结构，为费用谈判准备商业立场，对照交付数据审查现有安排，并评估超范围（out-of-scope）主张。

五个模式覆盖 AFA 全生命周期——从初始设计到范围争议应对。

---

## 模式

| 模式 | 触发词 | 输出 |
|------|---------|--------|
| 1——AFA 设计 | "设计费用结构" / "设计一个 AFA" / "脱离计时收费" / "这项工作采用固定费" | AFA 建议备忘录 + 总法律顾问签署简报 |
| 2——范围与费用匹配 | "这个范围支持固定费吗？" / "这个可以设上限吗？" | 范围—费用评估 + 建议说明 |
| 3——AFA 谈判简报 | "谈判费用" / "重新谈判该安排" / "AI 应当降低成本" | 谈判简报 + 谈话要点 |
| 4——AFA 健康检查 | "我们的 AFA 还成立吗？" / "费用健康检查" / "接近上限了" | AFA 健康评估 + 行动建议 |
| 5——范围争议评估 | "律所称超范围（OOS）" / "这在范围内吗？" / "这是 OOS 吗？" | 范围评估 + 争议应对说明 |

---

## 关键设计决策

**与 LPM 核心的边界。** fee-arrangement-structuring 跨案件和律所关系设计并谈判商业结构。budget-and-fee-manager（LPM 核心）在该结构内为单一案件构建分阶段预算并监控 WIP（在制品）差异。AFA 技能商定的安排正是预算技能所监控的对象。

**范围状态作为设计输入。** 模式 1 将范围状态（已定义 / 部分定义 / 未定义）作为 AFA 选择的主要变量。范围未定义 + 固定费 = 风险转移给律所并相应定价。本技能明确点出这一点，而非设计一个注定失败的 AFA。

**模式 5 用于范围争议。** 在初始 4 模式设计之后增加，因为测试表明"律所称这超范围"是一个与健康检查或重新谈判不同的独立工作流。该模式产出一份评估，参照委托条款验证或质疑该主张。

**法域适配。** 费率基准默认为英国/英镑。美国（AmLaw 数据）和澳大利亚基准可用——在预检或输入中说明。

---

## 在 OCM 生命周期中的位置

| 阶段 | 技能 |
|-------|-------|
| 计费规则 | engagement-terms-billing-guidelines（技能 1） |
| 律师库设计 | panel-design-selection（技能 2） |
| 律所选聘 | rfp-pitch-management（技能 3） |
| **费用安排** | **fee-arrangement-structuring（技能 4）← 本技能** |
| 案件指派 | matter-allocation-instruction（技能 5） |
| 发票审查 | invoice-review-compliance（技能 6） |
| 绩效管理 | performance-scorecard（技能 7） |
| 律师库审查 | panel-review-rationalisation（技能 8） |

---

## 跨技能联系

| 技能 | 联系 |
|-------|-----------|
| engagement-terms-billing-guidelines（技能 1） | OCG 设定 AFA 政策偏好；本技能为具体案件设计具体安排。 |
| rfp-pitch-management（技能 3） | RFP 过程中的竞争性费用提案锚定谈判立场。 |
| matter-allocation-instruction（技能 5） | 已商定的费用安排被引用于案件指派模板。 |
| invoice-review-compliance（技能 6） | AFA 类型决定发票结构和合规规则。固定费发票的审查方式与计时收费不同。 |
| budget-and-fee-manager（LPM 核心） | 此处商定的 AFA 结构 → 在 budget-and-fee-manager 中构建分阶段预算并监控 WIP。 |
| scope-change-controller（LPM 核心） | 模式 4 中识别的范围漂移应在 scope-change-controller 中记录并控制。 |

---

## 测试

第 1 阶段和第 2 阶段的测试提示词与断言集在构建日志中。

---

## 文件

- `fee-arrangement-structuring/SKILL.md`——技能说明
- `fee-arrangement-structuring-README.md`——本文档

---

## 许可证

Apache 2.0——LegalOps Consulting Limited
