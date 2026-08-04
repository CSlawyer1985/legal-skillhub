# 主要生成式人工智能（GAI）考量因素（GAI 画像术语表）

*摘自 NIST AI 600-1 附录 A。跨领域 GAI 议题：治理、第三方、部署前测试、结构化公众反馈、内容溯源、事件披露。*

## 概述

以下主要考量因素是从 GAI PWG（生成式人工智能工作组）磋商过程中提炼出的总体主题。这些考量因素（治理、部署前测试、内容溯源和事件披露）供任何设计、开发和部署 GAI 的组织自愿使用，也为管理 GAI 风险的行动提供参考。此处包含的关于主要考量因素的信息并非详尽无遗，而是突出强调从 GAI PWG 中提炼出的最相关议题。

致谢：没有社区和 NIST 工作人员 GAI PWG 负责人——George Awad、Luca Belli、Harold Booth、Mat Heyman、Yooyoung Lee、Mark Pryzbocki、Reva Schwartz、Martin Stanley 和 Kyra Yee——的宝贵分析与贡献，这些考量因素不可能形成。

## A.1. 治理

## A.1.1. 概述

与其他任何技术系统一样，治理原则和技术可用于管理与生成式人工智能模型、能力和应用相关的风险。组织可以选择将现有的风险分级适用于 GAI 系统，也可以选择修订或更新人工智能系统风险等级以应对这些独特的 GAI 风险。本节描述组织治理制度如何在 GAI 语境下被重新评估和调整，也涉及整个人工智能价值链治理中的第三方考量因素。

## A.1.2. 组织治理

GAI 的机会、风险和长期性能特征通常不如非生成式人工智能工具那样被充分理解，而且人类对其的认知和应对方式可能差异很大。因此，GAI 可能需要人工智能行动者（AI Actor）提供不同层级的监督，或采用不同的人机配置，以有效管理其风险。组织对 GAI 系统的使用也可能需要额外的人工审查、跟踪与记录，以及更高层级的管理监督。

人工智能技术可以跨多种模态产生多种输出，并呈现多类用户界面。这导致更广泛的人工智能行动者出于差异巨大的应用和用途语境与 GAI 系统交互。这些应用可包括数据标注与准备、GAI 模型开发、内容审核、代码生成与审查、文本生成与编辑、图像与视频生成、摘要、搜索和聊天。这些活动可以发生在组织环境内或公共领域中。

组织可以限制造成损害、超出既定风险容忍度、或与其容忍度或价值观相冲突的人工智能应用。适用于其他类型人工智能系统的治理工具和协议可应用于 GAI 系统。这些计划和行动包括：

- 可及性与合理便利
- 人工智能行动者资质与资格
- 与组织价值观的一致性
- 审计与评估
- 变更管理控制
- 商业使用
- 数据溯源
- 数据保护
- 数据保留
- 关键术语定义使用的一致性
- 退役处理
- 不鼓励匿名使用
- 教育培训
- 影响评估
- 事件响应
- 监控
- 退出机制（Opt-outs）
- 基于风险的控制
- 风险映射与衡量
- 基于科学的测试、评估、验证与确认（TEVV）实践
- 安全软件开发实践
- 利益相关方参与
- 合成内容检测与标注工具和技术
- 举报人保护
- 劳动力多样性与跨学科团队

在正式的人机协作环境以及不同层级的人机配置中，为 GAI 的使用制定可接受使用政策和指引，有助于降低因误用、滥用、不当改造以及系统与用户之间不匹配而产生的风险。这些实践只是使既有治理协议适应 GAI 语境的一个例子。

## A.1.3. 第三方考量因素

组织可能寻求在企业的各种应用中获取、嵌入、整合或使用开源或专有的第三方 GAI 模型、系统或生成数据。对这些 GAI 工具和输入的使用会对组织的所有职能产生影响——包括但不限于采购、人力资源、法律、合规和 IT 服务——无论这些职能由员工还是第三方执行。上文引用的许多行动均具有相关性，并提供了应对第三方考量因素的选项。

第三方 GAI 集成可能引发知识产权、数据隐私或信息安全风险的增加，这提示需要就第三方数据作为模型输入的收集与使用制定明确的透明度和风险管理指引。组织可以考虑对基础模型、微调模型和嵌入式工具适用不同的风险控制，并强化与外部 GAI 技术或服务提供商的交互流程。组织可以将标准或既有风险控制和流程适用于专有或开源 GAI 技术、数据和第三方服务提供商，包括收购与采购尽职调查、索取软件物料清单（SBOM）、适用服务水平协议（SLA），以及依据证明标准声明（SSAE）报告，以促进 GAI 系统的第三方透明度和风险管理。

