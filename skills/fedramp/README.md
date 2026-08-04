# FedRAMP 认证技能

一个为 FedRAMP 授权提供专家级端到端指引的 Claude 技能——从初始就绪度评估到 ATO 文档、控制映射、云架构审查和持续监控。

---

## 本技能做什么

本技能将 Claude 变成一位知识渊博的 FedRAMP 顾问。它涵盖云服务提供商（CSP）在当前 **NIST SP 800-53 Rev 5** 基线和 **CR26（FedRAMP 2026 年合并规则）** 框架下追求或维持 FedRAMP 认证的完整授权生命周期。

高层级上，本技能使 Claude 能够：

- 对照跨 14 个安全域的 75+ 项清单进行**就绪度和差距评估**
- 指导核心 **ATO 文档**的撰写：SSP、POA&M、SAP、SAR 以及所有必需附录（A–Q）
- 将全部 20 个 NIST 800-53 Rev 5 控制族的**控制映射**到具体系统实施
- 就**CR26 认证类别 A–D** 提供建议，它们取代了旧的 Low/Moderate/High/LI-SaaS 影响级别
- 为 AWS GovCloud、Azure Government 和 Google Cloud 提供**架构指引**——包括常见发现、继承模式和设计建议
- 支持**持续监控（ConMon）**义务：月度交付物、年度评估、POA&M 管理和偏差请求处理
- 引导 **FedRAMP 20x** 采用——现为主要授权路径，含持续授权和自动化证据收集
- 为 CSP 迎接 **OSCAL 强制要求**（2026 年 9 月 30 日）做准备——机器可读授权包提交

本技能截至 2026 年 7 月为现行，纳入了 CR26 认证类别 A–D、作为主要路径的 FedRAMP 20x、FedRAMP Ready 退役（2026 年 7 月 28 日）、2026 年 9 月 OSCAL 强制要求、2026 年 1 月 Security Inbox 要求以及 2024 年 12 月模板更新。

---

## 目标受众

| 受众                            | 受益方式                                                                                           |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **云服务提供商（CSP）**  | 驾驭授权流程、撰写 SSP 叙述、管理 POA&M、为 3PAO 评估做准备       |
| **ISSO / 安全工程师**      | 将控制映射到实施、识别差距、审查 SAR 发现、管理 ConMon 活动              |
| **合规经理 / GRC 团队** | 理解 FedRAMP 要求、跟踪整改 SLA、跨团队协调文档             |
| **云架构师**                | 从零设计满足 FedRAMP 要求的系统；理解边界界定           |
| **联邦机构人员**        | 理解应从 CSP 授权包中期待什么；评估 SSP 和 SAR 质量                 |
| **3PAO 评估员**                  | 参考控制族要求、测试用例范围和文档结构预期                |
| **顾问 / 咨询机构**    | 跨认证类别和授权阶段快速向客户提供准确的 FedRAMP 指引 |

---

## 常见使用场景

### 1. 就绪度评估

> _"We're a SaaS company on AWS GovCloud targeting FedRAMP Class B (Moderate equivalent). Are we ready?"_

技能会带您进行结构化差距分析——询问您的边界、加密态势、日志记录、IAM、策略和事件响应——并产出带建议的优先差距表。它还会建议是走 FedRAMP 20x（现为主要路径）还是传统机构授权包。

### 2. 撰写 SSP 控制叙述

> _"Help me write the control implementation statement for AC-2 (Account Management)."_

技能生成详细的、可直接供审核的散文，涵盖控制要求的每个动词，区分 CSP 与客户责任，并引用具体工具和策略。

### 3. 创建 POA&M 条目

> _"The 3PAO found that we don't have MFA on one of our admin interfaces. Help me write the POA&M entry."_

技能产出带所有必需字段的完整 POA&M 行：风险评级、整改计划、里程碑日期、责任人以及适用的偏差请求指引。

### 4. CR26 认证类别界定

> _"Our system processes law enforcement data. What certification class do we need and how many controls apply?"_

