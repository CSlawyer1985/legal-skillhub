# 欧盟 AI 法案快速评估——部署指南

> 📄 **[查看交互式技能页面 →](https://oliverschmidtprietz.github.io/EU-AI-Act-Suite/ai-act-quick/)**

版本历史见 [CHANGELOG.md](CHANGELOG.md)。

## 概述

欧盟 AI 法案快速评估——15-25 分钟的快速分诊，用于初步分类：

- **适应性 2 批信息采集**——问题最少，基于系统描述
- **6 步门禁序列**——范围、AI 系统测试、被禁止、附件 I、附件 III、GPAI
- **初步分类输出**，附置信度
- 已识别层级的**合规截止期限**
- 突出成员国特定考量的**法域标记**
- **模板化提议**——可选择升级为完整评估（分类、角色确定、义务映射、正式报告）
- **清晰的范围边界**——为分诊而设计，非最终认定

## 文件结构

```
ai-act-quick/
├── SKILL.md                              # Main skill instructions (deploy this)
├── CHANGELOG.md                          # Version history
├── evals/
│   └── evals.json                        # Test cases
└── references/
    ├── quick-decision-tree.md            # 6-step gate sequence
    ├── compliance-deadlines.md           # Tier-by-tier deadline lookup
    └── jurisdiction-flags.md             # Member State-specific flags
```

## 部署

### Claude.ai（用户技能）

1. 进入 **Settings → Profile → Custom Skills**（或等效位置）
2. 上传整个 `ai-act-quick/` 文件夹结构
3. 技能将在出现"quick AI Act check"（快速 AI 法案检查）、"preliminary assessment"（初步评估）、"Schnellprüfung"或"Ersteinschätzung"时自动触发

### Claude Code / 自定义 MCP 设置

1. 将 `ai-act-quick/` 文件夹复制到你的技能目录：
   ```bash
   cp -r ai-act-quick/ /path/to/your/skills/user/ai-act-quick/
   ```
2. 确保技能已在你的配置中注册

## 使用

### 快速开始

把你对系统的了解全部倒出来：

> "Quick AI Act check please — we're a SaaS in Berlin selling a meeting-summary
> tool that transcribes calls and produces action items using GPT-4. Customers
> are EU businesses. Does the AI Act apply, and what tier?"（请快速做一次 AI 法案检查——我们是柏林的 SaaS，销售一款使用 GPT-4 转写通话并生成行动项的会议摘要工具。客户是欧盟企业。AI 法案适用吗，属于哪个层级？）

技能将运行 15-25 分钟的分诊，返回带置信度的初步结论。

### 触发短语

- "Quick AI Act assessment"（快速 AI 法案评估）/ "Preliminary check"（初步检查）/ "Does the AI Act apply?"（AI 法案适用吗？）
- "Schnellprüfung" / "Ersteinschätzung" / "AI Act triage"（AI 法案分诊）
- "Run a quick classification"（运行快速分类）

### 工作流

| 阶段 | 说明 |
|-------|-------------|
| **阶段 1：快速语境** | 适应性 2 批信息采集（系统描述 + 角色/法域） |
| **阶段 2：快速分类** | 6 步门禁序列——范围、AI 系统、被禁止、附件 I、附件 III、GPAI |
| **阶段 3：初步输出** | 层级结论 + 置信度 + 法域标记 + 截止期限 |
| **阶段 4：模板化提议** | 可选升级为完整评估（分类、角色确定、义务映射、正式报告） |

## 能力摘要

| 功能 | 说明 |
|---------|-------------|
| 适应性信息采集 | 基于描述的少量问题流程（2 批） |
| 6 步门禁 | 范围 → AI 系统 → 被禁止 → 附件 I → 附件 III → GPAI |
| 置信度标记 | 每项结论附高 / 中 / 低置信度指示 |
| 截止期限查询 | 按层级的合规日期 |
| 法域标记 | 成员国特定信号（BSI / CNIL / Garante 等） |
| 升级 | 平滑升级至完整评估（分类、角色确定、义务映射、报告） |
| 范围纪律 | 输出明确标注为"初步"——不替代完整评估 |

## 监管依据

| 文件 | 引用 |
|----------|-----------|
| 欧盟 AI 法案 | 《条例（EU）2024/1689》 |
| 第 5 条 / 附件 I / 附件 III | 风险层级分类锚点 |
| 第 51 / 53 / 55 条 | GPAI 阈值和义务 |
| 合规截止期限 | 第十三编 + 欧盟委员会实施时间线 |

## 许可与免责声明

这是基于《条例（EU）2024/1689》的初步 AI 法案评估，为快速分诊而设计。不构成法律意见，也不替代完整评估——请通过完整风险层级分类、角色确定、义务映射、正式报告和合格法律顾问验证结果。

依据 AGPL-3.0 许可。

> **质量保证：** 本技能随附 `evals/` 文件夹中的评估测试，我会运行这些测试，将输出与预期结果核对。

---

*由 Oliver Schmidt-Prietz 创建——[OneZero Legal](https://onezero.legal)*
