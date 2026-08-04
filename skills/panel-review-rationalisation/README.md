# panel-review-rationalisation

**OCM Skills 插件**——8 项技能中的第 8 项
**状态：** 已完成——第 1 阶段和第 2 阶段已测试。模式 3 和模式 4 已发布，存在已知失败模式（见下文）。

---

## 本技能做什么

执行年度律师库（panel）审查周期和持续的律师库治理决策。将绩效计分卡数据、计费合规记录和越级委派（step-out）模式综合为律师库层面的建议。为律所退出、覆盖缺口评估和竞争性更新流程制作文档。

涵盖完整的律师库治理工作流：从年度健康评估到律所退出和席位更新。

---

## 模式

| 模式 | 触发 | 输出 |
|------|---------|--------|
| 1——律师库健康评估 | "Review our panel" / "Annual panel review" / "Is our panel working" | 律师库健康报告 + GC 律师库审查说明 |
| 2——律所退出管理 | "Exit [firm] from the panel" / "Write the exit notice" / "Formal panel removal" | 律所退出通知和过渡计划 + 内部退出记录 |
| 3——覆盖缺口分析 | "We have a gap" / "We don't have anyone for [area]" / "Coverage gap" | 覆盖缺口报告 + 补救方案说明 |
| 4——律师库更新简报 | "Refresh the panel" / "Fill the gap" / "Competitive process for [area]" | 律师库更新简报 + RFP 范围说明 |

---

## 关键设计决策

**退出前先有改进计划。** 领域知识编码了改进计划要求：以绩效为由退出但没有事先改进计划的，更难辩护。模式 2 不将其作为二元门禁——内部退出记录有"先前改进计划"字段记录该历史。

**模式 2 的 Type 2 占位符。** 律所退出通知使用 [Firm] 作为刻意的审查门禁——即使在会话中提供了律所名称，外部文档中仍保持 [Firm]。内部退出记录使用律所实际名称。与 invoice-review-compliance（技能 6）中的正式不合规通知采用相同模式。

**越级委派作为领先指标。** 越级委派频率连接到三种诊断：覆盖缺口、律师库律所绩效不佳或律师库纪律失败。这是将模式 3（缺口识别）连接回模式 1（律师库健康）并向前连接模式 4（更新）的方法论。

**模式 4 作为交接文档。** 律师库更新简报被框定为 rfp-pitch-management（技能 3）的范围化输入，而非独立决策。模板包含一个交接指令块，指明相应的技能 3 模式为下一步。

**后果框架。** 模式 1 律师库健康报告将每家律所映射到四种建议之一：保留、观察、改进计划或退出审查。每项建议都有定义的触发标准和后果。

---

## 已知限制——模式 3 和模式 4

模式 3 和模式 4 有在第 2 阶段测试中识别的已记录失败模式。对模式 3 的四次基于指令的修复尝试和对模式 4 的三次尝试均未改变失败模式。

**模式 3 失败模式：** 产出带编号战略选项的咨询式散文，而非结构化的覆盖缺口报告模板。以提供选项或问题菜单结尾。

**模式 4 失败模式：** 产出技能 3 执行文档（RFP、长名单、带具名律所的能力问卷），而非律师库更新简报模板。网页搜索在文档生成前运行。可能出现账户级上下文。

**根本原因：** 当输入是会话式的（模式 3）或执行导向的（模式 4）时，丰富的领域知识会覆盖模板指令。当模型具有足够的领域知识生成看似合理的替代内容时，它会忽略首标记锚点和 IS/IS NOT 定义。

**影响：** 模式 3 和模式 4 会在正确主题上产生有用内容，但可能不遵循模板结构。模式 1 和模式 2 是干净的。

**未来修订路径：** 在文档生成前进行两步式信息收集交换，或采用根本不同的设计——接受会话式语域并以不同方式路由到结构化输出。

---

## 在 OCM 生命周期中的位置

| 阶段 | 技能 |
|-------|-------|
| 计费规则 | engagement-terms-billing-guidelines（技能 1） |
| 律师库设计 | panel-design-selection（技能 2） |
| 律所选择 | rfp-pitch-management（技能 3） |
| 费用安排 | fee-arrangement-structuring（技能 4） |
| 案件委派 | matter-allocation-instruction（技能 5） |
| 发票审查 | invoice-review-compliance（技能 6） |
| 绩效管理 | performance-scorecard（技能 7） |
| **律师库审查** | **panel-review-rationalisation（技能 8）← 本技能** |

---

## 跨技能连接

| 技能 | 连接 |
|-------|-----------|
| performance-scorecard（技能 7） | 每家常设律所的计分卡等级为模式 1 律师库健康评估提供输入。主要数据输入。 |
| invoice-review-compliance（技能 6） | 计费合规率和违规记录为模式 1 提供输入。 |
| matter-allocation-instruction（技能 5） | 越级委派日志和案件委派记录为模式 1 和模式 3 的缺口识别提供输入。 |
| panel-design-selection（技能 2） | 定义审查评估每家律所的原始律师库结构和选择标准。 |
| rfp-pitch-management（技能 3） | 接收模式 4 律师库更新简报作为输入。执行竞争性流程以填补已识别的席位。 |
| engagement-terms-billing-guidelines（技能 1） | OCG 遵守情况是模式 1 中律师库保留标准。 |

---

## 测试

第 1 阶段和第 2 阶段的测试提示和断言集在构建日志中。

---

## 文件

- `panel-review-rationalisation/SKILL.md` — 技能说明
- `panel-review-rationalisation-README.md` — 本文档

---

## 许可证

Apache 2.0 — LegalOps Consulting Limited
