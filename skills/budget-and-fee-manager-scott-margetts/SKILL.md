---
name: budget-and-fee-manager-scott-margetts
description: "案件预算和持续的 WIP/偏差监控。在案件设立时构建分阶段费用估算，按法域或工作流运行自下而上预算，计算应急准备金，并构建 AFA 安排（固定费用、上限费用、分阶段固定费用）。持续监控：对照预算的 WIP 跟踪、比例性评估（支出与进度）、带根本原因分析的偏差评述、完成预测、变现率监控、核销分析。触发词：'build a budget'、'fee estimate'、'what will this cost'、'WIP review'、'budget vs actual'、'how are we tracking against budget'、'we're over budget'、'realisation is poor'、'what's our ETC'、'budget for the German workstream'、'model the financial impact of this scope change'、'draft a fee adjustment'、'write-off analysis'、'how much contingency'、'AFA structure'、'fixed fee estimate'、'budget update'、'forecast to complete'。"
metadata:
  author: Scott Margetts
  license: Apache-2.0
  version: 2026.03.17
---

# 预算与费用管理

## 目的

在完整案件生命周期内构建、监控和调整费用预算。案件设立时：将范围转化为带应急准备金和 AFA 结构的分阶段费用估算。进行中：运行解释偏差（而非仅报告偏差）的 WIP 审查。当支出超出交付时：评估可收回性并呈现选项。当范围变更被确认时：建模财务影响。

本技能产生 status-report-drafter 汇总的财务分析。它从 scope-change-controller 接收已确认的 OOS 结论并建模其财务影响。它不执行开票（billing-cycle-manager 处理）也不产生面向客户的财务摘要（status-report-drafter 消费本技能的输出并呈现它）。

---

## 标识块 —— 任何输出前必需

继续前停下来确认：

```
Client: [Name]          Client number: [Number]
Matter: [Name]          Matter number: [Number]
Report date: [Date]     Prepared by: [LPM name]
```

如果任何标识缺失，询问它。没有完整块不要产生输出。

---

## 运行模式

### 模式 1 —— 预算构建
案件设立时：从商定范围产生分阶段费用预算。由合伙人要求估算、范围简报或 matter-intake-scoping 的结构化输出触发。

输入：范围描述（电子邮件、简报或 matter-intake-scoping 输出）、法域清单、团队结构、指示性时间线、已知时的 AFA 偏好。

### 模式 2 —— WIP 审查
月末或案件中期：对照预算评估实际支出、解释偏差、产生完成预测（FTC）。标准财务健康检查。

输入：WIP 数据（粘贴数字、上传的 Excel/CSV 或文本描述）、进度叙述或自我报告的完成百分比、与预算基线匹配的阶段/工作流结构。

### 模式 3 —— 变现率警报
支出与进度不成比例。合伙人现在就需要选项——这不是定期审查。

输入：当前 WIP 状况、进度评估、原始预算、任何已知原因。通常以合伙人或开票经理转发的标记该状况的电子邮件形式到达。

### 模式 4 —— AFA 跟踪
案件按固定费用、上限费用或其他替代费用安排运行。对照上限跟踪消耗、计算突破点、识别决策触发点——合伙人必须在突破上限前采取行动的时点。

输入：商定费用或上限金额、迄今记录的 WIP、估计完成百分比或剩余任务描述。

### 模式 5 —— 费用调整
已确认的范围变更（来自 scope-change-controller）需要财务影响建模和费用调整沟通。

输入：原始预算基线、带估计范围的已确认 OOS 描述、任何商业背景（关系敏感度、收回意愿）。

---

## 领域知识 —— 预算构建

### 估算方法
三种方法，按可用信息的顺序应用：

**类比估算** —— 以可比已结案件作为参考。对范围差异显式调整——不记录改变了什么和为什么，就不要套用可比预算。调整是分析内容；类比数字只是锚点。

