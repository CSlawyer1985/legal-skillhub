---
name: eu-ai-act-obligations-oliver-schmidt-prietz
description: |
  基于角色 + 风险层级映射欧盟 AI 法案的全部法律义务，生成带 RACI 分配和实施优先级的可操作合规矩阵。当用户要求"映射 AI 法案义务"、"检查我们在 AI 法案下需要做什么"、"创建合规检查清单"、"检查部署者义务"、"评估提供者职责"，或提及 AI 法案下的第 26 条、第 16-17 条、AI 素养第 4 条、DPIA、基本权利评估或"Pflichtenkatalog"时，应使用本技能。
metadata:
  author: Oliver Schmidt-Prietz
  license: AGPL-3.0
  version: 2026.06.05
---

# 欧盟 AI 法案义务映射器（EU AI Act Obligations Mapper）

基于 AI 法案（《条例（EU）2024/1689》）下的**角色 + 风险层级**映射全部法律义务，生成带 RACI 分配和实施优先级的可操作合规矩阵。

## 免责声明（会话开始时显示，不阻塞）

> **重要提示：** 本技能基于欧盟 AI 法案（《条例（EU）2024/1689》）提供结构化的 AI 法案义务指引。不构成法律意见。合规措施的实施应涉及合格的法律顾问和相关技术专家。高风险义务的生效日期反映了 AI Omnibus 2026 的推迟（附件 III：2027 年 12 月 2 日；附件 I：2028 年 8 月 2 日）。

---

## 何时进行网络搜索

**激活时——搜索：**
```
EU AI Act harmonized standards EN ISO implementing requirements [current year]
EU AI Act conformity assessment notified bodies guidance [current year]
```

**管理体系——搜索：**
```
ISO 42001 AI management system alignment EU AI Act [current year]
EU AI Act quality management system requirements guidance
```

**国内规则——搜索：**
```
[user's jurisdiction] AI Act national implementation measures [current year]
[user's jurisdiction] AI Act supervisory authority designation
```

**合格评定——搜索：**
```
EU AI Act conformity assessment procedures latest guidance
EU AI Act notified body designations [current year]
```

---

## 工作流：一次一个问题

### 阶段 1：输入语境（知悉语境的适应性信息采集）

**第 1 步——语境检测（始终首先）：**

> "让我们映射你的 AI Act 义务。"
>
> 如果你已完成先前的 AI 法案评估（风险分类、角色确定或快速分诊），请粘贴下面的"评估语境"块。否则，用你自己的话描述你的情况。

**第 2 步——覆盖分析（内部——不向用户显示此表）：**

将语境块或叙述映射到以下 6 个字段：

| # | 字段 | 语境块中的来源 | 回退 |
|---|-------|----------------------|----------|
| 1 | 风险分类 | "Classification:"（分类：）行 | 询问 |
| 2 | 组织角色 | "Role:"（角色：）行 | 询问 |
| 3 | 组织规模 | "Org Size:"（组织规模：）行 | 询问 |
| 4 | 行业 | "Sector:"（行业：）行 | 询问 |
| 5 | 法域 | "Jurisdiction:"（法域：）行 | 询问 |
| 6 | 现有框架 | 不在语境块中 | 始终询问 |

如果风险层级尚未分类 → 先运行风险层级分类（第 3(1) 条下的 AI 系统测试；被禁止 / 高风险 / GPAI / 有限 / 最低）。
如果角色尚未确定 → 先确定（第 3 条和第 25 条下的提供者 / 部署者 / 进口者 / 分销者）。

**第 3 步——适应性追问：**

- 如提供了语境块 → 确认提取的字段，然后仅询问缺口。字段 1-5 通常已覆盖；只有字段 6（现有框架）需要询问。
- 如提供叙述 → 提取已覆盖的内容，以单一分组问题询问剩余缺口。
- 如提供的信息极少 → 在单次提示中询问全部缺失字段，以会话方式分组。

现有合规状态始终要询问，因为它是语境块中未携带的新信息。以会话方式提出：

> "还有一件事——你们已经具备哪些合规基础？（风险管理、数据质量、QMS、DPIA、事件报告、AI 素养培训，还是从零开始）"

信息采集最多 2 轮交互。如某字段仍不明确，标记为 `[UNCLEAR — proceeding with cautious assumptions]`（不明确——按谨慎假设继续）。

---

### 阶段 2：义务映射

基于角色 + 风险层级，加载适用的义务集。

阅读相关参考文件：

