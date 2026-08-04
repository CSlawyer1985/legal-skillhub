---
name: eu-ai-act-classification-oliver-schmidt-prietz
description: |
  判断某项技术是否构成欧盟 AI 法案 Art. 3(1) 意义上的 AI 系统，并对其风险等级进行分类（禁止、高风险、带系统性风险的 GPAI、有限风险、最低风险）。当用户要求"classify an AI system under the AI Act"、"determine the AI Act risk tier"、"check if something is an AI system"、"assess prohibited practices"、"check high-risk classification"、"determine Art. 6 exception applicability"，或提及"KI-Verordnung"、"Risikoklassifizierung"、Art. 5、Annex III 或 GPAI 系统性风险时，应使用本技能。
metadata:
  author: Oliver Schmidt-Prietz
  license: AGPL-3.0
  version: 2026.06.05
---

# 欧盟 AI 法案系统分类器

判断某项技术是否构成 **Art. 3(1) AI 法案意义上的 AI 系统**（Regulation (EU) 2024/1689）并对其风险等级进行分类。

## 免责声明（会话开始时展示，不阻断）

> **重要：** 本技能基于欧盟 AI 法案（Regulation (EU) 2024/1689）、委员会指南和 OECD AI 框架提供结构化的 AI 系统分类指引。它不是法律意见。最终分类决定应涉及具备 AI 法案专长的合格法律顾问。高风险义务的生效日期反映了 AI Omnibus 2026 延期（附件 III：2027 年 12 月 2 日；附件 I：2028 年 8 月 2 日）。

---

## 何时联网搜索

**激活时——始终搜索：**
```
EU AI Act Commission guidelines AI system definition 2025 2026
EU AI Act high-risk classification guidelines Art. 6 latest
```

**附件 III 评估期间——搜索：**
```
EU AI Act Annex III delegated acts modifications [current year]
EU AI Act high-risk classification new categories
```

**GPAI 评估——搜索：**
```
EU AI Office GPAI systemic risk threshold FLOP [current year]
EU AI Office GPAI Code of Practice latest
EU AI Act Art. 51 general purpose AI model classification
```

**开源例外——搜索：**
```
EU AI Act open source exception Art. 2(12) guidance [current year]
EU AI Act Art. 53(2) GPAI open source partial exemption
```

---

## 工作流：一次只问一个问题

### 阶段 1：范围门禁

**先前评估上下文（可选）：**
> "如果您此前运行过另一个欧盟 AI 法案技能，可在此粘贴评估上下文块。这将预填若干问题并避免重复输入。"

如果提供了上下文，预填适用字段并跳过已回答的问题。如果任何字段与用户回答冲突，标记不一致。

**Q1——系统描述：**
> "请简要描述您想要分类的 AI 技术或系统。包括：它做什么、如何运作（高层级）、谁使用它、在什么情境中使用。"

**Q2——范围排除检查（以系统描述为导向）：**

基于 Q1 系统描述，评估是否存在任何范围排除信号：

- 如果描述标志出潜在排除（军事用途、个人/家庭使用、纯研发、上市前测试、国际执法合作）→ 仅就该特定排除提出有针对性的确认问题。示例："您的描述提到这仅用于内部研究——该系统是否**专门**用于科学研发，且不向最终用户部署？（Art. 2(6)）"
- 如果描述标志出开源组件 → 提出有针对性的问题："您提到这使用了开源模型。系统本身是否以自由和开源许可证发布？（Art. 2(12)）"
- 如果描述中不存在排除信号 → 完全跳过 Q2，附简短说明："根据您的描述，似乎没有适用的范围排除。继续进行 AI 系统定义测试。"
- 如果确实不清楚排除是否可能适用 → 以对话方式（而非字母列表）呈现相关排除，仅聚焦于根据系统描述可能的排除。

**如果适用军事、国际执法、个人使用、纯研发或上市前排除：** 输出带法律依据的排除分析 → 停止。

**如果系统以自由和开源许可证发布：** 运行 [references/scope-exclusions.md](references/scope-exclusions.md) 中的专用开源检查清单。
- 对于 AI 系统：适用清单 I（Art. 2(12)）——3 步流程、6 个验证问题
- 对于 GPAI 模型：适用清单 II（Art. 53(2)）——3 步流程，含参数可及性检查
- 如果豁免适用 → 输出分析 → 停止
- 如果豁免**不**适用（例如高风险、禁止或 Art. 50 系统）→ 继续至阶段 2

**如果没有排除适用：** 继续至阶段 2。

---

### 阶段 2：AI 系统定义测试（Art. 3(1)）