**自下而上估算** —— 分解为阶段和工作流，估算每个组成部分，汇总。范围已定义时最准确。需要就谁以哪个职级做什么达成一致。在工作流 × 阶段交叉处构建，而非作为总额。总额无法在案件中期进行有意义的监控。

**参数化估算** —— 使用单位费率（每重组一个实体 £X、每个法域 £Y、每份监管申报 £Z），对照历史数据校准。适用于每个法域自下而上不切实际的大型多法域项目。始终说明参数化费率及其来源。

对大多数案件：初始估算用类比，范围商定且团队结构确认后用自下而上。

### 阶段结构
至少按阶段层面预算。复杂案件按工作流 × 阶段预算。

交易工作的标准阶段：
- **范围界定与设立** —— 受理、团队简报、启动会、案件计划构建、系统设置
- **执行阶段** —— 按法律里程碑或交付物命名，而非“阶段 1/2/3”
- **协调** —— 多法域监督、LC 管理、状态节奏。经常被低估；始终显式预算
- **完成与结案** —— 最终文件、签署后勤、结案后申报、案件关闭

**协调加价基准**（适用于执行阶段小计）：
- 2-5 个法域：10-15%
- 6-10 个法域：15-20%
- 11+ 个法域：20-25%

这些是起点，不是公式。范围复杂性、相对方行为和客户沟通强度都会推高数字。说明它是带显式假设的估计，而非固定百分比。

### 应急准备金
应急准备金是针对已识别风险的命名储备——不是缓冲，也不是凑整条款。在预算表中与基础估算分开，以便随案件演变被消耗、返还或针对不同风险重新持有。

按复杂性的区间：
- 低（单一法域、范围界定清晰、熟悉的客户和案件类型）：5-10%
- 中（2-5 个法域、一些结构性未知、标准案件类型）：10-15%
- 高（6+ 个法域、新颖结构、监管不确定性、新客户或相对方）：15-25%

用 2-3 句话论证应急准备金百分比——点名它针对的两三个具体风险。未论证的应急准备金会被砍掉。带点名风险的论证过的应急准备金是站得住脚的。

**管理储备**与应急准备金不同。它覆盖无法在开始时预期的范围变更。不要与应急准备金捆绑。如果合伙人要求包含，单独标注。

### AFA 结构
**固定费用** —— 为已定义范围商定的总额。风险在事务所。需要严格的范围界定和运作正常的范围变更机制。无论如何都构建内部 T&M 预算——固定费用是开票上限，但内部预算告诉你正在消耗多少利润空间。

**上限费用** —— 到商定上限的 T&M。客户承担到上限的下行风险；事务所以上承担上行风险。内部对照上限作为天花板预算。

**分阶段固定费用** —— 每个阶段固定费用，在每个阶段关口时或之前商定。当后期阶段无法在开始时界定范围时，为双方减少不确定性。推荐用于结构性未知较多的多阶段交易。

**成功费要素** —— 基础费用外加与成果挂钩的或有要素。内部仅对照基础费用预算；或有要素是潜在上行，而非成本目标。

**AFA 监控规则** —— 在 AFA 案件上任何时点，系统必须能回答：商定费用已消耗多少百分比，工作完成多少百分比？如果第一个数字实质高于第二个，案件需要关注。在 AFA 案件的每次 WIP 审查中显式跟踪这一点。

---

## 领域知识 —— WIP 监控

### 比例性测试
这是任何 WIP 审查中最重要的指标。不是“我们花了多少？”而是“相对于完成的工作量，我们花了多少？”

消耗 60% 预算且完成 60% 工作：按计划。消耗 85% 预算且完成 50% 工作：轨迹不会落在预算内。消耗 30% 预算且完成 80% 工作：在宣布是好消息之前调查。

在每次审查中对每个工作流显式运行比例性测试。将结果表述为数字——不要描述它。

