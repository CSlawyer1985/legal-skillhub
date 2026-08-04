# 澳大利亚信息安全手册（ISM）技能

> **免责声明：**本技能提供基于澳大利亚信号局（ASD）信息安全手册（2026 年 3 月版）的信息性指引。它不构成官方 ASD 指引或正式安全评估。系统授权决定、IRAP 评估结果和 ATO 签署是合格授权官和 ASD 认证的 IRAP 评估员的责任。对处理 SECRET 或 TOP SECRET 信息的系统，直接与 ASD 和相关涉密人员接洽。

---

## 1. 本技能做什么？

本技能赋予 Claude 对**澳大利亚信息安全手册（ISM）**的全面专业知识——ASD 面向澳大利亚政府实体、其承包商和供应链的权威网络安全框架。本技能基于 **2026 年 3 月版**的 ISM，该版本由澳大利亚信号局（ASD）发布，并以 OSCAL 1.1.2 机器可读格式提供。它适用于全部五个密级层面的系统：非密（NC）、OFFICIAL: Sensitive（OS）、PROTECTED（P）、SECRET（S）和 TOP SECRET（TS）。

本技能实施 ISM 的六步风险管理周期——定义、选择、实施、评估、授权和监控——并覆盖按四个功能分组的全部 23 项网络安全原则：治理（G1–G5）、保护（P1–P14）、检测（D1）和响应（R1–R3）。它遍历从安全治理到密码学等领域的全部 22 个指南章节，使用 NC/OS/P/S/TS 适用性标记体系按密级选择控制，其中更高密级堆叠所有较低级别控制。

本技能支持完整的 ISM 合规工作流谱系：产生带状态和证据要求的结构化控制表的差距分析；从系统安全计划（SSP）经安全风险评估、IRAP 评估、行动计划与里程碑（POA&M）到运行授权（ATO）的系统授权路径指导；带工件检查清单和评估员标准的 IRAP 评估准备；ISM 对齐的安全文档生成；以及 Essential Eight 与 ISM 关系澄清，包括成熟度级别（ML0–ML3）映射。

它还将补充性的《保护性安全政策框架》（PSPF）、ASD 管理的 IRAP 项目，以及 Essential Eight 合规与完整 ISM 合规之间的关系纳入认知——这是一个常被误解的区别，本技能直接加以处理。

---

## 2. 目标受众

| 角色 | 如何使用本技能 |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| CISO 和 CIO（政府） | 系统授权策略、基于风险的控制选择、IRAP 准备监督 |
| 网络安全架构师 | 控制到系统架构的映射、按密级界定范围、安全目标定义 |
| IRAP 评估员 | 评估工件检查清单、按密级的控制适用性、重新评估触发 |
| IT 安全经理 | 按领域的差距分析、补救路线图、POA&M 制定 |
| 政府承包商与供应链 | 确定承包系统的适用控制、PROTECTED 系统要求 |
| 安全文档专员 | SSP 起草、事件响应计划、持续监控计划、变更管理计划 |
| Essential Eight 项目负责人 | ML0–ML3 目标设定、Essential Eight 到 ISM 控制映射、E8 与完整 ISM 之间的差距 |
| 采购与供应商管理 | 供应链安全要求、供应商 ISM 评估范围 |

---

## 3. 常见用例

### 差距分析

- "为托管在 Azure 政府区域的 OFFICIAL: Sensitive 系统进行 ISM 差距分析。"
- "我们正在构建一个 PROTECTED 系统。NC 基线之上适用哪些 ISM 章节和控制？"
- "为我们本地部署的邮件平台识别当前 ISM 控制实施中的全部关键差距。"
- "为我们的混合云环境生成 ISM 第 7 章（信息技术安全）的差距表。"
- "我们已完成 Essential Eight ML2。我们还需要实施哪些额外 ISM 控制？"

### 控制指导

- "解释 ISM 控制 1336（多因素认证）——它要求什么，审计员期望什么证据？"
- "ISM 对事件日志记录有什么要求，NC 与 OS 与 PROTECTED 系统有何不同？"
- "哪些 ISM 控制管辖补丁管理，应用和操作系统打补丁的时间框架是什么？"
- "带我过一遍 PROTECTED 系统网络分段 的 ISM 要求。"
- "ISM 对密码密钥管理有什么要求？引用相关控制 ID。"

