# 欧盟 AI 法案知识引擎——部署指南

> 📄 **[查看交互式技能页面 →](https://oliverschmidtprietz.github.io/EU-AI-Act-Suite/ai-act-knowledge/)**

版本历史见 [CHANGELOG.md](CHANGELOG.md)。

## 概述

欧盟 AI 法案知识引擎——一个以 70 份官方欧盟来源文件为基础的权威监管问答技能：

- 来自 Regulation (EU) 2024/1689 全文的**条款级引用**
- 由结构化参考文件（第一至第十三标题）覆盖的**完整前言 + 13 个标题**
- 关于 AI 系统定义、禁止实践、高风险分类和 Digital Omnibus 的**委员会指南**
- **EDPB/EDPS 意见**，包括意见 28/2024（AI-DPIA 相互作用）和 2026 年联合意见
- **《实践守则》** —— GPAI 守则（3 个版本）、透明度守则（草稿 + 概览）
- **FRIA 材料** —— Art. 27 文本、丹麦研究所指南、ECNL 实务指南
- **协调标准** —— Art. 40 框架、prEN 18286、JTC 21 路线图
- 面向银行业、医疗器械、人力派遣、医疗保健、执法的**行业特定指引**
- **国家实施追踪** —— 德国 AI 法案、监管沙盒、国家服务台
- **事件报告模板** —— GPAI 严重事件、Art. 73 高风险草稿指引

## 文件结构

```
ai-act-knowledge/
├── SKILL.md                          # Main skill instructions (deploy this)
├── CHANGELOG.md                      # Version history
└── references/                       # 70 reference files across 15 subdirectories
    ├── core/                         # Regulation text by Title (I–XIII) + preamble + Annex III + decision trees
    ├── guidelines/                   # Commission guidelines (AI system definition, prohibited, GPAI, omnibus)
    ├── codes-of-practice/            # GPAI Code + Transparency Code (multiple versions)
    ├── opinions/                     # EDPB/EDPS opinions (2021, 2026, 28/2024)
    ├── standards/                    # Art. 40 harmonised standards, prEN 18286, JTC 21
    ├── fria/                         # Art. 27 FRIA — text + practical guides
    ├── governance/                   # AI Office FAQ, AI Pact, enforcement, timeline
    ├── national/                     # National implementation (DE bill, sandboxes, service desks)
    ├── sector-specific/              # Banking, medical devices, staffing
    ├── cybersecurity/                # ENISA advisories
    ├── law-enforcement/              # Europol AI policing
    ├── compliance-guides/            # AI literacy, SME guide, copyright/TDM, whistleblowing
    ├── impact-assessments/           # Commission IA + supporting study + healthcare 2026
    └── templates/                    # GPAI training data, serious incident, high-risk draft
```

## 部署

### Claude.ai（用户技能）

1. 进入 **Settings → Profile → Custom Skills**（或等效位置）
2. 上传整个 `ai-act-knowledge/` 文件夹结构
3. 当您询问 AI 法案条款、要求、处罚、GPAI 义务、FRIA 或任何 AI 法案主题时，技能将自动触发

### Claude Code / 自定义 MCP 设置

1. 将 `ai-act-knowledge/` 文件夹复制到您的技能目录：
   ```bash
   cp -r ai-act-knowledge/ /path/to/your/skills/user/ai-act-knowledge/
   ```
2. 确保技能已在您的配置中注册

## 使用

### 快速开始

提出任何 AI 法案问题：

> "What does Art. 27 require for a Fundamental Rights Impact Assessment, and
> when does it apply to deployers of high-risk systems?"

技能将路由到正确的参考文件并产出带引用的答案。

### 触发短语

- "Explain Art. X" / "What does Article X say?" / "AI Act requirements"
- "GPAI obligations" / "High-risk AI" / "Prohibited AI practices"
- "AI Act and GDPR" / "Fundamental rights impact assessment" / "AI literacy"
- "KI-Verordnung" / "Hochrisiko-KI" / "GPAI-Verhaltenskodex"

> 对于产出分类决定（而非知识答案）的评估工作流，请要求进行结构化风险等级分类。

### 工作流

| 步骤 | 描述 |
|------|-------------|
| **1. 问题分类** | 主题路由器确定要查阅的参考子目录 |
| **2. 加载参考** | 阅读定向参考文件（条款文本、指南、意见、守则） |
| **3. 综合** | 产出带条款级引用和相关条款交叉引用的答案 |

## 能力摘要

| 功能 | 描述 |
|---------|-------------|
| 条款级问答 | 基于完整条例文本（前言 + 13 个标题）的直接回答 |
| 委员会指南 | AI 系统定义、禁止实践、高风险、Digital Omnibus |
| EDPB/EDPS 意见 | 2021 年联合、2026 年联合、意见 28/2024（AI-DPIA） |
| 《实践守则》 | GPAI 守则（3 个版本）、透明度守则（草稿 + 概览） |
| FRIA 材料 | Art. 27 文本 + 丹麦研究所和 ECNL 实务指南 |
| 协调标准 | Art. 40 框架、prEN 18286、JTC 21 路线图 |
| 行业指引 | 银行业、医疗器械、人力派遣、医疗保健、执法 |
| 国家实施 | 德国 AI 法案、监管沙盒、成员国服务台 |
| 事件模板 | GPAI 严重事件报告、Art. 73 高风险草稿 |
| 跨框架 | AI 法案 ↔ GDPR、ENISA 网络安全叠加 |

## 监管依据

| 文件 | 引用 |
|----------|-----------|
| 欧盟 AI 法案 | Regulation (EU) 2024/1689（全文 + 序言） |
| 委员会指南 | AI 系统定义、Art. 5 禁止、Art. 6 高风险、Digital Omnibus |
| EDPB 意见 28/2024 | AI 处理的 DPIA |
| EDPB-EDPS 联合意见 | 2021 年和 2026 年 |
| GPAI 实践守则 | Art. 53/55 实施框架 |
| Art. 50 实践守则 | 透明度标注框架 |
| Art. 40 协调标准 | JTC 21 框架、prEN 18286 |
| ENISA 建议 | AI 网络安全、标准化 |

## 许可证与免责声明

本技能基于 Regulation (EU) 2024/1689 和官方欧盟机构来源提供结构化的 AI 法案监管信息。它不是法律意见。具体合规决定应涉及具备 AI 法案专长的合格法律顾问。

依据 AGPL-3.0 许可。

> **质量保证：** 本技能随附 `evals/` 文件夹中的评估测试，我运行这些测试以将输出与预期结果进行核对。

---

*由 Oliver Schmidt-Prietz 创建——[OneZero Legal](https://onezero.legal)*
