# 欧盟 AI 法案角色认定——部署指南

> 📄 **[查看交互式技能页面 →](https://oliverschmidtprietz.github.io/EU-AI-Act-Suite/ai-act-roles/)**

版本历史见 [CHANGELOG.md](CHANGELOG.md)。

## 概述

欧盟 AI 法案角色认定——确定组织在 AI 价值链中的角色并评估准提供者（quasi-provider）风险：

- **主要角色认定**——提供者、部署者、进口商、分销商
- **准提供者风险评估（第 25 条）**——实质性修改、品牌重塑、预期用途变更、高风险重新利用
- 主要角色和准提供者触发的**可视化决策树**
- **微调评估**——何时对 GPAI 模型进行微调会触发准提供者义务？
- 依第 3 条第 23 款和委员会指引的**实质性修改分析**
- **价值链义务映射**——哪些义务附着于哪些角色
- 面向 HR/劳动力 AI 部署的**劳动法叠加**
- 行业特定角色细微之处的**行业指引交叉引用**
- 附法律依据和后续行动的**角色认定仪表盘**输出

## 文件结构

```
ai-act-roles/
├── SKILL.md                              # 主要技能说明（部署此文件）
├── CHANGELOG.md                          # 版本历史
├── evals/
│   └── evals.json                        # 测试用例
└── references/
    ├── role-definitions.md               # 提供者、部署者、进口商、分销商——第 3 条定义
    ├── substantial-modification.md       # 第 3 条第 23 款实质性修改分析
    ├── quasi-provider-scenarios.md       # 第 25 条触发场景
    ├── finetuning-assessment.md          # 微调何时构成实质性修改
    ├── value-chain-obligations.md        # 各角色的义务图
    ├── compliance-deadlines.md           # 各角色的期限锚点
    ├── employment-law-overlay.md         # HR/劳动力特定叠加
    ├── sector-guidance-crossref.md       # 行业特定角色考量
    └── case-studies.md                   # 已完成的角色认定示例
```

## 部署

### Claude.ai（用户技能）

1. 进入**设置 → 个人资料 → 自定义技能**（或等效入口）
2. 上传整个 `ai-act-roles/` 文件夹结构
3. 技能将在出现"AI Act role"、"provider vs deployer"、"quasi-provider"、"Art. 25"、"substantial modification"或"Anbieter / Betreiber"时自动触发

### Claude Code / 自定义 MCP 设置

1. 将 `ai-act-roles/` 文件夹复制到您的技能目录：
   ```bash
   cp -r ai-act-roles/ /path/to/your/skills/user/ai-act-roles/
   ```
2. 确保技能已在您的配置中注册

## 用法

### 快速入门

描述您的组织如何使用该 AI：

> "我们是一家德国银行。我们从美国供应商处许可了一个现成的信用评分模型，
> 用我们自己的数据对其微调，并将输出重新包装给我们的客户。
> 我们是提供者、部署者，还是准提供者？"

技能将逐步走主要角色和准提供者决策树。

### 触发短语

- "Determine AI Act role" / "Provider or deployer?" / "Are we the deployer?"
- "Quasi-provider" / "Art. 25" / "Substantial modification" / "Wesentliche Veränderung"
- "Value chain responsibilities" / "Anbieter" / "Betreiber"
- "Does fine-tuning make us the provider?"

### 工作流

| 阶段 | 描述 |
|-------|-------------|
| **阶段 1：背景收集** | 自适应受理——组织如何使用该 AI、系统的来源/出处 |
| **阶段 2：主要角色认定** | 可视化决策树——提供者 / 部署者 / 进口商 / 分销商 |
| **阶段 3：准提供者风险评估（第 25 条）** | 触发评估树——实质性修改、品牌重塑、用途变更、高风险重新利用 |
| **阶段 4：角色认定仪表盘** | 输出：主要角色 + 准提供者结论 + 法律依据 + 义务预览 |

## 能力摘要

| 功能 | 描述 |
|---------|-------------|
| 主要角色认定 | 提供者、部署者、进口商、分销商——可视化决策树 |
| 准提供者评估 | 第 25 条触发树（实质性修改、品牌重塑、用途变更、高风险重新利用） |
| 微调分析 | 对 GPAI 模型微调何时构成实质性修改 |
| 实质性修改 | 附委员会指引的第 3 条第 23 款分析 |
| 价值链映射 | 各角色的义务，输入义务映射 |
| 劳动法叠加 | HR/劳动力特定角色考量 |
| 行业交叉引用 | 行业特定角色细微之处 |
| 角色仪表盘 | 附结论 + 法律依据 + 下一步的单页输出 |

## 监管依据

| 文件 | 引用 |
|----------|-----------|
| 欧盟 AI 法案 | 《欧盟条例 (EU) 2024/1689》 |
| 第 3 条 | 定义——提供者、部署者、进口商、分销商 |
| 第 3 条第 23 款 | 实质性修改定义 |
| 第 25 条 | AI 价值链上的责任（准提供者） |
| 委员会价值链指引 | 准提供者触发解释 |
| 第 16、26 条 | 各主要角色的义务 |

## 许可证与免责声明

本技能基于《欧盟条例 (EU) 2024/1689》和委员会价值链指引提供结构化的 AI 法案角色认定指引。它不是法律意见。最终角色认定应涉及具备 AI 法案专业知识的合格法律顾问。

依 AGPL-3.0 许可。

> **质量保证：** 本技能随附 `evals/` 文件夹中的评估测试，我会运行这些测试以检查其输出是否与预期结果一致。

---

*由 Oliver Schmidt-Prietz 创建——[OneZero Legal](https://onezero.legal)*
