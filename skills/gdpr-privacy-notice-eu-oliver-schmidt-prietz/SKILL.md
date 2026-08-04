---
name: gdpr-privacy-notice-eu-oliver-schmidt-prietz
description: |
  为任何欧盟/欧洲经济区法域和受众起草符合 GDPR/DSGVO 的隐私通知，输出为 .docx。当用户要求创建隐私政策/通知、提及"Datenschutzerklärung"、"politique de confidentialité"、"privacy notice"、需要第 13/14 条披露、AI 法案透明度、Cookie 政策，或需要面向求职者（"Bewerber-Datenschutz"）、员工（"Beschäftigten-Datenschutz"）、B2B 伙伴或 B2C 客户的通知时使用。涵盖德国（DSGVO+BDSG+TDDDG）、法国（RGPD+LIL+LCEN）、奥地利、意大利、西班牙、荷兰、比利时、爱尔兰、英国 GDPR。五种通知类型：网站/应用程序、求职者、员工、商业伙伴、B2C 客户。
metadata:
  author: Oliver Schmidt-Prietz
  license: AGPL-3.0
  version: 2026.06.05
---

# 泛欧盟 GDPR 隐私通知生成器（Pan-EU GDPR Privacy Notice Generator）

生成知悉法域、符合 GDPR 的专业 .docx 隐私通知。

## 工作流概述

```
1. SCOPE    → Notice type, jurisdiction(s), template choice
2. INTAKE   → Type-driven collection: controller info, data inventory, legal bases
3. DRAFT    → Generate notice from template + type profile + collected info
4. VERIFY   → Art. 13/14 compliance check + type-specific checks + AI Act check
5. DELIVER  → .docx output via docx skill
```

## 第 1 步：范围、通知类型与模板选择

### 确定通知类型（第一个问题）

在开始任何其他事项之前，先确定需要什么类型的隐私通知。加载 `references/NOTICE_TYPES.md` 并询问：

> "你需要什么类型的隐私通知？"

| 类型 | 说明 |
|---|---|
| **网站 / 应用程序** | 面向网站、网络应用或移动应用的访客、用户、订阅者 |
| **求职者 / 招聘** | 面向求职申请人和候选人（Bewerber、candidats） |
| **员工** | 面向员工、承包商、实习生（Beschäftigte、salariés） |
| **商业伙伴（B2B）** | 面向供应商、服务商、客户、伙伴的联系人 |
| **B2C 客户** | 面向客户/购买关系中的终端消费者 |
| **组合** | 一份或数份相互关联的通知面向多种受众 |

所选类型决定：
- 最终文件中包含/跳过哪些部分
- 信息采集期间探查哪些数据类别
- 哪些法律依据最可能适用
- 询问哪些类型特定的信息采集问题
- 适用哪些保留期限默认值

每种类型的完整**部分映射**、**数据画像**、**法律依据**、**信息采集问题**和**保留期限默认值**见 `references/NOTICE_TYPES.md`。

### 确定法域

询问服务面向哪些国家/市场。加载相应的参考文件：

| 目标市场 | 参考文件 |
|---|---|
| 德国 / DACH | `references/DE.md` |
| 法国 | `references/FR.md` |
| 其他欧盟（奥地利、意大利、西班牙、荷兰、比利时、爱尔兰、英国） | `references/OTHER_EU.md` |
| 始终加载 | `references/EU_COMMON.md` |

对于多法域服务，加载所有相关文件，并注明要求不同的地方（例如儿童年龄阈值、DPO 阈值、保留规则）。

### 模板选择

询问用户：

> "我将把隐私通知起草为专业的 .docx 文件。你有需要我用作基础的现有模板或隐私通知吗？如果没有，我将使用我们预建的模板之一。"

| 选项 | 行动 |
|---|---|
| 用户提供模板 | 以其 .docx 为基础——保留结构、措辞和格式；仅填充/调整 |
| 无用户模板 | 使用 docx 技能从 `references/templates.md` 生成 |

