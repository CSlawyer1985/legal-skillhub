# 《人工智能法》——欧盟委员会监管框架概述

欧盟委员会对人工智能监管框架的概述——基于风险的方法、关键条款和实施结构。

> **2026 年 AI 综合法案（AI Omnibus）——高风险日期推迟。** 本概述转载了欧盟委员会的官方文本，其中引用了第 113 条*原始*的高风险日期。2026 年 AI 综合法案将其推迟：附件 III / 第 6 条第 2 款 → **2027 年 12 月 2 日**（原为 2026 年 8 月 2 日）；附件 I / 第 6 条第 1 款 → **2028 年 8 月 2 日**（原为 2027 年 8 月 2 日）；第 111 条第 2 款存量截止日期 → **2027 年 12 月 2 日**。**未**推迟：第 50 条透明度、2026 年 8 月 2 日一般适用日期和第 57 条监管沙盒。关于操作性日期见 `../../../ai-act-high-risk/references/ai-omnibus-timeline-postponements.md`。

| 方面 | 详情 |
|--------|--------|
| 机构 | 欧盟委员会 |
| 日期 | 持续 |
| 来源 URL | https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai |
| NotebookLM 来源 ID | 96b46f73-... |

*德文：KI-Verordnung — Überblick über den Regulierungsrahmen der EK（《人工智能法》——欧盟委员会监管框架概述）*

---

## 概述