## A.1.4. 部署前测试概述

GAI 系统可能被开发、使用和改造的多种方式与语境，使风险映射和部署前测量工作变得复杂。稳健的测试、评估、验证与确认（TEVV）流程可以在人工智能生命周期的早期阶段迭代应用并记录在案，并以有代表性的人工智能行动者为参考（见 AI RMF 图 3）。在为 GAI 开发和成熟全新的、严格的早期生命周期 TEVV 方法之前，组织可以使用推荐的"部署前测试"实践来衡量性能、能力、局限、风险和影响。本节描述作为部署前 TEVV 组成部分的风险衡量与估计，并审视部署前测试方法论的现状。

## 当前部署前测试方法的局限

目前可用于 GAI 应用的部署前 TEVV 流程可能不充分、应用不系统，或未能反映部署语境、与部署语境不匹配。例如，通过电子游戏或为人类设计的标准化测试（如智力测验、职业资格考试）对 GAI 系统能力进行的轶事式测试，并不能保证 GAI 系统在这些领域的有效性或可靠性。同样，越狱（jailbreaking）或提示工程（prompt engineering）测试可能无法系统评估有效性或可靠性风险。

测量缺口可能源于实验室与真实环境设置之间的不匹配。当前的测试方法往往仍聚焦于实验室条件，或局限于基准测试数据集和 in silico（计算机模拟）技术，这些方法可能无法很好地外推至真实世界条件，或直接评估 GAI 在真实世界中的影响。例如，当前对 GAI 的测量缺口使得难以精确估计其潜在的生态系统层面或纵向风险，以及相关的政治、社会和经济影响。由于提示敏感性和使用语境的广泛异质性，基准与 GAI 系统真实世界使用之间的差距可能会扩大。

## A.1.5. 结构化公众反馈

结构化公众反馈可用于评估 GAI 系统是否按预期运行，并校准和验证传统测量方法。结构化反馈的例子包括但不限于：

- 参与式参与方法（Participatory Engagement Methods）：用于征求民间社会团体、受影响社区和用户反馈的方法，包括焦点小组、小型用户研究和调查。
- 现场测试（Field Testing）：用于确定人们如何与人工智能生成的信息互动、消费、使用和理解该信息，以及后续行动和效果的方法，包括用户体验（UX）、可用性及其他结构化、随机化实验。
- 人工智能红队（AI Red-teaming）：用于探测人工智能系统以发现缺陷和漏洞（如不准确、有害或歧视性输出）的结构化测试活动，通常在受控环境中并与系统开发者合作进行。

从结构化公众反馈中收集的信息可为设计、实施、部署批准、维护或退役决策提供依据。从这些活动中获得的成果和洞见可有多种用途，包括改进数据质量和预处理、加强治理决策，以及提升系统文档记录和调试实践。在实施反馈活动时，组织应遵循人类受试者研究要求和最佳实践，如知情同意和受试者补偿。

## 参与式参与方法

组织可以在临时或更结构化的基础上，设计和利用各种渠道让外部利益相关方参与产品开发或评审。与精选专家的焦点小组可就一系列问题提供反馈。小型用户研究可提供来自代表性群体或人群的反馈。匿名调查可用于征求或衡量对特定功能的反应。参与式参与方法通常不如现场测试或红队测试结构化，更常用于人工智能或产品开发的早期阶段。

## 现场测试

现场测试涉及用于评估风险和影响、模拟 GAI 系统部署条件的结构化环境。现场式测试可以从关注用户偏好和体验，转向关注人工智能风险和影响——包括负面和正面的。当与大量用户群体一起进行时，这些测试可以估算真实世界互动中风险和影响发生的可能性。

组织还可以在模型发布后的生产环境中直接向用户收集关于结果、损害和用户体验的反馈，并遵循知情同意和补偿等人类受试者标准。在实施反馈活动时，组织应遵循适用的人类受试者研究要求以及知情同意和受试者补偿等最佳实践。

## 人工智能红队

人工智能红队是一种不断发展的实践，指通常在受控环境中、并与正在开发人工智能模型的开发者合作开展的演练，以识别 GAI 模型或系统潜在的不良行为或后果、这些行为或后果可能如何发生，并对保障措施进行压力测试。人工智能红队可以在人工智能模型或系统向更广泛公众开放之前或之后进行；本节聚焦部署前语境中的红队测试。