`references/templates.md` 包括：13 部分结构、第 21 条异议框（视觉突出）、目的/保留期限表、Cookie 表、AI/自动化决策部分、儿童数据部分、带页码的规范页眉/页脚、A4 排版、目录，以及德、法、英三种语言的完整翻译。选择与目标法域匹配的语言。

**如用户提供模板**：忠实保留其结构和已验证的措辞。仅替换占位符并针对具体情况进行调整。不得改写已验证的法律语言。

### 多语言决策树

如果服务面向多个法域或语言群体，确定语言方案：

| 场景 | 方案 |
|---|---|
| **单一市场、单一语言** | 一份以市场语言写成的通知（例如仅德国 → 德语） |
| **单一市场、国际员工/用户** | 主要语言 + 英文版本。声明发生冲突时以哪个版本为准。 |
| **两个市场、两种语言** | 选项 A：两份独立通知（每种语言一份），各自自成一体。选项 B：双语通知，视觉上清晰分隔（例如并排双栏或顺序排列的各部分）。 |
| **泛欧盟 / 多市场** | 英文为主 + 关键市场的翻译。每份翻译应为独立完整的通知，而非部分翻译。 |
| **瑞士公司（nDSG + GDPR）** | 同时涵盖瑞士新联邦数据保护法（nFADP）和 GDPR。典型做法：一份通知同时引用两个制度，至少使用德语 + 法语（如适用加意大利语）。注意：nFADP 对一般处理无同意要求，但要求类似 GDPR 第 13/14 条的告知义务。 |

**双语文件的模板处理**：
- 以主要语言模板作为结构基础
- 确保两个语言版本都包含全部强制性披露（翻译缺口 = 合规缺口）
- 明确标注管辖语言版本（例如"In case of discrepancies, the [German/French] version shall prevail."（如有歧义，以[德文/法文]版本为准。））

**多语言核实清单**（如适用，加入第 4 步）：
- [ ] 每个语言版本中都包含全部强制性第 13/14 条披露
- [ ] 管辖版本已明确标识
- [ ] 法律术语翻译正确（非未经审查的机器翻译）
- [ ] 各法域的监管机构信息正确
- [ ] 法域特定要求在相应语言版本中得到处理

### 平台子类型（仅网站/应用程序类型）

如果通知类型为**网站 / 应用程序**，进一步对平台分类以预判数据类别。详情见 `references/NOTICE_TYPES.md` → "Website / App" → "Sub-Types & Data Profiles"。

| 子类型 | 典型的额外数据 |
|---|---|
| 宣传页/企业网站 | 仅联系表单、分析、Cookie |
| 电子商务 | 账户、支付、订单历史、配送、退货 |
| SaaS / 网络应用 | 账户、使用数据、功能日志、API 密钥、协作数据 |
| 移动应用 | 设备 ID、推送令牌、权限（相机、位置、联系人）、应用使用情况 |
| 市场平台 | 双重角色（买家/卖家）、评分、消息、支付托管 |
| 带 AI 功能的平台 | 训练数据、AI 输入/输出、模型决策、画像分析 |

## 第 2 步：信息采集

起草前收集**全部**信息。使用 `references/NOTICE_TYPES.md` 中的**类型画像**引导采集——每种类型预定义了可能的数据类别、法律依据和类型特定问题。

按逻辑分组提问，而非一次性全部询问。从 A 组开始（始终），然后使用类型画像确定要探查哪些类别以及询问哪些类型特定问题。

### A 组——控制者身份
- 公司名称、法律形式、注册号
- 注册地址
- 法定代表人（姓名 + 职务）
- 联系邮箱 + 电话
- 是否指定了 DPO？→ 联系方式（使用职能邮箱）

### B 组——数据清单
针对每个收集点（表单、账户创建、购买、Cookie、应用使用）：
- 收集哪些数据？
- 是强制性还是可选的？
- 来源是什么（直接来自用户、第三方、自动化）？