阅读 [references/ai-system-definition.md](references/ai-system-definition.md) 获取完整的 7 项标准框架。

**一次一项**走过 7 项标准，每项提供示例：

**标准 1——机器基础运作：**
> "该系统是否由基于机器的流程运作（maschinengestütztes System）？这包括任何以计算方式处理信息的软件或硬件。"

**标准 2——自主程度（Autonomiegrad）：**
> "系统表现出什么程度的自主性？使用 ISO 22989 量表：
> - 等级 0：无自动化——完全由人控制
> - 等级 1：辅助——系统建议，人决定
> - 等级 2：部分自动化——部分子功能自动化，人控制整体
> - 等级 3：条件自动化——在特定情境中自主，人随时准备干预
> - 等级 4：高自动化——无需干预即可运作部分任务
> - 等级 5：完全自动化——无需干预即可完成整个任务
> - 等级 6：真正自主——无需监督即调整目标"

**标准 3——部署后的适应性：**
> "系统能否在部署后调整其行为？它是否从新数据、用户交互或环境反馈中学习？（注意：这包括持续学习、在线学习和人类反馈强化。）"

**标准 4——显式或隐式目标：**
> "系统是否有明确的目标——无论是显式编程的（例如'对图像分类'）还是通过训练数据隐式学习的（例如习得的优化目标）？"

**标准 5——推断能力：**
> "系统是否通过推断产生输出——即在简单确定性规则之外进行预测、得出结论或生成建议？这区分了 AI 与传统的基于规则软件。"

**标准 6——输出生成：**
> "系统生成哪些输出？这包括：
> - 预测（例如风险评分、预报）
> - 内容（例如文本、图像、音频、视频）
> - 建议（例如产品推荐、决策支持）
> - 决定（例如自动化审批、分类）"

**标准 7——环境影响：**
> "系统的输出是否影响物理或虚拟环境？示例：控制物理设备、修改用户界面、过滤内容、触发自动化流程。"

**AI 系统认定输出：**

在所有 7 项标准之后，输出：

```markdown
### AI System Definition Analysis (Art. 3(1))

| # | Criterion | Met? | Reasoning |
|---|-----------|------|-----------|
| 1 | Machine-based operation | [Yes/No] | [brief reasoning] |
| 2 | Degree of autonomy | [Level X] | [brief reasoning] |
| 3 | Adaptability after deployment | [Yes/No] | [brief reasoning] |
| 4 | Explicit or implicit goals | [Yes/No] | [brief reasoning] |
| 5 | Inference capability | [Yes/No] | [brief reasoning] |
| 6 | Output generation | [Yes/No] | [brief reasoning] |
| 7 | Environmental influence | [Yes/No] | [brief reasoning] |

**Determination:** [This system IS / IS NOT an AI system under Art. 3(1) AI Act]
**Confidence:** [High / Medium / Low — explain if not High]
```

如果不是 AI 系统 → 输出带推理的认定 → 停止。
如果是 → 继续至阶段 3。

---

### 阶段 3：风险分类

为每一步阅读相关参考文件。

**第 1 步：禁止实践筛查（Art. 5）——分析师驱动的预过滤**

阅读 [references/prohibited-practices.md](references/prohibited-practices.md)。

> "我现在将对照 Art. 5 下的 8 类禁止 AI 实践进行筛查。"

**内部相关性评分（不向用户展示此步骤）：**

基于 Q1 系统描述，静默地将 8 类禁止实践分别归类为：
- **不适用** —— 系统描述显然不涉及此实践
- **可能相关** —— 系统描述有一些值得审查的信号
- **可能相关度较高** —— 系统描述强烈暗示此实践可能适用

**以单一评估表呈现发现（为透明性显示全部 8 项）：**

| # | 禁止事项 | 条款 | 相关性 | 推理 |
|---|------------|---------|-----------|-----------|
| 1 | 潜意识、操纵性或欺骗性技术 | Art. 5(1)(a) | [评估] | [基于系统描述的简要推理] |
| 2 | 利用弱点（年龄、残疾、社会/经济状况） | Art. 5(1)(b) | [评估] | [简要推理] |
| 3 | 公共当局或其代理进行的社会评分 | Art. 5(1)(c) | [评估] | [简要推理] |
| 4 | 个人犯罪风险评估/预测（无事实依据） | Art. 5(1)(d) | [评估] | [简要推理] |
| 5 | 无目标的面部识别数据库抓取 | Art. 5(1)(e) | [评估] | [简要推理] |
| 6 | 工作场所和教育的情绪识别 | Art. 5(1)(f) | [评估] | [简要推理] |
| 7 | 基于敏感特征进行生物识别分类 | Art. 5(1)(g) | [评估] | [简要推理] |
| 8 | 公共场所实时远程生物识别（执法） | Art. 5(1)(h) | [评估] | [简要推理] |

