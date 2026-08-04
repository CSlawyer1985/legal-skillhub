---
name: ip-management-compliance
version: "3.0.0"
description: ISO 56005 知识产权全流程管控母技能。8个业务子技能+1个共享检索模块统一入口，集成tavily-search实时网络检索。深度联动 patent-examination-guide 法律适用层 与 patent-infringement-guide 侵权分析层（版本见「版本与依赖说明」），形成三级协同架构。触发词：IP管理、ISO 56005、知识产权管理、专利全流程、合规管控、IP体系。
agent_created: true
author: 佛山辉宁知识产权服务有限公司
tags: [iso-56005, ip-management, compliance, parent-skill, ip-mgmt-search]
triggerPatterns:
  - "IP管理"
  - "ISO 56005"
  - "知识产权管理"
  - "专利全流程"
  - "合规管控"
  - "IP体系"
  - "知识产权全流程"
  - "IP管理体系"
sub-skills:
  - ip-mgmt-framework
  - ip-mgmt-strategy
  - ip-mgmt-innovation
  - ip-mgmt-tools
  - ip-mgmt-examination
  - ip-mgmt-risk
  - ip-mgmt-exploitation
  - ip-mgmt-audit
  - ip-mgmt-search
---

# ISO 56005 知识产权全流程管控技能（母技能）

## 技能概述

本技能是 **ISO 56005:2020《创新管理 知识产权管理指南》** 的统一入口，采用「母技能 + 8个业务子技能 + 1个共享检索模块」的架构。

**架构说明**：本母技能负责路由协调，各子技能已独立部署，可单独使用或组合使用。

### ISO 56005:2020 八项创新原则（§0.2 Principles）

本技能体系遵循 ISO 56005:2020 引言中确立的八项创新管理原则：

| # | 原则（英文） | 中文 | 在本技能体系中的体现 |
|---|-----------|------|-------------------|
| a | Realization of value | 价值实现 | ip-mgmt-audit（评价）+ ip-mgmt-exploitation（运用） |
| b | Future-focused leaders | 面向未来的领导者 | ip-mgmt-strategy（战略）+ ip-mgmt-framework §4.3（领导承诺） |
| c | Strategic direction | 战略方向 | ip-mgmt-strategy（战略制定与实施） |
| d | Culture | 文化 | ip-mgmt-framework §4.4（文化建设） |
| e | Exploiting insights | 利用洞察 | ip-mgmt-search（检索）+ ip-mgmt-tools（分析方法） |
| f | Managing uncertainty | 管理不确定性 | ip-mgmt-risk（风险识别与缓解） |
| g | Adaptability | 适应性 | ip-mgmt-framework §4.2（系统化IP管理持续改进） |
| h | Systems approach | 系统方法 | 母技能整体架构（非临时性、系统化管理） |

### 快速路由决策树

```
用户请求 → 关键词分析 → 匹配路由
  ├─ "FTO/侵权/风险"      → ip-mgmt-risk
  ├─ "审计/价值/评估/GB/T" → ip-mgmt-audit
  ├─ "商业化/许可/转让/SEP" → ip-mgmt-exploitation
  ├─ "检索/查新/对比文件"   → ip-mgmt-search
  ├─ "OA/审查/新颖性/创造性" → ip-mgmt-examination
  ├─ "交底书/发明披露/布局"  → ip-mgmt-innovation
  ├─ "战略/路线图/KPI"      → ip-mgmt-strategy
  ├─ "框架/体系/成熟度"      → ip-mgmt-framework
  ├─ "工具/方法/分析"        → ip-mgmt-tools
  └─ 无法唯一匹配            → 列出候选+适用场景对比
```

## 技能定位

