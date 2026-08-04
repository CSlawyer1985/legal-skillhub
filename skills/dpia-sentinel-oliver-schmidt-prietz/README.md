# DPIA Sentinel（数据保护影响评估哨兵）——部署指南

> 📄 **[查看交互式技能页面 →](https://oliverschmidtprietz.github.io/GDPR-DPIA-Sentinel/)**

## 概述

GDPR 数据保护影响评估（DPIA）哨兵——一个为 Claude 提供的结构化 DPIA 指引技能，提供：

- 针对 Art. 35(3) 强制性触发条件和 EDPB 九项标准分析的**阈值评估**
- 覆盖 7 个欧盟成员国（德、法、爱、比、荷、意、波）的**多法域黑名单/白名单检查**
- **EDPB 2026 DPIA 模板支持**——以官方统一欧盟格式（第 0–6 节）生成文档
- **双轨风险模型**——依 EDPB 方法论的固有设计风险（A 轨）与运营风险（B 轨）
- 从数据主体视角出发、含调节因素的 **5×5 风险评估**
- 所有措施的**实施状态跟踪**（已计划 / 部分实施 / 已实施）
- 作为独立上游评估门禁的**必要性与相称性**
- 面向风险相关处理基础设施的**资产清单**
- 带四种结果判定的 **Art. 36 事先协商**决策支持
- 依 EDPB 意见 28/2024 的 **AI 双阶段分析**（训练与部署）
- 通过模板填充实现的**可审计 .docx 文档生成**（EDPB 2026 格式、自定义 12 节报告、阈值备忘录、执行摘要、Art. 36 材料包）

## 文件结构

```
dpia-skill/
├── SKILL.md                              # 主要技能指令（部署此文件）
├── CHANGELOG.md                          # 版本历史
└── references/
    ├── edpb-criteria.md                  # EDPB 九项标准 + 多法域框架
    ├── edpb-2026-template.md             # EDPB 2026 DPIA 模板逐字段规范
    ├── edpb-2026-template-v1.docx        # 官方 EDPB 模板 .docx（可填充）
    ├── edpb-2026-population.md           # 模板的逐表填充指南
    ├── edpb-2026-explainer.md            # EDPB 2026 方法论参考
    ├── dpia-custom-template-v1.docx      # 自定义 12 节 DPIA 模板 .docx（可填充）
    ├── dpia-custom-population.md         # 自定义模板填充指南
    ├── scoring.md                        # 5×5 风险评分 + 调节因素 + 双轨
    ├── risk-catalog.md                   # 按处理类型的常见 DPIA 风险（A+B 轨）
    ├── templates.md                      # 文档模板（5 种格式）
    ├── sources.md                        # 监管来源引用
    └── jurisdictions/
        ├── de-dsk.md                     # 德国——DSK 黑名单
        ├── fr-cnil.md                    # 法国——CNIL 黑名单
        ├── ie-dpc.md                     # 爱尔兰——DPC 黑名单
        ├── be-apd.md                     # 比利时——APD 黑名单
        ├── nl-ap.md                      # 荷兰——AP 黑名单
        ├── it-garante.md                 # 意大利——Garante 黑名单
        ├── pl-uodo.md                    # 波兰——UODO 黑名单
        └── whitelists.md                 # 法、捷、西、奥白名单豁免
```

## 部署

### Claude.ai（用户技能）

1. 进入 **设置 → 个人资料 → 自定义技能**（或等效入口）
2. 上传整个 `dpia-skill/` 文件夹结构
3. 当你提及 DPIA、DSFA、Art. 35 或描述高风险处理时，技能自动触发

### Claude Code / 自定义 MCP 设置

1. 将 `dpia-skill/` 文件夹复制到你的技能目录：
   ```bash
   cp -r dpia-skill/ /path/to/your/skills/user/dpia-skill/
   ```
2. 确保技能已在你的配置中注册

## 使用

### 快速入门

直接描述你的处理活动：

> “我们计划部署一个根据求职者的简历和视频面试为其评分的 AI 系统。
> 该系统将在德国、法国和荷兰使用。
> 我们需要 DPIA 吗？”

技能将激活并引导你完成评估。

### 触发短语

- “Do I need a DPIA?” / “DSFA” / “Datenschutz-Folgenabschaetzung”
- “Art. 35” / “impact assessment” / “high-risk processing”
- “We want to deploy AI for...” / “profiling” / “large-scale monitoring”
- “Generate a DPIA report”

### 评估流程

| 阶段 | 描述 |
|-------|-------------|
| **阈值** | Art. 35(3) 触发条件 + 九项标准分析 + 国家黑名单检查 |
| **描述** | 依 Art. 35(7)(a) 的系统性处理描述 |
| **资产清单** | 按类型分组的风险相关资产（EDPB 2026，第 1.3 节） |
| **必要性** | 有效性 + 最少侵入测试（上游门禁） |
| **相称性** | 收益与影响平衡（上游门禁） |
| **固有风险** | A 轨（设计上）+ B 轨（运营），5×5 矩阵 + 调节因素 |
| **缓解措施** | 带实施状态的技术、组织和法律措施 |
| **剩余风险** | 总体判定：已批准 / 有条件批准 / 咨询监管机构 / 否决 |
| **文档** | 可审计 .docx 生成（EDPB 2026 或自定义格式） |

## 文档类型

| 模板 | 描述 |
|----------|-------------|
| EDPB 2026 DPIA 报告 | 官方统一格式（第 0–6 节，被所有欧盟监管机构认可） |
| 完整 DPIA 报告（自定义） | 带阈值分析和附件的自定义 12 节评估 |
| 阈值理由备忘录 | 2–3 页文档，说明为何**不**需要 DPIA |
| 执行摘要 | 1–2 页董事会/领导层摘要 |
| Art. 36 协商材料包 | 面向监管机构事先协商的提交材料 |

## 监管依据

| 文件 | 引用 |
|----------|-----------|
| GDPR 第 35 条 | DPIA 义务 |
| GDPR 第 36 条 | 事先协商 |
| EDPB DPIA 模板 v1.0（2026 年 3 月） | 欧盟统一的 DPIA 结构 |
| EDPB 指南 WP 248 rev.01 | DPIA 方法论和九项标准 |
| EDPB 意见 28/2024 | 针对 AI 处理的 DPIA |
| EDPB 指南 01/2025 | 假名化作为风险降低因素 |
| 各国监管机构 Art. 35(4) 清单 | 强制 DPIA 黑名单（7 个法域） |

## 版本历史

完整版本历史参见 [CHANGELOG.md](CHANGELOG.md)。

## 许可与免责声明

本技能基于公开可得的 GDPR 监管材料提供结构化指引。其不构成法律意见。所有 DPIA 决策都应涉及你的 DPO（第 35(2) 条）和合格法律顾问。

> **质量保证：** 本技能随附 `evals/` 文件夹中的评估测试，我运行这些测试以检查其输出是否符合预期结果。

---

*作者：Oliver Schmidt-Prietz — [OneZero Legal](https://onezero.legal)*