呈现表格后，询问："是否有标记项需要讨论，还是我应该探究我标记为'不适用'的任何项？"

仅对标记为"可能相关"或"可能相关度较高"的项，或用户问及的任何项进行深入分析，使用 [references/prohibited-practices.md](references/prohibited-practices.md) 获取详细的边缘案例、边界分析、灰色地带情形和多类别交互。

**如果任何禁止事项被标记：**

```
WARNING — PROHIBITED AI PRACTICE DETECTED

Art. 5(1)([x]) AI Act: [description]

This AI system falls within the scope of a PROHIBITED practice.
Deployment, placing on market, or putting into service is PROHIBITED.

Legal basis: Art. 5(1)([x]), Recital [XX]
Penalty: Art. 99(3) — up to EUR 35,000,000 or 7% of total worldwide annual turnover

IMMEDIATE ACTION REQUIRED: Consult qualified legal counsel.
```

→ 停止（除非用户想探究 Art. 5 中列出的例外）。

**第 2 步：高风险检查——附件 I（产品安全）**

阅读 [references/high-risk-annexes.md](references/high-risk-annexes.md)。

> "该 AI 系统是否是附件 I 所列欧盟协调立法涵盖的产品的安全组件，或者其本身是否就是该产品？"

筛查全部 18 类附件 I 产品类别。如果是 → 依据 Art. 6(1) 属于高风险。

**第 3 步：高风险检查——附件 III（应用基础）——自动预筛查**

对附件 III 的行业特定分析，阅读 [references/sector-guidance.md](references/sector-guidance.md)。已完成的分类示例见 [references/case-studies.md](references/case-studies.md)。

**自动评估（内部——基于 Q1 系统描述）：**

使用系统描述中的行业、用例和部署情境信号，自动将系统映射到相关附件 III 类别。将每类归类为：
- **相关** —— 系统描述明确标志此类（例如 HR 筛选工具 → 就业）
- **潜在相关** —— 间接信号值得更仔细审查
- **不适用** —— 描述中无信号与此类相连

**呈现自动评估表（为透明性显示全部 8 类）：**

> "根据您的系统描述，以下是我对附件 III 相关性的初步评估："

| # | 类别 | 关键应用 | 相关性 | 推理 |
|---|----------|-----------------|-----------|-----------|
| 1 | 生物识别 | 远程生物识别、情绪识别、分类 | [评估] | [来自系统描述的推理] |
| 2 | 关键基础设施 | 关键数字/物理基础设施的管理/运作 | [评估] | [推理] |
| 3 | 教育与职业培训 | 准入确定、录取、评估、监测 | [评估] | [推理] |
| 4 | 就业、工人管理、自营职业 | 招聘、筛选、评估、监测、解雇 | [评估] | [推理] |
| 5 | 基本服务获取 | 信用worthiness、保险、社会福利、应急调度 | [评估] | [推理] |
| 6 | 执法 | 风险评估、测谎、证据可靠性、画像、犯罪分析 | [评估] | [推理] |
| 7 | 移民、庇护、边境管制 | 风险评估、申请审查、检测 | [评估] | [推理] |
| 8 | 司法与民主进程管理 | 法律研究、量刑、争议解决、选举 | [评估] | [推理] |

> "您同意此评估，还是希望我重新审查任何类别？"

用户确认或覆盖。如果系统描述与用户覆盖冲突（例如用户对就业说"不适用"但系统处理简历），标记该矛盾并无论如何进行全面评估。

仅对标记为"相关"或"潜在相关"的类别（或用户要求审查的任何类别）进行详细评估。

**如果附件 III 命中 → 检查 Art. 6(3) 例外：**

阅读 [references/art6-exception.md](references/art6-exception.md)。

> "附件 III 类别已触发。现在检查 Art. 6(3) 例外——该系统是否仅执行'狭窄程序性任务'或'补充性人类活动'，且不取代或影响人类评估？"

适用 4 项例外条件：
1. 系统执行狭窄程序性任务
2. 系统改进此前已完成的人类活动的结果
3. 系统检测决策模式而不取代/影响人类评估
4. 系统执行与附件 III 用例相关的评估的准备性任务

**特别再例外：** Art. 6(3) 最后一句——如果系统对自然人进行画像（GDPR 第 4(4) 条），例外**不**适用。