| 层级 | 技能名称 | 职责 |
|-----|---------|------|
| **母技能** | ip-management-compliance | 统一入口、智能路由、跨模块协调 |
| **检索模块** | **ip-mgmt-search** | **专利检索核心引擎（PatSeek）+ tavily-search（实时网络搜索补充）** |
| **子技能1** | ip-mgmt-framework | IP管理框架搭建（独立技能） |
| **子技能2** | ip-mgmt-strategy | IP战略制定（独立技能） |
| **子技能3** | ip-mgmt-innovation | 创新全流程IP管理（独立技能） |
| **子技能4** | ip-mgmt-tools | IP工具与方法应用（独立技能） |
| **子技能5** | ip-mgmt-examination | 专利审查合规适配（独立技能） |
| **子技能6** | ip-mgmt-risk | IP风险管理（独立技能） |
| **子技能7** | ip-mgmt-exploitation | IP商业化与利用（独立技能） |
| **子技能8** | ip-mgmt-audit | IP审计与价值评估（独立技能） |

## ISO 56005 标准映射

| 标准条款 | 子技能 | 独立技能名称 | 说明 |
|---------|-------|------------|------|
| 第4章 知识产权管理框架（IP management Framework） | ip-mgmt-framework | `ip-mgmt-framework` | 框架搭建、组织环境、职责、文化、人力资本、财务法律 |
| 第5章 知识产权战略（IP Strategy） | ip-mgmt-strategy | `ip-mgmt-strategy` | 战略制定、战略实施、与业务/创新战略协调 |
| 第6章 创新过程中的知识产权管理（IP management in the innovation process） | ip-mgmt-innovation | `ip-mgmt-innovation` | 创新五阶段IP嵌入（识别机会→创建→验证→开发→部署） |
| 附录A 发明记录和披露 | ip-mgmt-innovation | `ip-mgmt-innovation` | 员工IP管理、发明记录表、NDA保密协议 |
| 附录B 知识产权创造、获取和维护 | ip-mgmt-examination | `ip-mgmt-examination` | IPR类型、技能组合、申请策略、审计、外部专业人员选聘 |
| 附录C 知识产权检索 | ip-mgmt-search | `ip-mgmt-search` | 检索目的、检索资源、数据库选择 |
| 附录D 知识产权评价 | ip-mgmt-audit | `ip-mgmt-audit` | 价值因素（法律/经济/技术）、评价三方法 |
| 附录E 知识产权风险管理 | ip-mgmt-risk | `ip-mgmt-risk` | 风险识别（内/外部）、FTO分析五步法、风险缓解 |
| 附录F 知识产权运用 | ip-mgmt-exploitation | `ip-mgmt-exploitation` | 许可、转让、合作、分拆、投资 |

## 母技能核心逻辑

### 1. 跨模块协调

当用户请求涉及多个子技能领域时，按以下顺序调度：

```
用户请求 → 母技能分析 → 子技能路由
                         ├─→ ip-mgmt-framework（基础框架）
                         │    ↓
                         ├─→ ip-mgmt-strategy（战略层）
                         │    ↓
                         ├─→ ip-mgmt-innovation（创新嵌入）
                         │    ↓
                         ├─→ ip-mgmt-tools（工具支持）
                         │    ↓
                         ├─→ ip-mgmt-examination（合规适配）
                         │    ↓
                         ├─→ ip-mgmt-risk（风险管理）
                         │    ↓
                         ├─→ ip-mgmt-audit（审计评估）
                         │    ↓
                         └─→ ip-mgmt-exploitation（商业化利用）
```

### 2. 输出规范

所有输出均采用结构化格式：
- **管理报告**：Markdown结构化报告
- **评估矩阵**：标准化评分表格
- **流程文档**：步骤化操作指引
- **合规检查**：清单式检查表

---

## ima知识库集成模块

### 概述

本技能集成 **ima 笔记知识库**（原向量知识库已迁移至 ima），支持在执行专利分析任务时自动检索相关法规条文，为审查合规、FTO分析、价值评估等场景提供**实时法规依据**。

**核心能力**：
- 🔍 **语义检索**：基于知识库的法规条文检索
- 📋 **来源追踪**：自动标注法条来源（专利法/实施细则/审查指南）
- ⚡ **智能触发**：根据任务类型自动判断是否需要检索法规库
- 🌐 **实时网络检索补充**：通过 `tavily-search` 技能获取非专利文献信息（行业动态、技术新闻、市场报告），作为法规知识库的重要补充（详见下方 [Tavily Search 集成]）