《[人工智能法](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024R1689)》（制定人工智能统一规则的欧盟条例 (EU) 2024/1689）是全球首部全面的人工智能法律框架。该规则的目标是在欧洲培育可信赖的人工智能。对《人工智能法》有任何疑问，请查看 [《人工智能法》单一信息平台](https://ai-act-service-desk.ec.europa.eu/en)。

《人工智能法》针对人工智能的特定用途，为 AI 开发者和部署者规定了基于风险的规则。《人工智能法》是支持可信赖 AI 发展的更广泛政策措施包的一部分，该措施包还包括 [AI 大陆行动计划](https://digital-strategy.ec.europa.eu/en/factpages/ai-continent-action-plan)、[AI 创新包](https://ec.europa.eu/commission/presscorner/detail/en/ip_24_383) 和 [AI 工厂](https://digital-strategy.ec.europa.eu/en/policies/ai-factories) 的启动。这些措施共同保障安全、基本权利和以人为本的 AI，并加强整个欧盟范围内 AI 的应用、投资和创新。

为促进向新监管框架的过渡，委员会推出了 [AI 公约（AI Pact）](https://digital-strategy.ec.europa.eu/en/policies/ai-pact)——一项自愿性倡议，旨在支持未来的实施、与利益相关方接触，并邀请欧洲内外的 AI 提供者和部署者提前遵守《人工智能法》的关键义务。与此同时，[《人工智能法》服务台](https://ai-act-service-desk.ec.europa.eu/en) 也为《人工智能法》在整个欧盟的顺利有效实施提供信息和支持。

## 为什么需要人工智能规则

《人工智能法》确保欧洲人能够信任 AI 所提供的价值。虽然大多数 AI 系统风险有限或没有风险，且有助于解决许多社会挑战，但某些 AI 系统会带来我们必须加以应对的风险，以避免不良后果。

例如，通常无法查明 AI 系统为什么作出某个决定或预测并采取某项特定行动。因此，可能难以评估某人是否受到不公平的不利对待，例如在招聘决定中或在公共福利计划申请中。

尽管现有立法提供了一些保护，但不足以应对 AI 系统可能带来的具体挑战。

## 基于风险的方法

《人工智能法》为 AI 系统定义了四个风险等级。

### 不可接受的风险

所有被认为对人身安全、生计和权利构成明确威胁的 AI 系统均被禁止。《人工智能法》禁止八种做法：

1. 有害的基于 AI 的操纵和欺骗
2. 有害的基于 AI 的漏洞利用
3. 社会评分
4. 个人刑事犯罪风险评估或预测
5. 无目标地抓取互联网或闭路电视（CCTV）素材以创建或扩大面部识别数据库
6. 工作场所和教育机构中的情绪识别
7. 推断某些受保护特征的生物特征分类
8. 执法目的在公共场所进行实时远程生物特征识别

这些禁令已于 2025 年 2 月生效。委员会发布了两份关键文件，以支持被禁止做法的实际适用：

- [《人工智能法》下被禁止 AI 做法的指南](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-guidelines-prohibited-artificial-intelligence-ai-practices-defined-ai-act)，提供法律解释和实际示例，帮助利益相关方理解并遵守禁令。
- [《人工智能法》AI 系统定义的指南](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-guidelines-ai-system-definition-facilitate-first-ai-acts-rules-application)，协助利益相关方确定《人工智能法》的范围。

### 高风险

可能对健康、安全或基本权利构成严重风险的 AI 用例被归类为高风险。这些高风险用例包括：

- 关键基础设施（如交通）中的 AI 安全组件，其失效可能危及公民的生命和健康
- 教育机构中使用的 AI 解决方案，可能决定某人接受教育的机会和职业生涯走向（如考试评分）
- 产品的基于 AI 的安全组件（如机器人辅助手术中的 AI 应用）
- 用于就业、员工管理和自雇机会的 AI 工具（如招聘用的简历筛选软件）
- 某些用于获得基本私人和公共服务的 AI 用例（如信用评分拒绝公民获得贷款的机会）
- 用于远程生物特征识别、情绪识别和生物特征分类的 AI 系统（如事后识别商店扒手的 AI 系统）
- 执法中可能干涉人们基本权利的 AI 用例（如评估证据的可靠性）
- 移民、庇护和边境控制管理中的 AI 用例（如签证申请的自动审查）
- 司法行政和民主进程中使用的 AI 解决方案（如准备法院裁决的 AI 解决方案）

高风险 AI 系统在投放市场之前必须遵守严格义务：

- 充分的风险评估和缓解体系
- 喂养系统的高质量数据集，以最大程度降低歧视性结果的风险
- 活动日志记录，确保结果的可追溯性
- 详细文档，提供关于系统及其目的的所有必要信息，供主管部门评估其合规性
- 向部署者提供清晰充分的信息
- 适当的人工监督措施
- 高水平的稳健性、网络安全和准确性

高风险 AI 的规则将于 2026 年 8 月和 2027 年 8 月生效。

### 透明度风险

这指的是与 AI 使用透明度需求相关的风险。《人工智能法》引入了具体的披露义务，以确保在必要时告知人类以维护信任。例如，在使用聊天机器人等 AI 系统时，应让人类意识到他们在与机器互动，以便作出知情决定。

此外，生成式 AI 的提供者必须确保 AI 生成的内容可被识别。除此之外，某些 AI 生成的内容应被清晰、醒目地标注，即深度伪造（deepfakes）和以就公共利益事项告知公众为目的发布的文本。

《人工智能法》的透明度规则将于 2026 年 8 月生效。

### 风险最小或无风险

《人工智能法》没有为被视为风险最小或无风险的 AI 引入规则。目前欧盟使用的大多数 AI 系统都属于这一类别。这包括 AI 电子游戏或垃圾邮件过滤器等应用。

## 高风险 AI 系统提供者的符合性程序

一旦 AI 系统投放市场，主管部门负责市场监督，部署者确保人工监督和监控，提供者建立上市后监控系统。提供者和部署者还将报告严重事件和故障。

## 一般用途 AI 模型

一般用途 AI（GPAI）模型可以执行广泛的任务，正在成为欧盟许多 AI 系统的基础。其中一些模型如果能力非常强或被广泛使用，可能带来系统性风险。为确保安全和可信赖的 AI，《人工智能法》为此类模型的提供者制定了规则。这包括透明度和版权相关规则。对于可能带来系统性风险的模型，提供者应评估并缓解这些风险。《人工智能法》关于 GPAI 的规则已于 2025 年 8 月生效。

## 支持合规

2025 年 7 月，委员会发布三份关键文书，支持 GPAI 模型的负责任开发与部署：

- [关于 GPAI 模型提供者义务范围的指南](https://digital-strategy.ec.europa.eu/en/library/guidelines-scope-obligations-providers-general-purpose-ai-models-under-ai-act) 澄清了《人工智能法》下 GPAI 义务的范围，帮助 AI 价值链上的参与者了解谁必须遵守这些义务。
- [GPAI 实践守则](https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai) 是由独立专家提交给委员会的自愿合规工具，提供实用指导，帮助提供者遵守《人工智能法》下与透明度、版权以及安全和安保相关的义务。
- [GPAI 模型训练内容公开摘要模板](https://digital-strategy.ec.europa.eu/en/library/explanatory-notice-and-template-public-summary-training-content-general-purpose-ai-models) 要求提供者概述用于训练其模型的数据。这包括数据的来源（涵盖大数据集和顶级域名）。该模板还要求提供数据处理方面的信息，使具有合法利益的当事方能够依欧盟法律行使其权利。

这些工具设计为协同运作。它们共同为 GPAI 模型提供者遵守《人工智能法》提供了清晰可操作的框架，在保障基本权利和公众信任的同时减少行政负担并促进创新。

委员会还在开发其他工具，为如何遵守《人工智能法》的透明度规则提供指导：

- 由 AI 办公室选定的[关于 AI 生成内容标记和标注的实践守则](https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content)。该守则将是指导生成式 AI 系统提供者和部署者遵守透明度义务的自愿工具。这些义务包括标记 AI 生成内容，以及披露图像和音频（包括深度伪造）以及文本的人工属性。
- 《透明 AI 系统指南》，用于澄清适用范围、相关法律定义、透明度义务、例外及相关横向问题。

这些支持文书正在编制中，将于 2026 年第二季度发布。了解更多关于 [AI 办公室如何支持《人工智能法》的实施](https://digital-strategy.ec.europa.eu/en/news/supporting-implementation-ai-act-clear-guidelines)。

## 治理与实施

[欧洲 AI 办公室](https://digital-strategy.ec.europa.eu/en/policies/ai-office) 和成员国主管部门负责实施、监督和执行《人工智能法》。AI 委员会、科学小组和咨询论坛指导和咨询《人工智能法》的治理。了解更多关于 [《人工智能法》的治理与执行](https://digital-strategy.ec.europa.eu/en/policies/ai-act-governance-and-enforcement)。

## 适用时间表

《人工智能法》于 2024 年 8 月 1 日生效，两年后即 2026 年 8 月 2 日全面适用，但有一些例外：

- 被禁止的 AI 做法和 AI 素养义务自 2025 年 2 月 2 日起进入适用
- 治理规则和 GPAI 模型义务于 2025 年 8 月 2 日起适用
- 高风险 AI 系统（嵌入受监管产品）的规则有延长的过渡期，直至 2027 年 8 月 2 日

## 简化提案

[简化数字包](https://digital-strategy.ec.europa.eu/en/policies/digital-rulebook) 提议修订以简化《人工智能法》的实施，确保规则保持清晰、简单且有利于创新。

委员会提议将高风险规则适用的时间表调整至最长 16 个月。这确保规则在公司拥有合适的支持工具（如标准）以促进实施时适用。

委员会还提议对《人工智能法》进行有针对性的修订，将：

- 强化 AI 办公室的权力，并集中对基于一般用途 AI 模型构建的 AI 系统的监督，减少治理碎片化
- 扩大授予中小企业和小型中盘股公司的某些简化措施，包括简化的技术文档要求
- 要求委员会和成员国促进 [AI 素养](https://digital-strategy.ec.europa.eu/en/policies/ai-talent-skills-and-literacy)，并在现有努力（如 AI 办公室最近改版的 AI 素养实践库）基础上确保对企业的持续支持，同时保留对高风险部署者的培训义务
- 扩大支持合规的措施，使更多创新者受益于将从 2028 年起设立的监管沙盒，并扩大真实世界测试的可能性
- 调整《人工智能法》的程序，澄清其与其他法律的相互作用，并改善其整体实施和运作

所有这些都补充了委员会及其 AI 办公室已经在采取的行动，以为企业和国家主管部门提供清晰度，例如通过指南、实践守则和 [《人工智能法》服务台](https://ai-act-service-desk.ec.europa.eu/en)。

立法提案已于 11 月 19 日通过。欧洲议会和欧盟理事会现正讨论和谈判关于 AI 的数字综合法案（Digital Omnibus）。

## 快速链接

- [《人工智能法》单一信息平台](https://ai-act-service-desk.ec.europa.eu/en)
- [《人工智能法》所有欧盟官方语言文本](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:L_202401689)
- [AI 公约](https://digital-strategy.ec.europa.eu/en/policies/ai-pact)
- [GPAI 实践守则](https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai)
- [条例的影响评估](https://digital-strategy.ec.europa.eu/en/library/impact-assessment-regulation-artificial-intelligence)
- [支持影响评估的研究](https://digital-strategy.ec.europa.eu/en/library/study-supporting-impact-assessment-ai-regulation)
- [《人工智能法》问答](https://digital-strategy.ec.europa.eu/en/faqs/navigating-ai-act)
- [欧洲 AI 办公室](https://digital-strategy.ec.europa.eu/en/policies/ai-office)
- [《人工智能法》的治理与执行](https://digital-strategy.ec.europa.eu/en/policies/ai-act-governance-and-enforcement)
- [即将发布的《人工智能法》指南](https://digital-strategy.ec.europa.eu/en/news/supporting-implementation-ai-act-clear-guidelines)
- [《人工智能法》的标准化](https://digital-strategy.ec.europa.eu/en/policies/ai-act-standardisation)