待探查的类别：
- **身份**：姓名、邮箱、电话、地址、出生日期、照片
- **账户**：凭证、偏好、设置、活动历史
- **技术性**：IP、设备 ID、浏览器指纹、日志
- **浏览**：访问页面、点击、会话时长、来源网站
- **交易**：订单、支付方式（经提供者）、发票
- **沟通**：消息、支持工单、评论
- **特殊类别**（第 9 条）：健康、生物识别、政治、宗教、性取向、民族出身、工会、基因——**如识别出任何第 9 条数据**：查阅 `EU_COMMON.md` → "Special Category Data (Art. 9)" 了解完整采集协议。为每个类别确定第 9(2) 条例外，确认双重法律依据（第 6 条 + 第 9(2) 条），并记录额外保障措施。按通知类型的常见触发：员工（教会税、残疾、病假、工会会费）、求职者（残疾、健康、宗教）、B2C（药房/保险/健身的健康数据）。
- **AI 相关**：AI 系统的输入、AI 生成的输出、自动化评分/决策

### C 组——目的与法律依据
为每项处理活动确定法律依据。参考 `EU_COMMON.md` 获取指引。

以表格呈现供用户确认：

| 目的 | 法律依据 | 数据类别 |
|---|---|---|
| 服务提供 / 合同履行 | 第 6(1)(b) 条 | [待填] |
| 账户管理 | 第 6(1)(b) 条 | [待填] |
| 法律/税务合规 | 第 6(1)(c) 条——[具体法律] | [待填] |
| 分析 | 第 6(1)(f) 条或同意 | [待填] |
| 营销 / 通讯 | 第 6(1)(a) 条同意 | [待填] |
| 基于 AI 的处理 | [按用例确定] | [待填] |

### D 组——接收者与转移
- 托管服务商 + 所在地
- 支付处理方
- 分析工具
- 电子邮件/营销工具
- CRM / 支持工具
- AI/ML 服务提供者（例如 OpenAI、Google AI、Anthropic）
- 任何其他处理者
- 向欧盟/欧洲经济区以外的转移 → 哪些国家、何种机制（充分性认定、SCC、DPF、BCR）

**DPA / 第 28 条交叉引用**——针对每个已识别的处理者：
- 核实数据委托处理协议（GDPR 第 28 条）已就位。如未就位，标记为**合规缺口**，需在通知定稿前整改。
- **通知中应披露的内容**：处理者名称（或类别）、目的、所在地、转移机制。不得在隐私通知中包含 DPA 条款、次级处理者清单或 TOM——这些属于第 28 条协议。
- **不应披露的内容**：具体技术/组织措施（第 32 条）、次级处理者链条、价格、SLA 细节。
- 如果用户确认某处理者没有 DPA：在摘要中注明并建议立即整改。隐私通知仍应点名该处理者/类别，但可加注控制者正在将协议正式化。
- 共同控制（第 26 条）：如适用，必须披露该安排的实质内容，包括各自的责任和数据主体联系点。

### E 组——Cookie 与追踪
- 使用的 Cookie 类别（必需、分析、营销、社交）
- 具体工具（Google Analytics、Meta Pixel、Matomo、HubSpot 等）
- CMP 方案（Usercentrics、Cookiebot、Axeptio、Didomi、Borlabs 等）
- 服务器端追踪？指纹识别？
- Cookie 存续期

### F 组——AI 与自动化处理
如果服务使用 AI/ML：
- 使用哪些 AI 系统、用于什么目的？
- 决策是纯自动化还是有人参与？
- 决策是否产生法律或类似重大影响（第 22 条）？
- 用户数据是否用于模型训练？
- AI 法案分类：被禁止 / 高风险 / 有限风险 / 最低风险？

### G 组——DPIA 指示器（GDPR 第 35 条）

检查是否可能需要进行数据保护影响评估（DPIA）。如适用以下指标中的**2 项或以上**，告知用户并建议将 DPIA 作为单独交付物：

