# 印度《数字个人数据保护法》（DPDPA）技能

> **免责声明：** 本技能基于《2023 年数字个人数据保护法》和《2025 年数字个人数据保护规则》提供信息性指引。它不构成法律意见。对涉及重大合规风险、数据保护委员会程序或复杂跨境情形的事项，请咨询合格的印度数据保护律师或您的数据保护官（DPO）。对等待中央政府通知的事项（SDF 指定、受限转移国家、规定的时限）的指引，已明确标记为临时性。

---

## 1. 本技能做什么

本技能赋予 Claude 对印度**《2023 年数字个人数据保护法》**（DPDPA）——2023 年 8 月 11 日由议会通过——以及**《2025 年数字个人数据保护规则》**（2025 年 11 月 13 日由电子与信息技术部（MeitY）通知）的深度专业知识。全面合规截止日期为**2027 年 5 月 13 日**（自规则通知起 18 个月），印度数据保护委员会（DPBI）自 2025 年 11 月起运作。

本技能覆盖该法的每一章和全部 23 条规则：双合法基础框架（第 6 条下的同意和第 7 条下的八项列举的合法使用）、第 4-10 条的数据受托人义务（通知要求、安全保障、违规通知、数据删除和儿童数据保护）、第 11-15 条的数据主体权利、第 16 条下的跨境转移规则、第 10 条和规则 13 下的重要数据受托人（SDF）附加义务，以及数据保护委员会的裁决权力和第 33 条下的完整处罚表。

本技能全程使用精确的 DPDPA 术语——数据受托人（Data Fiduciary）、数据主体（Data Principal）、数据处理者（Data Processor）、重要数据受托人（Significant Data Fiduciary）、数据保护委员会（Data Protection Board）——在有用时一次性映射到 GDPR 对应概念，然后保持 DPDPA 语言。每项义务都引用其管辖条款或规则（例如"必须按 DPDP 规则 2025 第 5 条和规则 3 提供通知"）。等待中央政府通知的事项——包括 SDF 指定、第 16 条下的受限国家清单、初创企业豁免和规定的响应时限——始终标记为临时性。

本技能对正在构建合规项目的印度组织同样有价值，对处理位于印度境内个人个人数据的全球公司也有价值——后者依据第 3 条触发域外适用。它产出结构化的差距分析表、满足规则 3 全部要求的独立通知草稿、对照规则 16 的数据处理协议审查、按委员会 72 小时时限的逐步违规通知程序、SDF 自我评估清单、GDPR 与 DPDPA 并排对比，以及第 9 条和规则 10、12 下的儿童数据合规审查。

---

## 2. 目标受众

| 角色                               | 如何使用本技能                                                                       |
| ---------------------------------- | -------------------------------------------------------------------------------------------- |
| 隐私与 DPO 团队                | 差距分析、通知起草、同意机制审查、违规通知 SOP            |
| 法律顾问                      | 法律意见的条款/规则引用、GDPR 与 DPDPA 对比、委员会投诉程序 |
| 合规经理                | 端到端合规路线图、处罚风险评估、处理登记映射          |
| 技术与产品团队         | 同意界面/体验审查、儿童年龄门禁要求、数据删除工作流               |
| CISO 与安全团队             | 第 8(3) 条/规则 7 安全保障要求、72 小时违规通知流程     |
| 全球/跨国组织 | 域外范围分析（第 3 条）、跨境转移指引（第 16 条）    |
| 供应商与数据处理者          | 规则 16 合同要求、子处理者义务                                     |
| 初创企业与中小企业                    | 范围分析、初创企业豁免监测、相称合规路线图             |

---

## 3. 常见使用场景

### 差距分析与就绪度

- "为我们的服务印度用户的 SaaS 平台执行 DPDPA 差距分析。"
- "我们已有 GDPR 合规。为 DPDPA 还需要哪些额外步骤？"
- "DPDPA 的哪些条款适用于我们在新加坡、有印度客户的公司？"
- "我们需要哪些证据来证明第 8(3) 条安全保障合规？"
- "将我们的数据处理活动映射到 DPDPA 合法基础——我们一直在使用合法利益。"

### 通知与同意

