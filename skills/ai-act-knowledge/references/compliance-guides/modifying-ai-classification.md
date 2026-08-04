# 欧盟 AI 法案下修改 AI：分类与合规

关于 AI 系统的修改如何影响 AI 法案下的分类与合规义务的分析。

| 方面 | 详情 |
|--------|--------|
| 机构 | artificialintelligenceact.eu |
| 日期 | 2025 |
| 来源 URL | https://artificialintelligenceact.eu/modifying-ai-classification-compliance/ |
| NotebookLM 来源 ID | c96d4792-... |

*德文：Aenderung von KI gemaess der KI-Verordnung: Klassifizierung und Compliance*

---

本文是由法律合规专业人士 Oystein Endal、Andrea Vrcic、Sidsel Nag、Nick Malter 和 Daylan Araz 撰写的客座文章（见文末作者部分），内容基于他们经营或咨询整合 AI 的企业的经验。如有任何问题或建议，请联系 Nick Malter：nick@trail-ml.com。

> **免责声明：** 本文提供和讨论的信息不构成、也不意图构成法律意见。必要时请寻求专业法律顾问。欧盟 AI 法案的内容可能被以与本文所述不同的方式解释。

## 摘要

- 修改 AI 系统或模型（包括 GPAI 模型）的主体可能成为欧盟 AI 法案下的提供者，导致更高的合规负担。对 AI 系统、模型和用例进行恰当评估是关键。
- 对修改的恰当评估，以 AI 系统或 GPAI 模型的范围以及提供者角色的明确为前提。阅读[这篇关于"通用人工智能模型的提供者"的文章](https://artificialintelligenceact.eu/providers-of-general-purpose-ai-models-what-we-know-about-who-will-qualify/)了解更多信息。
- 当 AI 系统被修改且属于高风险时，或当 GPAI 模型的通用性、能力或系统性风险发生重大变化时，提供者的合规责任发生转移。GPAI 模型被微调时即可能出现这种情况。
- 欧盟 AI 法案，特别是 GPAI 模型提供者的义务，是可以管理的。保留技术文档和 GPAI 模型摘要仅限于修改的范围。在大多数情况下，这些甚至是为合规以外的目的所要求的。
- 欧盟委员会选择设定相对较高的、基于计算量的阈值来界定何种修改构成 GPAI 模型的实质性修改，目前预计只有少数修改者会成为 GPAI 模型提供者。

## 引言

欧盟 AI 法案主要规制通用人工智能（GPAI）模型和 AI 系统的提供者，为欧盟境内 AI 的开发与部署建立了全面框架。虽然欧盟 AI 法案明确将全新 AI 系统或 GPAI 模型的开发者认定为提供者，但当价值链下游的某方修改了第三方的既有 AI 系统或 GPAI 模型时，情况就变得更加复杂。这引发了关于合规责任的问题，具体而言是欧盟 AI 法案下的提供者义务应由谁承担、谁能履行。

欧盟 AI 法案承认修改情形，规定了 AI 系统或 GPAI 模型的修改者何时成为提供者——实际上将监管义务从原始提供者全部或部分转移给修改者。

这种合规责任的转移，尤其是涉及高风险 AI 系统或 GPAI 模型时，是企业通常希望避免的情形，因为会带来额外的合规成本和负担。在欧盟 AI 法案下对角色、风险类别或 AI 模型进行错误分类会给企业带来重大合规风险，因为不遵守高风险 AI 系统或 GPAI 模型条款可能导致最高 1,500 万欧元或全球年收入 3% 的罚款。

随着 GPAI 模型提供者义务自 2025 年 8 月 2 日起生效，关于 AI 模型和系统修改及其合规影响的讨论对企业而言已变得日益紧迫和相关。

在本文中，我们——一个由 AI 公约成员和 AI 法案早期采用者组成的工作组——讨论欧盟 AI 法案下修改所产生的分类问题，并从从业者视角探讨合规挑战。我们特别聚焦于 GPAI 模型和应用。

## 欧盟 AI 法案下修改存在的问题

由于欧盟 AI 法案的定义宽泛，企业很难判断何时修改会使自身对所用模型承担提供者义务。"实质性修改"的决定性定义（见[第 3(23) 条](https://artificialintelligenceact.eu/article/3/)）在欧盟 AI 法案中仍然表述模糊。这给组织带来了不确定性。

正确分类的挑战在企业基于 GPAI 模型（如 OpenAI 的 GPT-4.5 或 Anthropic 的 Sonnet 4）构建系统或应用的情形下尤为突出。这些模型被刻意设计为可跨广泛用例适应，并可由价值链中的下游运营者定制。在这些情形下，回答"谁需要履行何种义务"可能很困难。

欧盟委员会有一些（进行中的）旨在澄清 AI 法案概念的举措。就高风险 AI 系统而言，CEN/CENELEC 标准的制定正在进行中，预计最早于 2026 年发布。这些标准应就如何获得对欧盟 AI 法案关于高风险 AI 系统规定的合规推定提供具体指引，但不聚焦于 GPAI 模型。就 GPAI 模型而言，欧盟委员会 AI 办公室的[《GPAI 行为准则》](https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai)聚焦于履行 GPAI 模型提供者义务以及具有系统性风险的 GPAI 模型。该行为准则最近补充了官方的[《GPAI 提供者指南》](https://digital-strategy.ec.europa.eu/en/library/guidelines-scope-obligations-providers-general-purpose-ai-models-under-ai-act)（GPAI 指南）。虽然这些是良好的第一步，但关于修改者在实践中何时成为提供者仍存在不确定性。

GPAI 指南引入了一个阈值：训练原始 GPAI 模型所需初始计算能力的三分之一（以 [FLOPs](https://blog.heim.xyz/flop-for-quantity-flop-s-for-performance/) 衡量），作为实质性修改与非实质性修改的区分标准。该阈值旨在澄清合规义务何时转移给修改者。然而，这种基于计算量的阈值虽然对微调等某些修改可能有用，但对其他无需大量计算资源即可实质性改变模型行为和风险的修改类型可能仍然不够。指南指出，该阈值仅仅是一个指示性标准。根据 [GPAI 指南](https://digital-strategy.ec.europa.eu/en/library/guidelines-scope-obligations-providers-general-purpose-ai-models-under-ai-act)第 62 段，确定修改是否实质性的总体规则归结为：修改是否可能实质性改变模型的通用性、能力或系统性风险。

鉴于这些情况，组织在实施适当措施以遵守欧盟 AI 法案方面面临挑战，在确定其用例和修改是否首先使其有资格成为（GPAI 模型）提供者方面也面临挑战。

### AI 模型和系统修改的常见问题

- **时间问题：** GPAI 模型提供者义务自 2025 年 8 月 2 日起适用。企业仍在努力确定自身是否需要对提供者承担额外条款义务。
- **模糊性：** 修改触发提供者身份的条件仍然界定模糊，留下大量解释空间。
- **缺乏指引：** CEN/CENELEC 的官方标准尚未发布，无法提供亟需的指引。AI 办公室的 GPAI 指南发布较晚，仍留下一些未决问题和法律不确定性。
- **不切实际的提案：** GPAI 指南中提出的基于计算量的重大修改阈值实用性有限。该阈值可能难以测量，尤其对下游主体而言。此外，其他类型的修改可能不需要大量计算，但对模型和风险可能有重大影响。问题仍在于后者是否真的改变欧盟 AI 法案下的合规负担。
- **祖父条款问题：** 尚不清楚在 2025 年 8 月 2 日之后实质性修改既有 GPAI 模型的主体，在上游模型提供者可能直到 2027 年 8 月才须履行提供者义务的情况下，应如何履行提供者义务。
- **缺乏供应商透明度：** 很难对第三方 AI 系统和模型进行彻底的符合性与影响评估并保持控制。此外，由于供应商沟通不足，往往缺乏明确界定的合同义务，问责存在模糊性。

## 何种修改可使你成为提供者？

在考虑是否存在可使某人成为提供者的修改之前，建议先进行评估，判断手头的系统或模型是否实际属于欧盟 AI 法案中 AI 系统或 GPAI 模型定义的适用范围。这看似微不足道，但在对运营角色进行分类时，事实证明有时是困难的。

在欧盟 AI 法案下，有多种方式可以成为提供者，既在 AI 系统层面，也在 AI 模型层面。特别是，欧盟 AI 法案概述了几种情形，在此类情形下，修改或部署 AI 系统的企业可能继承提供者的角色和责任：

1. 将既有 AI 模型**集成**到新的或既有的 AI 系统中（见[第 3(68) 条](https://artificialintelligenceact.eu/article/3/)）
2. 将高风险 AI 系统**更名**为自己产品（见[第 25 条](https://artificialintelligenceact.eu/article/25/)）
3. **改变用途**，使 AI 系统或模型变为高风险（见[第 25 条](https://artificialintelligenceact.eu/article/25/)）
4. 对既有高风险 AI 系统或 GPAI 模型进行**（实质性）修改**（见[第 25 条](https://artificialintelligenceact.eu/article/25/)和[序言第 109 段](https://artificialintelligenceact.eu/recital/109/)）

第一种情形涉及欧盟 AI 法案对"下游提供者"的定义（见[第 3(68) 条](https://artificialintelligenceact.eu/article/3/)），该定义可能最准确地描述了当前许多组织的情况。例如，将自有模型（"BYOM"）引入 AI 系统可能构成集成。但是，成为下游提供者并不必然触发 GPAI 模型提供者合规责任的转移，因为该术语更准确地描述的是 AI 系统提供者的角色。在这种情况下，组织需要验证高风险 AI 系统义务或透明度义务是否适用，以及 GPAI 模型的上游提供者是否明确排除了该模型在欧盟内的分发和使用。

虽然第二种和第三种情形——更名和改变用途——作为合规责任转移的阈值通常相当直接，但涉及实质性修改的情形则更加模糊，给组织带来重大解释挑战。

## AI 系统的实质性修改

根据 AI 法案，实质性修改是指对 AI 系统作出的、原始提供者的合格评定未预见的变更，且该变更影响高风险 AI 系统要求的合规性或影响 AI 系统的预期目的（见[第 3(23) 条](https://artificialintelligenceact.eu/article/3/)和[序言第 128 段](https://artificialintelligenceact.eu/recital/128/)）。注意，对高风险 AI 系统的正式合格评定只有在存在进行外部审计的公告机构或可适用（CEN/CENELEC 制定的）统一标准时才能进行。截至撰写本文时，这因此还不是有用的指引。

AI 法案还在[第 25 条](https://artificialintelligenceact.eu/article/25/)中明确处理修改问题，规定对高风险 AI 系统的实质性变更将提供者角色转移给修改者——但前提是该系统仍然是高风险的。这使实质性修改的概念与修改对风险水平的影响挂钩。

## GPAI 模型的实质性修改

就 GPAI 模型的修改而言，欧盟 AI 法案的界定程度较低。[序言第 109 段](https://artificialintelligenceact.eu/recital/109/)和[欧盟委员会的 FAQ](https://digital-strategy.ec.europa.eu/en/faqs/general-purpose-ai-models-ai-act-questions-answers)澄清，GPAI 模型的提供者义务限于修改的范围，但欧盟 AI 法案并未将 GPAI 模型修改直接与特定风险水平挂钩（仅与系统性或非系统性风险挂钩）。此外，欧盟 AI 法案没有明确提及 GPAI 模型语境下的实质性修改——但它确实明确将 GPAI 模型的微调列为修改，这表明修改还需要对模型产生相当实质性的影响。AI 办公室在 [GPAI 指南](https://digital-strategy.ec.europa.eu/en/library/guidelines-scope-obligations-providers-general-purpose-ai-models-under-ai-act)中确认了后者，指出在其看来，修改通常涉及在额外数据上训练模型。指南还大量聚焦于对 GPAI 模型进行微调和再训练。

为进一步支持这一区分，[GPAI 指南](https://digital-strategy.ec.europa.eu/en/library/guidelines-scope-obligations-providers-general-purpose-ai-models-under-ai-act)引入了基于计算量的阈值：如果修改使用的计算资源至少占最初训练该模型所需计算资源的三分之一，则推定该修改者已成为 GPAI 模型提供者。虽然该阈值增加了一些清晰度，但其局限性在指南的公开征求意见期间被指出，并得到 AI 办公室的承认。该阈值可能无法覆盖低计算量但仍实质性影响模型风险状况的修改，而且修改者可能难以可靠估算所需计算量——尤其是在无法获得上游提供者信息的情况下。欧盟委员会选择设定相对较高的阈值，目前预计只有少数修改者会成为 GPAI 模型提供者。

同样，该阈值是一个指示性标准，其他模型修改也可能构成实质性修改。[第 25 条](https://artificialintelligenceact.eu/article/25/)（规制高风险 AI 系统变更的条款）的以风险为核心的逻辑是否如一些人所建议的那样也适用于 GPAI 模型的修改，仍是一个悬而未决的问题。

### AI 模型修改的类型

对 AI 模型的修改可以有多种形式。正如 [Philipp Hacker 和 Matthias Holweg（2025）](https://dx.doi.org/10.2139/ssrn.5289125)所概述的，对 AI 模型最相关的修改类型可归为以下几类：

1. **不改变：** 使用预训练 AI 模型而不作任何修改。
2. **修改超参数：** 调整温度等参数。
3. **检索增强生成（RAG）：** 构建通过引用外部知识库或专有数据来增强模型输出的应用。
4. **自定义 GPT：** 创建具有指定指令、工具和个性的基础模型变体。
5. **微调：** 在专有或领域特定数据集上训练基础模型以定制其性能。
6. **模型或知识蒸馏：** 基于较大"教师"模型的输出训练较小的"学生"模型，通常是为了降低计算需求。

正如 Hacker 和 Holweg（2025）所论证的，实质性修改（即实质性改变风险状况或模型行为）存在于微调、模型蒸馏、通过参数操纵越狱或改变模型核心架构的情形。其他修改，尤其是那些不改变 AI 模型的风险状况、架构、通用性或预期目的的修改，很可能属于非实质性，即不触发 GPAI 模型提供者义务的变化。

## 这在实践中意味着什么？

遵循欧盟 AI 法案的总体逻辑，无论涉及 AI 系统还是 GPAI 模型，将"是否存在合规责任变化"的评估锚定在"修改是实质性还是非实质性"的评估上是有用的——而这又需要考察修改对风险的影响。

对于 **AI 系统**，这项工作相对清晰：修改 AI 系统的企业应审查变更是否影响系统的风险分类，例如澄清其是否变为高风险或仍然属于高风险。

对于 **GPAI 模型**，这项工作稍微复杂一些。在获得进一步指引且标准到位之前，修改 GPAI 模型的企业可考虑两种方法：

- **更为保守的方法**，默认将任何适配都视为潜在触发 GPAI 模型提供者义务转移的因素。这实质上包括保存所执行修改的文档和摘要，即使这些可能并非强制要求。
- **更为务实的方法**，据此仅当修改明显改变模型的行为、通用性或风险状况，或达到计算阈值时，才假定 GPAI 模型提供者义务适用。这种方法限制治理负担，但若受到质疑，可能需要更有力的论证。

无论如何，企业在对 GPAI 模型或（高风险）AI 系统作出任何变更时，都应进行风险和影响评估。

## 生成式 AI 实践：从业者示例与未决挑战

为让读者了解从业者目前在正确分类方面面临的挑战，下文列出（部分匿名的）真实案例。同时也会强调 AI 法案下与生成式 AI 案例相关的、尚待解决的进一步合规挑战。

### 案例 1：企业 IT 服务提供者

一家企业 IT 服务提供者利用 OpenAI 的 GPT-4 模型提供并销售一个在集中式解决方案中编排不同聊天机器人的平台。最终用户随后既可以与机器人聊天获取一般知识，也可以在安全环境中获取其公司内部知识。这是一个非常常见的"自定义 GPT"案例，服务提供者将其修改局限于提示词变更和添加 RAG 技术，同时以新名称分发该系统。

IT 服务提供者在评估合规时特别关注以下考虑：

- 首先，尚不清楚围绕 GPT-4 模型构建自定义机器人并以自有品牌提供服务是否使其有资格成为 GPAI 模型提供者。
- 其次，对于 2025 年 8 月 2 日的 GPAI 截止日期是否适用于其未经实质性修改核心模型而销售基于 GPT 的解决方案的业务，存在困惑。
- 第三，他们在确保 OpenAI 交付所需文档方面存在困难。

虽然该 IT 服务提供者确实因集成 OpenAI 模型而符合下游提供者的资格，但他们既不符合高风险 AI 系统提供者的资格（在使用政策中被排除并通过技术手段受限），也不符合 GPAI 模型提供者的资格，因为其修改范围非常有限，并未显著改变模型的风险。在这种情形下，至少就合规目的而言，他们不需要依赖 OpenAI 的文档，也不面临 GPAI 模型条款下的额外义务。该 IT 服务提供者咨询了其中一位作者所在的合规公司 [Trail](https://www.trail-ml.com/)，并决定采取保守方法，即围绕 GPAI 系统的架构和功能保留足够的技术文档——这些文档无论如何都应为开发目的而可获取。

### 案例 2：规模化企业的智能体 AI 平台

一家瑞士规模化企业 [Unique AI](https://www.unique.ai/) 提供构建智能体 AI 解决方案的平台，帮助银行、保险公司和私募股权公司改善其财务运营。这些方案包括投资研究、尽职调查和 KYC 流程等工作流。这里的主要挑战是确保能够独立执行操作的 AI 代理的合规性和适当安全性。然而，其在欧盟 AI 法案下的角色起初并不明确。

Unique AI 对欧盟 AI 法案进行了深入研究，既在内部进行，也得到律师事务所 WalderWyss 的支持，并获得了一份关于 Unique AI 在欧盟 AI 法案下定位的法律意见。根据客户设置和部署模式，Unique AI 在欧盟 AI 法案下可能扮演各种角色。

大多数客户选择单租户部署模式，由 Unique AI 托管和运行软件。基于对欧盟 AI 法案的法律解释，Unique 的运营方式使其在提供 AI 系统和模型时被定位为分销商而非提供者。这是因为 Unique AI 利用 Microsoft Azure 和 OpenAI 模型等现有商业 AI 产品，并通过提示链、RAG 和提示转 SQL 技术以上下文特定功能加以丰富，而不改变原始大语言模型（LLM）。Unique AI 不使用客户数据进行模型训练，并排除高风险用途，这进一步支持了该分类。因此，该公司不认为自己是 GPAI 模型的修改者，GPAI 模型提供者义务仍由上游提供者承担。

他们采用了 AI 治理框架，作为其智能体 AI 开发的基础，将信任、安全、问责、可靠性和透明度嵌入每个智能代理和工作流的核心架构，同时定期的内部基准测试防止模型漂移，并在所有用例中保持一致的质量。

为主动推进 AI 法案合规，Unique AI 于 2024 年 6 月按照 [David Rosenthal 的方法论](https://www.vischer.com/en/knowledge/blog/part-7-the-eu-ai-act-what-it-means-in-practice-for-most-companies/)进行了内部合格评定，由公司的首席信息安全官和首席数据官牵头。

随着监管环境的持续演变，该公司通过持续更新其公开的 AI 治理框架、积极参与监管咨询，以及通过每年举办的 AI 治理圆桌会议等举措与行业同行进行开放透明的合作，保持前瞻性的方法。

## 展望未来

随着欧盟 AI 法案进一步进入实施阶段，仍存在未决问题和合规挑战，特别是对集成和修改 AI 模型和系统的企业而言。

无论如何，GPAI 模型提供者的总体义务是可以管理的，因为它们实质上仅限于在修改范围内保存技术文档和摘要。当然，具有系统性风险的 GPAI 模型提供者面临更复杂的合规要求。AI 办公室假定，截至今日，[只有少数下游修改会达到相应的计算阈值](https://digital-strategy.ec.europa.eu/en/library/guidelines-scope-obligations-providers-general-purpose-ai-models-under-ai-act)，从而触发合规责任的转移。适当的指引正在制定中，同时已有足够的提示和代理指标可供集成者和修改者在过渡期内朝欧盟 AI 法案合规的方向努力。

AI 办公室还在 [GPAI 指南](https://digital-strategy.ec.europa.eu/en/library/guidelines-scope-obligations-providers-general-purpose-ai-models-under-ai-act)中表示，预计在 2025 年 8 月截止日期方面存在合规困难的 GPAI 模型提供者（包括进行修改的提供者）应通过其最近启动的 [AI 法案服务台](https://ai-act-service-desk.ec.europa.eu/en)主动与 AI 办公室联系。欧盟各成员国设立的 AI 法案服务台，如[德国](https://www.bundesnetzagentur.de/SharedDocs/Pressemitteilungen/EN/2025/20250703_KI_ServiceDesk.html)和[奥地利](https://www.rtr.at/rtr/service/ki-servicestelle/KI-Servicestelle.en.html)的服务台，在复杂案件中也可以是主动联系主管机关的另一种选择。

此外，许多大型 GPAI 模型提供者已[承诺](https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai#ecl-inpage-Signatories-of-the-AI-Pact)遵守《GPAI 行为准则》，包括 [OpenAI](https://openai.com/global-affairs/eu-code-of-practice/)、[Anthropic](https://www.anthropic.com/news/eu-code-practice)、[Google](https://www.mlex.com/mlex/artificial-intelligence/articles/2370945/google-signs-eu-s-code-of-practice-for-ai-models) 和 [Mistral](https://www.linkedin.com/posts/audreyherblinstoop_we-were-the-first-to-announce-it-and-today-activity-7355617443525881858-OT9j/)，这表明它们也有意以适当的 AI 模型文档支持下游运营者。这有助于在未来几个月缓解上文强调的供应商透明度不足问题。

## 对组织的一般性建议

如果您担心欧盟 AI 法案下 GPAI 模型和系统的修改问题，请查阅 AI 办公室的[官方 GPAI 指南](https://digital-strategy.ec.europa.eu/en/policies/guidelines-gpai-providers)，并开始按照 AI 办公室的解释评估用例。该指南包含组织何时应被视为 GPAI 模型提供者的更多示例。

已经开始更详细地思考欧盟 AI 法案合规问题的组织，应利用这一势头主动推进 AI 治理举措，并认识到 AI 治理远不止于监管合规。欧盟委员会[AI 公约](https://digital-strategy.ec.europa.eu/en/policies/ai-pact)等自愿性计划为围绕欧盟 AI 法案开展同行交流提供了机会，并有助于获得内部支持和对 AI 治理的认识。例如，本文的撰稿人今年早些时候主动创建了一个小型的非正式 AI 公约成员社区（"AIPEX"），在直接会议中讨论当前挑战及解决方案，AI 办公室成员也抽出时间参加了一次他们的会议。

### 欧盟 AI 法案准备的推荐行动与资源

- **编制目录并对 AI 用例和系统进行分类**，因为这是评估欧盟 AI 法案下角色和风险的基础。您可以使用免费的合规检查工具，例如 [AI 办公室](https://ai-act-service-desk.ec.europa.eu/en/eu-ai-act-compliance-checker)的、[AI Act 网站](https://artificialintelligenceact.eu/assessment/eu-ai-act-compliance-checker/)上的，或 [AI 治理平台提供商 Trail](https://www.trail-ml.com/eu-ai-act-compliance-checker) 的工具。在边缘情形下，在内部和外部（如与律师事务所）进行彻底分析。
- **在集成或适配 GPAI 模型和 AI 系统时进行风险和影响评估。**
- **保存对 AI 系统或模型任何修改的文档。** 这是一项直接了当的措施，在法律不确定性时期尤其有用。即使未触发监管义务，这通常对内部利益相关者或客户也是有用且必要的。
- **保持信息更新**，关注欧盟 AI 法案的动态，在新指南发布时主动推进合规。更详细的分析和观点也有助于完善您的治理方法，例如 [Hacker 和 Holweg（2025）](https://dx.doi.org/10.2139/ssrn.5289125)提出的用于对 AI 模型修改进行细粒度区分的"计算量与后果筛查"方法。

## 关于作者

来自非正式的 AI 公约交流小组（"AIPEX"）：

- [Oystein Endal](https://www.linkedin.com/in/%C3%B8ystein-endal-10832162/)，金融服务业和保险业的 AI 风险与合规经理。
- [Andrea Vrcic](https://www.linkedin.com/in/andrea-johansson-vrcic-6716a81b2/)，金融服务业和保险业的 AI 监管法律顾问。
- [Sidsel Nag](https://www.linkedin.com/in/sidsel-nag/)，咨询业 AI 伦理、监管与治理经理，丹麦标准化委员会成员。
- [Nick Malter](https://www.linkedin.com/in/nickmalter/)，AI 治理软件公司 [trail GmbH](https://www.trail-ml.com/) 的 AI 政策与治理经理，AIPEX 小组发起人。

来自 [Unique AI](https://www.unique.ai/)：

- [Daylan Araz](https://www.linkedin.com/in/daylan-a-720ba5227/) 是苏黎世 Unique AI 的数据合规官。他在开发 Unique 的全面 AI 治理框架方面发挥了关键作用。他牵头取得了 ISO 42001 认证，并为 ISO 27001、ISO 9001 和 SOC 2 认证作出了贡献。如需更多信息，请联系：aigovernance@unique.ai。