### 触发条件

**自动触发关键词**（命中以下任一关键词即触发检索）：

| 类别 | 关键词示例 |
|------|----------|
| **法条引用** | 专利法第XX条、实施细则第XX条、审查指南第XX章 |
| **三性判断** | 新颖性、创造性、实用性、保护客体 |
| **侵权判定** | 等同侵权、全面覆盖、禁止反悔、捐献原则 |
| **评估方法** | 三步法、技术启示、预料不到、协同效应 |
| **专利类型** | 实用新型客体、计算机程序、智力活动、疾病诊断 |
| **文件要求** | 说明书充分、权利要求清楚、得到支持 |

### 调用方式

#### 方式1：自动触发（推荐）

当用户请求涉及上述触发关键词时，技能自动执行：

```
用户：三步法判断创造性的具体步骤是什么？
         ↓
技能识别关键词：三步法、创造性
         ↓
自动触发 知识库检索
         ↓
输出：法条原文 + 审查解读
```

#### 方式2：手动触发

用户可通过以下方式显式调用：

| 调用方式 | 指令示例 |
|---------|---------|
| **直接询问** | "检索专利法第二十二条关于新颖性的规定" |
| **指令触发** | "请检索实用新型保护客体的判断标准" |

#### 方式3：子技能联动

子技能在执行特定任务时自动调用：

| 子技能 | 联动场景 | 典型查询 |
|-------|---------|---------|
| `ip-mgmt-examination` | 审查标准查询 | "实用新型客体 判断标准 三要素" |
| `ip-mgmt-risk` | FTO法规支持 | "等同侵权 全面覆盖原则 第六十五条" |
| `ip-mgmt-audit` | 价值评估法规 | "高质量专利评价 技术创新高度 评价维度" |
| `ip-mgmt-innovation` | 申请文件要求 | "说明书充分公开 权利要求清楚" |

### 检索脚本使用

法规检索通过 ima知识库 MCP 直连方式实现（详见 ima-mcp 联动配置）


## 版本与依赖说明

<!-- VERSION_TABLE_START -->
### 版本映射

| 技能 | 当前版本 | 最后更新 |
|-----|---------|---------|
| ip-management-compliance（母技能） | v3.0.0 | 2026-07-16 |
| ip-mgmt-framework | v3.0.0 | 2026-07-16 |
| ip-mgmt-strategy | v3.0.0 | 2026-07-16 |
| ip-mgmt-innovation | v3.0.0 | 2026-07-16 |
| ip-mgmt-tools | v3.0.0 | 2026-07-16 |
| ip-mgmt-examination | v3.0.0 | 2026-07-16 |
| ip-mgmt-risk | v3.0.0 | 2026-07-16 |
| ip-mgmt-exploitation | v3.0.0 | 2026-07-16 |
| ip-mgmt-audit | v3.0.0 | 2026-07-16 |
| ip-mgmt-search | v3.1.0 | 2026-07-16 |
<!-- VERSION_TABLE_END -->

### 运行时依赖

| 依赖技能 | 依赖类型 | 最低版本(能力地板) | 最后核验 | 说明 |
|---------|---------|----------------|---------|------|
| `patent-examination-guide` | 运行时 | ≥V1.13 | 2026-07-16 | 法律适用层：审查标准、法条适用、判断方法 |
| `patent-infringement-guide` | 可选联动 | ≥V3.13 | 2026-07-16 | 侵权分析层：侵权判定、规避设计 |
| `patent-navigation` | 可选联动（路由级） | ≥v1.0.0 | 2026-07-30 | 导航规划层：区域/产业/企业/研发/人才/服务六大专项导航（GB/T 39551） |

---

## 外部技能联动与共享基础设施

**三级协同架构**（全部配备 scripts/skill_linkage.py）：
- patent-examination-guide（法律适用层）：审查标准、法条适用、判断方法
- ip-management-compliance（体系管控层）：ISO体系、流程、制度、KPI
- patent-infringement-guide（侵权分析层）：侵权判定、规避设计