- "为我们的移动应用起草满足规则 3 全部要求的独立数据收集通知。"
- "审查我们当前的隐私政策，找出 DPDPA 合规差距。"
- "我们的同意与服务条款捆绑在一起。这在第 6 条下有效吗？"
- "我们如何实施满足第 6(4) 条的同意撤回机制？"
- "DPDPA 下的预勾选框和暗黑模式禁止规定是什么？"

### 儿童数据（第 9 条）

- "规则 12 下哪些年龄验证方法可被接受，适用于我们的平台？"
- "我们开展定向广告——第 9 条下对儿童用户需要哪些变更？"
- "我们对儿童账户使用会话分析是否违反第 9(2) 条？"
- "使用 DigiLocker 起草可验证的家长同意工作流。"

### 违规通知

- "带我走一遍向数据保护委员会提交的 72 小时违规通知流程。"
- "起草一份同时面向委员会（规则 6）和数据主体的违规通知模板。"
- "DPDPA 下什么构成'个人数据违规'，我们何时必须通知？"

### 重要数据受托人

- "我们可能被指定为 SDF 吗？第 10 条下适用哪些标准？"
- "第 10 条和规则 13 下对 SDF 适用哪些附加义务？"
- "我们的 DPO 在英国办公——这满足第 10 条的印度居留要求吗？"
- "SDF 的年度数据保护影响评估必须涵盖什么？"

### 跨境数据传输

- "我们能依据第 16 条将印度用户数据传输到我们爱尔兰的数据中心吗？"
- "DPDPA 的黑名单方法与 GDPR 的白名单方法有什么区别？"
- "我们如何为第 16 条下未来的受限国家通知做准备？"

### 数据主体权利

- "数据主体在 DPDPA 下享有哪些权利，在什么时限内？"
- "起草一份涵盖第 11-14 条的权利请求处理程序。"
- "我们能依据第 12 条拒绝删除请求吗？在什么情况下？"
- "第 14 条下的指定权利是什么，我们如何将其落地运作？"

### 供应商与处理者管理

- "对照规则 16 审查我们的标准供应商协议是否符合 DPDPA。"
- "规则 16 下数据处理协议必须包含哪些强制条款？"

---

## 4. 如何使用本技能

### 安装

1. 从此文件夹下载 `dpdpa.skill`。
2. 在 Claude 中，进入 **Settings → Skills**。
3. 点击 **Upload Skill** 并选择 `dpdpa.skill`。
4. 该技能现已在您的 Claude 会话中激活。

### 触发技能

当 DPDPA 相关话题出现时，技能自动激活。无需特殊命令。触发它的示例短语：

- _"DPDPA gap analysis"_ 或 _"India data privacy compliance"_
- _"Data Fiduciary obligations"_ 或 _"Data Principal rights"_
- _"Section 6 consent"_、_"Section 9 children's data"_、_"Section 10 SDF"_
- _"Rule 6 breach notification"_、_"Rule 13 SDF obligations"_、_"Rule 16 DPA terms"_
- _"Data Protection Board complaint"_、_"DPDP Rules 2025"_
- _"verifiable parental consent India"_、_"DPDPA vs GDPR"_
- _"India privacy law"_、_"MeitY data protection"_、_"cross-border transfer India"_

### 示例提示

```
Perform a DPDPA gap analysis for our B2C e-commerce platform with 2 million Indian users.
We currently rely on GDPR consent mechanisms. Produce a gap table covering all Data Fiduciary
obligations under Chapter II.
```

```
Draft a standalone data collection notice for our mobile app under Section 5 and Rule 3.
We collect: name, email, phone number, location, and purchase history. We share data with
payment processors and logistics partners. Include all mandatory Rule 3 elements.
```

```
We've had a security incident. 50,000 customer records including payment data were exposed.
Walk me through our obligations under Section 8(6) and Rule 6, including the 72-hour
Board notification timeline and Data Principal notification requirements.
```

```
Compare the DPDPA and GDPR across the following dimensions: lawful bases, data subject/principal
rights, cross-border transfer mechanisms, enforcement body powers, and penalty levels.
Produce a side-by-side table for our global privacy team.
```

```
We run an educational platform for children under 18 in India. Review our current practices
against Section 9 and Rules 10 and 12. We use session analytics, recommend content, and
serve advertisements. Identify all compliance gaps.
```

---

## 5. 技能实现细节

### 架构