**部署者 + 高风险** → 阅读 [references/high-risk-deployer-obligations.md](references/high-risk-deployer-obligations.md)
**提供者 + 高风险** → 阅读 [references/high-risk-provider-obligations.md](references/high-risk-provider-obligations.md)
**任何角色 + 低风险/最低** → 阅读 [references/low-risk-obligations.md](references/low-risk-obligations.md)
**非高风险附件 III（第 6(3) 条例外）** → 阅读 [references/art6-4-documentation.md](references/art6-4-documentation.md)
**GPAI 提供者** → 阅读 [references/gpai-obligations.md](references/gpai-obligations.md)
**触发 FRIA 的部署者** → 阅读 [references/fria-template.md](references/fria-template.md) 了解第 27 条 FRIA 方法论和可填写模板
**提供者合格评定** → 阅读 [references/conformity-assessment.md](references/conformity-assessment.md) 了解第 43 条路径选择、欧盟符合性声明和 CE 标志
**提供者上市后监测** → 阅读 [references/post-market-monitoring.md](references/post-market-monitoring.md) 了解第 72 条监测系统设计和严重事件报告
**欧盟数据库注册** → 阅读 [references/eu-database-registration.md](references/eu-database-registration.md) 了解第 49 条注册流程（提供者和部署者路径）
**所有角色** → 第 4 条 AI 能力义务始终适用

**义务数量预览：**

> "基于你作为 **[风险层级]** 系统的 **[角色]** 身份，你在 K 个类别中有 **N 项义务**。我将分 4 批逐一说明。"

**分批评估（以 4 批取代逐义务提问）：**

按类别分组呈现义务。对每批，显示该类别全部义务的表格，并要求用户一次性回应整批：

| 批次 | 类别 | 典型义务 |
|-------|----------|-------------------|
| 1 | 技术措施 | 按操作说明使用、监控、输入数据、日志保留、数据质量 |
| 2 | 组织措施 | 监督人员、告知受影响者、员工信息、AI 能力、事件报告、注册、配合机关 |
| 3 | 管理体系 | 风险管理、数据质量管理、QMS、上市后监测 |
| 4 | 影响评估 | DPIA、FRIA |

对每批呈现表格：

> **第 [X] 批，共 4 批：[类别]**
>
> | # | 义务 | 法律依据 | 优先级 | 状态 |
> |---|-----------|-------------|----------|--------|
> | 1 | [义务] | [条款] | [立即/短期/持续] | 已就位 / 部分处理 / 尚未处理 |
>
> "请对每项义务表明：已就位、部分处理或尚未处理。你只需回复编号即可（例如'1、3 = 已就位；2、4 = 部分；5 = 尚未处理'）。"

每批之后显示**进度指示**："第 [X] 批（共 4 批）完成。剩余 [N] 项义务。"

**智能默认值：** 如用户在阶段 1 表示"从零开始"，将所有义务默认标记为"尚未处理"并确认："由于你从零开始，我已将所有义务标记为尚未处理。有例外吗？"

目标：4-5 轮交互，而非 20 多轮。

标记优先级等级：**关键时限义务优先**（例如第 26(6) 条 6 个月日志保留必须在第一天即投入运行）。

#### GDPR 交叉引用检查

阅读 [references/gdpr-crosswalk.md](references/gdpr-crosswalk.md)。

在相关义务节点，建议现有的 GDPR 技能：

| 义务 | 触发 | 建议 |
|-----------|---------|------------|
| 第 26(9) 条 DPIA | 高风险部署者 | "进行 DPIA，纳入提供者关于系统能力和局限的第 13 条信息" |
| 第 26(11) 条 告知受影响者 | 部署者透明度 | "准备一份合并的 AI 法案/GDPR 透明度通知，涵盖第 26(11) 条和 GDPR 第 13/14 条" |
| 第 10 条 数据治理 | 提供者数据质量 | "进行数据清单审查，将 AI 训练数据与 GDPR 数据质量和最小化原则对照映射" |
| 第 26(7) 条 员工信息 | 工作场所 AI | "准备结合第 26(7) 条和 GDPR 第 13/14 条要求的员工 AI 透明度文件" |
| 第 26(5) 条 严重事件 | 检测到事件 | "建立双重事件报告程序，同时覆盖 AI 法案（第 73 条）和 GDPR（第 33/34 条）的时限" |
| 个人数据处理 | 任何处理个人数据的 AI | "审查你的 GDPR 第 28 条处理者协议，纳入 AI 法案合作条款（第 25(2) 条）" |

### 义务优先级决策树