人工智能红队输出的质量与红队自身的背景和专业水平相关。人口统计和学科多元的人工智能红队可以在 GAI 将被使用的各种语境中发现缺陷。为获得最佳效果，人工智能红队应展示领域专业知识，并了解部署语境中的社会文化层面。人工智能红队的结果在纳入组织治理与决策、政策和程序更新以及人工智能风险管理工作中之前，应进行额外分析。根据用例不同，可以适用不同类型的人工智能红队：

- 普通公众：由预期会使用模型或与其输出互动的一般用户（不一定是人工智能或技术专家）执行，他们将自己的亲身经历和视角带入人工智能红队任务。这些人可能已获得完成任务的指示和材料，而这些任务可能诱发有害的模型行为。这类演练与大型人工智能红队团队配合时可能更有效。
- 专家：由具备该领域或特定人工智能红队使用语境（如医学、生物技术、网络安全）专业知识的专家执行。
- 组合型：在难以识别和招募具备充分领域与语境专业知识的专家的情况下，人工智能红队演练可以同时利用专家和普通公众参与者。例如，专家红队成员可以修改或验证普通公众红队成员撰写的提示。这些方法还可能扩大人工智能风险攻击面的覆盖范围。
- 人机组合：由 GAI 与专家或非专家人类团队共同执行。GAI 主导的红队测试可能比纯人类红队更具成本效益。人类或 GAI 主导的人工智能红队可能更适合诱发不同类型的损害。

## A.1.6. 内容溯源概述

GAI 技术可用于许多应用，如内容生成和合成数据。GAI 输出的某些方面，例如深度伪造（deepfake）内容的生成，可能挑战我们区分人类生成内容与人工智能生成合成内容的能力。为帮助管理和缓解这些风险，溯源数据跟踪等数字透明机制可以追踪内容的来源和历史。溯源数据跟踪和合成内容检测有助于向用户提供关于真实内容和合成内容的更多信息访问，使其更好地了解人工智能系统的可信度。当与其他组织问责机制结合时，数字内容透明方法可以实现将负面结果追溯至其来源的流程，改善信息完整性，并维护公众信任。溯源数据跟踪和合成内容检测机制提供关于内容来源和历史的信息，以协助 GAI 风险管理工作。

溯源元数据可以包括关于 GAI 模型开发者或 GAI 内容创作者、创建日期/时间、地点、修改和来源的信息。可以对文本、图像、视频、音频和底层数据集跟踪元数据。溯源数据跟踪技术的实施有助于评估数字内容的真实性、完整性、知识产权和潜在篡改。一些知名的溯源数据跟踪技术包括数字水印、元数据记录、数字指纹和人工认证等。

## 溯源数据跟踪方法

用于 GAI 系统的溯源数据跟踪技术可用于跟踪数据输入、元数据和合成内容的历史与来源。溯源数据跟踪记录数字内容的来源和历史，从而可以确定其真实性。它由记录元数据以及在内容上添加显性和隐性数字水印的技术组成。数据溯源指通过元数据和数字水印技术跟踪输入数据的来源和历史。溯源数据跟踪流程可以包括并协助生命周期中可能无法全面了解或控制早期模型决策对下游性能和合成输出的各种权衡与级联影响的人工智能行动者。例如，通过选择水印模型来优先考虑稳健性（水印的持久性），人工智能行动者可能无意中降低计算复杂性（实施水印所需的资源）。组织加强内容溯源的风险管理工作包括：

- 跟踪 GAI 系统训练数据和元数据的溯源；
- 记录 GAI 系统内溯源数据的局限；
- 通过严格的 TEVV 流程监控部署中的系统能力和局限；
- 评估人类如何参与、互动或适应 GAI 内容（尤其是在以 GAI 内容为依据的决策任务中），以及他们对显性披露等溯源技术应用的反应。

组织可以记录并界定 GAI 系统的目标和局限，以识别溯源数据可能最有价值的缺口。例如，用于内容创作的 GAI 系统可能需要稳健的水印技术及相应的检测器来识别内容来源，或需要元数据记录技术以及元数据管理工具和存储库来追踪内容来源与修改。进一步将 GAI 任务定义收窄以纳入溯源数据，可以使组织最大限度地发挥溯源数据和风险管理工作的效用。

## A.1.7. 通过结构化公众反馈加强内容溯源

