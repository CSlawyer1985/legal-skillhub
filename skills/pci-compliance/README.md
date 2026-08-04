# PCI DSS 合规技能

> 一个面向安全、合规和工程团队的 Claude 技能，用于驾驭 PCI DSS v4.0.1 — 从 CDE 范围界定和 SAQ 选择，到差距评估、QSA 审计准备和整改规划。

---

## 1. 本技能的功能

PCI DSS 技能将 Claude 变成一位专业的 PCI DSS 合规顾问和经 QSA 训练的咨询师。它在完整的 PCI DSS 合规生命周期中提供结构化、可操作的指导 — 从定义持卡人数据环境（CDE）范围和选择正确的 SAQ 类型，到对照全部 12 项要求的差距评估、整改规划和 QSA 审计准备。

技能覆盖 **PCI DSS v4.0.1**（2024 年 6 月 — 现行版本），包括所有于 2025 年 3 月 31 日成为强制要求的新要求 — 扩展的 MFA、支付页面脚本完整性控制、钓鱼防护、自动化日志审查和针对性风险分析。它还支持从已退役的 **PCI DSS v3.2.1** 迁移的团队。

产出按任务定制：CDE 范围界定叙述、带证据要求的结构化差距评估表、带理由的 SAQ 选择决定、带 QSA 证据提示的控制层面实施指导，以及带 PCI DSS 控制引用的完整政策文档。

---

## 2. 目标受众

- **CISO 和安全经理**，为商户或服务提供商监督 PCI DSS 合规计划
- **合规分析师和 GRC 团队**，执行差距评估、维护 SAQ 文档或为年度 QSA 审计做准备
- **软件开发者与工程师**，构建接触持卡人数据的支付系统、电子商务应用或集成
- **架构师**，设计或审查与 CDE 交互的系统 — 网络分段、令牌化、P2PE、云环境
- **中小型商户**（2–4 级），完成年度 SAQ 并希望获得关于需要哪些控制及原因的专家指导
- **服务提供商**，管理其 PCI DSS 1 级或 2 级义务以及 TPSP 尽职调查

---

## 3. 常见用例

| 用例 | 示例提示词 |
|----------|---------------|
| **CDE 范围界定** | "Help me scope our CDE. We have a cloud-based e-commerce platform that uses Stripe for payments. What's in scope?" |
| **SAQ 选择** | "We're a Level 3 merchant accepting e-commerce payments only. We redirect customers to PayPal's hosted checkout. Which SAQ do we need?" |
| **差距评估** | "Run a PCI DSS v4.0.1 gap assessment. We're an SAQ D merchant. Here's our current environment..." |
| **v4.0 新要求** | "What are the new requirements in PCI DSS v4.0 that became mandatory in March 2025?" |
| **MFA 指导** | "What does Req 8.4.2 mean for our internal staff accessing CDE systems?" |
| **支付页面脚本** | "How do we comply with Req 6.4.3 and 11.6.1 for our e-commerce payment page?" |
| **政策生成** | "Write an Incident Response Plan aligned to PCI DSS Req 12.10." |
| **整改路线图** | "We have 12 non-compliant controls from our last assessment. Help me build a remediation roadmap." |
| **TPSP 管理** | "What does PCI DSS require for managing third-party service providers?" |
| **密钥管理** | "How do we implement PCI DSS Req 3.7 for encryption key management?" |

---

## 4. 如何使用本技能

技能在 Claude 中安装后，每当您询问 PCI DSS、支付卡安全、CDE、SAQ、ROC、QSA 评估、持卡人数据或相关主题时，它会自动激活。您无需按名称引用技能。

### 获得最佳结果的提示

**指明您的商户或服务提供商级别** — 这决定您的验证要求（SAQ vs ROC）并定制指导。例如：

> "We're a Level 2 merchant with 2 million transactions per year. We use a hosted payment page (redirect). What SAQ applies and what do we need to demonstrate?"

**描述您的支付环境** — 渠道（卡在场、电子商务、MOTO）、使用的第三方处理商、您是否存储任何持卡人数据，以及哪些系统在范围内。

