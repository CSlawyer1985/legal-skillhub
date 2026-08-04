---
name: eu-ai-act-triage-oliver-schmidt-prietz
description: |
  用于欧盟 AI 法案初步分类和合规评估的快速 15-25 分钟分诊。当用户要求"做一次快速的 AI 法案评估"、"检查 AI 法案是否适用于我们"、"运行初步分类"、"做 AI 法案分诊"、"快速检查"、"初步评估"、"Schnellprüfung"、"Ersteinschätzung"，或在投入完整分析前需要快速初始评估时，应使用本技能。
metadata:
  author: Oliver Schmidt-Prietz
  license: AGPL-3.0
  version: 2026.06.05
---

# 欧盟 AI 法案快速评估（EU AI Act Quick Assessment）

用于 AI 法案初步分类和合规评估的快速分诊工具（15-25 分钟）。生成初步输出，并路由到详细技能进行完整分析。

## 免责声明（会话开始时显示，不阻塞）

> **重要提示：** 这是基于《条例（EU）2024/1689》的初步 AI 法案评估，为快速分诊而设计。不构成法律意见，也不替代完整评估——请通过完整风险层级分类、在高风险分支可能成立时的第 6 条高风险深度分析、角色确定、义务映射、正式报告和合格法律顾问验证结果。高风险义务的生效日期反映了 AI Omnibus 2026 的推迟（附件 III：2027 年 12 月 2 日；附件 I：2028 年 8 月 2 日）。

---

## 何时进行网络搜索

**激活时——搜索：**
```
EU AI Act latest enforcement updates [current year]
EU AI Act Commission guidelines status [current year]
```

---

## 快速评估工作流

### 阶段 1：快速语境（适应性 2 批流程）

通过会话式 2 批方式收集语境。最多 2 轮交互——用户详细时 1 轮，仍有缺口时 2 轮。

#### 第 1 批：基本问题（始终询问）

以自然、会话式的欢迎语呈现这三个问题：

> **让我们开始快速欧盟 AI 法案评估。**
>
> 你可以用自己的话回答——一个短段落、要点列表都可以。只有需要更多细节时我才会追问。
>
> **1. 该 AI 系统做什么？**（2-3 句：它做什么、在高层面上如何工作、产出什么输出）
>
> **2. 系统部署在哪里？**（供参考：欧盟/欧洲经济区市场、瑞士但触及欧盟、欧盟之外但输出在欧盟使用，或无欧盟联系）
>
> **3. 你的组织与它是什么关系？**（供参考：内部开发、购买/获得许可、修改/微调、分销/进口，或为收购进行评估）

#### 覆盖分析（内部——不向用户显示）

用户回应第 1 批后，静默检查其回答是否覆盖全部 8 个必填字段。提取要慷慨——例如"德国中小企业"同时覆盖法域（DE）和组织规模（中型）；"简历筛选工具"覆盖行业（人力资源/雇佣）和受影响主体（员工/求职者）。

| # | 字段 | 从何处提取 |
|---|-------|-------------|
| 1 | 系统描述 | 第 1 批问题 1 |
| 2 | 部署语境 | 第 1 批问题 2 |
| 3 | 组织角色 | 第 1 批问题 3 |
| 4 | 行业 | 通常可从系统描述推断 |
| 5 | 受影响主体 | 通常可从系统描述 + 行业推断 |
| 6 | 修改情况 | 通常可从组织角色推断 |
| 7 | 组织规模 | 有时在语境中提及 |
| 8 | 法域 | 通常可从部署语境推断 |

将每个字段标记为：**已覆盖** / **部分覆盖** / **未覆盖**。

#### 第 2 批：适应性追问（仅在有缺口时）

- **8 个字段全部覆盖** → 跳过第 2 批。简要确认你的提取结果，进入阶段 2。
- **仍有缺口** → 发送一条仅覆盖缺失或部分覆盖字段的追问消息，以会话方式表述。不要重新询问已回答的内容。
- **部分覆盖的字段** → 使用确认提示，而非完整重问。示例："你提到了医疗保健——具体是医疗器械行业吗？"
- **不明确的字段** → 如第 2 批后仍无法解决，标记为 `[UNCLEAR — proceeding with cautious assumptions]`（不明确——按谨慎假设继续）并注明所作的假设。

示例追问（如行业、规模、法域缺失）：
> **只需再补充几个细节来完善全貌：**
>
> - 这属于哪个行业？（例如医疗保健、金融服务、人力资源/雇佣、教育、公共行政、其他）
> - 你的组织大约多大？（例如 50 名员工以下、50-249 名，或 250 名以上）
> - 涉及哪个或哪些欧盟/欧洲经济区国家？

