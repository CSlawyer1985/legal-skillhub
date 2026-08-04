# 数字运营韧性法案（DORA）技能

> **免责声明：** 本技能基于《条例（EU）2022/2554》以及 EBA、ESMA 和 EIOPA 发布的已通过 RTS/ITS，提供关于 DORA 义务的信息性指引。不构成法律意见。DORA 合规涉及欧盟金融服务法项下的重大义务——对于涉及主管机关互动、重大事件报告、TLPT 范围界定或信息登记册提交等事项，请咨询合格的 DORA 合规专业人士或你的法律顾问。

---

## 1. 本技能做什么？

本技能将 Claude 转变为欧盟金融机构及其 ICT 第三方服务提供者的专家级 **DORA 合规顾问**。它涵盖**《条例（EU）2022/2554》**——《数字运营韧性法案》——的全文，该法案自 **2025 年 1 月 17 日**起适用，以及欧洲监管机构（欧洲银行管理局 EBA、欧洲证券和市场管理局 ESMA、欧洲保险和职业养老金管理局 EIOPA）发布的所有已通过**监管技术标准（RTS）**和**实施技术标准（ITS）**。

DORA 横跨 9 章，涵盖五个实质性合规领域：**ICT 风险管理框架**（第二章，第 5–16 条）、**ICT 相关事件管理、分类和报告**（第三章，第 17–23 条）、**数字运营韧性测试**（第四章，第 24–27 条）、**ICT 第三方风险管理**（第五章，第 28–44 条）以及**信息共享安排**（第六章，第 45 条）。本技能提供跨所有章节的逐条指引，并在合规缺口最常见的领域尤为深入。

本技能的一个标志性特征是它能精确区分 DORA 的章节、框架以及落实每项义务的具体已通过 RTS/ITS。技能始终引用正确的欧盟委员会授权/实施条例编号（例如，ICT 风险管理 RTS 为 CDR（EU）2024/1774，事件分类标准为 CDR（EU）2024/1772，信息登记册模板为 CIR（EU）2024/2956）。它明确避免两个最常见的 DORA 合规错误：将 DORA 与 NIS2 混为一谈（DORA 是金融部门的特别法；NIS2 适用于 DORA 不适用之处）以及将 DORA 之前的 EBA ICT/安全风险指南引用为现行标准（该等指南已于 2025 年 1 月 17 日被 DORA 取代）。

本技能在**ICT 第三方风险管理**方面尤为全面——这是 DORA 最复杂的章节——涵盖 ICT 第三方风险政策、信息登记册（含 CIR（EU）2024/2956 规定的全部必填字段）、关键和重要 ICT 安排的合同条款（第 30(2) 条检查清单）、ICT 集中度风险评估、退出策略规划，以及欧洲监管机构指定的关键 ICT 第三方服务提供者（CTPP）监督框架。

---

## 2. 目标受众

| 受众 | 使用方式 |
| ------------------------------------------ | --------------------------------------------------------------------------------------------- |
| **首席风险官（CRO）** | ICT 风险框架设计、董事会治理义务（第 5 条）、ICT 风险偏好设定 |
| **CISO 与 IT 安全团队** | ICT 风险管理框架（第 6–14 条）、保护控制、检测、BCP/BIA |
| **合规经理** | 全部 5 个 DORA 支柱的差距评估、证据映射、主管机关就绪度 |
| **事件响应团队** | 第 17–19 条事件分类、重大事件判定、3 阶段报告时限 |
| **供应商/第三方风险团队** | 信息登记册建设、第 30 条合同审查、集中度风险评估 |
| **法务与合同团队** | 第 30(2) 条合同条款检查清单、分包 RTS、退出条款起草 |
| **董事会与管理机构** | 第 5 条董事会义务、ICT 风险偏好、预算与培训问责 |
| **ICT 服务提供者（云、SaaS）** | 了解 CTPP 指定标准、监督义务、审计和访问权 |
| **渗透测试人员和 TLPT 提供者** | 第 26 条 TLPT 范围、CDR（EU）2025/1190 要求、威胁情报阶段 |
| **规模较小的金融机构** | 简化 ICT 风险管理框架（第 16 条）的资格与义务 |

---

## 3. 常见用例

### 差距分析与就绪度评估

- _"为一家中型支付机构运行 DORA 差距分析。我们已有 IT 风险框架，但没有第 6 条要求的正式 ICT RMF。"_
- _"评估我们符合第二章（ICT 风险管理）和第五章（第三方风险）的情况。"_
- _"对于已有 ICT 治理框架的银行，最常被遗漏的 DORA 义务是什么？"_
- _"我们适用了第 16 条简化框架——我们有资格吗？该框架要求什么？"_

### ICT 风险管理框架（第二章）

- _"起草一份满足第 6 条和 CDR（EU）2024/1774 要求的 ICT 风险管理框架政策。"_
- _"第 5 条对董事会要求什么？起草董事会层面的 ICT 风险问责声明。"_
- _"按第 8 条，我们的 ICT 资产登记册必须包含什么？我们应如何将资产映射到关键职能？"_
- _"设计我们的补丁管理流程以满足第 7(d) 条。"_
- _"第 11 条对 ICT 业务连续性要求什么？我们如何为关键职能设定 RTO 和 RPO？"_

