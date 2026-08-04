# 欧盟 AI 法案义务映射器——部署指南

> 📄 **[查看交互式技能页面 →](https://oliverschmidtprietz.github.io/EU-AI-Act-Suite/ai-act-obligations/)**

版本历史见 [CHANGELOG.md](CHANGELOG.md)。

## 概述

欧盟 AI 法案义务映射器——为给定的角色 + 风险层级生成可操作的合规矩阵：

- **角色 × 层级义务矩阵**——提供者、部署者、进口者、分销者，跨越被禁止、高风险、GPAI、第 50 条、最低风险
- 每项义务的 **RACI 分配**（负责 Responsible / 问责 Accountable / 咨询 Consulted / 知会 Informed）
- 按合规截止期限排序的**实施优先级**
- **技术措施**——风险管理、数据治理、日志记录、透明度、人工监督、准确性/稳健性、网络安全
- **组织措施**——质量管理、上市后监测、事件报告、合格评定
- **管理体系**——哪些是必需的（例如第 17 条 QMS）对比推荐的
- 所需的**影响评估**（DPIA、FRIA、合格评定）及交叉引用
- **GDPR 对照表**——AI 法案与 GDPR 义务之间的重叠与互动
- **监管叠加**——行业特定层级（银行、医疗器械、雇佣）
- 为第 6(3) 条例外使用者提供**第 6(4) 条文档**支持
- 附件 III 高风险系统的**欧盟数据库注册**工作流
- 含优先级决策树的**合规路线图**

## 文件结构

```
ai-act-obligations/
├── SKILL.md                                  # Main skill instructions (deploy this)
├── CHANGELOG.md                              # Version history
├── evals/
│   └── evals.json                            # Test cases
└── references/
    ├── high-risk-provider-obligations.md     # Art. 16, 9, 10, 11, 12, 13, 14, 15
    ├── high-risk-deployer-obligations.md     # Art. 26, 27 (FRIA)
    ├── gpai-obligations.md                   # Art. 53, 55, Code of Practice
    ├── low-risk-obligations.md               # Art. 50 transparency + voluntary measures
    ├── technical-measures.md                 # Risk mgmt, data governance, logging, etc.
    ├── organizational-measures.md            # QMS, post-market monitoring, incident reporting
    ├── management-systems.md                 # Art. 17 QMS specifics
    ├── conformity-assessment.md              # Annex VI/VII procedures
    ├── post-market-monitoring.md             # Art. 72 post-market system
    ├── eu-database-registration.md           # Art. 71 EU database workflow
    ├── art6-4-documentation.md               # Art. 6(4) exception documentation
    ├── fria-template.md                      # Fundamental Rights Impact Assessment scaffold
    ├── gdpr-crosswalk.md                     # AI Act ↔ GDPR mapping
    ├── regulatory-overlays.md                # Sector-specific compliance layers
    ├── compliance-roadmap.md                 # Priority decision tree + sequencing
    └── case-studies.md                       # Worked obligation-mapping examples
```

## 部署

### Claude.ai（用户技能）

1. 进入 **Settings → Profile → Custom Skills**（或等效位置）
2. 上传整个 `ai-act-obligations/` 文件夹结构
3. 当你要求映射义务、构建合规检查清单或评估 AI 法案下的提供者/部署者职责时，技能将自动触发

### Claude Code / 自定义 MCP 设置

1. 将 `ai-act-obligations/` 文件夹复制到你的技能目录：
   ```bash
   cp -r ai-act-obligations/ /path/to/your/skills/user/ai-act-obligations/
   ```
2. 确保技能已在你的配置中注册

## 使用

### 快速开始

告诉技能你的角色和风险层级（或仅描述系统）：

> "We're the deployer of a high-risk AI system used for credit scoring in
> Germany. What obligations do we have, and what should we prioritise in
> the first 6 months?"（我们是在德国用于信用评分的高风险 AI 系统的部署者。我们有哪些义务，前 6 个月应优先做什么？）

技能将生成带 RACI 和优先级的定制义务矩阵。

### 触发短语

- "Map AI Act obligations"（映射 AI 法案义务）/ "Check what we need to do"（检查我们需要做什么）/ "Compliance checklist"（合规检查清单）
- "Deployer obligations"（部署者义务）/ "Provider duties"（提供者职责）/ "Art. 26" / "Art. 16-17"
- "AI literacy Art. 4"（AI 素养第 4 条）/ "DPIA" / "FRIA" / "fundamental rights assessment"（基本权利评估）
- "Pflichtenkatalog"

### 工作流

| 阶段 | 说明 |
|-------|-------------|
| **阶段 1：输入语境** | 知悉语境的适应性信息采集——角色、风险层级、行业、法域；如提供先前技能输出则加以利用 |
| **阶段 2：义务映射** | 按层级的义务清单，含优先级决策树 |
| **阶段 3：实施路线图** | 对照截止期限的排序计划，识别速赢项 |
| **阶段 4：义务矩阵输出** | 带 RACI 标记的矩阵：技术措施、组织措施、管理体系、影响评估、GDPR 交叉引用 |

## 能力摘要

| 功能 | 说明 |
|---------|-------------|
| 角色 × 层级矩阵 | 所有组合（提供者/部署者/进口者/分销者 × 被禁止/高风险/GPAI/第 50 条/最低风险） |
| RACI 分配 | 逐义务的 R/A/C/I 标记 |
| 技术措施 | 第 9、10、11、12、13、14、15 条实施指引 |
| 组织措施 | 第 17 条 QMS、上市后监测、事件报告 |
| 合格评定 | 附件 VI / VII 程序路由 |
| 欧盟数据库注册 | 第 71 条高风险系统注册 |
| FRIA 支持 | 第 27 条基本权利影响评估脚手架 |
| GDPR 对照表 | 映射到 GDPR 义务（DPIA、控制者/处理者） |
| 行业叠加 | 银行、医疗器械、雇佣、生物识别 |
| 合规路线图 | 优先级决策树 + 知悉截止期限的排序 |

## 监管依据

| 文件 | 引用 |
|----------|-----------|
| 欧盟 AI 法案 | 《条例（EU）2024/1689》——第三、四、五编 |
| 第 9–15 条 | 高风险系统的技术要求 |
| 第 16–17 条 | 提供者义务 + QMS |
| 第 26–27 条 | 部署者义务 + FRIA |
| 第 50 条 | 透明度义务 |
| 第 53、55 条 | GPAI 义务（标准 + 系统性风险） |
| 第 71 条 | 欧盟数据库注册 |
| 第 72 条 | 上市后监测 |
| GPAI 行为守则 | 第 53 条实施框架 |
| GDPR | 用于 DPIA + 控制者/处理者义务的对照表 |

## 许可与免责声明

本技能基于《条例（EU）2024/1689》提供结构化的 AI 法案义务指引。不构成法律意见。合规措施的实施应涉及合格的法律顾问和相关技术专家。

依据 AGPL-3.0 许可。

> **质量保证：** 本技能随附 `evals/` 文件夹中的评估测试，我会运行这些测试，将输出与预期结果核对。

---

*由 Oliver Schmidt-Prietz 创建——[OneZero Legal](https://onezero.legal)*
