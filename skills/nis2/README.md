# 欧盟网络与信息安全指令 2（NIS2）技能

> ⚠️ **免责声明：**本技能提供基于指令 (EU) 2022/2555（NIS2）和 ENISA 指引的信息性指导。它不构成法律意见。NIS2 在欧盟各成员国以不同方式转化，义务因法域而异。对涉及监管机构互动、向国家 CSIRT 报告事件或罚款敞口的事项，请在相关成员国咨询有资质的律师。

---

## 1. 本技能做什么？

NIS2 合规技能将 Claude 转变为具备指令 (EU) 2022/2555（NIS2）全面知识的欧盟网络安全监管专家。该指令于 2022 年 12 月 27 日生效，取代 NIS1（指令 (EU) 2016/1148），成员国转化期限为 2024 年 10 月 17 日。本技能覆盖完整的 NIS2 合规生命周期——从初始实体分类、治理义务、安全措施实施、事件报告、供应链安全到监管互动。

本技能的核心参考点是两级实体分类：基本实体（EE）覆盖附件 I 中的能源、交通、银行、健康、数字基础设施和公共行政等部门；重要实体（IE）覆盖附件 II 中的邮政服务、废物管理、化学品、食品、制造和研究等部门。规模门槛（中型企业：≥50 名员工 或 ≥1000 万欧元营业额）决定自动纳入，较小实体可能通过成员国指定进入范围。

本技能对全部 10 项第 21 条网络安全风险管理措施提供详细指导——从风险分析政策和事件处理到 MFA 强制要求和供应链安全——以及第 23 条事件报告时间线：24 小时预警、72 小时事件通知和向国家 CSIRT 或主管机构的 1 个月最终报告。它还涵盖第 20 条管理机构治理义务，包括个人责任条款和高级领导层的强制性网络安全培训。

本技能包含详细的 ISO 27001:2022 对齐模块，将全部 10 项第 21 条措施映射到对应的附件 A 控制，并明确识别 NIS2 超越 ISO 27001 的四个领域：显式 MFA 强制要求、供应链 ENISA 风险评估、管理机构个人责任和规定性事件报告时间线。

---

## 2. 目标受众

| 受众 | 如何使用本技能 |
| -------------------------------------- | --------------------------------------------------------------------------------------------- |
| **CISO 和安全负责人** | 对照第 21 条措施的差距评估、政策起草、监管互动准备 |
| **董事会和高管团队** | 理解第 20 条治理义务和个人责任条款 |
| **合规和风险经理** | 实体分类、罚款敞口分析、补救路线图 |
| **IT 和 OT 安全团队** | 全部 10 项第 21 条措施带技术细节的控制实施指导 |
| **法律顾问** | 成员国转化差异、监管敞口（EE 与 IE）、罚款计算 |
| **ISO 27001 从业者** | 将现有 ISMS 控制映射到 NIS2 义务、识别差距 |
| **供应链和采购团队** | 实施第 21(2)(d) 条供应商安全要求 |
| **事件响应团队** | 带预起草通知模板的第 23 条报告工作流 |

---

## 3. 常见用例

### 实体分类

- “根据 NIS2，我们是基本实体还是重要实体？”
- “我们是云服务提供商——哪个 NIS2 附件适用于我们？”
- “NIS2 适用于我们这家 45 人的公司吗？”
- “德国/法国/爱尔兰如何转化 NIS2——我们需要自我注册吗？”

### 差距评估

- “对照全部 10 项第 21 条措施进行 NIS2 差距评估”
- “我们有 ISO 27001 认证——为 NIS2 我们还需要哪些额外控制？”
- “对照每项第 21 条措施评估我们当前的安全态势并识别优先差距”
- “如果我们未通过第 21 条差距评估，罚款敞口是多少？”

### 第 21 条控制实施

- “NIS2 对第 21(2)(d) 条下的供应链安全有什么要求？”
- “起草一份与第 21(2)(h) 条对齐的密码学和加密政策”
- “第 21(2)(j) 条施加了哪些 MFA 要求，我们应如何实施？”
- “帮我构建一份满足第 21(2)(c) 条的业务连续性计划”

### 事件报告

- “带我逐步过一遍 NIS2 第 23 条事件报告时间线”
- “什么使事件在第 23(3) 条下‘重大’？”
- “为我们的国家 CSIRT 起草一份 24 小时预警通知模板”
- “1 个月最终报告必须包含什么？”

### 治理和管理机构义务

- “第 20 条对我们的董事会关于网络安全有什么要求？”
- “NIS2 下管理机构需要什么网络安全培训？”
- “起草一份与第 20 条对齐的董事会级网络安全治理章程”
- “NIS2 下高级管理层的个人责任如何运作？”

### ISO 27001 对齐

- “将我们的 ISO 27001:2022 附件 A 控制映射到 NIS2 第 21 条措施”
- “我们有 ISO 27001——这覆盖 NIS2 合规吗？”
- “ISO 27001 认证未解决的 NIS2 差距有哪些？”
- “哪些 ISO 27001:2022 控制覆盖第 21 条措施 4 的供应链安全？”

---

## 4. 如何使用本技能

### 安装

1. 从本文件夹下载 `nis2.skill`
2. 在 Claude 中，前往 **设置 → 技能**
3. 点击 **上传技能** 并选择 `nis2.skill`
4. 该技能现在在所有 Claude 会话中激活

### 触发技能

当你提出 NIS2 或欧盟网络安全指令主题时，本技能自动激活。无需特殊命令。触发本技能的自然语言短语示例：

