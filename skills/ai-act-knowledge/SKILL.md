---
name: ai-act-knowledge
description: |
  欧盟 AI 法案知识引擎——以 70 份官方欧盟来源文件为基础的权威监管问答（包括 2026 年委员会关于 Art. 6 高风险分类的指南草稿——一般原则、附件 I、附件 III）。基于完整条例文本、委员会指南、EDPB/EDPS 意见、《实践守则》、协调标准、FRIA 指南、事件模板和行业特定指引，以条款级引用回答关于 AI 法案的任何问题。当用户询问"EU AI Act"、"AI Act regulation"、"Regulation 2024/1689"、"KI-Verordnung"、要求"explain an AI Act article"、"what does Article X say"、"AI Act requirements"、"AI Act penalties"、"AI Act timeline"、"GPAI obligations"、"high-risk AI"、"prohibited AI practices"、"AI Act and GDPR"、"fundamental rights impact assessment"、"AI Act standards"、"AI Act national implementation"、"AI literacy"、"serious incident reporting"、"Digital Omnibus"、"AI regulatory sandbox"，或任何关于欧盟人工智能监管的问题时，应使用本技能。德语术语同样触发："KI-Gesetz"、"KI-Verordnung"、"Hochrisiko-KI"、"KI-Kompetenz"、"Grundrechte-Folgenabschaetzung"、"GPAI-Verhaltenskodex"。对于产出分类决定而非知识答案的评估工作流，提议在会话内运行结构化风险等级分类。
metadata:
  author: Oliver Schmidt-Prietz
  license: AGPL-3.0
  version: 2026.06.21
---

# 欧盟 AI 法案知识引擎

Regulation (EU) 2024/1689——欧盟人工智能法案——的权威知识库。基于跨 15 个子目录的 **70 份结构化参考文件**（包括 `references/commission-guidelines/` 下 2026 年委员会关于 Art. 6 分类的指南草稿——一般原则、附件 I、附件 III），来源仅限官方欧盟机构（欧盟委员会、EDPB、EDPS、ENISA、EBA、欧洲刑警组织、AI Office、EUR-Lex）。每份回答必须引用具体条款、段落、序言或指南章节。

## 免责声明（会话开始时展示，不阻断）

> **重要：** 本技能基于欧盟 AI 法案（Regulation (EU) 2024/1689）和官方欧盟机构来源提供结构化的 AI 法案监管信息。它不是法律意见。具体合规决定应涉及具备 AI 法案专长的合格法律顾问。

---

## 何时联网搜索

参考文件覆盖截至 2026 年 3 月的官方来源。当用户询问该日期之后的事件、执法行动、国家实施更新或非官方分析（律所观点、智库论文）时搜索网络。对细分主题，有用的查询包括：`CEN CENELEC JTC 21 harmonised standards [year]`、`EU AI Act Digital Omnibus trilogue [year]`、`[Member State] AI Act supervisory authority [year]`。

---

## 工作流

### 第 1 步：问题分类

| 问题类型 | 信号词 | 行动 |
|---------------|-------------|--------|
| **条款查询** | "What does Art. X say" | 直接读文件 → 逐字引用 |
| **概念解释** | "What is..."、"explain..."、"define..." | 找到定义 + 背景 + 序言 |
| **义务映射** | "What must a [role] do" | 按角色 + 风险等级路由 |
| **分类帮助** | "Is this high-risk?"、"Is this an AI system?" | 阅读 `core/decision-trees.md`，走相关决策树 |
| **跨框架** | "AI Act and GDPR"、"medical devices + AI" | 跨领域的多文件综合 |
| **时间线 / 截止日期** | "When does X apply?" | `governance/implementation-timeline.md` |
| **处罚 / 执法** | "What are the fines?" | `core/regulation-title-VI-X-governance.md`（Art. 99） |
| **国家实施** | 特定国家 | `national/` 文件 + 最新更新的网络搜索 |
| **事件报告** | "Serious incident"、"what to report" | `templates/` 文件 |
| **行业特定** | 医疗保健、银行业、人力资源、执法 | `sector-specific/` 或 `law-enforcement/` 文件 |

