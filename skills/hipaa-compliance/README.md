# HIPAA 合规技能

一个全面的 Claude 技能，在四个领域提供专业的 HIPAA 合规指导：文档审查、政策生成、技术保障措施和通俗语言教育。

> ⚠️ **免责声明：** 本技能仅提供资讯性指导，不构成法律意见。正式合规认定请咨询合格的 HIPAA 律师或合规官。

---

## 本技能的功能

HIPAA 合规技能将 Claude 转变为一位知识渊博的 HIPAA 顾问，能够处理医疗和医疗相关组织中出现的各种合规问题。

在高层面上，技能做四件事：

1. **审查内容和文档中的 HIPAA 合规问题** — 它分析政策、系统架构、工作流和供应商协议，产出带规则引用、风险级别（高 / 中 / 低）和优先整改步骤的结构化发现。
2. **生成 HIPAA 合规的政策、通知和模板** — 它产出可直接使用的文档，包括隐私实践通知（NPP）、业务伙伴协议（BAA）、授权书、违约响应计划、风险评估模板和员工培训确认书 — 全部带行内 CFR 引用。
3. **就软件系统的技术保障措施提供建议** — 它指导开发者和架构师了解 HIPAA 的行政、物理和技术保障要求，并提供针对现代云环境（AWS、Azure、GCP）、API 安全、加密标准、审计日志和 DevOps 实践的具体指导。
4. **用通俗语言解释 HIPAA 规则** — 它将密集的监管文本转化为适合任何受众的易懂解释，始终先给出通俗语言摘要，再深入监管细节。

技能由四份详细参考文件支撑，覆盖隐私规则、安全规则、违约通知规则和完整的文档模板库 — 根据问题实际需要选择性加载。

---

## 目标受众

本技能设计用于服务在工作中接触受保护健康信息（PHI）的各类用户：

| 受众 | 他们如何使用本技能 |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **软件开发者** | 为处理 ePHI 的系统获取关于加密标准、访问控制、审计日志、云配置和 FHIR/API 安全的可操作指导 |
| **医疗合规官** | 审查政策和程序的差距、生成必需文档（NPP、BAA、风险评估），并获得带 CFR 引用的合规问题解答 |
| **法律与隐私团队** | 理解新供应商关系中的 HIPAA 义务、起草或审查 BAA、评估违约通知义务 |
| **普通业务员工** | 用通俗语言理解 HIPAA 要求什么、什么算 PHI，以及如何妥善处理患者信息 |
| **医疗 IT 与安全团队** | 对照安全规则评估系统、建立风险分析文档、响应安全事件，并评估违约通知义务 |
| **初创公司与数字健康公司** | 理解 HIPAA 是否适用于他们、覆盖实体与业务伙伴身份意味着什么，以及基线合规是什么样子 |

---

## 常见用例

### 合规审查

- "Review our patient intake form for HIPAA compliance"
- "Is our current EHR data-sharing workflow HIPAA compliant?"
- "Audit our AWS architecture — we store ePHI in S3 and RDS"
- "We're onboarding a new billing vendor. What HIPAA obligations apply?"
- "Review this draft BAA — are there any missing required provisions?"

### 文档与政策生成

- "Generate a Notice of Privacy Practices for our clinic"
- "Draft a Business Associate Agreement for our cloud storage vendor"
- "Create an internal HIPAA Privacy Policy for our workforce"
- "Write a HIPAA Authorization Form for releasing records to a third party"
- "Generate a Security Incident Report template for our team"
- "Create a HIPAA compliance checklist for our annual review"

### 技术保障措施

- "What encryption is required for a mobile app that stores patient data?"
- "What audit logs do we need to maintain for HIPAA, and for how long?"
- "We use Google Cloud — do we need a BAA? What services are HIPAA-eligible?"
- "What does HIPAA require for user authentication in our patient portal?"
- "We're building a FHIR API — what security controls do we need?"
- "Can we use real patient data in our dev/test environment?"

### 教育与解释

- "What is the difference between a Covered Entity and a Business Associate?"
- "What are the 18 HIPAA identifiers?"
- "What does 'minimum necessary' mean in practice?"
- "When is a security incident a reportable breach vs. not?"
- "What are the penalties for a HIPAA violation?"
- "Does HIPAA apply to my employer wellness app?"

### 违约响应

- "We had a laptop stolen — do we need to report this?"
- "An employee emailed PHI to the wrong patient. Is this a breach?"
- "Walk me through the 4-factor breach risk assessment"
- "What are our notification deadlines if we confirm a breach?"
- "Draft a breach notification letter for affected individuals"

---

## 如何使用本技能

### 安装

下载 `hipaa-compliance.skill` 并安装到 Claude 的技能设置中。安装后，当您的对话涉及 HIPAA 相关主题时，技能会自动激活。

### 触发技能

技能设计为在广泛的医疗和合规相关语言上触发。您不需要特殊语法 — 只需自然描述您的需求。触发短语包括：

- 直接提及：_HIPAA、PHI、ePHI、covered entity（覆盖实体）、business associate（业务伙伴）、BAA_
- 文档请求：_"draft a privacy notice," "generate a BAA," "create a risk assessment"_
- 合规问题：_"is this HIPAA compliant?", "what does HIPAA require for...?"_
- 系统审查：_"review our architecture," "audit our data handling"_
- 违约情景：_"we had a data incident," "employee accessed the wrong records"_