技能将系统的数据敏感性映射到适当的 CR26 认证类别（A、B、C 或 D），并解释相应的控制基线。它还注明熟悉旧框架的 CSP 的传统 Low/Moderate/High 对应级别。

### 5. NIST 800-53 控制映射

> _"Which controls cover encryption in transit, and how should we implement them on Azure Government?"_

技能将问题映射到特定控制族（SC、IA），描述 FedRAMP 参数要求，并提供 Azure 特定的实施指引。

### 6. 架构审查

> _"Review our architecture for FedRAMP compliance gaps."_

给定系统描述，技能识别常见发现——未记录的对外连接、FIPS 不合规、IAM 过度授权、日志缺口、缺少 OSCAL 工具——并建议整改措施。

### 7. FedRAMP 20x 路径指引

> _"What is FedRAMP 20x and how do we pursue it?"_

技能解释 FedRAMP 20x 作为 CR26 下的主要授权路径——涵盖持续授权、模块化 API 驱动提交、自动化证据收集，以及它与传统机构授权包的区别。

### 8. 持续监控支持

> _"What do we need to submit to our agency AO every month?"_

技能概述月度与年度 ConMon 义务、POA&M SLA 要求，以及如何处理供应商依赖和偏差请求。

### 9. 3PAO 合作指引

> _"How do we select and work with a 3PAO?"_

技能解释 FedRAMP Marketplace 要求、A2LA R311 咨询/评估分离规则，以及 CSP 在审查和批准 SAP 与 SAR 文档方面的责任。

### 10. OSCAL 就绪度

> _"What is OSCAL and what do we need to do before September 30, 2026?"_

技能解释 OSCAL 强制要求（RFC-0024）、机器可读授权包需要什么，以及如何在 2026 年 9 月 30 日截止日期前开始为 OSCAL 导出构建 SSP 数据结构。

---

## 关键 CR26 变更（2026 年 7 月）

| 变更                             | 详情                                                                                                                                                                                                |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **认证类别 A–D**      | 取代 FIPS 199 基线标签（依据 NTC-0004）：类别 A = 新的试点/过渡基线（外部框架入口，例如 SOC 2 Type II），类别 B = LI-SaaS + Low，类别 C = Moderate，类别 D = High |
| **FedRAMP Ready 退役**          | 2026 年 7 月 28 日——不再有新指定；现有 Ready CSP 必须过渡到 FedRAMP 20x 或完整授权                                                                                          |
| **FedRAMP 20x 成为主要路径** | 持续授权、模块化提交、自动化证据——不只是试点                                                                                                                   |
| **JAB P-ATO 退役**              | FedRAMP PMO 现在是唯一授权机构                                                                                                                                                         |
| **OSCAL 强制要求**                  | 所有 CSP 必须在 2026 年 9 月 30 日前提交机器可读的 OSCAL 包                                                                                                                             |

---

## 如何使用本技能

### 安装

1. 从此仓库下载 `fedramp.skill`
2. 在 Claude 中，进入 **Settings → Skills**
3. 上传 `.skill` 文件
4. 技能现已激活——Claude 将自动将其用于 FedRAMP 相关问题

### 触发技能

当您提及以下主题时，技能自动激活：

- FedRAMP、ATO、Authority to Operate、CR26
- SSP、SAP、SAR、POA&M
- NIST 800-53、控制族、控制映射
- FedRAMP 认证类别（A、B、C、D）或旧影响级别（Low、Moderate、High、LI-SaaS）
- FedRAMP 20x、OSCAL、持续授权
- 3PAO、持续监控、ConMon
- 联邦政府云安全、AWS GovCloud、Azure Government

### 示例提示

```
"Assess our FedRAMP readiness. We're a SaaS company running on AWS GovCloud targeting Class B (Moderate equivalent)."

"Write an SSP control narrative for SC-8 (Transmission Confidentiality and Integrity)."

"Create a POA&M entry for a High finding: missing MFA on the admin portal."

"Map the AU control family to our AWS CloudTrail and Security Hub setup."

"What architecture changes do we need to meet FedRAMP Class C (High equivalent) requirements?"

"Explain the CR26 Certification Classes and how they map to the old impact levels."

"What do we need to do to prepare for the September 30, 2026 OSCAL mandate?"
```