### 第 2 步：查找并阅读参考文件

使用下面的**主题路由器**找到正确文件。对大多数问题，阅读 2-3 个文件：一手来源、条例条款文本，以及任何解释性指南或意见。

每个 `references/` 子目录都包含一个列出其文件的 `README.md`。对主题路由器中未涵盖的主题，使用 `Glob` 按关键词搜索 `references/` 目录。

始终检查序言（`core/regulation-preamble-recitals.md`）以获取对含糊条款的解释性背景。

### 第 3 步：带引用综合

**引用格式：**

| 来源类型 | 格式 |
|-------------|--------|
| 条例文本 | Art. 6(1)(a) AI Act — "[引文文本]" |
| 序言 | Recital 47 AI Act — "[引文文本]" |
| 委员会指南 | EC Guidelines on [主题]，Section X — "[引文文本]" |
| EDPB/EDPS 意见 | EDPB Opinion 28/2024，Point X — "[引文文本]" |
| 《实践守则》 | GPAI Code of Practice，Measure X.Y — "[引文文本]" |
| 行业指引 | MDCG 2025-6，FAQ X — "[引文文本]" |

**规则：**
- 先给直接答案，再给法律依据
- 引用操作性文本，而不仅是转述
- 当指引"正在制定中"（见观察清单）时，明确说明
- 当条例含糊时，引用相关序言并注明不确定性
- 对德语用户，首次引用时包含德文条款标题："Art. 9 (Risikomanagementsystem)"
- 条例文本 > 授权法案 > 指南 > 《实践守则》 > 意见。来源冲突时，更高权威优先
- 委员会指南是不具约束力的软法——引用时注明这一点

---

## 主题路由器

对未列于此的主题，使用 `Glob` 按关键词搜索 `references/`，或检查每个子目录中的 `README.md`。

