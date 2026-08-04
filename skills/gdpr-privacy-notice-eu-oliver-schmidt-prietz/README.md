# 欧盟隐私通知——部署指南

> 📄 **[查看交互式技能页面 →](https://oliverschmidtprietz.github.io/GDPR-Privacy-Notice-EU/)**

## 概述

泛欧盟 GDPR 隐私通知生成器——为 Claude 设计的综合起草技能，生成知悉法域、符合 GDPR 的专业 .docx 隐私通知：

- **五种通知类型**：网站/应用程序、求职者、员工、商业伙伴（B2B）、B2C 客户
- **多法域覆盖**：德国（DSGVO+BDSG+TDDDG）、法国（RGPD+LIL+LCEN）、奥地利、意大利、西班牙、荷兰、比利时、爱尔兰、英国 GDPR
- **多语言支持**：德语、法语、英语——含双语和泛欧盟选项
- **AI 法案透明度集成**：AI 法案第 50 条披露要求
- **类型驱动式信息采集**：针对每种通知类型定制的数据类别、法律依据和保留期限默认值
- **第 13/14 条合规验证**：交付前的结构化检查清单
- **Cookie 与追踪部分**：含 CMP 集成指引
- **第 21 条异议框**：按 GDPR 要求视觉突出、单独呈现
- **DPIA 指示器筛查**：标记可能需要进行第 35 条评估的情形
- **审计就绪的 .docx 输出**，采用专业排版

## 文件结构

```
privacy-notice-eu/
├── SKILL.md                              # Main skill instructions (deploy this)
└── references/
    ├── templates.md                      # Document template: structure, formatting, translations
    ├── EU_COMMON.md                      # Pan-EU GDPR requirements (Art. 13/14 checklist, legal bases)
    ├── DE.md                             # Germany-specific requirements (BDSG, TDDDG, DSK guidance)
    ├── FR.md                             # France-specific requirements (CNIL recommendations, LIL, LCEN)
    ├── OTHER_EU.md                       # AT, IT, ES, NL, BE, IE, UK GDPR specifics
    └── NOTICE_TYPES.md                   # Type profiles: section maps, data categories, intake questions
```

## 部署

### Claude.ai（用户技能）

1. 进入 **Settings → Profile → Custom Skills**（或等效位置）
2. 上传整个 `privacy-notice-eu/` 文件夹结构
3. 当你提及隐私通知、Datenschutzerklaerung、politique de confidentialite、第 13/14 条或相关话题时，技能将自动触发

### Claude Code / 自定义 MCP 设置

1. 将 `privacy-notice-eu/` 文件夹复制到你的技能目录：
   ```bash
   cp -r privacy-notice-eu/ /path/to/your/skills/user/privacy-notice-eu/
   ```
2. 确保技能已在你的配置中注册

## 使用

### 快速开始

只需告诉 Claude 你需要什么：

> "I need a privacy notice for our SaaS platform. We're a German GmbH based in Berlin,
> targeting customers in Germany and France. We use Google Analytics, Stripe for payments,
> and OpenAI for an AI chatbot feature."（我需要为我们 SaaS 平台制作一份隐私通知。我们是一家位于柏林、面向德国和法国客户的德国 GmbH 公司。我们使用 Google Analytics、用 Stripe 收款，并用 OpenAI 提供 AI 聊天机器人功能。）

技能将激活并引导你完成信息采集流程。

### 触发短语

- "Create a privacy notice"（创建隐私通知）/ "Datenschutzerklaerung erstellen" / "politique de confidentialite"
- "Privacy policy for our website"（我们网站的隐私政策）/ "Art. 13 GDPR"
- "Bewerber-Datenschutz" / "applicant privacy notice"（求职者隐私通知）
- "Employee data protection notice"（员工数据保护通知）/ "Beschaeftigten-Datenschutz"

### 工作流

| 步骤 | 说明 |
|------|-------------|
| **1. 范围** | 通知类型、法域、语言、模板选择 |
| **2. 信息采集** | 类型驱动式收集：控制者信息、数据清单、法律依据、处理者、Cookie、AI |
| **3. 起草** | 从模板 + 类型画像 + 收集的信息生成通知 |
| **4. 验证** | 第 13/14 条合规检查 + 类型特定检查 + AI 法案检查 |
| **5. 交付** | 专业的 .docx 输出，附生成后检查清单 |

### 通知类型

| 类型 | 典型用例 |
|------|------------------|
| **网站 / 应用程序** | 访客、用户、订阅者——含子类型（宣传页、电子商务、SaaS、移动端、市场平台、AI 平台） |
| **求职者** | 求职申请人和候选人 |
| **员工** | 员工、承包商、实习生 |
| **B2B 伙伴** | 供应商、服务商、客户的联系人 |
| **B2C 客户** | 购买/服务关系中的终端消费者 |
| **组合** | 一份或相互关联的多份通知面向多种受众 |

## 监管依据

| 文件 | 引用 |
|----------|-----------|
| GDPR 第 13 条和第 14 条 | 对数据主体的告知义务 |
| GDPR 第 21(4) 条 | 异议权的突出呈现 |
| GDPR 第 22 条 | 自动化决策透明度 |
| 欧盟 AI 法案第 50 条 | AI 透明度义务 |
| BDSG（德国） | 第 26 条员工数据、DPO 阈值 |
| CNIL 建议（法国） | 2020 年隐私通知指引 |
| TDDDG（德国） | 电信媒体/Cookie 要求 |

## 版本历史

见 [CHANGELOG.md](CHANGELOG.md)。

## 许可与免责声明

本技能基于公开可获取的 GDPR 监管材料提供起草指引。不构成法律意见。所有隐私通知在发布前均应由合格的数据保护法律顾问和贵组织的数据保护官（DPO）审查。

> **质量保证：** 本技能随附 `evals/` 文件夹中的评估测试，我会运行这些测试，将输出与预期结果核对。

---

*由 Oliver Schmidt-Prietz 创建——[OneZero Legal](https://onezero.legal)*