```
dpdpa/
├── SKILL.md                          # Core skill — DPDPA expertise, response formats,
│                                     #   all Chapter II-VIII obligations, penalty schedule
└── references/
    ├── sections-reference.md         # All 44 sections of the Act with obligation summaries
    ├── rights-and-obligations.md     # Deep-dive: Data Fiduciary obligations, Data Principal
    │                                 #   rights, children's data, breach notification, Rule 16
    ├── rules-2025.md                 # DPDP Rules 2025 rule-by-rule guide (Rules 1–23)
    │                                 #   with operational requirements
    └── gdpr-comparison.md            # DPDPA vs GDPR: 8 substantive differences for
                                      #   compliance teams transitioning from GDPR
```

### SKILL.md 中包含什么

- **身份与范围**：覆盖该法（2023 年）和规则（2025 年）的印度 DPDPA 合规顾问专家角色
- **基础规则**：规范每份回答的 7 条规则——仅数字范围、仅两种合法基础、DPDPA 术语、条款/规则引用、该法与规则的区别、阶段感知指引、未通知事项标记
- **响应格式表**：每种任务类型的输出格式（差距分析、通知起草、权利处理、违规通知、GDPR 对比等）
- **DPDPA 概览**：关键日期、执法机构、逐章结构
- **第二章深入**：第 4-10 条——所有数据受托人义务及具体要求
- **第三章**：第 11-15 条——数据主体权利和义务
- **第四章**：第 16-17 条——跨境转移和豁免
- **第五章**：委员会权力、限制和投诉流程
- **处罚表**：第 33 条和附表——所有违规类别的处罚金额
- **差距分析模板**：三个差距表（所有数据受托人、儿童数据、SDF）
- **参考文件指引**：何时以及加载哪些参考文件

### 参考文件中包含什么

| 文件                        | 内容                                                                                                                                                                                                                                                                        |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sections-reference.md`     | 全部 44 个条款，附义务摘要、适用性说明和对规则的交叉引用                                                                                                                                                                     |
| `rights-and-obligations.md` | 数据受托人义务（第 4-10 条）、数据主体权利（第 11-15 条）、儿童数据（第 9 条/规则 10、12）、违规通知程序（第 8(6) 条/规则 6）和数据处理协议强制条款（规则 16）的扩展论述                             |
| `rules-2025.md`             | 全部 23 条 DPDP 规则 2025 的逐条指南：规则 3 通知要求、规则 6 违规通知、规则 7 安全保障、规则 10 年龄验证、规则 12 家长同意方法、规则 13 SDF 义务、规则 16 处理者合同、规则 17 申诉机制 |
| `gdpr-comparison.md`        | DPDPA 与 GDPR 的八个实质差异：合法基础、同意标准、跨境转移机制、执法机构模式、处罚结构、儿童数据方法、数据主体/主体义务、属地范围                                             |

### 用于构建技能的输入

| 来源                                                              | 描述                                                       |
| ------------------------------------------------------------------- | ----------------------------------------------------------------- |
| 《2023 年数字个人数据保护法》                          | 全文——跨 8 章的全部 44 个条款                     |
| 《2025 年数字个人数据保护规则》                        | MeitY 于 2025 年 11 月 13 日通知的全部 23 条规则                   |
| 电子与信息技术部（MeitY）指引 | 官方通知和监管背景                         |
| GDPR（EU）2016/679                                                  | 用于比较分析和过渡指引                  |
| 印度数据保护委员会框架                            | 委员会结构、投诉流程、处罚确定因素 |

### 技能触发短语

`DPDPA`、`DPDP Act`、`DPDP Rules 2025`、`India data privacy`、`India personal data protection`、
`Data Fiduciary`、`Data Principal`、`Significant Data Fiduciary`、`Data Protection Board of India`、
`Section 6 consent`、`Section 7 legitimate uses`、`Section 9 children's data`、`Section 10 SDF`、
`Section 16 cross-border`、`Rule 6 breach notification`、`Rule 13 SDF obligations`、
`Rule 16 processor contract`、`verifiable parental consent India`、`DPDPA gap analysis`、
`DPDPA vs GDPR`、`India privacy law global company`、`MeitY data protection`、
`13 May 2027 compliance`、`72-hour breach notification India`

---

## 6. 作者

**Hemant Naik**
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)

技能版本：1.6.2 —— 2026 年 7 月