1. 对个人的**系统性评估/评分**（画像分析、信用评分、绩效评估）
2. 具有法律或类似重大影响的**自动化决策**（第 22 条）
3. 对公众可进入区域进行**系统性监控**（闭路电视、Wi-Fi 追踪）
4. **特殊类别数据**或大规模处理的刑事定罪数据（第 9/10 条）
5. **大规模处理**个人数据（高数据量、广泛地域范围、众多数据主体）
6. 以数据主体不会合理预期的方式**匹配或合并**不同来源的数据集
7. **弱势数据主体**（员工、儿童、患者、老年人）
8. **技术的创新性使用**（生物识别、AI/ML、物联网、用于个人数据的区块链）

**如标记 2 项以上指标**：
- 告知用户："根据所描述的处理活动，似乎需要进行 GDPR 第 35 条下的数据保护影响评估（DPIA）。"
- 解释对通知的影响：隐私通知应提及已进行 DPIA（不披露 DPIA 内容本身）
- 建议："DPIA 是独立的合规工作，应在处理开始前进行。本隐私通知技能可以起草通知，但 DPIA 应作为独立文件准备。"
- 检查各国的强制性 DPIA 清单（德国：DSK 清单；法国：CNIL 的需 DPIA 处理操作清单）

### 起草前摘要

收集完成后，生成结构化摘要供用户确认：

```
NOTICE TYPE: [Website / Applicant / Employee / B2B / B2C / Combined]
CONTROLLER: [Name, form, address]
JURISDICTION(S): [Countries]
PLATFORM: [Type / Sub-type if website]
DPO: [Yes/No + contact]
DATA CATEGORIES: [List by collection point]
PURPOSES + BASES: [Table]
PROCESSORS: [List with locations]
TRANSFERS: [Countries + mechanisms]
COOKIES: [Categories + tools + CMP — if applicable per type]
AI PROCESSING: [Yes/No + details]
RETENTION: [Key periods — cross-check with type defaults]
SPECIFICS: [Anything unusual]
SECTIONS TO INCLUDE: [Based on type section map]
SECTIONS TO SKIP: [Based on type section map]
```

在继续起草前与用户确认。

## 第 3 步：起草通知

### 按类型选择部分

对所选通知类型使用 `references/NOTICE_TYPES.md` 中的**部分映射**。仅包含标记为 ✅ 或 ⚠️（如适用）的部分。跳过标记为 ❌ 的部分。这避免无关内容（例如求职者通知中的 Cookie 表）。

对于覆盖多种受众的**组合通知**，见 `references/NOTICE_TYPES.md` → "Combined Notices" 了解结构选项（单一全面式、分离式或分层式）。

### 标准结构（完整版——按类型调整）

```
PRIVACY NOTICE / DATENSCHUTZERKLÄRUNG / POLITIQUE DE CONFIDENTIALITÉ
[Company Name]
Last updated: [DATE]

1. WHO WE ARE (Controller identity + DPO)
2. WHAT DATA WE COLLECT (by category, with source + mandatory/optional)
3. WHY WE PROCESS YOUR DATA (purposes + legal bases table, incl. retention per purpose)
4. WHO RECEIVES YOUR DATA (recipients + processors)
5. INTERNATIONAL TRANSFERS (countries + safeguards)
6. HOW LONG WE KEEP YOUR DATA (retention table — can be merged with section 3)
7. YOUR RIGHTS (all applicable rights + exercise procedure)
8. COOKIES & TRACKING (categories + management + CMP reference)
9. AI & AUTOMATED DECISIONS (if applicable — Art. 22 + AI Act)
10. DATA SECURITY (general measures, no sensitive technical details)
11. CHILDREN'S DATA (if applicable — age threshold + mechanism)
12. CHANGES TO THIS NOTICE (notification method)
13. CONTACT (email + postal + form link)
```

### 起草规则

- **语言**：用法域语言撰写。多法域时，主要语言在前，并清晰说明管辖版本。
- **语气**：以"你"/"Sie"/"vous"称呼读者。清晰、易理解的语言——非法律人士也能看懂。
- **第 21 条异议权**：必须与其他权利**突出且分离地**呈现（GDPR 第 21(4) 条）。在德文通知中，单独的"WIDERSPRUCHSRECHT"部分是标准做法。
- **法律依据**：精确引用条款编号（例如"Art. 6(1)(f) DSGVO"，而非仅"合法利益"）。
- **保留期限**：使用附法律理由的具体期限，而非模糊语言。
- **AI 披露**：如使用 AI，即使第 22 条并非严格适用，也包含专门部分——AI 法案要求透明度。
- **表格**：目的/依据/保留期限和 Cookie 类别使用表格。它们提高可读性。
- **无内部引用**：最终文件不得包含对本技能、CNIL 指南或其他起草辅助工具的引用。

