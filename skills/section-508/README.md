# 第 508 条（美国联邦信息通信技术无障碍）技能

> **免责声明：** 本技能基于公开可得的第 508 条标准和 WCAG 2.0 文档提供教育与咨询指引。其不构成法律意见。无障碍一致性认定、过度负担认定和采购决策必须由合格法律顾问和无障碍专家参与。第 508 条要求由美国无障碍委员会（US Access Board，36 CFR Part 1194）和总务管理局（GSA）执行。

---

## 1. 本技能做什么

本技能将 Claude 转变为**1973 年《康复法案》第 508 条**（29 U.S.C. § 794d）的专家顾问。该条经 1998 年《劳动力投资法案》修订，并由**修订版第 508 条标准**（36 CFR Part 1194，2018 年 1 月 18 日生效）更新。它帮助联邦机构、联邦承包商和信息通信技术（ICT）供应商在全部信息与通信技术范围内实现并展示无障碍合规。

本技能以 2018 年标准修订为基础，该修订将 **WCAG 2.0 A 级和 AA 级**作为网络内容（E205）、软件（E204）和电子文档的技术标准。它涵盖完整的 ICT 范围——网络内容、软件、电子文档、硬件（自助终端、复印机、电话）、视频和音频、电信、创作工具和支持文档——以及 E202 项下所有适用的例外，包括过度负担、根本性改变、国家安全系统、后台设备和既有 ICT。

本技能不是提供泛泛的无障碍建议，而是将每个请求路由到结构化输出类型：VPAT/ACR 逐节填写、带准则引用的无障碍审计问题表、带修复优先级的差距评估、带 FAR 条款引用的采购 RFP 文本、过度负担文件化程序，以及 PDF 无障碍检查清单。所有输出均引用具体的**第 508 条条款**（如 E205、E302.1）或 **WCAG 2.0 成功准则**（如 SC 1.4.3）——绝不只是原则。

本技能还涵盖辅助技术测试矩阵——JAWS + Chrome、NVDA + Chrome/Firefox、VoiceOver + Safari、TalkBack + Chrome、Dragon NaturallySpeaking——并理解联邦采购周期，包括 FAR 条款 52.239-2 和 OMB 备忘录 M-24-08（2024 年 1 月）。

---

## 2. 目标受众

| 受众 | 如何使用本技能 |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **联邦机构第 508 条协调员** | 差距评估、审计规划、政策起草、采购条款审查、机构报告 |
| **联邦 CIO 与 IT 领导层** | 项目级合规状况审查、过度负担认定、修复路线图优先级排序 |
| **联邦采购/合同官员** | RFP 第 508 条文本、FAR 条款 52.239-2 适用、VPAT 评估指引、供应商评估 |
| **向联邦机构销售的 ICT 供应商和承包商** | 使用 VPAT 2.x WCAG 版填写 VPAT/ACR、修复规划、一致性证据文件化 |
| **开发人员和工程师** | 准则级实施指引、ARIA 模式、HTML 修复、键盘无障碍、自动化测试工具选择 |
| **用户体验（UX）设计师** | 颜色对比要求（SC 1.4.3、1.4.11）、焦点可见性（SC 2.4.7）、错误识别（SC 3.3.1–3.3.4）、表单标签 |
| **内容作者和文档创建者** | PDF 无障碍要求、文档标记、阅读顺序、表单字段标签 |
| **法律与合规团队** | 过度负担文件化程序、替代访问方式要求、法律引用映射（29 U.S.C. § 794d、36 CFR Part 1194） |
| **QA 与无障碍测试人员** | 测试方法、辅助技术 + 浏览器配对、审计文档模板、VPAT 缺陷识别 |

---

## 3. 常见用例

### VPAT 与无障碍一致性报告（ACR）填写

- 帮我为联邦采购完成一份 VPAT 2.x WCAG 版 ACR
- “支持”“部分支持”“不支持”和“不适用”之间有什么区别？
- 审查这份 VPAT——哪些缺陷会导致联邦采购官员拒绝它？
- 我们的供应商提交的是 VPAT 1.x 版——我们应该要求什么替代？
- 我们应在 ACR 中记录什么测试方法？

### 无障碍审计与差距评估

- 对我们的联邦门户网站运行第 508 条差距评估——我们有这些已知问题
- 产出带准则引用、元素引用和修复步骤的审计问题表
- 我们在许多元素上未通过 SC 1.4.3——给我一个分优先级的修复计划
- 识别哪些 WCAG 2.0 AA 成功准则在联邦系统中最常被违反
- 我们正在从遗留系统迁移——如何在启动前评估新系统的 508 合规性？