### 示例提示词

```
# 文档审查
"Here is our current data sharing agreement with our billing vendor.
Please review it for HIPAA compliance and flag any missing provisions."

# 模板生成
"Generate a Notice of Privacy Practices for Valley Medical Group,
a multi-specialty outpatient clinic in California. Effective date: January 1, 2025."

# 技术指导
"We're building a telehealth platform on AWS. What HIPAA technical safeguards
do we need to implement? We're using EC2, RDS (PostgreSQL), S3, and SES."

# 违约评估
"An employee sent a spreadsheet containing names, DOBs, and diagnoses for
47 patients to the wrong email address. The recipient responded saying
they didn't open it. Walk me through whether we have a reportable breach."

# 教育
"Explain the minimum necessary standard and give me three concrete
examples of how it applies in a hospital setting."
```

### 输出格式

根据请求类型，输出遵循结构化格式：

- **合规审查** → 发现表（问题 / CFR 引用 / 风险级别 / 建议）+ 优先行动事项
- **模板** → 带 `[PLACEHOLDER]` 字段和行内 CFR 引用的完整文档
- **技术评估** → 按行政 / 物理 / 技术组织的保障措施检查清单
- **教育** → 通俗语言摘要，后附监管细节和示例

---

## 技能实现细节

### 架构

```
hipaa-compliance/
├── SKILL.md                          # 核心技能 — 工作流、提示词、快速参考表
└── references/
    ├── privacy-rule.md               # 45 CFR Part 164, Subparts A & E — 完整隐私规则
    ├── security-rule.md              # 45 CFR Part 164, Subpart C — 完整安全规则
    ├── breach-notification.md        # 45 CFR Part 164, Subpart D — 违约通知规则
    └── templates.md                  # 9 份可直接使用的 HIPAA 文档模板
```

技能使用**渐进披露** — Claude 只加载与具体问题相关的参考文件，保持上下文高效，同时确保需要时覆盖全面。

### 参考文件覆盖

| 文件 | 关键内容 |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `privacy-rule.md` | 患者权利（访问、修订、会计、限制）、NPP 要求、最低必要标准、授权规则、允许的披露（TPO + §164.512）、特殊 PHI 类别、18 个标识符、去标识化方法、营销/筹款规则 |
| `security-rule.md` | 全部 54 项安全规则实施规范及必需/可寻址指定、风险分析方法论（与 NIST SP 800-30 对齐）、云架构指导（AWS/Azure/GCP）、移动/BYOD、DevOps/CI-CD、完整实施检查清单 |
| `breach-notification.md` | 4 因素违约风险评估、通知时间线和方式、HHS 报告门户指导、BA 通知链、民事和刑事处罚层级、违约响应工作流、常见情景表 |
| `templates.md` | NPP、BAA、HIPAA 隐私政策、授权书、员工培训确认书、安全事件报告、违约风险评估、风险分析模板、HIPAA 合规检查清单 |

### 构建本技能所用的输入

技能基于设计期间提供的以下要求构建：

| 输入 | 取值 |
| ---------------------- | ---------------------------------------------------------------------------------------------------- |
| **核心能力** | 合规审查、政策/模板生成、技术保障措施建议、通俗语言教育 |
| **目标受众** | 开发者、合规官、法律团队、普通业务员工（上述全部） |
| **参考深度** | 详细 — 完整覆盖隐私规则、安全规则和违约通知规则 |
| **监管依据** | 45 CFR Parts 160 和 164（HIPAA），经 HITECH（2009）修订 |
| **技术范围** | 云环境（AWS/Azure/GCP）、现代应用架构、FHIR API、移动/BYOD、DevOps |
| **文档模板** | 覆盖最常用 HIPAA 合规文档的 9 份模板 |
| **技能格式** | Claude Skill（`.skill` 文件），含 `SKILL.md` + 4 份随附参考文件 |

### 设计决策

**受众感知的语气：** 技能被明确指示根据提问者调整深度和语言 — 开发者获得技术细节和代码级指导、合规官获得 CFR 引用、普通员工获得通俗语言解释。

**风险分层：** 所有合规发现按高 / 中 / 低风险分类，帮助用户确定整改工作的优先级。

**法律免责声明：** 每份合规产出都包含免责声明，说明这是资讯性指导而非法律意见，确保用户理解本工具的适当角色。

**州法标记：** 技能设计为在州法可能施加比 HIPAA 更严格要求时予以注明（尤其是心理健康、HIV/艾滋病和生殖健康信息）。

**加密指导：** 技能正确地将加密表述为 HIPAA 下的"可寻址"（addressable），同时传达 AES-256 / TLS 1.2+ 是行业标准 — 这是通用合规工具经常弄错的重要细微差别。

---

## 作者

**Hemant Naik**
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)

_技能使用 Claude Skill 框架创建。参考内容基于 45 CFR Parts 160 和 164 以及截至构建日期现行的 HHS 指南。请始终对照最新的 HHS 出版物核验，并咨询法律顾问以完成正式合规认定。_