虽然自动错误收集系统等间接反馈方法很有用，但它们往往缺乏终端用户直接输入所能提供的语境和深度。组织可以利用部署前测试部分所述的反馈方法，通过人工智能红队等途径获取外部来源的输入。

将部署前和部署后的外部反馈整合到 GAI 模型及相应应用的监控流程中，有助于提高对性能变化的认知，并缓解输出带来的潜在风险和损害。在 GAI 系统和数字内容透明方法部署之前和之后，有多种方式可以捕获和利用用户反馈，以深入了解认证有效性和脆弱性、对抗性威胁对技术的影响，以及内容溯源方法对用户和社区产生意外后果的情况。此外，组织可以跟踪和记录数据集的溯源，以识别人工智能生成数据是 GAI 系统性能问题的潜在根本原因的情形。

## A.1.8. 事件披露概述

人工智能事件可以定义为"一个或多个人工智能系统的开发、使用或故障直接或间接导致以下损害之一的事件、情形或一系列事件：对个人或群体健康（包括心理损害和精神健康损害）造成伤害或损害；关键基础设施管理和运行的扰乱；侵犯人权或违反适用法律下旨在保护基本权利、劳动权利和知识产权的义务；或对财产、社区或环境造成损害。"人工智能事件可以以聚合形式发生（即系统性歧视），也可以以急性形式发生（即针对单个个体）。

## 人工智能事件跟踪与披露现状

目前不存在报告和记录人工智能事件的正式渠道。然而，已经建立了一些公开数据库来记录其发生。这些报告渠道以临时方式决定跟踪哪些类型的事件。例如，有些按媒体报道量进行跟踪。

记录、报告和分享关于 GAI 事件的信息，可以通过协助相关人工智能行动者将影响追溯至其来源，帮助缓解和预防有害后果。提高对 GAI 事件报告的认知和标准化，可以促进这种透明度，并改善整个人工智能生态系统中的 GAI 风险管理。

## 文档记录与人工智能行动者的参与

人工智能行动者应了解自己在报告人工智能事件中的角色。为更好地理解以往事件并采取措施防止未来发生类似事件，组织可以考虑制定公开事件报告指南，其中包含关于人工智能行动者职责的信息。这些指南将帮助人工智能系统运营者识别整个人工智能生命周期中的 GAI 事件，并与无论角色如何的人工智能行动者进行协调。在事件披露语境中，对 GAI 系统第三方输入和插件的文档记录与审查对人工智能行动者尤为重要；通过此类插件交付的 LLM 输入和内容往往呈分布式，且访问控制不一致或不充分。

包括记录、记载和分析 GAI 事件在内的文档记录实践，有助于与相关人工智能行动者更顺畅地分享信息。定期信息共享、变更管理记录、版本历史和元数据，也能为响应和管理人工智能事件的人工智能行动者提供支持。

- 附录 B 参考文献 Acemoglu, D. (2024) The Simple Macroeconomics of AI https://www.nber.org/papers/w32487 AI Incident Database. https://incidentdatabase.ai/

Atherton, D. (2024) Deepfakes and Child Safety: A Survey and Analysis of 2023 Incidents and Responses. AI Incident Database. https://incidentdatabase.ai/blog/deepfakes-and-child-safety/

Badyal, N. et al. (2023) Intentional Biases in LLM Responses. arXiv. https://arxiv.org/pdf/2311.07611 Bing Chat: Data Exfiltration Exploit Explained. Embrace The Red. https://embracethered.com/blog/posts/2023/bing-chat-data-exfiltration-poc-and-fix/

Bommasani, R. et al. (2022) Picking on the Same Person: Does Algorithmic Monoculture lead to Outcome Homogenization? arXiv. https://arxiv.org/pdf/2211.13972

Boyarskaya, M. et al. (2020) Overcoming Failures of Imagination in AI Infused System Development and Deployment. arXiv. https://arxiv.org/pdf/2011.13416

Browne, D. et al. (2023) Securing the AI Pipeline. Mandiant. https://www.mandiant.com/resources/blog/securing-ai-pipeline

Burgess, M. (2024) Generative AI's Biggest Security Flaw Is Not Easy to Fix. WIRED. https://www.wired.com/story/generative-ai-prompt-injection-hacking/

Burtell, M. et al. (2024) The Surprising Power of Next Word Prediction: Large Language Models Explained, Part 1. Georgetown Center for Security and Emerging Technology. https://cset.georgetown.edu/article/the-surprising-power-of-next-word-prediction-large-languagemodels-explained-part-1/