#### 信息规范化（内部——在阶段 2 之前）

进入阶段 2 前，将所有收集的信息规范化为结构化 8 字段格式，使阶段 2 的门禁序列可以一致地引用字段：

1. **系统描述**——自由文本
2. **部署语境**——以下之一：欧盟/欧洲经济区市场、瑞士但触及欧盟、欧盟之外但输出在欧盟使用、无欧盟联系
3. **组织角色**——以下之一：内部开发、购买/获得许可、修改/微调、分销/进口、评估中
4. **行业**——映射为：医疗保健/医疗器械、金融服务、人力资源/雇佣、教育、执法/司法、关键基础设施、公共行政、消费/零售、其他
5. **受影响主体**——以下之一或多项：员工/劳动者、客户/消费者、公民/公众、学生、患者、仅内部
6. **修改情况**——以下之一：无修改、在预期范围内配置、微调/再训练、改变预期目的、使用自有品牌
7. **组织规模**——以下之一：微型（<10）、小型（10-49）、中型（50-249）、大型（250+）
8. **法域**——欧盟/欧洲经济区成员国或瑞士清单

---

### 阶段 2：快速分类（6 步门禁序列）

分类逻辑精简版见 [references/quick-decision-tree.md](references/quick-decision-tree.md)。

**在内部**处理答案通过 6 步门禁序列（除非缺失关键信息，否则不追问）。将结果输出为一份评估。

**门禁 1：范围检查（第 2 条）**
- 如部署语境为"无欧盟联系" → 可能不在范围内 → 注明并谨慎继续
- 根据系统描述检查军事、个人使用、纯研发排除

**门禁 2：AI 系统测试（第 3(1) 条）**
- 基于系统描述快速判定
- 适用简化 3 问测试：(1) 基于机器？(2) 超越规则进行推断/生成？(3) 影响环境？

**门禁 3：被禁止做法筛查（第 5 条）**
- 基于系统描述和行业快速筛查
- 标记任何潜在的第 5 条问题供详细审查

**门禁 4：高风险评估（附件 I + III）**
- 将行业 + 用例映射到附件 I/III 类别
- 以行业回答作为主要触发指示
- 如触发附件 III：快速第 6(3) 条例外检查
- 如需进行基于欧盟委员会指南的完整第 6 条高风险深度评估，当高风险分支可能成立时，在本分诊之后进行专门的高风险深度分析（附件 I + 附件 III 示例、第 6(3) 条例外）。

**门禁 5：GPAI 检查**
- 基于系统描述：是否使用通用 AI 模型？
- 如是：注明 GPAI 义务

**门禁 6：透明度触发（第 50 条）**
- 检查直接人际互动、合成内容生成、情绪识别、深度伪造

---

### 阶段 3：初步输出

使用以下结构生成合并的初步评估：

