# ISO 42001 人工智能管理体系

面向 Claude 的 ISO/IEC 42001:2023 人工智能管理体系（AIMS）合规专家顾问。

---

## 本技能做什么

ISO 42001 技能将 Claude 转变为精通 ISO/IEC 42001:2023 的首席审核员和 AIMS 实施顾问。它全面覆盖世界上第一个 AI 管理体系国际标准——从差距评估到认证就绪，深度涵盖 AI 风险评估、AI 系统影响评估（AISIA）、全部 38 项附录 A 控制措施以及 AI 治理政策生成。

**适用对象：**

- AI 提供者（开发、训练或部署 AI 系统的组织）
- AI 使用者（将第三方 AI 整合到其运营中的组织）
- 管理 AI 治理义务的 GRC、合规和法律团队
- 需要了解哪些控制措施适用于其 AI 系统的软件和数据科学团队
- 对标欧盟《人工智能法案》并需要 AIMS 基础的组织
- 需要参考资料源的认证机构和审核员

---

## 能力

### 差距分析

对所有强制条款（4–10）和全部 38 项附录 A 控制措施进行结构化评估。输出带 🔴/🟡/🟢 状态、证据要求和分阶段修复路线图的优先级差距登记册。

### AI 系统影响评估（AISIA）

分步引导强制性的 AISIA 流程——记录 AI 系统、识别受影响人群、评估影响维度（严重性、可逆性、广度、同意、人类监督）、分类影响级别（低/中/高）并确定相应的控制要求。

### AI 风险评估

涵盖所有 AI 风险类别——模型风险（偏见、漂移、幻觉、对抗性攻击）、数据风险（质量、投毒、隐私）、运营风险（范围蔓延、人类过度依赖）和供应链风险（第三方模型、API 依赖）。输出带可能性 × 严重性评分和风险处理决策的风险登记册。

### 适用性声明（SoA）

生成完整的 SoA 表格，涵盖全部 38 项附录 A 控制措施，含适用性决定、理由和实施状态——可供审核员审查。

### 政策生成

起草所有核心 AIMS 政策，含文件控制块、ISO 42001 条款和控制措施引用，并整合负责任 AI 原则：

- AI 政策（条款 5.2）
- AI 风险管理政策
- AI 可接受使用政策
- AI 数据治理政策
- AI 事件管理政策
- AI 系统生命周期政策
- AI 供应商管理政策

### 认证就绪

产出第一阶段（文件审查）和第二阶段（实施验证）审计检查清单，含 RAG 状态、逐条款证据要求及常见审核员关注领域。

### 框架整合

将 ISO 42001 映射至：

- **ISO 27001:2022** ——整合式 ISMS + AIMS
- **NIST AI RMF** ——将 Map/Measure/Manage/Govern 映射至 42001 条款
- **欧盟《人工智能法案》** ——AISIA 对应基本权利影响评估（FRIA）；高风险 AI 系统控制措施
- **ISO 31000** ——AI 风险评估方法对齐

---

## 技能内容

```
ISO-42001.skill
└── skills/iso42001/
    ├── SKILL.md                              # 核心技能——每次触发时加载
    └── references/
        ├── iso42001-controls-annex-a.md      # 全部 38 项控制措施及说明和按角色的适用性
        ├── iso42001-clauses-requirements.md  # 强制条款 4–10 完整详述
        └── iso42001-ai-risk-assessment.md    # AI 风险评估 + AISIA 方法与模板
```

---

## 安装

### Claude.ai（聊天界面）

1. 下载 [`ISO-42001.skill`](https://github.com/Sushegaad/Claude-Skills-Governance-Risk-and-Compliance/raw/main/ISO%2042001%20-%20Claude%20Skill/ISO-42001.skill)
2. 打开 [Claude.ai](https://claude.ai) → **自定义 → 技能**
3. 点击**上传技能**并选择下载的文件
4. 当您的对话涉及 ISO 42001 主题时，技能自动激活

### Claude Code（CLI / 开发者）

```shell
/plugin marketplace add Sushegaad/Claude-Skills-Governance-Risk-and-Compliance
/plugin install iso42001@grc-skills
```

---

## 示例提示

安装技能后，试试以下内容：

**差距评估：**

> "我们是一家 SaaS 公司，通过 API 将 GPT-4 用于客户支持聊天机器人，并使用自定义 ML 模型进行流失预测。运行一次 ISO 42001 差距评估。我们目前没有任何 AIMS 文档。"

**AISIA：**

> "帮我为我们自动化的员工绩效评估系统完成一次 AI 系统影响评估。它使用 ML 推荐评级。影响 2,000 名员工。"

**AI 风险评估：**

> "我们正在为内部法律文件起草部署一个大语言模型，应评估哪些关键 AI 风险？"

**政策生成：**

> "为一家中型金融服务公司起草 AI 可接受使用政策。我们使用第三方 AI 工具，包括 Microsoft Copilot 和一个自定义信用风险模型。"

**SoA：**

> "为全部 38 项 ISO 42001 附录 A 控制措施生成适用性声明。我们是 AI 提供者。将 A.10 退役控制措施标记为尚不适用——我们的 AI 系统均处于早期部署阶段。"

**认证就绪：**

> "我们计划 3 个月后参加 ISO 42001 第二阶段审计。需要什么证据，审核员最可能测试什么？"

**欧盟 AI 法案对齐：**

> "我们正在构建一个使用 AI 筛选简历的招聘工具。我们的 ISO 42001 AISIA 如何帮助满足欧盟 AI 法案的高风险要求？"

---

## 标准覆盖

| 领域 | 覆盖 |
| --------------------- | ---------------------------------------------------------------------------------------------------- |
| 标准 | ISO/IEC 42001:2023（2023 年 12 月 18 日） |
| 强制条款 | 4 至 10（完整覆盖） |
| 附录 A 控制措施 | 9 个领域（A.2–A.10）的全部 38 项控制措施 |
| 角色 | AI 提供者、AI 使用者或两者 |
| AI 风险类别 | 模型、数据、运营、供应链、监管/声誉 |
| AISIA | 完整流程——文档、人群识别、影响维度、分类、控制措施 |
| 影响级别 | 低、中、高（各级别附控制要求） |
| 整合 | ISO 27001、NIST AI RMF、欧盟 AI 法案、ISO 31000 |
| 认证路径 | 第一阶段 + 第二阶段检查清单；监督审计指引 |

---

## 触发短语

当您的对话包含以下内容时，技能自动激活：

`ISO 42001`、`ISO/IEC 42001`、`AI Management System`、`AIMS`、`AI governance standard`、`AISIA`、`AI System Impact Assessment`、`Annex A controls for AI`、`AI risk assessment ISO`、`responsible AI framework`、`AI certification`、`AI policy ISO`、`Statement of Applicability AI`、`AI lifecycle controls`、`AI supplier management ISO`、`EU AI Act management system`、`NIST AI RMF ISO mapping`、`AI incident management ISO`、`AI transparency standard`、`AI bias controls`

---

## 关于

**作者：** Hemant Naik
**仓库：** [Sushegaad/Claude-Skills-Governance-Risk-and-Compliance](https://github.com/Sushegaad/Claude-Skills-Governance-Risk-and-Compliance)
**许可证：** MIT
**覆盖的标准版本：** ISO/IEC 42001:2023

> 本技能基于公开可得的 ISO 42001 文档和专家解读提供合规指引。其不替代专业的法律、审计或咨询建议。寻求 ISO 42001 认证的组织应聘请经认可的认证机构。