Canadian Centre for Cyber Security (2023) Generative artificial intelligence (AI) - ITSAP.00.041.

https://www.cyber.gc.ca/en/guidance/generative-artificial-intelligence-ai-itsap00041 Carlini, N., et al. (2021) Extracting Training Data from Large Language Models. Usenix. https://www.usenix.org/conference/usenixsecurity21/presentation/carlini-extracting

- Carlini, N. et al. (2023) Quantifying Memorization Across Neural Language Models. ICLR 2023. https://arxiv.org/pdf/2202.07646

- Carlini, N. et al. (2024) Stealing Part of a Production Language Model. arXiv. https://arxiv.org/abs/2403.06634

Chandra, B. et al. (2023) Dismantling the Disinformation Business of Chinese Influence Operations. RAND. https://www.rand.org/pubs/commentary/2023/10/dismantling-the-disinformation-business-ofchinese.html

Ciriello, R. et al. (2024) Ethical Tensions in Human-AI Companionship: A Dialectical Inquiry into Replika. ResearchGate. https://www.researchgate.net/publication/374505266_Ethical_Tensions_in_HumanAI_Companionship_A_Dialectical_Inquiry_into_Replika

Dahl, M. et al. (2024) Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models. arXiv. https://arxiv.org/abs/2401.01301

De Angelo, D. (2024) Short, Mid and Long-Term Impacts of AI in Cybersecurity. Palo Alto Networks. https://www.paloaltonetworks.com/blog/2024/02/impacts-of-ai-in-cybersecurity/

De Freitas, J. et al. (2023) Chatbots and Mental Health: Insights into the Safety of Generative AI. Harvard Business School. https://www.hbs.edu/ris/Publication%20Files/23-011_c1bdd417-f717-47b6-bccb5438c6e65c1a_f6fd9798-3c2d-4932-b222-056231fe69d7.pdf

Dietvorst, B. et al. (2014) Algorithm Aversion: People Erroneously Avoid Algorithms After Seeing Them Err. Journal of Experimental Psychology. https://marketing.wharton.upenn.edu/wpcontent/uploads/2016/10/Dietvorst-Simmons-Massey-2014.pdf

Duhigg, C. (2012) How Companies Learn Your Secrets. New York Times. https://www.nytimes.com/2012/02/19/magazine/shopping-habits.html

Elsayed, G. et al. (2024) Images altered to trick machine vision can influence humans too. Google DeepMind. https://deepmind.google/discover/blog/images-altered-to-trick-machine-vision-caninfluence-humans-too/

Epstein, Z. et al. (2023). Art and the science of generative AI. Science. https://www.science.org/doi/10.1126/science.adh4451

Feffer, M. et al. (2024) Red-Teaming for Generative AI: Silver Bullet or Security Theater? arXiv. https://arxiv.org/pdf/2401.15897

Glazunov, S. et al. (2024) Project Naptime: Evaluating Offensive Security Capabilities of Large Language Models. Project Zero. https://googleprojectzero.blogspot.com/2024/06/project-naptime.html

Greshake, K. et al. (2023) Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection. arXiv. https://arxiv.org/abs/2302.12173

Hagan, M. (2024) Good AI Legal Help, Bad AI Legal Help: Establishing quality standards for responses to people's legal problem stories. SSRN. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4696936

Haran, R. (2023) Securing LLM Systems Against Prompt Injection. NVIDIA. https://developer.nvidia.com/blog/securing-llm-systems-against-prompt-injection/

Information Technology Industry Council (2024) Authenticating AI-Generated Content. https://www.itic.org/policy/ITI_AIContentAuthorizationPolicy_122123.pdf

Jain, S. et al. (2023) Algorithmic Pluralism: A Structural Approach To Equal Opportunity. arXiv. https://arxiv.org/pdf/2305.08157

Ji, Z. et al (2023) Survey of Hallucination in Natural Language Generation. ACM Comput. Surv. 55, 12, Article 248. https://doi.org/10.1145/3571730

Jones-Jang, S. et al. (2022) How do people react to AI failure? Automation bias, algorithmic aversion, and perceived controllability. Oxford. https://academic.oup.com/jcmc/article/28/1/zmac029/6827859]

Jussupow, E. et al. (2020) Why Are We Averse Towards Algorithms? A Comprehensive Literature Review on Algorithm Aversion. ECIS 2020. https://aisel.aisnet.org/ecis2020_rp/168/