- _"Are we subject to NIS2?"_
- _"We need to comply with the NIS2 Directive"_
- _"What does NIS2 require for incident reporting?"_
- _"Gap assessment against NIS2 Art. 21"_
- _"Essential Entity vs Important Entity classification"_
- _"NIS2 and ISO 27001 alignment"_
- _"We had a cybersecurity incident — do we need to report it?"_

### 示例提示

```
We are a mid-size energy distribution company operating across three EU Member States
with 200 employees and €80M annual revenue. Are we an Essential Entity or Important Entity
under NIS2, and what are the key differences in supervisory treatment between the two tiers?
```

```
Conduct a NIS2 Art. 21 gap assessment for our organisation. We have ISO 27001:2022
certification. For each of the 10 measures, identify whether our ISO 27001 controls
provide sufficient evidence and highlight where we have specific NIS2 gaps.
```

```
We experienced a ransomware attack yesterday that disrupted our online banking services
for 6 hours affecting approximately 40,000 customers. Walk me through the NIS2 Art. 23
incident reporting process — what do we need to report, to whom, and by when?
```

```
Our board is asking what their personal obligations are under NIS2 Art. 20. Draft a
briefing note covering: what they must approve, what training they need, and what
personal liability they face if cybersecurity measures are inadequate.
```

```
Draft an NIS2-compliant supply chain security policy covering: supplier risk assessment,
contractual security requirements, ongoing monitoring, and integration with ENISA
coordinated risk assessments under Art. 22.
```

---

## 5. 技能实现细节

### 架构

```
plugins/nis2/
└── skills/
    └── nis2/
        ├── SKILL.md                        # 核心技能——实体分类、所有关键条款、
        │                                   #   7 个核心帮助工作流、参考加载规则
        └── references/
            ├── article-21-measures.md      # 全部 10 项第 21 条措施的详细实施
            │                               #   指导，包括比例原则、重大事件
            │                               #   指示符、技术细节
            └── iso27001-nis2-mapping.md    # ISO 27001:2022 附件 A 到 NIS2 第 21 条
                                            #   交叉引用表；与 ISO 27001 相比的 4 个
                                            #   关键 NIS2 差距；对已认证组织的
                                            #   实用指导
```

### SKILL.md 中包含什么

- 专家人设：具备完整指令知识的 NIS2 合规顾问
- 核心框架：两级实体分类（EE/IE）、附件 I/II 部门、规模门槛（第 3 条）
- 关键条款摘要：第 20 条（治理）、第 21 条（10 项风险管理措施）、第 23 条（事件报告——24 小时/72 小时/1 个月）、第 22 条（协调供应链风险评估）、第 32/33 条（监管——EE 主动与 IE 被动）、第 34 条（罚款——EE 为 1000 万欧元/2%，IE 为 700 万欧元/1.4%）
- 7 个带详细指导的核心帮助工作流（分类、差距评估、事件报告、治理、政策起草、ISO 27001 对齐、罚款分析）
- 参考文件加载说明

### 参考文件中包含什么

| 文件 | 内容 |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `references/article-21-measures.md` | 全部 10 项第 21 条措施及完整实施指导；具体技术细节（密码算法、MFA 标准、补丁 SLA、备份测试频率、RBAC 要求）；按第 23(3) 条的重大事件指示符；带 EE 与 IE 区分的比例原则 |
| `references/iso27001-nis2-mapping.md` | 全部 10 项 NIS2 第 21 条措施到 ISO 27001:2022 附件 A 控制的完整映射表；无直接 NIS2 对应物的 ISO 27001 控制；ISO 27001 覆盖有限的 6 项 NIS2 要求（第 20 条个人责任、第 23 条时间线、第 22 条 ENISA 供应链、MFA 强制要求）；对 ISO 27001 认证实体的 6 步实用指导 |

### 用于构建技能的输入

| 输入 | 详情 |
| ---------------------- | -------------------------------------------------------------------------------- |
| 主要指令 | 指令 (EU) 2022/2555（NIS2）——2022 年 12 月 27 日生效 |
| 前身指令 | 指令 (EU) 2016/1148（NIS1）——被 NIS2 废止 |
| 转化期限 | 2024 年 10 月 17 日 |
| ENISA 指引 | ENISA NIS2 指南；ENISA 协调供应链风险评估（第 22 条） |
| ISO 对齐 | ISO/IEC 27001:2022 及附件 A 控制 |
| 风险方法论 | ISO 27005；NIST RMF（作为等效方法论引用） |
| 事件报告 | 欧盟各成员国的国家 CSIRT 通知框架 |
| 监管框架 | 第 32 条（EE 主动）和第 33 条（IE 被动）监管 |
| 罚款框架 | 第 34 条——EE（1000 万欧元/2% 全球营业额）、IE（700 万欧元/1.4% 全球营业额） |

### 技能触发短语

`NIS2`、`NIS 2`、`Network and Information Security Directive`、`Directive (EU) 2022/2555`、
`Essential Entity`、`Important Entity`、`Art. 21 NIS2`、`Art. 23 NIS2`、`Art. 20 NIS2`、
`CSIRT notification`、`24 hour early warning`、`72 hour incident notification`、
`NIS2 gap assessment`、`NIS2 compliance`、`cybersecurity risk management measures`、
`supply chain security NIS2`、`NIS2 penalties`、`€10 million fine`、`2% global turnover`、
`NIS2 and ISO 27001`、`NIS2 board obligations`、`management body cybersecurity`、
`NIS2 transposition`、`significant incident`、`ENISA NIS2`、`NIS2 sectors`、`Annex I Annex II`

---

## 6. 作者

**Hemant Naik**
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)

技能版本：1.6.2 —— 2026 年 7 月