```
         ┌─────────────────────────┐
         │ ROLE + RISK TIER        │
         └────────────┬────────────┘
                      │
    ┌─────────────────┼──────────────────┐
    │                 │                  │
    ▼                 ▼                  ▼
┌─────────┐   ┌──────────────┐   ┌──────────────┐
│ PROVIDER│   │   DEPLOYER   │   │ GPAI MODEL   │
│         │   │              │   │ PROVIDER     │
└────┬────┘   └──────┬───────┘   └──────┬───────┘
     │               │                  │
     ▼               ▼                  ▼
 High-Risk?      High-Risk?        Systemic Risk?
 ├─ YES:         ├─ YES:           ├─ YES:
 │ Art. 8-17     │ Art. 26         │ Art. 53 + 55
 │ Art. 17 QMS   │ Art. 27 FRIA    ├─ NO:
 │ Art. 9 Risk   │ Art. 26(9) DPIA │ Art. 53
 │ Art. 43 CA    │ Art. 49(3) Reg  └────────────
 │ Art. 49 Reg   └────────────
 │               ├─ NO (Art. 50):
 ├─ NO           │ Art. 50 only
 │ (Art. 50):    ├─ NO (Minimal):
 │ Art. 50       │ Art. 4 only
 │ +Art. 6(4)    └────────────
 │ if Annex III
 └────────────

 ALL ROLES: Art. 4 AI Competence (always applies)
```

已完成的义务映射示例见 [references/case-studies.md](references/case-studies.md)。

---

### 阶段 3：实施路线图

按时间线对义务分组：

**1. 立即（部署前 / 如已部署则已逾期）：**
- 按操作说明使用系统（第 26(1) 条）
- 监控系统就位（第 26(5) 条）
- 指派合格的监督人员（第 26(2) 条）
- 日志保留机制投入运行（第 26(6) 条）
- AI 能力措施（第 4 条）

**2. 短期（部署后 3 个月内）：**
- 风险管理系统投入运行（第 9 条）
- 数据质量管理（第 10 条）
- 在欧盟数据库中注册（第 49 条）
- 完成 DPIA（第 26(9) 条）
- 如需要完成 FRIA（第 27 条）
- 员工信息（第 26(7) 条）

**3. 持续（不间断）：**
- 系统监控（第 26(5) 条）
- 日志记录和记录保存（第 12 条、第 26(6) 条）
- 事件报告（第 26(5) 条第三句）
- 配合机关（第 26(12) 条）
- 上市后监测数据贡献

**4. 定期（固定间隔）：**
- 风险重新评估（第 9 条——建议每年）
- AI 能力培训更新（第 4 条）
- 文件审查与更新
- 测试和验证（第 15 条）

详细要求见 [references/technical-measures.md](references/technical-measures.md)、[references/organizational-measures.md](references/organizational-measures.md) 和 [references/management-systems.md](references/management-systems.md)。

完整的合规时间线（含季度行动日历、按组织规模的资源估算和活动间依赖映射）参见 [references/compliance-roadmap.md](references/compliance-roadmap.md)。

---

### 阶段 4：义务矩阵输出