### 系统授权

- "带我走一遍新 OFFICIAL: Sensitive SaaS 平台的完整系统授权路径。"
- "PROTECTED 级系统的系统安全计划（SSP）必须包含什么？"
- "什么是授权官，他们做出哪些风险接受决定？"
- "我们已收到 IRAP 评估报告。从报告到 ATO 决定之间会发生什么？"
- "什么触发已获得 ATO 的系统的重新授权？"

### IRAP 评估准备

- "在我们为 OS 系统聘请 IRAP 评估员之前，必须准备哪些工件？"
- "我们如何核实所选评估员在当前 ASD IRAP 注册簿上？"
- "PROTECTED 系统的评估范围是什么，评估员将审查哪些控制？"
- "系统必须多久重新评估一次，什么构成触发提前重新评估的'重大变更'？"
- "为我们的团队起草一份 IRAP 评估准备检查清单。"

### 安全文档生成

- "为我们的 OFFICIAL: Sensitive 网络应用起草系统安全计划（SSP）大纲。"
- "为 PROTECTED 政府系统生成一份 ISM 对齐的事件响应计划。"
- "创建映射到 ISM 要求的持续监控计划模板。"
- "起草一份引用相关 ISM 章节和控制 ID 的变更管理计划。"

### Essential Eight 与 ISM

- "Essential Eight 与完整 ISM 之间是什么关系？E8 ML3 意味着 ISM 合规吗？"
- "将 Essential Eight 缓解措施映射到其对应的 ISM 控制 ID。"
- "我们被要求达到 Essential Eight ML2。这满足我们机构的 ISM 义务吗？"
- "应用控制的成熟度级别是什么，ML2 在实践中要求什么？"

---

## 4. 如何使用本技能

### 安装

1. 从本文件夹下载 `ism.skill`。
2. 在 Claude 中，前往 **设置 → 技能**。
3. 点击 **上传技能** 并选择 `ism.skill`。
4. 该技能现在在你的 Claude 会话中激活。

### 触发技能

当 ISM 相关主题出现时，本技能自动激活。无需特殊命令。触发它的示例短语：

- _"ISM controls"_ 或 _"Australian Information Security Manual"_
- _"ASD compliance"_、_"IRAP assessment"_、_"IRAP assessor"_
- _"PROTECTED system"_、_"OFFICIAL: Sensitive"_、_"system authorisation"_
- _"Essential Eight vs ISM"_、_"Maturity Level"_、_"ML2 Essential Eight"_
- _"System Security Plan"_、_"SSP"_、_"ATO authorisation"_
- _"NC/OS/P/S/TS classification"_、_"ISM chapter"_、_"ISM gap analysis"_
- _"Australian government cybersecurity"_、_"PSPF"_、_"ASD framework"_

### 示例提示

```
We are a government agency migrating our case management system to AWS GovCloud. The system
handles OFFICIAL: Sensitive data. Perform an ISM gap analysis across the key chapters:
System Security Plan, access control, event logging, vulnerability management, and patch
management. Produce a gap table with: Control ID | Chapter | Description | Applicability |
Status | Evidence Needed | Gap Notes.
```

```
Walk me through the complete system authorisation pathway for a new PROTECTED-level
collaboration platform. List every required artefact, who is responsible for each,
the typical sequence of activities from scoping to ATO, and what triggers a re-assessment.
```

```
Draft an ISM-aligned System Security Plan (SSP) outline for an OFFICIAL: Sensitive
government web application hosted on-premises. Include all mandatory sections with
references to the relevant ISM chapters and control IDs. Include a document control block.
```

```
We are preparing for an IRAP assessment of our PROTECTED system in 90 days.
Generate a preparation checklist covering: required documentation artefacts, network
diagrams, evidence of implemented controls, assessor verification steps, and common
assessment findings we should proactively remediate.
```

```
Explain the difference between Essential Eight ML2 and full ISM compliance for a
PROTECTED system. Produce a mapping table showing: each Essential Eight mitigation |
corresponding ISM control IDs | what ISM controls for PROTECTED systems are NOT
covered by the Essential Eight.
```