**引用具体要求** — 如需针对性指导，引用要求编号（如 `Req 8.4.2`、`Req 6.4.3`）以获得更聚焦、可操作的回复。

### 示例交互

```
You:     We're a Level 3 e-commerce merchant. We use a JavaScript payment widget from
         Stripe embedded in our checkout page. Do we qualify for SAQ A?

Claude:  No — because you control the checkout page that hosts the Stripe widget and
         your JavaScript can affect how the widget behaves, you do not meet SAQ A
         criteria. You are likely SAQ A-EP. Key requirements include:
         - Req 6.4.3: Inventory all scripts on your payment page; implement
           Content Security Policy (CSP) or Sub-Resource Integrity (SRI)
         - Req 11.6.1: Deploy tamper detection for HTTP headers and payment page content
         - Req 11.3: Quarterly ASV scans
         Here is the full SAQ A-EP control scope and what you need to implement...
```

---

## 5. 技能实现细节

### 架构

```
pci-compliance/
├── SKILL.md                           # 核心技能逻辑和工作流
└── references/
    ├── pci-dss-requirements.md        # 全部 12 项要求及子控制与证据
    ├── pci-dss-saq-guide.md           # SAQ 选择指南、所有 SAQ 类型、ROC/AOC/ASV
    └── pci-dss-v4-changes.md          # v3.2.1 → v4.0/v4.0.1 迁移指南和变更日志
```

### SKILL.md 中包含的内容

- **人设**：Claude 扮演 PCI DSS 合规顾问和经 QSA 训练的咨询师
- **输出格式矩阵**：将每种任务类型映射到特定输出格式
- **CDE 核心概念**：PAN、SAD、账户数据类型、范围缩减策略（令牌化、P2PE、分段）
- **商户和服务提供商级别**：每个级别的验证要求
- **定义式方法与定制式方法**：各自何时适用以及要求什么
- **SAQ 快速参考**：全部 8 种 SAQ 类型及约略控制数量
- **5 个核心工作流**：CDE 范围界定、差距评估、SAQ 选择、控制实施、政策生成
- **v4.0 变更表**：与 v3.2.1 的关键区别
- **补偿性控制**：它们如何运作及何时适用

### 参考文件中的内容

| 文件 | 内容 |
|------|----------|
| `pci-dss-requirements.md` | 全部 12 项要求及子控制、QSA 证据要求和常见差距 |
| `pci-dss-saq-guide.md` | SAQ 选择决策树、全部 8 种 SAQ 类型的资格标准、ROC/AOC/ASV/QSA/ISA 参考 |
| `pci-dss-v4-changes.md` | 版本时间线、所有新的 v4.0 要求（未来生效 → 强制）、关键概念变更、迁移检查清单 |

### 构建技能所用的输入

- **PCI DSS v4.0.1**（PCI SSC，2024 年 6 月）— 全部 12 项要求和子要求
- **PCI DSS v4.0**（PCI SSC，2022 年 3 月）— 含未来生效要求和定制式方法
- **PCI DSS v3.2.1 至 v4.0 变更摘要**（PCI SSC）— 变更日志和迁移参考
- **PCI DSS SAQ 文件 v4.0** — 全部 8 种 SAQ 类型及资格标准
- **PCI SSC ROC 模板 v4.0.1** — 评估结构参考
- **PCI SSC 针对性风险分析指南** — TRA 方法论和要求

### 技能触发短语

`PCI DSS` · `PCI compliance` · `payment card` · `cardholder data` · `CDE` · `SAQ` · `ROC` · `AOC` · `QSA` · `ASV scan` · `PAN storage` · `SAD` · `tokenisation` · `P2PE` · `Requirement 1` 至 `Requirement 12` · `v4.0` · `merchant level` · `service provider` · `network segmentation` · `payment page` · `web skimming` · `Magecart` · `TPSP` · `key management` · `PCI scope`

---

## 6. 作者

**技能设计者：** Hemant Naik
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)
**构建工具：** Claude（Anthropic），使用 Claude Skills 框架
**日期：** 2026 年 3 月
**技能版本：** 1.6.2
**标准覆盖：** PCI DSS v4.0.1（2024 年 6 月）和 PCI DSS v4.0（2022 年 3 月）