Kalai, A., et al. (2024) Calibrated Language Models Must Hallucinate. arXiv. https://arxiv.org/pdf/2311.14648

Karasavva, V. et al. (2021) Personality, Attitudinal, and Demographic Predictors of Non-consensual Dissemination of Intimate Images. NIH. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9554400/

Katzman, J., et al. (2023) Taxonomizing and measuring representational harms: a look at image tagging. AAAI. https://dl.acm.org/doi/10.1609/aaai.v37i12.26670

Khan, T. et al. (2024) From Code to Consumer: PAI's Value Chain Analysis Illuminates Generative AI's Key Players. AI. https://partnershiponai.org/from-code-to-consumer-pais-value-chain-analysis-illuminatesgenerative-ais-key-players/

Kirchenbauer, J. et al. (2023) A Watermark for Large Language Models. OpenReview. https://openreview.net/forum?id=aX8ig9X2a7

Kleinberg, J. et al. (May 2021) Algorithmic monoculture and social welfare. PNAS. https://www.pnas.org/doi/10.1073/pnas.2018340118

Lakatos, S. (2023) A Revealing Picture. Graphika. https://graphika.com/reports/a-revealing-picture Lee, H. et al. (2024) Deepfakes, Phrenology, Surveillance, and More! A Taxonomy of AI Privacy Risks. arXiv. https://arxiv.org/pdf/2310.07879 Lenaerts-Bergmans, B. (2024) Data Poisoning: The Exploitation of Generative AI. Crowdstrike. https://www.crowdstrike.com/cybersecurity-101/cyberattacks/data-poisoning/ Liang, W. et al. (2023) GPT detectors are biased against non-native English writers. arXiv. https://arxiv.org/abs/2304.02819 Luccioni, A. et al. (2023) Power Hungry Processing: Watts Driving the Cost of AI Deployment? arXiv. https://arxiv.org/pdf/2311.16863 Mouton, C. et al. (2024) The Operational Risks of AI in Large-Scale Biological Attacks. RAND. https://www.rand.org/pubs/research_reports/RRA2977-2.html. Nicoletti, L. et al. (2023) Humans Are Biased. Generative Ai Is Even Worse. Bloomberg.

- https://www.bloomberg.com/graphics/2023-generative-ai-bias/.

National Institute of Standards and Technology (2024) Adversarial Machine Learning: A Taxonomy and

Terminology of Attacks and Mitigations https://csrc.nist.gov/pubs/ai/100/2/e2023/final National Institute of Standards and Technology (2023) AI Risk Management Framework. https://www.nist.gov/itl/ai-risk-management-framework

National Institute of Standards and Technology (2023) AI Risk Management Framework, Chapter 3: AI Risks and Trustworthiness. https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Foundational_Information/3-sec-characteristics

National Institute of Standards and Technology (2023) AI Risk Management Framework, Chapter 6: AI RMF Profiles. https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Core_And_Profiles/6-sec-profile

- National Institute of Standards and Technology (2023) AI Risk Management Framework, Appendix A: Descriptions of AI Actor Tasks.

- https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Appendices/Appendix_A#:~:text=AI%20actors% 20in%20this%20category,data%20providers%2C%20system%20funders%2C%20product

- National Institute of Standards and Technology (2023) AI Risk Management Framework, Appendix B: How AI Risks Differ from Traditional Software Risks.

- https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Appendices/Appendix_B

National Institute of Standards and Technology (2023) AI RMF Playbook. https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook

National Institue of Standards and Technology (2023) Framing Risk https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Foundational_Information/1-sec-risk

National Institute of Standards and Technology (2023) The Language of Trustworthy AI: An In-Depth Glossary of Terms https://airc.nist.gov/AI_RMF_Knowledge_Base/Glossary

National Institue of Standards and Technology (2022) Towards a Standard for Identifying and Managing Bias in Artificial Intelligence https://www.nist.gov/publications/towards-standard-identifying-andmanaging-bias-artificial-intelligence

Northcutt, C. et al. (2021) Pervasive Label Errors in Test Sets Destabilize Machine Learning Benchmarks. arXiv. https://arxiv.org/pdf/2103.14749

- OECD (2023) "Advancing accountability in AI: Governing and managing risks throughout the lifecycle for trustworthy AI", OECD Digital Economy Papers, No. 349, OECD Publishing, Paris. https://doi.org/10.1787/2448f04b-en