**路由级联动**（无 skill_linkage.py 数据共享，属路由+决策输入关系）：
- patent-navigation（导航规划层）：母技能路由表「专利导航」入口指向该技能；其导航结论作为 ip-mgmt-strategy / ip-mgmt-innovation 的决策输入，并向下游衔接 ip-mgmt-audit（经济价值量化，GB/T 42748-2023）与 ip-mgmt-exploitation（商业化/许可/并购）。

**共享基础设施**：ima 知识库（中国大陆知识产权（IP专用，337条，~965MB））、联动规则 mcp-config/linkage-rules.yaml。

**子技能×审查指南联动矩阵**：

| IP管理子技能 | 审查指南子技能 | 联动场景 |
|------------|-------------|---------|
| ip-mgmt-examination | patent-exam-substantive | 三性评估/OA答复（双向） |
| ip-mgmt-risk | patent-exam-reexamination | 无效宣告应对（双向） |
| ip-mgmt-innovation | patent-exam-substantive | AI/计算机可专利性 |
| ip-mgmt-audit | patent-exam-substantive | 创造性标准 价值评分 |
| ip-mgmt-exploitation | patent-exam-procedures | 开放许可/期限补偿 |
| ip-mgmt-strategy | patent-exam-pct-national | 国际战略制定 |

## 高价值专利申请前评估路由（整合版）

### 核心模块路由表

| HPA模块 | 功能说明 | 路由目标子技能 | ISO依据 |
|---------|---------|---------------|---------|
| **模块1** 专利发明披露与技术交底书生成 | 基础信息库自动调用+智能解析+分领域预制模板 | `ip-mgmt-innovation` | Annex A, Annex B, §6.3 |
| **模块2** 创新全流程专利检索与分析 | 5阶段精准检索+检索式智能生成+穷尽性自动校验 | `ip-mgmt-search` | Annex C, §6 |
| **模块3** 专利可专利性（三性）全流程评估 | 预评估/全量评估/终评三级+标准化评述模板 | `ip-mgmt-examination` | Annex C, Annex D |
| **模块4** 专利FTO侵权风险分析 | ISO标准化7步流程+规避设计指引 | `ip-mgmt-risk` | Annex E |
| **模块5** 专利稳定性与无效分析 | 稳定性前置评估+无效风险应对+证据组合策略 | `ip-mgmt-risk` | Annex D, Annex E |
| **模块6** 专利价值评价与高价值专利培育 | ISO 56005三维度量化评价+创新全流程绑定培育 | `ip-mgmt-audit` | Annex D, Annex F |
| **模块7** 专利管理架构与合规职责适配 | 职责适配+合规管控+能力建设 | `ip-mgmt-framework` | §4.3, §4.4, §4.5 |
| **模块8** 流程适配与效率优化 | 创新阶段自动识别+批量处理+工作流集成 | `ip-mgmt-innovation` | §6.1 |
| **模块9** Word文档输出功能 | 基于模板的Word报告生成 | `ip-mgmt-tools` | — |
| **模块10** 一键式专利申请前评估流水线 | 全流程自动化串联 | `ip-mgmt-innovation` | — |
| **模块11** 实用新型专利保护客体专项评估 | 三要素判断框架+计算机程序/材料/食品客体规则 | `ip-mgmt-examination` | — |
| **模块12** 外观设计专利申请专项指引 | GUI外观设计+合案申请+产品名称规范 | `ip-mgmt-examination` | — |

### 快速路由指南