---

## 5. 技能实现细节

### 架构

```
ism/
├── SKILL.md                              # 核心技能——ISM 框架、23 项网络安全
│                                         #   原则、六步风险管理周期、控制适用性
│                                         #   标记、五个核心工作流、关键术语
└── references/
    ├── guidelines-overview.md            # 全部 22 个 ISM 指南章节，带领域
    │                                     #   摘要和关键控制领域
    └── control-applicability.md          # 完整控制适用性框架、
                                          #   密级界定规则（NC/OS/P/S/TS）、
                                          #   Essential Eight 到 ISM 控制映射
```

### SKILL.md 中包含什么

- **身份和范围**：面向澳大利亚政府实体和供应链的专家 ISM 合规顾问；基于 2026 年 3 月 ISM 版
- **默认密级**：未指定密级时为 OFFICIAL: Sensitive（OS）
- **响应格式表**：差距分析、控制指导、系统授权、IRAP 准备、安全文档和一般问题的输出格式
- **ISM 框架结构**：跨四个功能（治理、保护、检测、响应）的 23 项网络安全原则；22 个指南章节
- **六步风险管理周期**：定义 → 选择 → 实施 → 评估 → 授权 → 监控
- **控制适用性标记**：NC/OS/P/S/TS 密级体系和堆叠规则
- **核心工作流**：差距分析（包括状态定义）、系统授权路径、IRAP 评估准备、安全文档生成、Essential Eight 与 ISM
- **关键术语表**：ASD、IRAP、SSP、ATO、PSPF、Essential Eight、安全目标、OSCAL
- **参考文件加载指导**：按任务类型何时加载每个参考文件

### 参考文件中包含什么

| 文件 | 内容 |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `guidelines-overview.md` | 全部 22 个 ISM 指南章节：安全治理、信息安全文档、物理安全、人员安全、信息技术安全、软件开发、数据库系统、电子邮件、网络管理、网络设计、密码学、网关安全、数据传输、经评估产品、ICT 设备、介质管理、系统加固、系统管理、系统监控、系统生命周期、外包和专业系统——每个带领域摘要、关键控制领域和常见合规差距 |
| `control-applicability.md` | 按密级的完整控制适用性框架；NC 基线控制（适用于所有系统）；OS、P、S 和 TS 堆叠控制；密级界定决策规则；全部 8 项缓解措施在各级成熟度的 Essential Eight 到 ISM 控制 ID 映射；带成文理由正式排除控制的指导 |

### 用于构建技能的输入

| 来源 | 描述 |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| ASD 信息安全手册（2026 年 3 月版） | 完整框架，包括全部 23 项网络安全原则、22 个指南章节，以及以 OSCAL 1.1.2 发布的所有控制清单 |
| ASD Essential Eight Explained | 全部 8 项缓解措施的成熟度模型（ML0–ML3） |
| ASD Essential Eight to ISM Mapping | 将 E8 缓解措施关联到 ISM 控制 ID 的官方 ASD 映射文件 |
| 保护性安全政策框架（PSPF） | 用于密级标记和信息处理的配套框架 |
| ASD IRAP 项目文件 | IRAP 评估员标准、评估范围要求、重新评估触发 |

### 技能触发短语

`ISM controls`、`Australian Information Security Manual`、`ASD compliance`、
`IRAP assessment`、`IRAP assessor`、`infosec registered assessors program`、
`PROTECTED system`、`OFFICIAL: Sensitive`、`TOP SECRET system`、`SECRET system`、
`NC OS P S TS classification`、`system authorisation`、`Authorisation to Operate`、
`ATO government`、`System Security Plan`、`SSP ISM`、`Essential Eight vs ISM`、
`Essential Eight maturity level`、`ML0 ML1 ML2 ML3`、`ISM gap analysis`、
`ISM chapter`、`ISM guideline`、`Australian government cybersecurity`、
`PSPF security`、`ASD framework`、`cyber security principles ASD`、
`Govern Protect Detect Respond ASD`、`six-step risk management ISM`

---

## 6. 作者

**Hemant Naik**
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)

技能版本：1.6.2 —— 2026 年 7 月