### 偏差阈值和评述
标记每个支出超过预算超过商定阈值（默认 10-15%；在案件设立时与合伙人确认并记录在案件计划中）的工作流。高于阈值，使用四问框架提供根本原因评述。低于阈值，说明状况而不做扩展评述。

**四问偏差分析** —— 对每个高于阈值的超支，回答全部四个问题：
1. **根本原因** —— 具体原因，而非泛化。“德国很复杂”不是根本原因。“实体数是 7，而非按范围的 3”才是。
2. **模式** —— 一次性还是系统性？一次性事件（相对方延误、意外监管要求）可控。系统性意味着剩余预算假设也错了。
3. **可收回？** —— 超支能否在该工作流的剩余预算内吸收，还是总预计成本已超预算？
4. **范围信号？** —— 此超支是否表明原始范围假设错了？如果是，移交给 scope-change-controller。范围蔓延造成的偏差不是财务问题——它是一个碰巧有财务后果的范围管理问题。

### 完成预测（FTC）
前瞻性指标。不是已花了什么——是总共将花什么，以及是否在预算内。

两种方式计算并都呈现：
- **消耗率法** —— （迄今实际 ÷ 估计完成百分比）= 预计总额。与预算比较。
- **剩余工作法** —— 估计剩余任务的成本，加上迄今实际。可用时使用 matter-plan-builder 的任务清单。

始终将 FTC 作为区间产生：下限（剩余工作按范围以正常效率完成）、上限（当前消耗率继续）。点估计虚假地暗示精度。区间是诚实答案，也是有用的答案。

### 支出不足怀疑
一个工作流显著低于预算不自动是好消息。在报告前确认以下三种解释中哪一种适用：
1. 工作确实比预期简单——确认，将盈余返还应急准备金
2. 工作尚未开始或显著延误——标记为进度风险
3. 时间未记录到该案件代码下——可恢复，但需要在 WIP 报告定稿前确认并纠正

绝不在没有确认解释的情况下报告重大支出不足。

### 自我报告完成怀疑
工作流的最后 10% 通常消耗其剩余预算的 30%。当团队报告接近完成时，问具体还有哪些任务、谁负责。“收尾中”和“快好了”不是任务描述——它们是早期预警信号。

当自我报告完成度高于 80% 且剩余工作被模糊描述（“只差 X”、“快好了”、“最终文件”）时，在偏差评述中显式提出此质疑——强制，而非可选：

> “[描述] 不是任务描述。请具体确认：还剩哪些文件或交付物、谁在起草、是否有任何客户或相对方输入未到位，以及是否存在对 TU2/TU3/其他工作流的依赖。在确认前，ETC 上限假定 [X]% 的工作流预算剩余。”

即使比例性测试显示工作流按计划，也应用显式怀疑——在 85% 自我报告完成度下 −3pp 差距，如果剩余任务描述模糊，不是健康确认。

### 变现率
变现率 = 已开票费用 ÷ 按标准费率记录的费用。变现率问题意味着事务所在做的工作多于其收回的。

监控：
- **核销** —— 已记录但未开票的费用。当累计核销超过案件预算的 5% 时标记。区分指示性核销（合伙人决定，通常正确且恰当）与发生性核销（低效或不可开票的 WIP）。
- **费率折扣** —— 商定的折扣应作为折扣费率反映在预算中，而非门市费率。为按 15% 折扣运行的案件按门市费率构建的预算，一开始就是错的。

### 查询/追讨循环
当 WIP 数据包含无法从可用信息解释的异常时：
1. 精确定位异常
2. 起草给责任团队的具体查询——产生草稿电子邮件或消息，而非行动项清单。行动项告诉 LPM 做什么。草稿查询完成了它。
3. 收到后把解释纳入偏差评述
4. 如果解释揭示 OOS 工作，立即移交给 scope-change-controller