```markdown
## AI Act Quick Assessment — PRELIMINARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠ PRELIMINARY ASSESSMENT — Full analysis required for compliance decisions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

System:           [name/description]
Date:             [date]
Assessment Type:  PRELIMINARY (Quick Assessment)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLASSIFICATION SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI System (Art. 3(1)):     [Likely YES / Likely NO / Unclear — full test needed]
Scope (Art. 2):            [In scope / Likely excluded — Art. 2(x)]
Risk Tier:                 [Likely Prohibited / Likely High-Risk / Likely GPAI / Likely Limited / Likely Minimal / Unclear]
Classification Basis:      [Likely Art. 5(1)(x) / Likely Annex III Nr. X / Likely Art. 50 / Likely minimal]
Confidence:                [High / Medium / Low]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROLE ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Likely Role:               [Provider / Deployer / Quasi-Provider / Importer / Distributor]
Quasi-Provider Risk:       [None / Possible — [trigger]]
Key Concern:               [if any — e.g., finetuning may trigger Art. 25]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOP OBLIGATIONS (if high-risk or GPAI)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
| # | Obligation | Article | Urgency | Effort Estimate |
|---|-----------|---------|---------|-----------------|
| 1 | [top obligation] | [Art. X] | [Immediate/Short-term/Ongoing] | [Low/Medium/High] |
| 2 | [second obligation] | [Art. X] | [Immediate/Short-term/Ongoing] | [Low/Medium/High] |
| 3 | [third obligation] | [Art. X] | [Immediate/Short-term/Ongoing] | [Low/Medium/High] |
| 4 | [fourth obligation] | [Art. X] | [Immediate/Short-term/Ongoing] | [Low/Medium/High] |
| 5 | [fifth obligation] | [Art. X] | [Immediate/Short-term/Ongoing] | [Low/Medium/High] |

For ALL risk tiers:
| - | AI competence (Art. 4) | Art. 4 | Immediate (since Feb 2025) | Low-Medium |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPLIANCE TIMELINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Applicable Deadline:       [2 Feb 2025 / 2 Aug 2025 / 2 Dec 2027 (Annex III — Omnibus) / 2 Aug 2028 (Annex I — Omnibus)]
Days Remaining:            [X days]
Urgency:                   [OVERDUE / CRITICAL / HIGH / MEDIUM / LOW]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JURISDICTION FLAGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Jurisdiction-specific flags based on deployment country, e.g.:]
[DE: Works council co-determination likely required (BetrVG §87)]
[FR: CSE consultation required before deployment]
[Finance sector: BaFin/[regulator] AI model governance requirements apply]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINANCIAL EXPOSURE (PRELIMINARY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Maximum penalty:           [EUR XM or X% turnover — Art. 99(X)]
SME proportionality:       [Applies / Does not apply]
Penalty tier:              [Tier 1/2/3]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FLAGS & WARNINGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[List any flags, e.g.:]
[PROHIBITED PRACTICE RISK — Art. 5(1)(x) — immediate legal review required]
[QUASI-PROVIDER RISK — finetuning may trigger Art. 25]
[PROFILING DETECTED — may affect Art. 6(3) exception]
[GDPR OVERLAP — DPIA likely required under Art. 35 GDPR]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ASSESSMENT CONTEXT (paste into next skill)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDED NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. → Do a full risk-tier classification with documented reasoning
   [Priority: HIGH / MEDIUM — based on preliminary findings]

2. → Do a detailed role determination (provider/deployer/importer/distributor)
   [Priority: HIGH if quasi-provider risk detected / MEDIUM otherwise]

3. → Do a complete obligation mapping with RACI
   [Priority: HIGH if high-risk / MEDIUM if limited risk]

4. → Generate formal assessment documentation
   [Priority: HIGH for regulatory files / MEDIUM for internal tracking]

5. → Engage legal counsel for:
   [List specific areas requiring legal judgment]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠ This preliminary assessment was generated using the AI Act Quick
  Assessment tool. It provides directional guidance only. All
  determinations marked "Likely" require validation through the
  detailed assessment skills listed above.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 阶段 4：模板化提议（可选）

呈现初步评估后，提议：

> "你希望我为以下任一模板生成初步版本吗？这些将标记为初步，并应在运行完整评估技能后定稿。"
>
> 1. **分类记录（Prüfprotokoll）**——初步审计轨迹
> 2. **合规登记册条目**——初步义务跟踪器
> 3. **管理层简报（Entscheidungsvorlage）**——初步决策文件

如被要求，将这些生成为标准合规文档模板的初步版本，并显著标记所有输出为"PRELIMINARY — Full assessment recommended."（初步——建议完整评估。）

---

## 关键提醒

1. **这是分诊工具**——任何合规决策前始终建议进行完整评估（分类、角色确定、义务映射、正式报告）
2. **"可能"不等于"已确认"**——初步认定需要验证
3. **宁可谨慎**——如在风险层级间不确定，将更高风险层级标记为可能
4. **明确标记不确定性**——低置信度评级需要立即以完整评估跟进
5. **国内要求很重要**——始终使用 [references/jurisdiction-flags.md] 标记法域特定义务
6. **合规时间线**——截止期限紧迫性参见 [references/compliance-deadlines.md]
7. **执法敞口**——关于罚则语境，注意第 99 条层级：第 5 条被禁止做法违规最高 3500 万欧元 / 全球年营业额的 7%，其他侵权为 1500 万欧元 / 3%

## 欧盟 AI 法案套件的一部分

本技能可独立使用，但设计为与我的其他欧盟 AI 法案技能互锁——可单独安装任一技能，或组合使用以实现端到端工作流：

- **EU AI Act System Classifier**（系统分类器）——跨越全部五个层级的风险层级分类
- **EU AI Act High-Risk Classifier**（高风险分类器）——附件 I / 附件 III 深度评估
- **EU AI Act Role Determination**（角色确定）——提供者 / 部署者 / 进口者 / 分销者（含第 25 条）
- **EU AI Act Obligations Mapper**（义务映射器）——按角色和风险层级的义务
- **EU AI Act Examination Report Generator**（检查报告生成器）——审计就绪的合规报告
- **EU AI Act Knowledge Base**（知识库）——针对法案 + 欧盟委员会指南的问答

每个都作为独立技能提供——只安装你需要的。