| 任务类型 | 关键词 | 路由子技能 |
|---------|-------|-----------|
| 技术交底书 | "交底书"、"发明披露"、"技术方案描述" | `ip-mgmt-innovation` |
| 专利检索 | "检索"、"对比文件"、"新颖性检索" | **`ip-mgmt-search`（实际执行引擎）** |
| 检索方法指导 | "检索策略"、"检索式构建"、"检索规范" | `ip-mgmt-tools`（方法论指南） |
| 三性评估 | "新颖性"、"创造性"、"实用性"、"可专利性" | `ip-mgmt-examination` |
| FTO分析 | "FTO"、"侵权风险"、"自由实施" | `ip-mgmt-risk` |
| 无效分析 | "稳定性"、"无效"、"无效分析"、"专利稳定性" | `ip-mgmt-risk` |
| 价值评估 | "价值评价"、"高价值培育"、"GB/T 42748-2023" | `ip-mgmt-audit` |
| 专利导航 | "专利导航"、"区域规划"、"产业规划"、"研发导航"、"人才管理导航"、"GB/T 39551" | `patent-navigation` |
| 管理架构 | "IP架构"、"合规职责"、"RACI" | `ip-mgmt-framework` |
| 一键流水线 | "全流程评估"、"一键评估" | `ip-mgmt-innovation` |
| Word输出 | "生成报告"、"Word"、"文档输出" | `ip-mgmt-tools` |
| 实用新型客体 | "实用新型客体"、"保护客体" | `ip-mgmt-examination` |
| 外观设计 | "外观设计"、"GUI"、"合案" | `ip-mgmt-examination` |
| 技术完善 | "技术完善"、"培育建议"、"实施例完善" | `ip-mgmt-innovation` |
| 权利要求布局 | "权利要求布局"、"国际申请"、"PCT" | `ip-mgmt-innovation` |
| 创造性评估 | "创造性评估"、"三步法"、"技术启示" | `ip-mgmt-examination` |
| 实用性审查 | "实用性"、"可实施性"、"积极效果" | `ip-mgmt-examination` |

### 核心铁律（最高优先级）

> **⚠️ 绝对红线：对比文件必须真实检索，禁止臆造**
>
> 所有专利检索与分析任务，**检索出的每一篇对比文件/现有技术必须真实存在、可验证**。

| 规则类型 | 具体要求 | 违规处理 |
|---------|---------|---------|
| **信息完整性** | 每篇对比文件必须包含：申请号、专利号、专利类型、专利名称、申请人、权利人、申请日、公开/公告日、IPC分类号、法律状态、原文链接 | 缺失任一字段视为不合格 |
| **来源真实性** | 对比文件必须来自官方数据库（CNIPA/EPO/WIPO/USPTO/JPO）或可验证的商业数据库 | 不得使用无法验证的来源 |
| **内容可验证** | 对比文件的技术信息必须与原文一致 | 不得臆造或模糊描述 |
| **禁止臆造** | **绝对禁止**生成不存在的专利号、申请人、公开日等技术信息 | 一经发现，本次任务结论全部作废 |

---

## 执行优先级

> **适用场景说明**：以下优先级适用于**新建 IP 管理体系时的初始化顺序规划**。对于日常单一任务场景（如仅查询一个价值评估），按需直接调用对应子技能即可，无需从 P0 开始逐个执行。

| 优先级 | 子技能 | 适用场景 |
|-------|-------|---------|
| P0（体系根基） | ip-mgmt-framework、ip-mgmt-risk、ip-mgmt-examination | 新建 IP 管理体系时，框架、风险、合规三者必须优先建立 |
| P1（核心支撑） | ip-mgmt-strategy、ip-mgmt-innovation、ip-mgmt-audit | 在 P0 基础上推进战略规划、创新嵌入与审计评价 |
| P2（按需执行） | ip-mgmt-tools、ip-mgmt-exploitation | 日常专项任务或商业化运营阶段按需调用 |

## 子技能快速索引

### ip-mgmt-framework
- **核心功能**：组织环境分析（§4.1）、系统化IP管理建立（§4.2）、IP管理职责与领导承诺（§4.3）、文化建设（§4.4）、人力资本（§4.5）、财务考量（§4.6）、法律考量（§4.7）

### ip-mgmt-strategy
- **核心功能**：战略制定（§5.2）、战略实施（§5.3）、战略目标设定（§5.1）