### 事件分类与报告（第三章）

- _"我们发生了一次持续 6 小时、影响 3,000 笔支付交易的系统中断。按 DORA 这属于重大 ICT 事件吗？"_
- _"带我了解第 19 条下的 3 阶段重大 ICT 事件报告时限。"_
- _"向主管机关提交的初始通知（4 小时）报告需要包含哪些内容？"_
- _"使用第 18 条标准和 CDR（EU）2024/1772 阈值起草我们的 ICT 事件分类矩阵。"_
- _"我们遭遇了重大网络威胁但没有实际事件。可以按第 19(2) 条提交自愿报告吗？"_

### 韧性测试（第四章）

- _"第 24 条要求所有金融机构每年进行哪些测试？"_
- _"我们的组织是否达到第 26(8) 条的 TLPT 阈值？我们是一家大型投资公司。"_
- _"带我了解第 26 条和 CDR（EU）2025/1190 下的 TLPT 流程。"_
- _"按第 27 条，我们的外部 TLPT 测试人员必须持有何种资质？"_

### ICT 第三方风险（第五章）

- _"我们有 45 项 ICT 服务安排。如何按 CIR（EU）2024/2956 建设信息登记册？"_
- _"审查我们与 AWS 的合同是否符合 DORA 第 30(2) 条。缺少哪些条款？"_
- _"第 28(6) 条下的 ICT 集中度风险是什么，我们如何评估？"_
- _"为我们的关键云基础设施提供者起草退出策略。"_
- _"我们的哪些 ICT 服务安排需要完整的第 30(2) 条条款，哪些只需要较轻的第 30(3) 条条款？"_

---

## 4. 如何使用本技能

### 安装

1. 从本文件夹下载 `dora.skill` 文件
2. 在 Claude 中进入 **Settings → Skills**
3. 点击 **Upload Skill** 并选择 `dora.skill`
4. 该技能立即在你的 Claude 会话中生效

### 触发技能

当你的消息涉及 DORA 或其实施细则时，技能会自动激活。触发它的示例短语：

- _"DORA compliance"_
- _"DORA gap analysis"_
- _"ICT risk management framework DORA"_
- _"Art. 17 incident reporting"_
- _"Register of Information DORA"_
- _"DORA third-party risk"_
- _"TLPT financial entity"_
- _"DORA contractual provisions"_
- _"digital operational resilience"_
- _"DORA vs NIS2"_
- _"critical ICT third-party service provider"_

### 示例提示词

```
"Run a full DORA gap analysis for a mid-size EU investment firm. We have
existing ISO 27001 certification, a basic incident response process, and
a vendor management policy. We do not have a formal DORA ICT risk
management framework, no Register of Information, and our cloud contracts
predate DORA. Produce a gap table across all four substantive DORA pillars."
```

```
"We experienced a ransomware incident that encrypted our trading system
for 8 hours, affecting approximately €2.3M in delayed transactions and
15,000 client accounts. Walk me through: (1) whether this is a major ICT
incident under Art. 18, (2) the reporting timeline, and (3) what content
the initial 4-hour notification must contain."
```

```
"We have 60 ICT service arrangements including AWS (critical), Microsoft
365, Bloomberg Terminal, and 57 other SaaS vendors. Build us a Register
of Information structure per CIR (EU) 2024/2956 and identify which
arrangements require full Art. 30(2) contractual provisions."
```

```
"Review the following ICT service contract with our cloud provider against
DORA Art. 30(2)(a)–(i) requirements. Identify missing provisions and draft
the replacement clauses needed for compliance."
```

```
"We are a large payment institution. Do we meet the TLPT threshold under
Art. 26(8)? If yes, walk us through the complete TLPT process from scope
definition through competent authority notification and attestation."
```

---

## 5. 技能实现细节

### 架构

```
dora/
├── SKILL.md                          # Core skill — 9-chapter DORA structure, in-scope
│                                     #   entities, Art. 5–16 (ICT RMF), Art. 17–23
│                                     #   (incident management), Art. 24–27 (testing),
│                                     #   Art. 28–44 (third-party risk), gap analysis
│                                     #   workflows, Register of Information, TLPT process,
│                                     #   common DORA errors
└── references/
    ├── rts-its-guide.md              # All 12 adopted RTS/ITS: regulation number, article
    │                                 #   mapping, application date, and key requirements
    ├── article-reference.md          # All 64 DORA articles with obligation summaries
    │                                 #   and key sub-paragraph citations
    ├── third-party-risk.md           # Deep-dive: Art. 28–44, Register of Information
    │                                 #   mandatory fields, Art. 30 contractual provisions,
    │                                 #   ICT concentration risk, exit strategies, CTPP oversight
    └── incident-classification.md    # Art. 17–23 incident management process, CDR 2024/1772
                                      #   classification criteria, 3-stage reporting timelines,
                                      #   templates, and voluntary reporting provisions
```