```markdown
## AI Act Compliance Obligations Matrix
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Role: [Role]  |  Risk Tier: [Tier]  |  Basis: [legal basis]
Organization: [name]  |  Date: [date]

### Technical Measures
| # | Obligation | Legal Basis | Priority | Status | RACI | Effort |
|---|-----------|-------------|----------|--------|------|--------|
| 1 | Use system per operating instructions | Art. 26(1) | Immediate | [ ] | IT=R, Legal=A | Low |
| 2 | Monitor system operation | Art. 26(5) | Immediate | [ ] | IT=R, Compliance=A | Medium |
| 3 | Ensure input data relevance | Art. 26(4) | Immediate | [ ] | IT=R, Business=A | Medium |
| 4 | Retain auto-generated logs (6 months) | Art. 26(6) | Immediate | [ ] | IT=R, Legal=A | Low |
| 5 | Data quality management | Art. 10 | Short-term | [ ] | IT=R, Data=A | High |

### Organizational Measures
| # | Obligation | Legal Basis | Priority | Status | RACI | Effort |
|---|-----------|-------------|----------|--------|------|--------|
| 1 | Assign qualified oversight persons | Art. 26(2) | Immediate | [ ] | HR=R, Legal=A | Medium |
| 2 | Inform affected persons | Art. 26(11) | Immediate | [ ] | Legal=R, Comms=A | Medium |
| 3 | Inform employees/works council | Art. 26(7) | Short-term | [ ] | HR=R, Legal=A | Medium |
| 4 | AI competence training | Art. 4 | Short-term | [ ] | HR=R, Mgmt=A | Medium |
| 5 | Incident reporting procedure | Art. 26(5) s.3 | Immediate | [ ] | Legal=R, IT=C | High |
| 6 | Register use in EU database | Art. 49(3) | Short-term | [ ] | Legal=R | Low |
| 7 | Cooperate with authorities | Art. 26(12) | Ongoing | [ ] | Legal=R, Mgmt=A | Low |

### Management Systems Required
| System | Legal Basis | Scope | Existing? |
|--------|------------|-------|-----------|
| Risk Management | Art. 9 | Continuous lifecycle risk assessment | [ ] |
| Data Quality Mgmt | Art. 10 | Training/validation/test data governance | [ ] |
| Quality Management | Art. 17 | Processes, procedures, compliance concept | [ ] |
| Post-Market Monitoring | Art. 72 | Monitoring throughout lifetime | [ ] |

### Impact Assessments Required
| Assessment | Legal Basis | When | Status |
|-----------|------------|------|--------|
| DPIA | Art. 26(9) + Art. 35 GDPR | Before deployment | [ ] |
| Fundamental Rights Assessment | Art. 27 | Before deployment (public bodies + certain private) | [ ] |

### GDPR Cross-References
| AI Act Obligation | GDPR Parallel | Recommended Action |
|------------------|---------------|----------------|
| Art. 26(9) DPIA | Art. 35 GDPR | Perform DPIA per Art. 35 GDPR incorporating Art. 13 information |
| Art. 26(11) inform persons | Art. 13/14 GDPR | Draft combined AI Act + GDPR transparency notice |
| Art. 10 data governance | Art. 25 GDPR (DPbD) | Conduct data inventory and governance review |
| Art. 26(7) employee info | Art. 13/14 GDPR | Prepare employee AI transparency documentation |
| Incident reporting | Art. 33/34 GDPR | Establish dual AI Act/GDPR incident reporting procedure |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY:
TOTAL: [X] obligations | [Y] immediate | [Z] require legal judgment
Timeline: [X] already compliant | [Y] gaps identified | [Z] not yet assessed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ASSESSMENT CONTEXT (paste into next skill)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
System: [name]
Classification: [risk tier]
Basis: [legal basis]
Role: [role]
Quasi-Provider: [risk level]
Sector: [sector]
Jurisdiction: [list]
Org Size: [size]
Art. 50: [applicable triggers]
GPAI: [yes/no, systemic risk]

NEXT STEPS:
→ Generate formal assessment documentation (classification rationale + obligation matrix)
→ Address [Y] immediate gaps as priority
→ Establish management systems within [timeline]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 关键提醒

1. **第 4 条 AI 能力适用于所有角色和所有风险层级**——即使是最低风险系统
2. **第 26(6) 条日志保留（6 个月）**——必须在部署第一天即就位
3. **第 26(9) 条 DPIA**——必须在部署**之前**完成，而非之后
4. **第 27 条 FRIA**——公共机构、提供公共服务的私营实体，以及保险风险评估（附件 III 第 5(b) 项）和社会福利资格（附件 III 第 5(c) 项）系统的部署者需要
5. **第 26(5) 条事件报告**——"毫不迟延"向提供者和机关报告
6. **中小企业比例原则**——第 62 条要求机关考虑中小企业能力
7. **过渡期各不相同**——被禁止做法（2025 年 2 月）、GPAI（2025 年 8 月）、高风险附件 III（**2027 年 12 月**——Omnibus 自 2026 年 8 月推迟）、高风险附件 I（**2028 年 8 月**——Omnibus 自 2027 年 8 月推迟）。AI Omnibus 是进行中的立法文件；依赖这些日期前，请通过网络搜索核实推迟的当前状态。
8. **搜索最新协调标准**——技术实施标准仍在制定中
9. **执法敞口**——排列缺口优先级时考虑罚则层级：第 5 条被禁止做法违规最高 3500 万欧元 / 全球年营业额的 7%，其他侵权为 1500 万欧元 / 3%（第 99 条）。执法通过国家市场监管机关进行，GPAI 则由 AI 办公室负责。
10. **法域特定义务**——参见 [references/regulatory-overlays.md](references/regulatory-overlays.md)，了解在 AI 法案义务之外适用的各国雇佣法、金融监管机构和数据保护叠加要求
11. **合规时间线与资源**——参见 [references/compliance-roadmap.md](references/compliance-roadmap.md)，了解季度行动日历、按组织规模的资源估算和分阶段合规路线图模板

## 欧盟 AI 法案套件的一部分

本技能可独立使用，但设计为与我的其他欧盟 AI 法案技能互锁——可单独安装任一技能，或组合使用以实现端到端工作流：

- **EU AI Act Quick Assessment**（快速评估）——15-25 分钟初步分诊
- **EU AI Act System Classifier**（系统分类器）——跨越全部五个层级的风险层级分类
- **EU AI Act High-Risk Classifier**（高风险分类器）——附件 I / 附件 III 深度评估
- **EU AI Act Role Determination**（角色确定）——提供者 / 部署者 / 进口者 / 分销者（含第 25 条）
- **EU AI Act Examination Report Generator**（检查报告生成器）——审计就绪的合规报告
- **EU AI Act Knowledge Base**（知识库）——针对法案 + 欧盟委员会指南的问答

每个都作为独立技能提供——只安装你需要的。
