# ISO 27001 合规技能

> 面向安全与合规团队的 Claude 技能，用于驾驭 ISO/IEC 27001——从差距分析和风险评估到政策生成和控制实施。

---

## 1. 本技能做什么

ISO 27001 技能将 Claude 变成一位专家级 ISO 27001 主任审核员和 ISMS 实施顾问。它提供信息安全管理体系（ISMS）完整生命周期中结构化、可审计的指引——从初始差距评估到认证就绪。

本技能同时覆盖 **ISO 27001:2013**（114 项控制、14 个领域）和 **ISO 27001:2022**（93 项控制、4 个主题），默认使用现行 2022 版本。它理解强制条款（4–10）、所有附件 A 控制、强制文件要求以及两个版本之间的差异——包括 2022 年引入的 11 项新控制。

输出按任务定制：结构化差距分析表、带文件控制块的完整政策文档、逐控制实施指南、风险登记册和适用性声明（SoA）模板。

---

## 2. 目标受众

本技能为从事 ISO 27001 认证、维护或过渡的**安全与合规团队**设计。它对以下人员最有用：

- 监督 ISMS 实施或审计准备的**信息安全经理（ISM）**和 **CISO**
- 进行差距评估或维护 SoA 和风险登记册的**合规分析师**
- 寻求特定附件 A 控制实施指引的**安全工程师**
- 为第 1 阶段或第 2 阶段认证审核做准备的**内部审核员**
- 支持客户首次认证或从 2013 过渡到 2022 的**顾问**

---

## 3. 常见使用场景

| 使用场景 | 示例提示 |
|----------|---------------|
| **差距分析** | "Run a gap analysis of our current ISMS against ISO 27001:2022 Clause 6 and Annex A organisational controls." |
| **政策生成** | "Write me a complete Access Control Policy mapped to ISO 27001:2022." |
| **控制实施指引** | "How do I implement A.5.23 — Information security for use of cloud services?" |
| **风险评估** | "Help me build a risk register using the likelihood × impact methodology." |
| **风险处理计划** | "Generate a risk treatment plan based on these five identified risks." |
| **适用性声明** | "Create a SoA template covering all 93 Annex A controls for a SaaS company." |
| **认证就绪** | "What mandatory documents do I need before our Stage 2 audit?" |
| **2013 → 2022 过渡** | "What are the key differences between ISO 27001:2013 and 2022, and what do I need to update?" |
| **控制映射** | "Which 2022 controls map to the old A.12 Operations Security domain?" |
| **审计准备** | "What evidence will an auditor look for when reviewing our incident management controls?" |

---

## 4. 如何使用本技能

技能在 Claude 中安装后，每当您询问 ISO 27001、ISMS、附件 A 控制或相关合规主题时，它会自动激活。您无需按名称引用技能。

### 最佳效果提示

**明确版本** —— 说明您使用的是 ISO 27001:2013、2022 还是两者。如果您不指定，技能默认使用 2022。

**提供组织背景** —— 行业、规模和 ISMS 范围有助于技能定制输出。例如：

> "We're a 200-person SaaS company. Help me do a gap analysis of our Annex A organisational controls against ISO 27001:2022."

**指明具体控制或条款** —— 对实施指引，引用控制 ID（例如 `A.8.12`）或条款编号（例如 `Clause 6.1`）会产生更有针对性的响应。

**一次只要求一件事** —— 技能可以处理复杂的多步骤任务，但在单个提示中同时要求差距分析、政策和风险登记册可能产生宽泛的输出。按顺序逐项处理每个任务更有效。

### 示例交互

```
You:     Write me an Incident Response Policy mapped to ISO 27001:2022.

Claude:  [Generates a full policy document including:
          - Document control block (version, author, review date)
          - Purpose and scope
          - Policy statement
          - Roles and responsibilities
          - Incident classification and response procedures
          - Mapping to Clauses 8.1 and Annex A controls A.5.24–A.5.28
          - Review cycle and references]
```

---

## 5. 技能实现细节

### 架构

技能遵循三层结构：

```
iso27001/
├── SKILL.md                          # Core skill logic and workflows
└── references/
    ├── annex-a-2022.md               # All 93 ISO 27001:2022 Annex A controls
    ├── annex-a-2013.md               # All 114 ISO 27001:2013 Annex A controls
    └── control-mapping.md            # 2013 ↔ 2022 cross-reference table
```

技能触发时，`SKILL.md` 被加载到 Claude 的上下文中。参考文件按需加载——每项任务仅加载相关的一个或多个文件——保持上下文窗口高效。

### SKILL.md 中包含什么

- **角色**：Claude 扮演 ISO 27001 主任审核员和 ISMS 顾问
- **输出格式矩阵**：将每种任务类型映射到特定输出格式（表格、文档、叙述）
- **强制条款摘要**：条款 4–10，含每条款的关键交付物
- **4 个核心工作流**：差距分析、政策与文档生成、控制实施指引、风险评估
- **政策到控制映射表**：将 11 项常见政策链接到其 ISO 27001 条款和附件 A 控制
- **版本对比表**：2013 与 2022 并排差异
- **强制文件清单**：ISO 27001:2022 认证所需的 14 项记录
- **参考文件加载逻辑**：何时加载每个参考文件的规则

### 参考文件中包含什么

| 文件 | 内容 |
|------|----------|
| `annex-a-2022.md` | 全部 93 项控制及 ID、名称和描述；2022 新控制以 ⭐ 标记 |
| `annex-a-2013.md` | 跨 14 个领域的全部 114 项控制及 ID 和名称 |
| `control-mapping.md` | 完整 2022→2013 映射表；11 项新控制清单；合并/重命名控制说明 |

### 用于构建技能的输入

本技能基于以下输入构建：

- **ISO/IEC 27001:2022** —— 强制条款（4–10）、附件 A 控制集（93 项控制）、文件要求
- **ISO/IEC 27001:2013** —— 附件 A 控制集（跨 14 个领域的 114 项控制）
- **ISO/IEC 27002:2022** —— 控制描述和实施指引（信息性参考）
- **公开可得的过渡指引** —— 2013 与 2022 附件 A 控制之间的映射、11 项新控制摘要
- **常见 ISMS 审计实践** —— 典型审核员证据预期、强制文件清单、差距分析方法论
- **风险评估方法论** —— 可能性 × 影响评分、风险处理选项（接受 / 规避 / 转移 / 缓解）、风险登记册结构

### 技能触发短语

技能在以下任一主题上激活（非穷尽）：

`ISO 27001` · `ISO/IEC 27001` · `ISMS` · `Annex A` · `gap analysis` · `Statement of Applicability` · `SoA` · `risk register` · `risk treatment plan` · `information security policy` · `certification readiness` · `2013 to 2022 transition` · `control implementation` · `internal audit` · `management review` · `nonconformity`

---

## 6. 作者

**技能设计者：** Hemant Naik
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)
**使用构建：** Claude（Anthropic），采用 Claude Skills 框架
**日期：** 2026 年 3 月
**技能版本：** 1.6.2
**标准覆盖：** ISO/IEC 27001:2013 和 ISO/IEC 27001:2022
