# 欧盟 AI 法案系统分类器——部署指南

> 📄 **[查看交互式技能页面 →](https://oliverschmidtprietz.github.io/EU-AI-Act-Suite/ai-act-classifier/)**

版本历史见 [CHANGELOG.md](CHANGELOG.md)。

## 概述

欧盟 AI 法案系统分类器——面向 Claude 的结构化 AI 法案评估技能，提供：

- **Art. 2 范围排除分析**（军事、个人使用、纯研发、上市前、国际执法），含系统描述引导的定向排查
- **Art. 3(1) AI 系统定义测试** —— 基于委员会指南和 OECD AI 框架的 7 项标准分析
- **开源豁免检查清单** —— 针对 Art. 2(12)（AI 系统）和 Art. 53(2)（GPAI 模型）的专用路径
- **Art. 5 禁止实践筛查**，按委员会指南采用以主体为中心的解读
- **高风险分类** —— 附件 I 产品安全路径 + 附件 III 应用基础路径
- **Art. 6(3) 例外评估**，含 Art. 6(4) 文件要求
- **GPAI 模型评估**与风险等级分类并行运行——标准 GPAI（Art. 53）和系统性风险 GPAI（Art. 55）
- **Art. 50 透明度义务触发**，含《实践守则》多层标记指引
- **行业特定指引**，针对高风险附件 III 类别（就业、教育、生物识别、执法等）
- **合规截止日期查询**，按风险等级和提供者/部署者角色
- **分类仪表板输出** —— 含法律依据、截止日期和后续行动的单页摘要

## 文件结构

```
ai-act-classifier/
├── SKILL.md                              # Main skill instructions (deploy this)
├── CHANGELOG.md                          # Version history
├── evals/
│   └── evals.json                        # 3 test cases (with-skill vs. baseline)
└── references/
    ├── ai-system-definition.md           # Art. 3(1) 7-criteria test + worked examples
    ├── scope-exclusions.md               # Art. 2 exclusion checklists (incl. open-source)
    ├── prohibited-practices.md           # Art. 5 prohibitions — full subject-centric analysis
    ├── high-risk-annexes.md              # Annex I + Annex III routes
    ├── art6-exception.md                 # Art. 6(3) exception with Art. 6(4) docs
    ├── gpai-systemic-risk.md             # Art. 51/53/55 GPAI thresholds and obligations
    ├── art50-transparency.md             # Art. 50 transparency + Code of Practice marking
    ├── sector-guidance.md                # Sector-specific high-risk guidance
    ├── jurisdiction-requirements.md      # Member-state-specific implementation notes
    ├── compliance-deadlines.md           # Deadlines by tier + role
    ├── enforcement-framework.md          # Penalties, market surveillance, AI Office
    └── case-studies.md                   # Worked classification examples
```

## 部署

### Claude.ai（用户技能）

1. 进入 **Settings → Profile → Custom Skills**（或等效位置）
2. 上传整个 `ai-act-classifier/` 文件夹结构
3. 当您提及 AI 法案分类、风险等级、KI-Verordnung、附件 III、禁止实践或 GPAI 系统性风险时，技能将自动触发

### Claude Code / 自定义 MCP 设置

1. 将 `ai-act-classifier/` 文件夹复制到您的技能目录：
   ```bash
   cp -r ai-act-classifier/ /path/to/your/skills/user/ai-act-classifier/
   ```
2. 确保技能已在您的配置中注册

## 使用

### 快速开始

描述您想要分类的 AI 技术：

> "We're building a CV-screening tool that ranks job applicants for our HR team.
> It uses a fine-tuned LLM to score candidates against job descriptions. Do we
> need to treat this as high-risk under the AI Act?"

技能将激活并带您完成分类。

### 触发短语

- "Classify an AI system under the AI Act" / "AI Act risk tier"
- "Is this an AI system?" / "Art. 3(1)" / "Prohibited practice?"
- "High-risk classification" / "Annex III" / "Art. 6 exception"
- "GPAI systemic risk" / "KI-Verordnung" / "Risikoklassifizierung"

> 对于*不*产生分类的纯条款查询问题，直接根据所引条例文本回答，而不运行分类器。

### 工作流

| 阶段 | 描述 |
|-------|-------------|
| **阶段 1：范围门禁** | Art. 2 排除分析（军事、个人、研发、上市前、ILE）+ 开源检查清单（Art. 2(12) / Art. 53(2)） |
| **阶段 2：AI 系统测试** | 基于委员会指南和 OECD 框架的 Art. 3(1) 7 项标准定义测试 |
| **阶段 3：风险分类** | 按顺序执行第 1-3 步（Art. 5 → 附件 I → 附件 III + Art. 6(3) 例外）；第 4 步 GPAI 评估**并行**运行；第 5 步 Art. 50 透明度检查 |
| **阶段 4：分类仪表板** | 单页输出：风险等级、法律依据、截止日期、义务摘要、后续步骤建议 |

## 能力摘要

| 功能 | 描述 |
|---------|-------------|
| 范围排除（Art. 2） | 系统描述引导的定向排查——仅呈现相关排除 |
| 开源检查清单 | 针对 Art. 2(12) AI 系统和 Art. 53(2) GPAI 模型的专用 3 步流程 |
| AI 系统定义 | 带委员会/OECD 指引的 7 项标准 Art. 3(1) 测试 |
| 禁止实践 | Art. 5 筛查——按委员会指南采用以主体为中心的解读 |
| 高风险：附件 I | 产品安全路径（Art. 6(1)） |
| 高风险：附件 III | 应用基础路径（Art. 6(2)），含 Art. 6(3) 例外 |
| Art. 6(3) 例外 | 有文件的豁免，含 Art. 6(4) 注册义务 |
| GPAI 评估 | 并行轨道——标准 GPAI（Art. 53）+ 系统性风险 GPAI（Art. 55） |
| Art. 50 透明度 | 交互、合成内容、情绪识别、深度伪造标记 |
| 行业指引 | 针对附件 III 类别的定向指引（就业、教育、生物识别等） |
| 法域说明 | 成员国特定实施要求 |
| 截止日期查询 | 按等级的合规日期（禁止 / 高风险 / GPAI / Art. 50 / 最低限度） |
| 分类仪表板 | 单页摘要输出 |

## 监管依据

| 文件 | 引用 |
|----------|-----------|
| 欧盟 AI 法案 | Regulation (EU) 2024/1689 |
| 委员会 AI 系统定义指南 | Art. 3(1) 解释 |
| 委员会禁止 AI 实践指南 | Art. 5 执法解读 |
| 委员会高风险分类指南 | Art. 6 + 附件 III |
| OECD AI 框架 | 底层技术定义 |
| GPAI 实践守则 | Art. 53/55 实施 |
| Art. 50 实践守则（透明度） | 多层标记框架 |

## 许可证与免责声明

本技能基于欧盟 AI 法案（Regulation (EU) 2024/1689）、委员会指南和 OECD AI 框架提供结构化指引。它不构成法律意见。最终分类决定应涉及具备 AI 法案专长的合格法律顾问。

依据 AGPL-3.0 许可。

> **质量保证：** 本技能随附 `evals/` 文件夹中的评估测试，我运行这些测试以将输出与预期结果进行核对。

---

*由 Oliver Schmidt-Prietz 创建——[OneZero Legal](https://onezero.legal)*