| 用户询问 | 阅读这些文件 |
|-----------------|-----------------|
| **定义**（Art. 3） | `core/regulation-title-I-general.md` → `guidelines/ai-system-definition.md` |
| **"这是 AI 系统吗？"** | `core/decision-trees.md`（树 A）→ `guidelines/ai-system-definition.md` |
| **禁止实践**（Art. 5） | `guidelines/prohibited-practices-full.md` → `core/regulation-title-II-prohibited.md` |
| **高风险分类**（Art. 6） | `core/decision-trees.md`（树 B）→ `core/annex-iii-high-risk.md` |
| **高风险要求**（Art. 8–15） | `core/regulation-title-III-high-risk.md` → `core/regulation-preamble-recitals.md` |
| **风险管理**（Art. 9） | `core/regulation-title-III-high-risk.md` → `standards/standardisation-overview.md` |
| **数据治理**（Art. 10） | `core/regulation-title-III-high-risk.md` → `opinions/edpb-opinion-28-2024.md` |
| **透明度**（Art. 50） | `core/regulation-title-IV-transparency.md` → `codes-of-practice/transparency-code-draft-2.md` |
| **GPAI 义务**（Art. 51–56） | `core/regulation-title-V-gpai.md` → `codes-of-practice/gpai-code-final.md` |
| **GPAI 系统性风险** | `core/regulation-title-V-gpai.md`（Art. 51）→ `codes-of-practice/gpai-code-detailed.md` |
| **提供者义务** | `core/regulation-title-III-high-risk.md`（Art. 16–25） |
| **部署者义务** | `core/regulation-title-III-high-risk.md`（Art. 26） |
| **提供者 vs. 部署者** | `core/decision-trees.md`（树 C）→ `compliance-guides/modifying-ai-classification.md` |
| **FRIA**（Art. 27） | `fria/article-27-fria.md` → `fria/ecnl-fria-guide.md` |
| **合格评定**（Art. 43） | `core/regulation-title-III-high-risk.md`（Art. 43）→ `standards/standardisation-overview.md` |
| **处罚 / 罚款**（Art. 99） | `core/regulation-title-VI-X-governance.md`（Art. 99） |
| **时间线 / 截止日期** | `governance/implementation-timeline.md` |
| **FAQ** | `governance/ai-office-faq.md` → `governance/ec-qa-navigating-ai-act.md` |
| **AI 法案 + GDPR** | `opinions/edpb-opinion-28-2024.md` → `opinions/edpb-edps-joint-opinion-2026.md` |
| **医疗器械** | `sector-specific/medical-devices-ai.md` |
| **银行业 / 金融** | `sector-specific/banking-ai-implications.md` → `core/annex-iii-high-risk.md`（领域 8） |
| **就业 / 人力资源** | `sector-specific/staffing-businesses-ai.md` → `core/annex-iii-high-risk.md`（领域 4） |
| **执法** | `law-enforcement/europol-ai-policing.md` → `core/regulation-title-II-prohibited.md`（Art. 5 RBI） |
| **Digital Omnibus** | `guidelines/digital-omnibus.md` → `opinions/edpb-edps-joint-opinion-2026.md` |
| **标准 / 协调标准** | `standards/harmonised-standards-map.md` → `standards/standardisation-overview.md` |
| **网络安全** | `cybersecurity/enisa-ai-cybersecurity.md` → `cybersecurity/enisa-cybersecurity-standardisation.md` |
| **严重事件**（Art. 73） | `templates/draft-guidance-art73-high-risk.md` → `templates/serious-incident-template-gpai.md` |
| **德国** | `national/german-ai-bill.md` → `national/national-implementation-plans.md` |
| **国家实施** | `national/national-implementation-plans.md` → 最新网络搜索 |
| **修改 AI 系统** | `compliance-guides/modifying-ai-classification.md` |
| **中小企业 / 初创企业** | `compliance-guides/small-businesses-guide.md` |
| **举报** | `compliance-guides/whistleblowing-ai-act.md` → `governance/whistleblower-tool.md` |
| **版权 / TDM** | `compliance-guides/copyright-tdm-consultation.md` → `core/regulation-title-V-gpai.md` |
| **AI 素养**（Art. 4） | `compliance-guides/ai-literacy-repository.md` → `core/regulation-title-I-general.md` |
| **监管沙盒** | `national/regulatory-sandboxes.md` |
| **开源**（Art. 2(12)） | `core/regulation-title-I-general.md` → `core/regulation-title-V-gpai.md`（Art. 53(2)） |
| **序言解释** | `core/regulation-preamble-recitals.md` |

---

## 关键时间线

| 日期 | 适用内容 | 条款 |
|------|-------------|---------|
| **2025 年 2 月 2 日** | 禁止实践（Art. 5）+ AI 素养（Art. 4） | Art. 113(a) |
| **2025 年 8 月 2 日** | GPAI 义务（Art. 51–56）+ 治理 + 处罚 | Art. 113(b) |
| **2026 年 8 月 2 日** | 一般适用——Art. 50 透明度（50(1)/(3)/(4) + 新系统的 50(2)）+ 大多数其余条款 | Art. 113 *（50(2) 遗留标记：2026 年 12 月 2 日）* |
| **2027 年 12 月 2 日** | 高风险 AI（附件 III） | Art. 6(2) *（Omnibus 从 2026 年 8 月 2 日延期）* |
| **2028 年 8 月 2 日** | 附件 I 产品中的高风险 AI（医疗器械、机械等） | Art. 6(1) *（Omnibus 从 2027 年 8 月 2 日延期）* |

> **AI Omnibus 2026** 推迟了高风险生效日期。2026 年 Art. 6 分类指南草稿见 [Commission guidelines references/commission-guidelines/](references/commission-guidelines/)，引用链见 `../ai-act-high-risk/references/ai-omnibus-timeline-postponements.md`。