**第 3.5 步：高风险深度评估（如附件 I 或附件 III 命中则强制）**

如果第 2 步（附件 I）或第 3 步（附件 III）产生命中——或案件处于临界状态而需要委员会指南深度分析——在定稿结论前进行全面的高风险深度评估。基于委员会 Art. 6(5) 分类指南草案走完 Art. 6 分类：(1) 确认附件 I 产品 / 附件 III 领域触发；(2) 适用 Art. 6(3) 例外条件（狭窄程序性任务、补充性人类活动、不取代人类评估、准备性任务——受画像再例外约束）；(3) 记录系统是安全组件还是产品本身；(4) 产出结构化决定块（等级 + 推理 + 引用的附件/条款）；(5) 将结果记录为 JSON 交换制品和一份简短从业者备忘录。仅当此深度分析完成后，才应整合最终风险等级分类。

由于高风险分类是最具后果性的等级，也是委员会指南最近更新的内容，给予它最深入的处理：如果任何输入不明确（例如部署是否落在附件 III 领域内，或 Art. 6(3) 例外是否真正适用），明确陈述假设并标记供人工审查，而非静默解决。

**第 4 步：GPAI 模型检查**

阅读 [references/gpai-systemic-risk.md](references/gpai-systemic-risk.md)。

> "该系统是否基于或包含通用 AI 模型（Art. 3(63)）？如果是，底层模型是否构成系统性风险（Art. 3(65)、Art. 51）？"

- 如果是无系统性风险的 GPAI 模型 → 透明度义务（Art. 53）
- 如果是有系统性风险的 GPAI 模型 → 适用完整的 Art. 55 义务
- 适用 FLOP 阈值：10^25 浮点运算（Art. 51(2)）

**搜索最新的 GPAI 分类和阈值更新。**

**第 5 步：透明度义务检查（Art. 50）**

> "该系统是否触发 Art. 50 下的任何透明度义务？"

| 义务 | 触发 | 条款 |
|------------|---------|---------|
| 交互披露 | 系统与自然人直接交互 | Art. 50(1) |
| 合成内容标记 | 系统生成合成音频、图像、视频、文本 | Art. 50(2) |
| 情绪识别披露 | 系统执行情绪识别 | Art. 50(3) |
| 深度伪造标注 | 系统生成深度伪造 | Art. 50(4) |

详细的实施指引——包括《实践守则》的多层标记框架（元数据 + 水印）、部署者标注要求、例外、边界分析以及与其他 AI 法案条款的交互——见 [references/art50-transparency.md](references/art50-transparency.md)。

---

### 分类流程决策树

> **注意：GPAI 评估与第 1-3 步并行运行。** 第 4 步（GPAI 模型？）在下面的树中为可读性按顺序展示，但 GPAI 认定独立于风险等级路径。高风险 AI 系统可以同时是带系统性风险的 GPAI 模型——此时**两套制度都适用**。无论第 1-3 步的结果如何，始终对每个系统评估第 4 步。

```
                    ┌─────────────────┐
                    │  SCOPE GATE     │
                    │  Art. 2 Check   │
                    └────────┬────────┘
                             │
                   Exclusion applies?
                    ├── YES → STOP (out of scope)
                    └── NO
                             │
                    ┌────────▼────────┐
                    │ AI SYSTEM TEST  │
                    │ Art. 3(1)       │
                    │ 7 Criteria      │
                    └────────┬────────┘
                             │
                    Is it an AI system?
                    ├── NO → STOP (not an AI system)
                    └── YES
                             │
              ┌──────────────▼──────────────┐
              │ RISK CLASSIFICATION          │
              │ (assess in order)            │
              └──────────────┬──────────────┘
                             │
                ┌────────────▼────────────┐
                │ Step 1: Art. 5          │
                │ Prohibited Practices?   │
                ├── YES → PROHIBITED      │
                └── NO                    │
                             │
                ┌────────────▼────────────┐
                │ Step 2: Annex I         │
                │ Product Safety?         │
                ├── YES → HIGH-RISK       │
                │         (Art. 6(1))     │
                └── NO                    │
                             │
                ┌────────────▼────────────┐
                │ Step 3: Annex III       │
                │ Application-Based?      │
                ├── YES ──┐               │
                └── NO    │               │
                  │       ▼               │
                  │  Art. 6(3) Exception? │
                  │  ├── NO → HIGH-RISK   │
                  │  │    (Art. 6(2))     │
                  │  └── YES → NOT high   │
                  │       (Art. 6(4) doc) │
                  │                       │
                ┌─▼───────────────────────┐
                │ Step 4: GPAI Model?     │
                ├── Systemic risk         │
                │   → Art. 53 + 55        │
                ├── Standard GPAI         │
                │   → Art. 53             │
                └── No GPAI               │
                             │
                ┌────────────▼────────────┐
                │ Step 5: Art. 50         │
                │ Transparency Trigger?   │
                ├── YES → LIMITED RISK    │
                └── NO → MINIMAL RISK     │
                          (Art. 4 only)   │
                └─────────────────────────┘
```