---

## 技能实现细节

### 文件结构

```
fedramp/
├── SKILL.md                          # Main skill — routing logic, all five domains
└── references/
    ├── readiness-checklist.md        # 75+ item readiness checklist (14 categories)
    ├── ssp-guide.md                  # SSP section-by-section writing guide + appendices A–Q
    ├── poam-guide.md                 # POA&M fields, deviation types, SLA table
    └── sap-sar-guide.md              # SAP/SAR structure, 3PAO guidance, CSP review tips
```

### 构建方式

本技能使用 **Claude Skill Creator** 框架编写，该框架将知识组织为分层、渐进披露的格式：

- **SKILL.md**（主文件）：包含一个路由表，根据用户意图将 Claude 导向正确的领域、截至 2026 年 7 月 FedRAMP（CR26）的现行状态摘要，以及五个领域章节（就绪度、ATO 文档、控制映射、架构、ConMon）
- **参考文件**：需要更深层指引时按需加载——保持主技能精简聚焦

**用于构建技能的输入：**

- FedRAMP CR26（2026 年合并规则）文档，含通知 NTC-0004 和 PMO 公告（fedramp.gov）
- FedRAMP Rev 5 基线文档和过渡指南
- NIST SP 800-53 Rev 5 控制族和参数要求
- FedRAMP CSP 授权手册（v4.2，2025 年 11 月）
- FedRAMP 年度评估指引（v3.0，2024 年 2 月）
- FedRAMP Rev 5 模板发布说明（2024 年 12 月）
- RFC-0024 OSCAL 强制要求文档
- FedRAMP SSP、POA&M、SAP、SAR 模板结构
- A2LA R311 3PAO 咨询/评估分离要求
- FedRAMP 2026 年 1 月 Security Inbox 指令

**设计决策：**

- 技能顶部使用**快速引用路由表**，使 Claude 能立即导航到正确章节，而非每次查询都通读全文
- **CR26 认证类别 A–D** 是主要框架；保留传统 Low/Moderate/High 映射以帮助过渡中的 CSP
- **输出格式与请求类型匹配**（差距评估用表格、控制叙述用散文、POA&M 用结构化行）——确保输出立即可用
- 参考文件**模块化并按需加载**，按 Skill Creator 指南将主技能保持在 500 行以内
- 所有指引锚定于**当前 FedRAMP 状态**（CR26、Rev 5、2026 年 7 月要求），并明确标注 CR26 变更，避免过时建议

### 依赖

- 无需外部工具或 API
- 完全在 Claude 的上下文窗口内运行
- 官方 FedRAMP 模板以 URL 引用（https://www.fedramp.gov/documents-templates/）——不内嵌，因为这些模板由 FedRAMP PMO 定期更新

---

## 版本历史

| 版本   | 日期       | 变更                                                                                                                                                                                                                                                                                                                                                                                  |
| --------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1.5.0** | 2026 年 7 月  | 将 CR26 认证类别映射更正为官方 NTC-0004（A = 试点/过渡，B = LI-SaaS + Low，C = Moderate，D = High）；CR26 更名为"2026 年合并规则"；POA&M 整改 SLA 更正为 ConMon 绩效管理指南值（High 30 天 / Moderate 90 天 / Low 180 天）；使用一手来源断言重新运行基准：使用技能 92% vs 基线 84% |
| **1.4.0** | 2026 年 7 月  | CR26 更新：认证类别 A–D、FedRAMP 20x 成为主要路径、FedRAMP Ready 退役（2026 年 7 月 28 日）、OSCAL 强制要求（2026 年 9 月 30 日）、JAB P-ATO 退役                                                                                                                                                                                                               |
| **1.0.0** | 2026 年 3 月 | 初始发布，含 Rev 5 基线、ConMon 指引、OSCAL 认知                                                                                                                                                                                                                                                                                                                    |

---

## 作者

**Hemant Naik**
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)
2026 年 7 月