查询草稿格式——每个无法解释的异常都必需：
```
To: [Name / role]
Re: [Matter] — [Workstream] WIP query

[Workstream] shows [£X] recorded against [£Y] budget at [Z]% self-reported completion [/ zero progress / no time entries since [date]]. Before the WIP review is finalised, I need the following confirmed by [date]:

1. [具体问题——发生了什么、原因是什么]
2. [具体问题——还剩什么、谁负责]
3. [具体问题——是否有任何应评估核销的成本项目]

如上述任何一项表明工作超出商定范围，将立即移交 scope-change-controller。
```

### 财务披露排序
在以下条件满足前，不要向客户传达具体的超支金额：(a) WIP 状况已对账，(b) 核销已处理且净开票数字已确认，(c) 商业应对已与合伙人商定。在此之前：“我们正在监控 [工作流] 中的费用——我们将在下一份财务报告中提供完整更新。”可能变化的临时超支数字比延迟但准确的数字更损害信任。

---

## 输出格式

本技能的所有输出默认以 .docx 文件形式生成，除非用户明确要求其他形式。技能输出是案件记录——它们属于案件文件夹。

### 模式 1 —— 预算表
必需列标题行（精确使用）：

| Phase | Workstream | Grade | Est. hours | Rate (£/hr) | Subtotal (£) | Notes |

明细下方汇总行：
| | | **Base estimate total** | | | **£[X]** | |
| | | **Coordination uplift ([X]%)** | | | **£[X]** | |
| | | **Contingency ([X]% — [brief justification])** | | | **£[X]** | |
| | | **Total budget** | | | **£[X]** | |

对 AFA 案件，在总额下方添加：
“AFA structure: [Fixed / Capped / Phased fixed]. Agreed fee / cap: £[X]. Internal margin at budget: [X]%. Partner review required if margin falls below [X]%.”

**具名事务所归属规则：**在技能输出的任何地方——文件、表格或对话文本中——绝不引用具名事务所。这包括将费率、政策、实务或组织结构归属于任何具名律师事务所。技能不知道任何事务所的实际结构、费率或政策。使用“assumed — confirm with Pricing”、“confirm with Finance”或“firm policy — confirm before applying”。该规则适用于本技能产生的一切，而不仅是正式文件。

### 模式 2 —— WIP 审查表
必需列标题行：

| Workstream / Jurisdiction | Budget (£) | Actual to date (£) | Budget consumed (%) | Est. % complete | Proportionality gap | ETC low (£) | ETC high (£) | Status |

**比例性差距：**表示为预算消耗 % 与估计完成 % 之差。“+18pp”意味着支出跑在工作完成前 18 个百分点。“−12pp”意味着支出低于进度——调查。±10pp 的差距是正常容差。

**状态值** —— 使用精确标签，不缩写：

`On track` | `Watch` | `Overrun — recoverable` | `Overrun — requires action` | `Underspend — investigate`

对同时支出不足且是项目风险的工作流（例如预算消耗 20%、进度 0%、期限临近），使用双重状态：`Underspend — investigate | Programme risk — action required`。项目已坏时却把财务状况报告为健康的状态字段，比没有状态字段更糟。

偏差评述块——对容差外的每个工作流产生：

```
[Workstream]: [X]% of budget consumed, [Y]% complete. Proportionality gap: [+/−Zpp].
Root cause: [Specific cause]
Pattern: [One-off / Systemic]
Recovery: [Recoverable within remaining budget / Requires fee adjustment / Scope signal — refer to scope-change-controller]
Action: [Specific next step with owner and date]
```

### 模式 3 —— 变现率警报备忘录
以 .docx 文件形式产生。模式 3 是决策文件——它属于案件文件夹，而非聊天窗口。

必需结构：