**总计：** 5 个文件约 1,650 行（SKILL.md + 4 个参考文件）

### SKILL.md 包含的内容

- **六项基础规则**——防止最常见的 DORA 咨询错误（NIS2 混同、遗留 EBA 指南、章节命名、逐条引用、第二章与第三章的区分、正确的 RTS/ITS 引用）
- **响应格式路由**——9 种任务类型映射到具体输出格式
- **DORA 结构一览**——逐章表格（第 1–64 条）附主题摘要
- **在范围内的金融机构（第 2 条）**——10 多种实体类型；比例原则和简化框架资格（第 4 条、第 16 条）
- **第二章（第 5–16 条）**——逐条：治理、ICT RMF、系统/工具、识别、保护、检测、响应/恢复、备份、学习、沟通、简化框架
- **第三章（第 17–23 条）**——事件管理流程、分类标准、3 阶段报告时限表、支付相关事件
- **第四章（第 24–27 条）**——年度测试计划、TLPT 阈值标准、TLPT 流程、测试人员资质、TIBER-EU 对齐
- **第五章（第 28–44 条）**——ICT 第三方风险政策、信息登记册、集中度风险、退出策略、第 30(2) 条条款检查清单、CTPP 监督框架、首席监督员权力
- **第六章（第 45 条）**——自愿信息共享安排
- **4 阶段差距分析框架**——覆盖治理、事件管理、测试和第三方风险
- **信息登记册必填字段**——按 CIR（EU）2024/2956
- **TLPT 流程**——7 步端到端流程
- **常见 DORA 合规错误**——7 项错误及正确做法

### 参考文件包含的内容

| 文件 | 内容 |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `rts-its-guide.md` | 全部 12 项已通过的欧盟委员会授权/实施条例：CDR（EU）2024/1502（CTPP 标准）、CDR（EU）2024/1773（第三方风险政策）、CDR（EU）2024/1774（ICT RMF）、CDR（EU）2024/1772（事件分类）、CIR（EU）2024/2956（信息登记册）、CDR（EU）2025/301（事件报告）、CIR（EU）2025/302（报告模板）、CDR（EU）2025/1190（TLPT）、CDR（EU）2025/532（分包）、CDR（EU）2025/420（JET）、CDR（EU）2025/295（监督协调统一）、CDR（EU）2024/1505（监督费用） |
| `article-reference.md` | DORA 全部 64 条：简短义务摘要、关键子款，以及每条的适用 RTS/ITS 引用 |
| `third-party-risk.md` | 第 28–44 条深度解析：完整的信息登记册必填字段集；第 30(2)(a)–(i) 条合同条款及说明性注释；ICT 集中度风险评估方法；退出策略规划要求；CTPP 指定标准和首席监督员监督流程 |
| `incident-classification.md` | 第 17–23 条事件管理：按 CDR（EU）2024/1772 的分类标准及重要性阈值；重大事件判定决策流程图；3 阶段报告时限及各阶段内容要求；重大网络威胁自愿报告；支付事件规则（第 23 条） |

### 用于构建技能的资料

| 资料 | 说明 |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **《条例（EU）2022/2554》** | DORA 全文——全部 64 条和 9 章；载于 2022 年 12 月 27 日《欧盟官方公报》L 333 |
| **12 项已通过的 RTS/ITS（CDR/CIR）** | EBA、ESMA、EIOPA 通过的所有欧盟委员会授权和实施条例（完整清单见 rts-its-guide.md） |
| **EBA、ESMA、EIOPA 指引** | 欧洲监管机构关于 DORA 实施的问答、咨询文件和最终意见 |
| **NIS2 指令（EU）2022/2555** | 用于第 4(2) 条 DORA 特别法（lex specialis）的澄清引用 |
| **TIBER-EU 框架** | 用于 TLPT 对齐（第 26 条）的引用 |
| **DORA 之前的 EBA 指南（EBA/GL/2019/04）** | 仅用于提示：自 2025 年 1 月 17 日起，该指南对在范围内的实体已被取代 |

### 技能触发短语

`DORA`、`Digital Operational Resilience Act`、`Regulation (EU) 2022/2554`、`DORA compliance`、`DORA gap analysis`、`ICT risk management framework`、`ICT RMF DORA`、`Art. 6 DORA`、`Art. 17 DORA`、`Art. 19 DORA`、`Art. 26 DORA`、`Art. 28 DORA`、`Art. 30 DORA`、`TLPT`、`threat-led penetration testing`、`Register of Information`、`major ICT incident`、`ICT incident reporting`、`ICT third-party risk`、`critical ICT third-party`、`CTPP`、`DORA third-party policy`、`ICT concentration risk`、`DORA contractual provisions`、`DORA simplified framework`、`digital operational resilience testing`、`DORA vs NIS2`、`EBA DORA`、`ESMA DORA`、`EIOPA DORA`、`financial entity ICT`、`DORA RTS`、`DORA ITS`

---

## 6. 作者

**Hemant Naik**
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)

技能版本：1.6.2 —— 2026 年 7 月