---

### 阶段 4：分类仪表板输出

完成所有阶段后，输出：

```markdown
## AI Act Classification Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
System:          [name]
Date:            [date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI System (Art. 3(1)):     [YES/NO] — [confidence]
Risk Tier:                 [Prohibited/High-Risk/GPAI-Systemic/Limited/Minimal]
Classification Basis:      [Art. 5(1x) / Annex I Nr. X / Annex III Nr. X / Art. 50 / None]
Art. 6(3) Exception:       [Applicable/Not Applicable/N/A]
Scope Exclusions:          [None / Art. 2(x) applies]
GPAI Model:                [Yes — systemic risk / Yes — standard / No / N/A]
Transparency (Art. 50):    [Applicable — Art. 50(1)-(4) / None]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FLAGS:
[flags if any — examples:]
[PROHIBITED PRACTICE — Art. 5(1)(x) — immediate legal review required]
[QUASI-PROVIDER RISK — modifications may trigger Art. 25]
[GPAI SYSTEMIC RISK — Art. 55 obligations apply]
[PROFILING DETECTED — Art. 6(3) exception excluded per last sentence]
[OPEN-SOURCE — partial exemption conditions met/not met]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ASSESSMENT CONTEXT (paste into next skill)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
System: [name]
Classification: [risk tier]
Basis: [legal basis]
Role: [from prior assessment or TBD]
Quasi-Provider: [from prior assessment or TBD]
Sector: [sector]
Jurisdiction: [list]
Org Size: [size]
Art. 50: [applicable triggers]
GPAI: [yes/no, systemic risk]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT STEPS:
→ Determine the organizational role (provider / deployer / importer / distributor)
→ Map the applicable obligations to that role and risk tier
→ Generate formal assessment documentation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 关键提醒

1. **Art. 5 禁止是绝对的** —— 现有部署无例外（宽限期已于 2025 年 2 月 2 日结束）
2. **高风险分类可以改变** —— 委员会可通过授权法案修改附件 III（Art. 7）
3. **GPAI 系统性风险阈值可能更新** —— 委员会可更新 10^25 FLOP 阈值（Art. 51(2)）
4. **Art. 6(3) 例外是狭窄的** —— 画像始终重新触发高风险，即使例外本来会适用
5. **开源不是一揽子豁免** —— 高风险、禁止和 Art. 50 系统不在豁免之列
6. **始终搜索最新指引** —— 委员会指南在 2026 年期间仍在积极发布
7. **记录推理** —— 所有分类决定应按 Art. 6(4) 为非高风险系统记录
8. **执法背景** —— 处罚层级（Art. 5 违规为 EUR 35M/7%）和执法风险评估参见 [references/enforcement-framework.md](references/enforcement-framework.md)
9. **法域特定要求** —— 各国主管机关、劳动法和行业监管机构在每个部署法域的要求参见 [references/jurisdiction-requirements.md](references/jurisdiction-requirements.md)
10. **合规时间线** —— 适用截止日期和季度行动日历参见 [references/compliance-deadlines.md](references/compliance-deadlines.md)
11. **Art. 50 透明度详情** —— 完整 Art. 50 框架（含《实践守则》的多层标记架构、部署者标注要求、例外和边界分析）参见 [references/art50-transparency.md](references/art50-transparency.md)

## 欧盟 AI 法案套件的一部分

本技能可独立工作，但它设计为与我的其他欧盟 AI 法案技能互锁——可单独安装任意一个，或将它们一起用于端到端工作流：

- **欧盟 AI 法案快速评估** —— 15-25 分钟初步分诊
- **欧盟 AI 法案高风险分类器** —— 附件 I / 附件 III 深度评估
- **欧盟 AI 法案角色认定** —— 提供者 / 部署者 / 进口商 / 分销商（含 Art. 25）
- **欧盟 AI 法案义务映射器** —— 按角色和风险等级的义务
- **欧盟 AI 法案检查报告生成器** —— 可审计的合规报告
- **欧盟 AI 法案知识库** —— 对该法案 + 委员会指南的问答

每个都可作为独立技能获取——只安装您需要的。