## 第 4 步：合规验证

交付前，按以下顺序执行结构化最终检查：

**1. 重读第 1 步加载的法域参考文件**（DE.md、FR.md、OTHER_EU.md）。交叉核对：
- 监管机构名称、地址和 URL 与控制者注册地对应正确
- 保留期限与法域特定的法律引用匹配（而非仅通用默认值）
- 标准措辞块（第 21 条异议、投诉权、控制者引言）使用参考文件中该法域已验证的语言
- 任何尚未处理的法域特定要求（例如德国员工/求职者的 BDSG 第 26 条、法国营销的《邮电法典》第 L.34-5 条）

**2. 对照 `EU_COMMON.md` → "Mandatory Disclosures Checklist"（强制性披露检查清单）核实第 13/14 条强制性披露。** 每一项都必须存在，或明确标注不适用并说明理由。

**3. 额外检查：**

- [ ] 第 21 条异议权分离且突出呈现
- [ ] 点名的监管机构正确（核对法域参考文件）
- [ ] 如已指定 DPO，包含 DPO 联系方式
- [ ] Cookie 部分与实际 Cookie 使用一致（如按类型包含）
- [ ] 保留期限具体（不是无标准的"as long as necessary"（按需保留））
- [ ] 转移机制与实际处理者所在地一致
- [ ] 如适用，处理了 AI/自动化决策
- [ ] 如服务可供未成年人访问，处理了儿童数据
- [ ] 特殊类别数据（第 9 条）：披露双重法律依据（第 6 条 + 第 9(2) 条）、识别具体例外、提及额外保障措施
- [ ] 语言与目标法域匹配
- [ ] 无残留占位符文本（[...]、___、TODO）
- [ ] 存在更新日期
- [ ] 各部分与类型部分映射一致（无无关部分、无缺失必需部分）

**4. 类型特定检查**（来自 `references/NOTICE_TYPES.md`）：

**求职者**：引用了 BDSG 第 26 条（德国）？人才库同意是否分开？除非获得同意，拒绝后保留期限 ≤ 6 个月？如数据来自招聘机构，是否使用第 14 条？

**员工**：以 BDSG 第 26 条为主要依据（德国）？如相关，提及劳资委员会？披露 IT 监控？复杂的保留链条完整？

**B2B**：如数据非直接来自数据主体，是否进行第 14 条披露？披露数据来源？联系人与缔约实体之间的区分是否清晰？

**B2C 客户**：软性选择加入条件是否满足（德国：《反不正当竞争法》第 7(3) 条）？披露支付处理方？忠诚度计划条款清晰？如适用，披露画像分析？

**5. AI 法案合规**（如存在 AI 功能）：
- [ ] 告知用户他们正在与 AI 互动（AI 法案第 50 条）
- [ ] 在适用处披露 AI 生成内容
- [ ] 高风险 AI：透明度义务已满足
- [ ] 披露 GDPR 第 22 条权利与 AI 系统之间的联系

## 第 5 步：交付为 .docx

使用 docx 生成技能生成最终文件（Claude.ai Projects 中的 `/mnt/skills/public/docx/SKILL.md`，或 Claude Code 中的 `docx-processing-anthropic` 技能）。如无 docx 技能可用，生成格式良好的 Markdown 作为回退。

### 文档排版标准

- **页面尺寸**：A4（欧盟文件标准）
- **字体**：Arial 或 Calibri，正文 11pt，标题按比例加大
- **页边距**：四周 2.5 厘米（欧盟标准）= 1417 DXA
- **结构**：编号标题（1.、2.、3...），超过 3 页的文件加目录
- **表格**：浅边框、表头行底纹、可读的单元格内边距
- **页眉**：公司名称或"Privacy Notice"
- **页脚**：页码、"Last updated: [DATE]"

