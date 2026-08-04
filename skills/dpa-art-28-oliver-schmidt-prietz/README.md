# DPA Art. 28 GDPR（《通用数据保护条例》第 28 条数据处理协议）——部署指南

> 📄 **[查看交互式技能页面 →](https://oliverschmidtprietz.github.io/GDPR-Data-Processing-Agreement/)**

版本历史参见 [CHANGELOG.md](CHANGELOG.md)。

## 概述

DPA Art. 28 GDPR——数据处理协议（AVV / Auftragsverarbeitungsvertrag）及第 26 条共同控制人安排（Joint Controller Arrangements）的审查、起草与修订：

- **5 种操作模式**自动路由——REVIEW_QUICK、REVIEW_NEG（谈判级）、DRAFT、REDLINE、JOINT_CONTROLLER
- **双语输出**——德语与英语，质量对等
- **双重视角**——控制人视角与处理人视角审查
- **两种审查深度**——快速（Art. 28(3)(a)–(h) 覆盖检查）与谈判级（逐条风险评分）
- **欧盟委员会 SCC 锚定**——基于欧盟委员会实施决定（EU）2021/915
- **模板库**——商业、混合与严格型 DPA 模板（德文 + 英文）；JCA 模板（德文 + 英文）
- **常见缺陷目录**——快速识别供应商提供草稿中的缺陷
- **谈判备用立场**——为争议条款预先起草的替代措辞
- **SCC 模块指南**——国际传输场景下何时及如何将模块 1–4 接入 DPA
- **层级选择助手**——将商业/混合/严格模板与交易情境匹配
- **严格质量门禁**——交付前核实 Art. 28(3) 覆盖情况

## 文件结构

```
dpa-art28/
├── SKILL.md                                       # 主要技能指令（部署此文件）
├── CHANGELOG.md                                   # 版本历史
├── references/
│   ├── 2021-915-commission-text-en.md             # 欧盟委员会实施决定（EU）2021/915 — 英文
│   ├── 2021-915-commission-text-de.md             # 欧盟委员会实施决定（EU）2021/915 — 德文
│   ├── art28-3-checklist.md                       # Art. 28(3)(a)–(h) 覆盖检查清单
│   ├── art26-joint-controller.md                  # Art. 26 JCA 框架
│   ├── common-defects.md                          # 供应商 DPA 缺陷目录
│   ├── negotiation-fallbacks.md                   # 争议条款的备用立场
│   ├── sccs-module-guide.md                       # 国际传输 SCC 整合
│   └── tier-selection.md                          # 商业/混合/严格层级助手
├── templates/
│   ├── dpa-commercial-de.md                       # 商业型 DPA — 德文
│   ├── dpa-commercial-en.md                       # 商业型 DPA — 英文
│   ├── dpa-hybrid-de.md                           # 混合型 DPA — 德文
│   ├── dpa-hybrid-en.md                           # 混合型 DPA — 英文
│   ├── dpa-strict-de.md                           # 严格型 DPA — 德文
│   ├── dpa-strict-en.md                           # 严格型 DPA — 英文
│   ├── jca-de.md                                  # JCA 模板 — 德文
│   └── jca-en.md                                  # JCA 模板 — 英文
└── workflows/
    ├── review-quick.md                            # REVIEW_QUICK 流程
    ├── review-negotiation.md                      # REVIEW_NEG 流程
    ├── draft.md                                   # DRAFT 流程
    ├── redline.md                                 # REDLINE 流程
    └── joint-controller.md                        # JOINT_CONTROLLER 流程
```

## 部署

### Claude.ai（用户技能）

1. 进入 **设置 → 个人资料 → 自定义技能**（或等效入口）
2. 上传整个 `dpa-art28/` 文件夹结构
3. 技能将在出现“DPA”“AVV”“Auftragsverarbeitung”“Art. 28 contract”“redline this DPA”“JCA”或“joint controller agreement”时自动触发

### Claude Code / 自定义 MCP 设置

1. 将 `dpa-art28/` 文件夹复制到你的技能目录：
   ```bash
   cp -r dpa-art28/ /path/to/your/skills/user/dpa-art28/
   ```
2. 确保技能已在你的配置中注册

## 使用

### 快速入门

粘贴一份 DPA 或请求生成一份：

> “请审查供应商提供的这份 DPA——我方是控制人。先做快速检查，
> 然后告诉我 Art. 28(3) 下缺少什么，以及我应当对哪些内容提出异议。”

或者：

> “请为一家处理员工数据、位于欧盟的处理人起草一份严格级德语 DPA，
> 并包含面向我方美国子公司的 SCC 模块 2。”

### 触发短语

- “DPA” / “AVV” / “Auftragsverarbeitung” / “Auftragsverarbeitungsvertrag”
- “Art. 28 contract” / “Data processing agreement” / “Processor agreement”
- “Review this DPA” / “Draft a DPA” / “Redline this DPA”
- “Art. 26 arrangement” / “JCA” / “Joint controller agreement”

### 模式路由器

| 模式 | 适用场景 |
|------|------|
| **REVIEW_QUICK** | 快速检查 Art. 28(3)(a)–(h) 覆盖情况 |
| **REVIEW_NEG** | 谈判级逐条风险评分 |
| **DRAFT** | 基于所选模板层级生成新 DPA |
| **REDLINE** | 对现有草稿标注拟议修改 |
| **JOINT_CONTROLLER** | 第 26 条共同控制人安排工作流 |

## 能力摘要

| 功能 | 说明 |
|---------|-------------|
| 双语（德/英） | 两种语言质量对等 |
| 双重视角 | 控制人侧与处理人侧审查 |
| 欧盟委员会 SCC | 基于实施决定（EU）2021/915 |
| 模板库 | 3 个 DPA 层级 × 2 种语言 + JCA × 2 种语言 |
| 缺陷目录 | 常见供应商 DPA 缺陷及诊断信号 |
| 谈判备用立场 | 为争议条款预先起草的替代措辞 |
| SCC 整合 | 国际传输模块指引（模块 1–4） |
| 层级选择 | 商业/混合/严格与交易情境匹配 |
| 质量门禁 | 交付前核实 Art. 28(3) 覆盖情况 |

## 监管依据

| 文件 | 引用 |
|----------|----------|
| GDPR（欧盟通用数据保护条例）第 28 条 | 控制人—处理人关系 |
| GDPR 第 28(3)(a)–(h) 条 | 强制性的 DPA 内容 |
| GDPR 第 26 条 | 共同控制人安排 |
| 欧盟委员会实施决定（EU）2021/915 | 欧盟范围内 DPA 标准合同条款 |
| 欧盟委员会实施决定（EU）2021/914 | 国际传输 SCC（模块 1–4） |

## 许可与免责声明

本技能提供结构化的 GDPR 第 28 条/第 26 条缔约指引，不构成法律意见。经谈判达成的 DPA 和 JCA 在签署前应由合格的数据保护法律顾问审查。

依据 AGPL-3.0 许可发布。

> **质量保证：** 本技能随附 `evals/` 文件夹中的评估测试，我运行这些测试以检查其输出是否符合预期结果。

---

*作者：Oliver Schmidt-Prietz — [OneZero Legal](https://onezero.legal)*
