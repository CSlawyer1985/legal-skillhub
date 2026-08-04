# 欧盟《人工智能法案》第 50 条透明度评估器——部署指南

版本历史参见 [CHANGELOG.md](CHANGELOG.md)。

## 概述

欧盟《人工智能法案》**第 50 条透明度评估器**——一个可独立使用但也与套件联动的技能，用于识别第 50(1)–(5) 条中的哪些透明度义务适用于某系统，并指引必须实施的内容和实施时限。它产出两项交付物：一份正式的**迷你报告**和一份带缺口标记的**逐义务合规检查清单**。

- **五项义务，两种角色**——50(1) 交互披露和 50(2) 合成内容标记（提供者）；50(3) 情绪/生物识别通知和 50(4) 深度伪造/公共利益文本标签（部署者）；50(5) 交付质量（跨领域）
- **触发与豁免逻辑**——一般消费者明显性测试（50(1)）、辅助功能豁免（50(2)）、第 5 条门槛（50(3)）以及狭窄的 50(4) 例外
- **实施深度**——最终版《实务守则》的分层标记架构、欧盟官方标签图标集以及按模态的放置要求
- **带日期、兼顾 Omnibus 的路线图**——2026 年 8 月 2 日、2026 年 12 月 2 日遗留宽限期（2026 年 6 月 29 日经理事会通过，待刊于官方公报）、2026 年 7 月 22 日签署截止日期，以及 2027 年 2 月 2 日守则互操作日期
- **独立但可串联**——接收分类器的 `ASSESSMENT CONTEXT` 块，并输出其自身的可移植第 50 条合规块

## 文件结构

```
ai-act-transparency/
├── SKILL.md                              # 主要技能指令（部署此文件）
├── CHANGELOG.md                          # 版本历史
├── evals/
│   └── evals.json                        # 测试用例
└── references/
    ├── art50-duties.md                   # 五项义务 + 50(6) 治理
    ├── obviousness-and-exceptions.md     # 明显性测试、豁免、边界、跨条款互动
    ├── code-of-practice-final.md         # 最终版《实务守则》（2026 年 6 月 10 日）——提供者标记 + 部署者标签
    ├── commission-guidelines-art50.md    # 欧盟委员会第 50 条指南草稿（2026 年 5 月 8 日）
    ├── eu-labelling-icons.md             # 欧盟官方图标集 + 设计/放置要求
    ├── timeline-and-grace.md             # 带日期路线图 + 数字 Omnibus 宽限期（已通过，待刊官方公报）
    ├── implementation-checklists.md      # 提供者 / 部署者 / 中小企业行动检查清单
    ├── report-template-art50.md          # 迷你报告、检查清单和可移植合规块模板
    └── sources.md                        # 审计级来源清单（URL、状态、最后核验时间、不确定性层级）
```

## 部署

### Claude.ai（用户技能）

1. 进入 **设置 → 个人资料 → 自定义技能**（或等效入口）
2. 上传整个 `ai-act-transparency/` 文件夹结构
3. 技能将在出现“Art. 50 transparency obligations”“do we need to label AI content / deepfakes”“AI chatbot disclosure”“synthetic content marking”“Kennzeichnungspflicht”或“Transparenzpflichten”时自动触发

### Claude Code / 自定义 MCP 设置

1. 将 `ai-act-transparency/` 文件夹复制到你的技能目录：
   ```bash
   cp -r ai-act-transparency/ /path/to/your/skills/user/ai-act-transparency/
   ```
2. 确保技能已在你的配置中注册

## 使用

### 快速入门

可以全新开始，也可以从先前技能交接上下文：

> “我们正以自有品牌推出一款 AI 支持聊天机器人和一款图像生成器。哪些第 50 条
> 透明度义务适用，我们要实施什么，截止何时？”

或从分类器串联：

> “这是分类器的 ASSESSMENT CONTEXT 块——评估我们的第 50 条透明度义务
> 并产出报告和检查清单。”

### 触发短语

- “Check Art. 50 transparency obligations” / “Transparenzpflichten”
- “Do we need to label AI content / deepfakes” / “Kennzeichnungspflicht”
- “AI chatbot disclosure” / “synthetic content marking” / “watermarking”
- “What must we implement under Art. 50 and by when”

### 工作流

| 阶段 | 描述 |
|-------|-------------|
| **阶段 1：信息接收** | 系统描述 + 可选的 `ASSESSMENT CONTEXT` 摄入 |
| **阶段 2：角色确定** | 提供者 / 部署者 / 两者 |
| **阶段 3：触发确定** | 逐义务触发 + 明显性/例外测试 |
| **阶段 4：实施深挖** | 每个被触发义务应构建什么 |
| **阶段 5：带日期路线图** | 兼顾 Omnibus 的截止日期 |
| **阶段 6：输出** | 迷你报告 + 检查清单 + 可移植合规块 |

## 监管依据

| 文件 | 引用 |
|----------|-----------|
| 欧盟《人工智能法案》 | 法规（EU）2024/1689，第 50 条及序言第 132–137 段 |
| 深度伪造定义 | 第 3(60) 条 |
| 罚则档次 | 第 99(4) 条——第二档（1500 万欧元 / 3%） |
| 《AI 生成内容透明度实务守则》 | 最终版，2026 年 6 月 10 日（第 50(7) 条） |
| 欧盟委员会第 50 条指南 | 草稿，2026 年 5 月 8 日（第 96(1)(d) 条） |
| 数字 Omnibus | 50(2) 遗留标记宽限至 2026 年 12 月 2 日——已通过（理事会 2026 年 6 月 29 日最终放行），待刊于官方公报 |

## 许可与免责声明

本技能基于法规（EU）2024/1689、《AI 生成内容透明度实务守则》最终版及欧盟委员会第 50 条指南草稿产出结构化的第 50 条透明度指引。其不构成法律意见。该守则是自愿性的，遵守守则并非合规的决定性证据；只有欧盟法院（CJEU）才能对第 50 条作出权威解释。输出在用于监管用途前应由合格法律顾问审查。

依据 AGPL-3.0 许可发布——参见仓库根目录的 [LICENSE](../../LICENSE)。

---

*作者：Oliver Schmidt-Prietz —— OneZero Legal*