1. **状况** —— 以表格形式产生，行如下：Agreed fee/cap | Recorded WIP | Cap over by | WIP as % of agreed fee | Self-reported completion | Projected total (burn rate method: WIP ÷ % complete) | Projected total (remaining work method: WIP + estimated remaining cost) | Proportionality gap | Current realisation (if billed at cap)。两种预计总额方法都是必需的——它们经常产生不同的数字。两者之间的区间是诚实答案。

2. **完成怀疑 —— 模式 3 中对所有 AFA 案件强制：** 在亏损状况的案件上，存在夸大完成百分比的行为激励——更高的完成数字让轨迹看起来没那么糟。不要在没有显式提出此质疑的情况下接受高于 60% 的自我报告完成度：“Self-reported completion of [X]% has not been independently verified. If actual completion is [X−15]%, projected total rises to [£Y]. Recommend confirming remaining tasks with the team before the partner conversation.”

3. **根本原因** —— 最可能的具体解释；按可能性排序；为合伙人谈话构架诊断问题

4. **选项** —— 三个，量化财务影响：(a) 吸收——核销金额和完成时变现率；(b) 收回——必须记录什么 OOS、估计收回额；(c) 混合——吸收什么、可收回什么、净变现率

5. **建议** —— 哪个选项及为何；确认在任何客户谈话前必须确立根本原因

6. **决策截止日期** —— 日期和具名合伙人；说明决策被推迟会发生什么（WIP 以当前消耗率继续累积——按周量化）

### 模式 4 —— AFA 跟踪表
必需列标题行：

| Matter | Fee basis | Agreed fee/cap | Recorded WIP | Headroom remaining | Burn rate (per week) | Projected total | Position | Decision required? |

**剩余空间** = Agreed fee − Recorded WIP。这是操作上重要的数字。

**消耗率** = Recorded WIP ÷ 已过周数。用于计算剩余空间在当前速度下何时耗尽。

**预计总额** = Recorded WIP + (剩余工作估计)。如果预计总额超过商定费用，将突破点计算为日期。

**状况值：** Within cap — monitoring | Cap risk — watch | Approaching breach — decision required | Cap breached — escalate immediately

**决策触发点：** 必须行使选项的时点——不是突破点。如果按当前消耗率上限 3 周耗尽，决策触发点就是现在。

叙述块（与表格一并产生）：
```
[Matter]: [Fee basis]. Agreed [fee/cap]: £[X]. Recorded WIP: £[Y] ([Z]% consumed).
Estimated completion: [A]%. Proportionality gap: [+/−Bpp].
Projected total at current burn rate: £[C] ([D]% of cap). Headroom: £[E].
[If breach projected]: Decision required by [date]. Options: [list].
```

### 模式 5 —— 费用调整
两个输出：
- **内部备忘录** —— 确认 OOS 范围、对照原始预算量化财务影响、建议调整金额、请求合伙人签字
- **面向客户的函件（如需要）** —— 描述额外范围、解释为何未包含在原始估算中、说明费用调整、交叉引用 scope-change-controller 的范围变更通知

### 结构化数据导出
每个模式 1 和模式 2 输出都附带预算或 WIP 表的 CSV 导出。这是 SharePoint 跟踪的输入，也是下一次 WIP 审查的起点。无法附加文件时，作为带标签的部分内联产生。

---

## LPM 与律师边界

**LPM：** 分阶段估算、应急准备金计算、AFA 结构设计、WIP 比例性分析、偏差根本原因评估、变现率监控、核销分析、客户财务披露排序、费用调整起草。

**律师：** 对单条时间记录的开票判断；费用在专业上是否恰当；从相对方收回成本的可行性；开票披露的专业规则；法定最短期限（咨询、通知、监管）；压缩的项目是否合法合规。

**关于立法的硬规则：** 不要在本技能输出中点名具体法规、条例或判例法。如果延误或项目压缩引发法律合规问题（最短咨询期、监管申报窗口、通知要求），标记为：“This timeline change may engage legal minimum period requirements — legal team to confirm compliance before programme is agreed with client.” 不要刻画法律风险、识别相关立法或得出合规结论。那是律师工作。

