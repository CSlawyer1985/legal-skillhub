# TIA（转移影响评估）——部署指南

> 📄 **[查看交互式技能页面 →](https://oliverschmidtprietz.github.io/GDPR-Transfer-Impact-Assessment/)**

## 概述

GDPR 转移影响评估技能——为 Claude 提供的结构化第五章转移指引。结合：

- **EDPB《建议 01/2020》**六步方法论（监管主干）
- **CNIL TIA 指南**（最终版，2025 年 1 月）——结构化评估表和第 3 步三向结论
- **EDPB《建议 02/2020》**——监视法评估的四项基本保障框架
- **EDPB《指南 05/2021》**——转移定性的三项累积标准，含 12 个示例场景
- **Rosenthal 方法**的影响——务实的第 3 步 C 块（"对该数据的现实风险"），无需统计概率计算
- **12 个预建国家画像**——美国（非 DPF）、美国（DPF）、英国、印度、中国、巴西、澳大利亚、新加坡、土耳其、阿联酋、南非、俄罗斯 + 通用问卷
- **平衡的第 49 条处理**——EDPB《指南 2/2018》+ 慕尼黑高等地区法院（OLG München，21 U 3882/25 e，2026 年）的司法对立立场
- **审计就绪的输出**——Markdown 报告 + .docx 正式文件 + 用于 RoPA 数据交换的 JSON delta

## 文件结构

```
skills/tia/
├── SKILL.md                              # Main skill instructions (deploy this)
├── CHANGELOG.md                          # Version history
├── README.md                             # This file
├── evals/
│   └── evals.json                        # 12 behavioural test cases
└── references/
    ├── edpb-six-steps.md                 # EDPB Rec 01/2020 methodology
    ├── essential-guarantees.md           # EDPB Rec 02/2020 four-pillar framework
    ├── transfer-qualification.md         # EDPB Guidelines 05/2021 — 3 criteria + 12 examples
    ├── art49-derogations.md              # Art. 49 balanced assessment (EDPB + judicial)
    ├── supplementary-measures.md         # Catalog (technical / contractual / organisational)
    ├── schrems-ii-holdings.md            # C-311/18 key holdings + implications
    ├── tia-template.md                   # Document template structure
    ├── interchange-delta.md              # RoPA delta format
    ├── sources.md                        # Regulatory source references
    └── country-profiles/
        ├── us-non-dpf.md                # USA outside DPF
        ├── us-dpf.md                    # USA DPF-certified
        ├── uk-post-adequacy.md          # UK (adequacy renewed Dec 2025)
        ├── in.md                        # India
        ├── cn.md                        # China
        ├── br.md                        # Brazil
        ├── au.md                        # Australia
        ├── sg.md                        # Singapore
        ├── tr.md                        # Turkey
        ├── ae.md                        # UAE (DIFC / ADGM / mainland)
        ├── za.md                        # South Africa
        ├── ru.md                        # Russia
        └── generic-assessment.md        # Guided questionnaire for unlisted countries
```

## 部署

### Claude.ai（用户技能）

1. 进入 **Settings → Profile → Custom Skills**（或等效位置）。
2. 上传整个 `tia/` 文件夹结构。
3. 技能在出现"TIA"、"Transfer Impact Assessment"、"Schrems II"、"third-country transfer"（第三国转移）、"Art. 46"、"Art. 49"及类似术语时触发。

### Claude Code / 自定义设置

```bash
# Symlink the skill from the monorepo
ln -s ~/CLAUDE_PROJECTS/SKILLS/claude-skills/skills/tia ~/.claude/skills/tia
```

## 使用

### 快速开始

触发技能的示例提示词：

- "We're using SCCs Module 2 to transfer HR data to our payroll processor in India. Do I need supplementary measures?"（我们使用 SCC 模块 2 将 HR 数据传输给印度的工资处理方。我需要补充措施吗？）
- "I need a TIA for our US cloud provider — they're DPF-certified."（我需要为我们已获得 DPF 认证的美国云服务商做 TIA。）
- "Is remote support access from our Indian sub-processor considered a Chapter V transfer?"（我们印度次级处理者的远程支持访问算第五章转移吗？）
- "Can we rely on Art. 49(1)(b) for our global SaaS user data flows to the US?"（我们全球 SaaS 用户数据流向美国可以依赖第 49(1)(b) 条吗？）

### 触发短语

- "TIA"、"Transfer Impact Assessment"（转移影响评估）
- "Schrems II"、"Chapter V"（第五章）
- "Art. 44 / 45 / 46 / 47 / 49"
- "transfer to [country]"（转移至[国家]）（美国、印度、中国等）
- "SCCs assessment"（SCC 评估）、"BCRs"
- "supplementary measures"（补充措施）
- "DPF transfer"（DPF 转移）、"EU-US Data Privacy Framework"（欧盟-美国数据隐私框架）
- "adequacy decision"（充分性认定）
- "essential guarantees"（基本保障）
- "Drittlandsübermittlung"、"Drittlandtransfer"

### 评估模式

| 模式 | 何时使用 | 输出 |
|---|---|---|
| 单项转移评估 | 一项已知转移 | Markdown + .docx TIA |
| 批量 / 登记册 | 多项转移 | 登记册 + 逐项转移流水线 + 转移风险摘要 |
| 发现（独立） | 无 RoPA、多项转移 | 发现式引导 → 登记册 → 评估 |
| RoPA 导入 | 已有 RoPA sidecar | 导入转移 → 逐项评估 |
| 充分性快速通道 | 目的地有充分性认定 | 轻量评估 + 监测触发 |
| 第 49 条路径 | 可能适用克减 | 平衡评估（EDPB + 司法） |
| 仅转移定性 | "这到底算不算转移？" | 定性结论 |
| 审查 / 更新 | 已有 TIA + 法律变化 | 对受影响部分的重新评估 |

## 输出

| 格式 | 用途 |
|---|---|
| Markdown TIA 报告 | 会话内预览、工作文件 |
| .docx 正式 TIA 文件 | 合规档案、CNIL 风格表格、签署块 |
| JSON Delta | RoPA 数据交换——修补 `tia_ref`、`tia_status`、`supplementary_measures[]`、日期 |
| 转移风险摘要 | 批量评估的一页高管概览 |

## 监管依据

| 文件 | 引用 | 用途 |
|---|---|---|
| GDPR 第五章 | 第 44–49 条 | 法律条文 |
| Schrems II | 欧洲法院 C-311/18（2020 年 7 月 16 日） | 充分性 + TIA 义务 |
| EDPB《建议 01/2020》 | v2.0（2021 年 6 月 18 日） | 六步方法论 |
| EDPB《建议 02/2020》 |（2020 年 11 月 10 日） | 基本保障 |
| EDPB《指南 05/2021》 | v2.0（2023 年 2 月 14 日） | 转移定性 |
| EDPB《指南 2/2018》 |（2018 年 5 月 25 日） | 第 49 条克减（EDPB 观点） |
| CNIL TIA 指南 | 2025 年 1 月（最终版） | 实用的结构化表格 |
| 慕尼黑高等地区法院，21 U 3882/25 e |（2026 年 5 月 11 日） | 全球服务的第 49(1)(b) 条 |
| 实施决定（EU）2023/1795 |（2023 年 7 月 10 日） | 欧盟-美国 DPF 充分性 |

## 跨技能集成

| 技能 | 方向 | 流转内容 |
|---|---|---|
| RoPA | 入站 | 读取 sidecar；筛选第三国转移；预填第 1 步 |
| RoPA | 出站 | 每项已评估转移发出 delta 文件（符合 RoPA 入站模式 v1.0） |
| DPIA Sentinel | 仅标记 | 如第 3 步揭示高风险处理，标记供第 35 条 DPIA 考虑（不自动触发） |

## 版本历史

完整版本历史见 [CHANGELOG.md](CHANGELOG.md)。

## 许可与免责声明

AGPL-3.0。见仓库 LICENSE。

**本技能基于 EDPB 建议、CNIL 指引和新兴判例法提供结构化的 GDPR 第五章指引。不构成法律意见。最终决定应让 DPO 和合格法律顾问参与，尤其在技能标记某项转移需要暂停或重组时。技能的国家画像反映各画像中所述"最后核实"日期时的法律和实践状况——正式使用前请核实当前状态。**

> **质量保证：** 本技能随附 `evals/` 文件夹中的评估测试，我会运行这些测试，将输出与预期结果核对。

---

*由 Oliver Schmidt-Prietz 创建——[OneZero Legal](https://onezero.legal)*