- OECD (2024) "Defining AI incidents and related terms" OECD Artificial Intelligence Papers, No. 16, OECD Publishing, Paris. https://doi.org/10.1787/d1a8d965-en

- OpenAI (2023) GPT-4 System Card. https://cdn.openai.com/papers/gpt-4-system-card.pdf

- OpenAI (2024) GPT-4 Technical Report. https://arxiv.org/pdf/2303.08774 Padmakumar, V. et al. (2024) Does writing with language models reduce content diversity? ICLR.

- https://arxiv.org/pdf/2309.05196 Park, P. et. al. (2024) AI deception: A survey of examples, risks, and potential solutions. Patterns, 5(5).

- arXiv. https://arxiv.org/pdf/2308.14752

Partnership on AI (2023) Building a Glossary for Synthetic Media Transparency Methods, Part 1: Indirect Disclosure. https://partnershiponai.org/glossary-for-synthetic-media-transparency-methods-part-1indirect-disclosure/

Qu, Y. et al. (2023) Unsafe Diffusion: On the Generation of Unsafe Images and Hateful Memes From TextTo-Image Models. arXiv. https://arxiv.org/pdf/2305.13873

Rafat, K. et al. (2023) Mitigating carbon footprint for knowledge distillation based deep learning model compression. PLOS One. https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0285668

Said, I. et al. (2022) Nonconsensual Distribution of Intimate Images: Exploring the Role of Legal Attitudes in Victimization and Perpetration. Sage. https://journals.sagepub.com/doi/full/10.1177/08862605221122834#bibr47-08862605221122834

Sandbrink, J. (2023) Artificial intelligence and biological misuse: Differentiating risks of language models and biological design tools. arXiv. https://arxiv.org/pdf/2306.13952

Satariano, A. et al. (2023) The People Onscreen Are Fake. The Disinformation Is Real. New York Times. https://www.nytimes.com/2023/02/07/technology/artificial-intelligence-training-deepfake.html

Schaul, K. et al. (2024) Inside the secret list of websites that make AI like ChatGPT sound smart. Washington Post. https://www.washingtonpost.com/technology/interactive/2023/ai-chatbot-learning/

Scheurer, J. et al. (2023) Technical report: Large language models can strategically deceive their users when put under pressure. arXiv. https://arxiv.org/abs/2311.07590

Shelby, R. et al. (2023) Sociotechnical Harms of Algorithmic Systems: Scoping a Taxonomy for Harm Reduction. arXiv. https://arxiv.org/pdf/2210.05791

Shevlane, T. et al. (2023) Model evaluation for extreme risks. arXiv. https://arxiv.org/pdf/2305.15324 Shumailov, I. et al. (2023) The curse of recursion: training on generated data makes models forget. arXiv. https://arxiv.org/pdf/2305.17493v2

Smith, A. et al. (2023) Hallucination or Confabulation? Neuroanatomy as metaphor in Large Language Models. PLOS Digital Health. https://journals.plos.org/digitalhealth/article?id=10.1371/journal.pdig.0000388

Soice, E. et al. (2023) Can large language models democratize access to dual-use biotechnology? arXiv. https://arxiv.org/abs/2306.03809

Solaiman, I. et al. (2023) The Gradient of Generative AI Release: Methods and Considerations. arXiv. https://arxiv.org/abs/2302.04844

Staab, R. et al. (2023) Beyond Memorization: Violating Privacy via Inference With Large Language Models. arXiv. https://arxiv.org/pdf/2310.07298

Stanford, S. et al. (2023) Whose Opinions Do Language Models Reflect? arXiv. https://arxiv.org/pdf/2303.17548

Strubell, E. et al. (2019) Energy and Policy Considerations for Deep Learning in NLP. arXiv. https://arxiv.org/pdf/1906.02243

The White House (2016) Circular No. A-130, Managing Information as a Strategic Resource. https://www.whitehouse.gov/wpcontent/uploads/legacy_drupal_files/omb/circulars/A130/a130revised.pdf

The White House (2023) Executive Order on the Safe, Secure, and Trustworthy Development and Use of Artificial Intelligence. https://www.whitehouse.gov/briefing-room/presidentialactions/2023/10/30/executive-order-on-the-safe-secure-and-trustworthy-development-and-use-ofartificial-intelligence/

The White House (2022) Roadmap for Researchers on Priorities Related to Information Integrity Research and Development. https://www.whitehouse.gov/wp-content/uploads/2022/12/RoadmapInformation-Integrity-RD-2022.pdf?

