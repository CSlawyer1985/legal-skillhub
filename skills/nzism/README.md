# NZISM 合规技能

> 面向新西兰政府机构及其供应链的 Claude 技能，用于掌握《新西兰信息安全手册》（NZISM）——从差距分析和系统认证，到控制实施和政策生成。

---

## 1. 本技能做什么？

NZISM 技能将 Claude 变成新西兰信息安全手册（NZISM）专家顾问。它为新西兰政府的信息安全管理全生命周期提供结构化、权威的指引——从初始差距评估，到正式的认证与授权（C&A），再到持续监控。

NZISM 由**政府通信安全局（GCSB）**通过其**国家网络安全中心（NCSC NZ）**发布和维护。它是新西兰政府机构强制性的信息安全框架，涵盖 18 个以上安全领域的控制，并支持从"非保密"到"绝密"的新西兰政府信息分类体系（ISCS）。

输出针对任务定制：结构化差距分析表、分步 C&A 路径、附 NZISM 控制引用的完整政策文件、分类决策指南、控制实施计划和处置要求摘要。

---

## 2. 目标受众

本技能面向**新西兰政府机构、承包商及其供应链**。它对以下人群最有用：

- 监督 NZISM 合规、系统认证或授权的**首席信息安全官（CISO）**和**机构安全经理**
- 进行差距评估、准备 SSP 或维护风险登记册的**合规分析师**
- 寻求特定领域（网络、访问控制、密码学等）控制实施指引的**信息技术团队和系统架构师**
- 必须依合同满足与 NZISM 同等义务的**新西兰政府第三方供应商和承包商**
- 准备或进行认证与授权评估的**内部和外部评估员**
- 在合作前评估供应商安全态势的**采购官员**

---

## 3. 常见用例

| 用例 | 示例提示词 |
|----------|---------------|
| **差距分析** | "对照 NZISM，对我们机构当前对某个受限（Restricted）系统的控制进行差距分析。" |
| **C&A 准备** | "为受限（Restricted）系统的认证与授权，我需要准备哪些文件？" |
| **政策生成** | "编写一份映射到 NZISM 控制的访问控制政策。" |
| **控制指引** | "对于处理机密（In-Confidence）数据的系统，我如何实施 NZISM 审计日志控制？" |
| **分类决策** | "我们有一个处理员工绩效数据和部分内阁相关文件的系统。我们应该分配什么分类级别？" |
| **云风险评估** | "我们想把 Restricted 数据迁移到 AWS 新西兰区域。适用哪些 NZISM 控制和批准？" |
| **供应商义务** | "对于处理 Restricted 政府数据的 SaaS 供应商，我们必须通过合同施加哪些安全义务？" |
| **密码学指引** | "对于机密（Confidential）系统上的静态数据，NZISM 要求什么加密标准？" |
| **事件报告** | "我们发生了涉及 Restricted 政府记录的数据泄露。我们的 NZISM 报告义务是什么？" |
| **检查清单** | "给我 NZISM 中的强制性机构义务检查清单。" |

---

## 4. 如何使用本技能

技能在 Claude 中安装后，只要您询问 NZISM、新西兰政府信息安全、GCSB/NCSC NZ 合规或相关主题，它就会自动激活。您无需按名称引用该技能。

### 获得最佳效果的提示

**说明分类级别** —— NZISM 控制在"非保密"、"受限"和"机密"之间差异显著。告诉 Claude 您在处理哪个级别会产生更有针对性的指引。例如：

> "我们正在为一家新西兰政府机构构建一个新的 Restricted 系统。我们需要哪些控制？"

**描述您的系统背景** —— 机构类型、系统用途、托管环境（本地、新西兰云、境外）和用户数量都有助于技能定制其输出。

**点明控制领域** —— 对于实施指引，指明领域（例如，"审计与日志"、"网络安全"、"密码学"）会产生更可操作的回应。

**对工作流具体化** —— 本技能可以帮助进行差距分析、政策编写、C&A 准备、供应商评估和分类决策。告诉它您需要哪个工作流有助于聚焦输出。

---

## 5. 技能实施详情

```
NZISM - Claude Skill/
├── nzism.skill                  ← 在 Claude 中安装此文件
└── NZISM-README.md              ← 本文件

plugins/nzism/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── nzism/
│       ├── SKILL.md             ← 核心技能说明
│       └── references/
│           ├── control-groups.md         ← 全部 18 个 NZISM 控制部分
│           └── classification-framework.md ← 分类级别与控制适用性
└── nzism.skill
```

**框架：** 《新西兰信息安全手册》（NZISM），由 GCSB/NCSC NZ 发布

**涵盖的关键主题：**
- 新西兰政府信息分类体系（ISCS）——从"非保密"到"绝密"
- 全部 18 个以上 NZISM 控制部分（治理、物理、人事、网络、访问控制、密码学、审计、云、移动等）
- 认证与授权（C&A）流程——SSP、风险评估、ATO
- 强制性机构义务和文件
- 第三方与供应链安全义务
- 云计算指引和数据驻留要求
- 相关新西兰立法：《2020 年隐私法》、《2005 年公共记录法》、保护性安全要求（PSR）

**触发短语：** NZISM、NZ government security、GCSB compliance、NCSC NZ、Restricted system、Confidential system、NZ classification、agency security policy、system certification、IRAP NZ、C&A NZ、government cybersecurity NZ

---

## 6. 作者

**Hemant Naik**
电子邮件：hemant.naik@gmail.com
GitHub：[Sushegaad/Claude-Skills-Governance-Risk-and-Compliance](https://github.com/Sushegaad/Claude-Skills-Governance-Risk-and-Compliance)
网站：[sushegaad.github.io/Claude-Skills-Governance-Risk-and-Compliance](https://sushegaad.github.io/Claude-Skills-Governance-Risk-and-Compliance/)
许可证：MIT