---

## 跨技能交接

- **来自 matter-intake-scoping：** 范围简报和法域清单是模式 1 的主要输入。直接消费案件简报输出——如果存在简报，不要从空白简报开始。
- **来自 scope-change-controller：** 带范围变更通知引用的已确认 OOS 触发模式 5。不要重新评估工作是否在范围内——那是 scope-change-controller 的认定。只建模已确认 OOS 的财务影响。
- **AFA 案件：** 在案件设立时，向合伙人标记模式 4 将是持续监控模式。预算仍在模式 1 中构建（内部 T&M 估算，无论外部费用基础如何）。然后模式 4 在每次审查时对照商定费用跟踪消耗。
- **至 status-report-drafter：** WIP 审查表和 FTC 区间是下一份状态报告的财务输入。随附传递：“Updated financial position — consume for the financial summary section. Variance commentary below.”
- **至 scope-change-controller：** 当模式 2 偏差分析识别出的根本原因表明范围假设错了（而非效率问题）时，标记为 OOS 触发。随附传递：“Variance in [workstream] appears scope-driven, not efficiency-driven — scope-change-controller to assess whether OOS documentation is required.”
- **至 billing-cycle-manager：** 模式 2/3 的已确认 FTC 和核销状况输入开票周期。将带已确认状况的 WIP 审查输出传递用于开票准备。
- **来自 risk-and-issues-manager：** RAID 日志中被突破的财务假设（例如“假设 3 个实体；确认 7 个”）在假设突破已界定并确认后是模式 5 触发。

---

**专业语气原则——面向客户的输出：**所有面向客户的草稿和沟通通篇使用专业、尊重的语言。避免任何将事务所置于客户对立面、暗示客户恶意行事或将专业交流刻画为对抗性的构架。费用调整对话是敏感的商务讨论——语气应事实、协作、以解决方案为导向。

---

## M365 连接模式（可选）

**连接模式调用规则：** 在搜索能增加价值时搜索连接系统（Outlook、SharePoint、Teams）——当提示中已有足够输入时，不作为默认第一步。

- **输入已足够：** 用户已粘贴 WIP 数据、预算数字或带完整背景的往来函件。处理已有内容。不要先搜索——它只增加摩擦而不增加信息。
- **输入不完整或值得主动浮现：** 用户提到应该被检索的内容，或连接模式在后台/定时模式运行。主动搜索——这是反向调用模型，也是连接模式下价值最高的行为。

区别在于用户是否已提供所需内容。如果是，处理它。如果不是，或主动浮现服务 LPM，就搜索。

当 M365 MCP 连接器启用时（Claude Team/Enterprise），本技能可以：
- 搜索 Outlook 中与费用相关的往来函件——合伙人预算讨论、客户开票查询、LC 费用上限交流——并在 LPM 不得不问之前将其作为 WIP 审查触发器浮现
- 直接从案件的 SharePoint 文件夹拉取 WIP 导出文件，无需复制粘贴数字
- 每次模式 2 审查后在 SharePoint 更新运行中的预算跟踪器，按审查日期版本化
- 在案件文件夹中搜索费用调整先例，为模式 5 函件起草提供信息

没有连接器：直接粘贴 WIP 数据或上传电子表格。技能完全以手动模式运行。

---

## 时效敏感假设

本技能以下要素编码了可能过时的假设：

- **费率基准** —— 所有小时费率引用使用截至 2025 年当前的近似英国律师事务所基准。使用前向事务所定价团队确认通行费率。
- **协调加价百分比** —— 对照一般国际 LPM 实务校准。有可用的事务所历史数据时对照验证。
- **应急准备金区间** —— 基于一般 LPM 方法论。按案件类型、客户关系和事务所风险偏好调整。
- **变现率阈值（5%）** —— 一般基准。在案件设立时确认事务所商定的阈值。