生成文件前阅读 docx 技能说明。新文件使用 `docx-js`。遵循 docx 技能的全部关键规则（DXA 宽度、列表用 LevelFormat.BULLET、表格用 ShadingType.CLEAR 等）。

### 交付

呈现 .docx 文件并附：
1. 所包含内容的简要确认
2. 任何未决问题或所作的假设
3. 发布前进行法律审查的建议

> **重要提示**：始终建议用户在发布前让合格的法律顾问审查通知。此工具辅助起草——它不替代法律意见。

### 生成后检查清单与批准工作流

向用户呈现以下检查清单，以引导其内部审查和发布流程：

**法律审查**：
- [ ] 隐私通知已由合格的数据保护法律顾问 / DPO 审查
- [ ] 全部法律依据已确认为适合具体处理活动
- [ ] 保留期限已对照现行法律要求核实
- [ ] 转移机制已确认为有效且最新（尤其是 DPF 认证、SCC 版本）
- [ ] 第 9 条特殊类别处理：双重法律依据和保障措施已审查

**技术审查**：
- [ ] 所列处理者和工具均实际在使用（无过时条目）
- [ ] Cookie 表与网站实际设置的 Cookie 一致（用浏览器开发者工具审计）
- [ ] 数据流与技术架构一致（与 IT/工程部门核实）
- [ ] 联系方式（邮箱、邮政地址、DPO）正确且有人监控

**翻译 QA**（如为多语言）：
- [ ] 每个语言版本均由具备法律专业知识的母语者审查
- [ ] 法律术语已验证（非原始机器翻译）
- [ ] 所有版本包含相同的实质性内容
- [ ] 管辖版本已明确标注

**发布要求**：
- [ ] 通知可从任何页面 2 次点击内访问（德国：联邦最高法院要求）
- [ ] 按适当方式链接在网站页脚 / 应用设置 / 入职流程中
- [ ] 先前版本连同生效日期存档（用于审计轨迹）
- [ ] Cookie 横幅 / CMP 更新为引用当前隐私通知
- [ ] 已告知员工 / 求职者更新后的通知（如适用）

**持续审查触发条件**——建议用户在以下情形审查通知：
- 引入新的处理者或工具
- 增加新的处理目的
- 法律框架发生变化（新的充分性认定、法院裁决、监管指引）
- 公司经历合并、收购或重组
- 发生揭示未披露处理的数据泄露
- 最低限度：年度审查

## 交叉引用

- **违规响应**：如果用户还需要违规通知程序，引用 `breach-sentinel` 技能
- **DPIA**：如处理可能属于高风险，建议将数据保护影响评估（GDPR 第 35 条）作为单独工作
- **Cookie 政策**：可整合进隐私通知或作为单独文件——询问用户偏好

## 写作风格指南

| 应做 | 应避免 |
|---|---|
| "you" / "your data" / "Sie" / "Ihre Daten" | "the user" / "the data subject" / "der Betroffene" |
| 短而清晰的句子 | 密集的法律段落 |
| 复杂处理给出具体示例 | 模糊语言（"various data"、"diverse Daten"） |
| 结构化信息用表格 | 目的/保留期限用文字墙 |
| 精确的条款引用 | 笼统的"in accordance with applicable law"（依据适用法律） |
| 主动语态 | 可避免的被动结构 |
| 兼具法律精确性的平实语言 | 纯法律术语或过度简化的语言 |

## 相关 GDPR 技能

本技能可独立使用，但与我的其他欧盟数据保护技能搭配效果良好——可单独安装任一技能或组合使用：

- **DPIA Sentinel**——第 35 条数据保护影响评估
- **GDPR Breach Sentinel**——第 33/34 条违规响应与通知
- **Transfer Impact Assessment (TIA)**——第五章转移评估
- **DPA Art. 28**——控制者-处理者协议（AVV）
- **Legitimate Interest**——第 6(1)(f) 条合法利益评估/利益平衡测试