### ip-mgmt-innovation
- **核心功能**：创新五阶段IP嵌入（§6.2-6.6）、可专利性评估、专利布局规划

### ip-mgmt-tools
- **核心功能**：工具选择决策树、专利信息分析方法（技术生命周期/功效矩阵/引证分析）、文档管理体系

### ip-mgmt-examination
- **核心功能**：申请文件合规检查清单、OA答复策略、创造性/实用性审查细则

### ip-mgmt-risk
- **核心功能**：FTO 7步流程、风险评估矩阵、侵权预警机制、专利无效分析
- **Tavily Search 集成**：在FTO分析的"检索与清洗处理"步骤中，使用 `tavily-search` 补充非专利文献检索（行业动态、技术新闻、市场报告等）

### ip-mgmt-exploitation
- **核心功能**：商业化模式分析、许可定价方法、SEP管理

---

## Tavily Search + 模板与参考

**Tavily Search**：通过 tavily-search 技能补充非专利文献检索，作为FTO中检索步骤的首选工具。结果标注URL，不可作为侵权比对唯一依据。

**模板资源**（templates/）：专利申请文件合规检查表、无效分析报告模板、IP风险评估矩阵、许可协议框架、战略制定模板；（assets/word-templates/）价值评价报告模板.docx。

**参考资料**（references/）：ISO 56005 原文解读/审查指南解读。

## 🔴 关键检查点（母技能调度层）

| 检查点 | 触发时机 | 审核内容 |
|--------|---------|---------|
| **子技能路由确认** | 用户请求到达、自动路由判定后 | 路由判定是否匹配用户意图；🔴 若路由判定不唯一，必须列出候选子技能并要求用户确认，不得自行假定路由目标；🔴 路由确认未通过前不得继续后续处理 |
| **跨技能联动一致性** | 多子技能协同输出后 | 各子技能输出之间的数据一致性（如同一专利在不同模块中评估结论不矛盾） |
| **检索结果交叉验证** | 检索返回>3条结果时 | 验证检索结果的法条版本(2020修正/2023审查指南/2026修改)与时效性 |
| **外部技能调用前置确认** | 触发patent-examination-guide或patent-infringement-guide联动前 | 确认调用方向、数据格式、预期输出与母技能调度一致 |

---

## 失败模式与恢复策略（调度层）

| 触发条件 | 一线修复 | 仍失败则 |
|---------|---------|---------|
| 子技能路由无法唯一判定（多子技能命中） | 列出候选子技能+适用场景对比，要求用户选择 | 默认加载最相关子技能，标注"可切换至X" |
| 子技能执行中调用外部检索无结果 | 扩展检索关键词、切换检索数据库 | 标注"检索无结果"，基于内置知识库继续 |
| 子技能联动链条中断（下游子技能加载失败） | 跳过失败子技能，输出部分结果+缺失说明 | 标注"部分模块不可用，结论可能不完整" |
| 知识库服务不可用 | 回退至静态引用 | 回退到关键词匹配检索模式 |
| 用户请求横跨3个以上子技能领域 | 输出"多领域综合分析"框架，明确各子技能输出边界 | 标注"部分交叉领域结论需人工综合判断" |
| 多个同级子技能对同一问题给出矛盾建议 | 标注矛盾点+各技能的依据法条/条款，列出分歧矩阵 | 升级为"需专家裁决"并建议人工复核 |

---

## 反例与注意事项

### P0 致命禁止

| # | 禁止操作 | 原因 |
|---|---------|------|
| 1 | **跨子技能输出结论矛盾时不标注不一致** | 矛盾结论交付客户将严重损害专业可信度 |
| 2 | **母技能绕过子技能直接给出专业结论** | 子技能封装了领域最佳实践，绕过等于放弃领域知识 |

### P1 质量禁止

| # | 禁止操作 |
|---|---------|
| 3 | 用户请求明确属于某子技能范畴时不自动路由而要求用户手动选择 |
| 4 | 输出子技能结果时不做母技能层的一致性校验 |
| 5 | RAG检索结果不标注来源和检索时间 |