### 采购与 RFP 文本

- 为新的案件管理系统 RFP 起草第 508 条文本
- FAR 条款 52.239-2 要求什么，何时强制适用？
- 我们应在 ICT 采购合同中包含哪些修复 SLA（关键、高、中等级发现）？
- 在源选择期间如何评估竞争供应商的 VPAT？
- 我们正在续签合同——OMB M-24-08 下适用哪些更新的 508 要求？

### PDF 与电子文档无障碍

- 带我在第 508 条和 SC 1.3.1 下使机构 PDF 无障碍
- 必需的 PDF 标签是什么，如何在 Acrobat Pro 中验证它们？
- 我们的 Word 文档导出为未标记的 PDF——如何修复源文档？
- 如何在 SC 4.1.2 下将表单字段标签关联到无障碍 PDF？

### 过度负担与例外文件化

- 带我在 E202.6 下走一遍过度负担认定程序
- 机构负责人或 CIO 必须签署什么文件以适用过度负担例外？
- 主张过度负担时我们必须提供什么替代访问方式？
- 2018 年 1 月 18 日之前采购的既有 ICT 是否要求 508 合规？
- E202.3 下的国家安全系统例外何时适用？

### 政策与程序制定

- 为我们的联邦机构起草第 508 条无障碍政策
- 撰写涵盖角色、职责、测试方法和汇报的第 508 条项目计划
- 联邦机构的 508 项目应包括哪些角色和职责？
- 起草采购程序，确保 ICT 采购从一开始就包含 508 要求

---

## 4. 如何使用本技能

### 安装

1. 从 `Section 508 - Claude Skill/` 文件夹下载 `section-508.skill` 文件
2. 在 Claude 中，进入 **设置 → 技能**
3. 上传 `.skill` 文件
4. 技能会在相关对话中自动激活——无需特殊命令

### 触发技能

当您的消息涉及联邦语境下的第 508 条、联邦 ICT 无障碍、VPAT 填写或 WCAG 合规时，技能自动触发。激活它的示例短语：

- _"We need to complete a VPAT for our federal agency customer"_
- _"What does Section 508 require for our web application?"_
- _"Our 508 audit found a contrast failure — how do we fix it?"_
- _"Help me write the accessibility section of our RFP"_
- _"What assistive technologies should we test against for federal compliance?"_
- _"Can we claim an undue burden exception for this legacy system?"_
- _"What does OMB M-24-08 change for our 508 program?"_

### 示例提示

```
"Complete a VPAT 2.x WCAG Edition for a web-based document management
system. The product supports JAWS with Chrome, has full keyboard
navigation, but fails SC 1.4.3 on 12% of text elements and has
unlabelled form fields in the advanced search module."
```

```
"Run a Section 508 gap assessment for our federal web portal. Flag all
WCAG 2.0 AA criteria we likely fail based on these audit findings:
missing alt text on charts, no skip navigation, session timeouts with
no warning, and auto-playing video on the homepage."
```

```
"Draft Section 508 procurement language for an RFP for a new HR
information system. Include FAR clause 52.239-2, VPAT requirements,
testing methodology requirements, and remediation SLAs for critical,
high, and medium accessibility findings."
```

```
"Walk me through the complete PDF accessibility checklist for a 50-page
regulatory guidance document that needs to comply with Section 508.
Include tag structure, reading order, form fields, images, and
verification steps in Acrobat Pro."
```

```
"Our agency wants to claim an undue burden exception for a legacy
financial system. Walk me through the determination process: what cost
analysis is required, who must sign the determination, what alternative
means of access we must provide, and how to document it for audit."
```

---

## 5. 技能实现细节

### 架构

```
plugins/section-508/skills/section-508/
├── SKILL.md                        # 主技能：监管框架、谁须合规、
│                                   # ICT 覆盖（E101–E103）、例外（E202）、
│                                   # 全部 WCAG 2.0 POUR 准则表（A 级和 AA 级）、
│                                   # 常用工作流（VPAT、审计、PDF、采购、
│                                   # 过度负担）、响应格式路由
└── references/
    └── wcag-mapping.md             # 第 508 条条款映射；WCAG 2.0 A 级和 AA 级
                                    # 常见失败及测试方法与修复；
                                    # 功能绩效准则（第 3 章）；
                                    # 辅助技术测试矩阵；
                                    # PDF 无障碍检查清单；常见 VPAT
                                    # 缺陷；关键法律引用

Section 508 - Claude Skill/
├── Section-508-README.md           # 本文件
└── section-508.skill               # 独立可安装技能文件
```