---

## 观察清单——即将发布的官方来源

以下内容正在制定中。当用户询问这些主题时，注明官方指引预期将发布并提供联网搜索：

- 高风险分类（实务）指南——2026 年
- 透明度要求（Art. 50）指南——2026 年
- 提供者/部署者义务指南——2026 年
- **官方 FRIA 模板**（Art. 27）——2026 年
- 实质性修改指南——2026 年
- **欧委会/EDPB 关于 AI 法案 + GDPR 相互作用的联合指南**——2026 年

来源：`guidelines/guidelines-roadmap.md`

---

## 套件集成

本技能是 5 个工作流技能的深度参考层。当用户的问题表明他们需要结构化评估而非知识答案时，推荐正确的技能：

| 用户需求 | 交接给 |
|-----------|-------------|
| 结构化分类评估 | `/ai-act-classifier` |
| 角色认定（提供者/部署者） | `/ai-act-roles` |
| 带 RACI 矩阵的合规清单 | `/ai-act-obligations` |
| 格式化合规文档 | `/ai-act-report` |
| 快速 15 分钟分诊 | `/ai-act-quick` |

如果用户提供了来自其他技能的**评估上下文**块，用它来定制答案（聚焦他们的风险等级、角色、行业、法域）。

---

## 跨框架参考

知识库覆盖这些重叠中的 AI 法案一侧。对另一框架（GDPR、MDR 等），依赖训练知识或网络搜索——参考文件不包含非 AI 法案的条例文本。

| 重叠 | AI 法案一侧 | 参考文件 |
|---------|------------|----------------|
| **GDPR** —— 训练数据、DPIA | Art. 10、Art. 26(9) | `opinions/edpb-opinion-28-2024.md` |
| **医疗器械** —— MDR/IVDR | Art. 6(1)、附件 I | `sector-specific/medical-devices-ai.md` |
| **银行业** —— CRD、MiFID II | 附件 III 领域 5、8 | `sector-specific/banking-ai-implications.md` |
| **就业** —— 国家劳动法 | 附件 III 领域 4 | `sector-specific/staffing-businesses-ai.md` |
| **执法** —— LED | 附件 III 领域 6、Art. 5(1)(h) | `law-enforcement/europol-ai-policing.md` |
| **版权** —— DSM 指令 | Art. 53(1)(c)-(d) | `compliance-guides/copyright-tdm-consultation.md` |
| **网络安全** —— CRA | Art. 15 | `cybersecurity/enisa-ai-cybersecurity.md` |
| **举报** —— 指令 2019/1937 | Art. 87 | `compliance-guides/whistleblowing-ai-act.md` |

---

## 关键提醒

1. **不编造引用。** 绝不发明条款编号、序言编号或指南章节。如果在参考文件中找不到某条款，如实说明。

2. **来源层级。** 条例文本 > 授权法案 > 委员会指南 > 《实践守则》 > EDPB 意见 > 行业指引。冲突时更高权威优先。

3. **格局不断演变。** 主要委员会指南仍在制定中（见观察清单）。在这些领域回答时标记此不确定性。

4. **德语支持。** 每个参考文件都包含德文标题。对德语用户："Art. 9 (Risikomanagementsystem)"、"Art. 5 (Verbotene Praktiken)"。

5. **ISO/IEC 缺口。** ISO 42001 和 ISO 23894 相关但需付费访问——不在知识库中。讨论标准对齐时提及它们的存在。

6. **Digital Omnibus。** 该提案将显著修改 AI 法案。讨论受影响的条款时，同时标记现行法律和拟议变更。见 `guidelines/digital-omnibus.md`。

7. **处罚层级。** Art. 5 违规：EUR 35M / 7% 营业额。高风险要求：EUR 15M / 3%。向当局提供不实信息：EUR 7.5M / 1%。适用中小企业上限（Art. 99(5)–(6)）。