Thiel, D. (2023) Investigation Finds AI Image Generation Models Trained on Child Abuse. Stanford Cyber Policy Center. https://cyber.fsi.stanford.edu/news/investigation-finds-ai-image-generation-modelstrained-child-abuse

Tirrell, L. (2017) Toxic Speech: Toward an Epidemiology of Discursive Harm. Philosophical Topics, 45(2), 139-162. https://www.jstor.org/stable/26529441

Tufekci, Z. (2015) Algorithmic Harms Beyond Facebook and Google: Emergent Challenges of Computational Agency. Colorado Technology Law Journal. https://ctlj.colorado.edu/wpcontent/uploads/2015/08/Tufekci-final.pdf

Turri, V. et al. (2023) Why We Need to Know More: Exploring the State of AI Incident Documentation Practices. AAAI/ACM Conference on AI, Ethics, and Society. https://dl.acm.org/doi/fullHtml/10.1145/3600211.3604700

Urbina, F. et al. (2022) Dual use of artificial-intelligence-powered drug discovery. Nature Machine Intelligence. https://www.nature.com/articles/s42256-022-00465-9

- Wang, X. et al. (2023) Energy and Carbon Considerations of Fine-Tuning BERT. ACL Anthology. https://aclanthology.org/2023.findings-emnlp.607.pdf

- Wang, Y. et al. (2023) Do-Not-Answer: A Dataset for Evaluating Safeguards in LLMs. arXiv. https://arxiv.org/pdf/2308.13387

Wardle, C. et al. (2017) Information Disorder: Toward an interdisciplinary framework for research and policy making. Council of Europe. https://rm.coe.int/information-disorder-toward-an-interdisciplinaryframework-for-researc/168076277c

Weatherbed, J. (2024) Trolls have flooded X with graphic Taylor Swift AI fakes. The Verge. https://www.theverge.com/2024/1/25/24050334/x-twitter-taylor-swift-ai-fake-images-trending

Wei, J. et al. (2024) Long Form Factuality in Large Language Models. arXiv. https://arxiv.org/pdf/2403.18802

- Weidinger, L. et al. (2021) Ethical and social risks of harm from Language Models. arXiv. https://arxiv.org/pdf/2112.04359 Weidinger, L. et al. (2023) Sociotechnical Safety Evaluation of Generative AI Systems. arXiv. https://arxiv.org/pdf/2310.11986

- Weidinger, L. et al. (2022) Taxonomy of Risks posed by Language Models. FAccT '22. https://dl.acm.org/doi/pdf/10.1145/3531146.3533088

West, D. (2023) AI poses disproportionate risks to women. Brookings. https://www.brookings.edu/articles/ai-poses-disproportionate-risks-to-women/

Wu, K. et al. (2024) How well do LLMs cite relevant medical references? An evaluation framework and analyses. arXiv. https://arxiv.org/pdf/2402.02008

Yin, L. et al. (2024) OpenAI's GPT Is A Recruiter's Dream Tool. Tests Show There's Racial Bias. Bloomberg.

- https://www.bloomberg.com/graphics/2024-openai-gpt-hiring-racial-discrimination/

Yu, Z. et al. (March 2024) Don't Listen To Me: Understanding and Exploring Jailbreak Prompts of Large Language Models. arXiv. https://arxiv.org/html/2403.17336v1

Zaugg, I. et al. (2022) Digitally-disadvantaged languages. Policy Review. https://policyreview.info/pdf/policyreview-2022-2-1654.pdf

Zhang, Y. et al. (2023) Human favoritism, not AI aversion: People's perceptions (and bias) toward generative AI, human experts, and human–GAI collaboration in persuasive content generation. Judgment and Decision Making. https://www.cambridge.org/core/journals/judgment-and-decisionmaking/article/human-favoritism-not-ai-aversion-peoples-perceptions-and-bias-toward-generative-aihuman-experts-and-humangai-collaboration-in-persuasive-contentgeneration/419C4BD9CE82673EAF1D8F6C350C4FA8

Zhang, Y. et al. (2023) Siren's Song in the AI Ocean: A Survey on Hallucination in Large Language Models.

- arXiv. https://arxiv.org/pdf/2309.01219

Zhao, X. et al. (2023) Provable Robust Watermarking for AI-Generated Text. Semantic Scholar. https://www.semanticscholar.org/paper/Provable-Robust-Watermarking-for-AI-Generated-Text-ZhaoAnanth/75b68d0903af9d9f6e47ce3cf7e1a7d27ec811dc