### SKILL.md 中的内容

- **YAML frontmatter**，含技能名称、描述和自动触发短语
- **响应格式路由表**——任务类型到输出格式的映射（VPAT/ACR、审计、差距评估、修复计划、采购文本、政策、一般问题）
- **监管框架**——谁须合规、2018 年修订标准的结构（E205/E204 采用 WCAG 2.0 AA、功能绩效、硬件、支持文档）
- **ICT 覆盖**——涵盖的完整 ICT 类型清单（网络、软件、文档、硬件、视频/音频、电信、创作工具、支持文档）
- **例外（E202）**——过度负担、根本性改变、国家安全系统、后台设备、既有 ICT
- **完整 POUR 准则表**——全部 WCAG 2.0 A 级和 AA 级成功准则，含准则代码、级别和要求（可感知、可操作、可理解、稳健）
- **常用工作流**——VPAT 2.x 分步填写、无障碍审计方法、PDF 无障碍要求、采购（FAR 52.239-2）、过度负担文件化程序
- **参考文件指引**——指示 Claude 加载 `references/wcag-mapping.md` 获取深度内容的说明

### 参考文件中的内容

| 文件 | 内容 |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `references/wcag-mapping.md` | 第 508 条条款映射（E205.2/E205.3/E205.4/E204/第 3 章/第 4 章/第 6 章 ↔ WCAG 2.0）；WCAG 2.0 A 级常见失败（1.1.1、1.3.1、2.1.1、1.4.1、4.1.2）及具体失败模式、测试方法和代码级修复；WCAG 2.0 AA 级常见失败（1.4.3、1.4.4、2.4.5、2.4.7、3.3.3、3.3.4）；功能绩效准则（第 3 章，302.1–302.9）；辅助技术测试矩阵（JAWS、NVDA、VoiceOver macOS/iOS、TalkBack、Dragon、键盘、高对比度、浏览器缩放、ZoomText）；PDF 无障碍检查清单及验证方法和 Acrobat Pro 工具；常见采购 VPAT 缺陷；关键法律引用（29 U.S.C. § 794d、36 CFR Part 1194、FAR 39.2、FAR 52.239-2、OMB M-24-08） |

### 用于构建技能的输入

| 来源 | 描述 |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **29 U.S.C. § 794d** | 第 508 条法定授权与范围 |
| **36 CFR Part 1194** | 美国无障碍委员会修订版第 508 条标准（2018 年 1 月 18 日生效）——权威技术标准 |
| **WCAG 2.0（W3C，2008 年 12 月）** | 依 E205 以引用方式并入的全部 38 项 A 级和 AA 级成功准则 |
| **VPAT 2.x WCAG 版** | ITI VPAT 模板结构——表 1–3、功能绩效准则、软件/支持文档章节 |
| **FAR 副部 39.2 和条款 52.239-2** | 联邦采购条例第 508 条采购要求 |
| **OMB 备忘录 M-24-08（2024 年 1 月）** | 更新的联邦机构第 508 条项目管理要求 |
| **Section508.gov 指引** | GSA 测试资源、机构汇报、VPAT 模板、无障碍成熟度模型 |
| **ARIA 创作实践指南（W3C）** | 自定义小部件的键盘模式和 ARIA 要求 |
| **PDF/UA（ISO 14289）** | 电子文档要求引用的 PDF 无障碍标准 |
| **辅助技术兼容性** | JAWS、NVDA、VoiceOver、TalkBack、Dragon NaturallySpeaking 兼容性测试方法 |

### 技能触发短语

`Section 508` · `508 compliance` · `Revised Section 508 Standards` · `36 CFR Part 1194` · `VPAT` · `Accessibility Conformance Report` · `ACR` · `federal ICT accessibility` · `federal accessibility` · `WCAG 2.0 AA federal` · `508 audit` · `508 gap assessment` · `508 remediation` · `PDF accessibility` · `508 procurement` · `FAR 52.239-2` · `OMB M-24-08` · `undue burden` · `fundamental alteration exception` · `legacy ICT exception` · `assistive technology testing` · `JAWS NVDA VoiceOver federal` · `Section 508 testing` · `functional performance criteria` · `508 VPAT completion` · `federal web accessibility`

---

## 6. 作者

**Hemant Naik**
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)
