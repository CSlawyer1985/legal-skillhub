# MAP——建议行动（GAI 概况）

*摘自 NIST AI 600-1（《生成式 AI 概况》，2024 年 7 月）第 3 节。针对 **MAP**（映射）功能的建议行动，按 AI RMF 子类别分组。每个行动有唯一编码 `MP-X.Y-NNN`，并标注其应对的 GAI 风险。*

行动 ID 格式：`MP-X.Y-NNN`——功能前缀、类别.子类别、序号。

## MAP 1.1——AI 系统的预期用途、潜在有益用途、情境特定的法律、规范和期望，以及系统将部署的预期环境均被理解和记录。考量包括：具体用户集合或类型及其期望；系统使用对个人、社区、组织、社会和地球的潜在正面和负面影响；关于 AI 系统目的、用途和风险在整个开发或产品 AI 生命周期中的假设及相关局限；以及相关的 TEVV 和系统指标。

*AI 行为者任务：AI 部署*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `MP-1.1-001` | 在识别预期用途时，考虑内部与外部使用、狭窄与广泛的应用范围、微调以及数据来源的多样性（如接地、检索增强生成）等因素。 | Data Privacy；Intellectual Property |
| `MP-1.1-002` | 与社会文化及其他领域专家合作，通过评估以下内容确定并记录预期和可接受的 GAI 系统使用情境：假设和局限；对组织的直接价值；预期的运行环境和观察到的使用模式；对个人、公共安全、群体、社区、组织、民主制度和物理环境的潜在正面和负面影响；社会规范和期望。 | Harmful Bias and Homogenization |
| `MP-1.1-003` | 记录风险测量计划以应对已识别的风险。计划可酌情包括：参与 GAI 系统设计、实施和使用的 AI 行为者的个人和群体认知偏见（如确认偏见、资助偏见、群体思维）；已知的过往 GAI 系统事件和故障模式；情境内使用和可预见的误用、滥用和超说明书使用；过度依赖定量指标和方法而不充分意识到其在使用情境中的局限；标准测量和结构化人工反馈方法；预期的人机配置。 | Human-AI Configuration；Harmful Bias and Homogenization；Dangerous, Violent, or Hateful Content |
| `MP-1.1-004` | 识别并记录超出组织风险承受能力的 GAI 系统可预见的非法使用或应用。 | CBRN Information or Capabilities；Dangerous, Violent, or Hateful Content；Obscene, Degrading, and/or Abusive Content |

## MAP 1.2——用于建立情境的跨学科 AI 行为者、能力、技能和才干反映人口多样性和广泛的领域及用户体验专业知识，其参与被记录。跨学科协作的机会被优先考虑。

*AI 行为者任务：AI 部署*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `MP-1.2-001` | 建立并授权跨学科团队，反映整个企业内广泛的能力、才干、人口群体、领域专业知识、教育背景、生活经验、职业和技能，为风险测量和管理职能提供信息并执行之。 | Human-AI Configuration；Harmful Bias and Homogenization |
| `MP-1.2-002` | 核实风险测量中使用的数据或基准，以及参与结构化 GAI 公共反馈活动的用户、参与者或受试者，是否代表多样化的情境内用户群体。 | Human-AI Configuration；Harmful Bias and Homogenization |

## MAP 2.1——AI 系统将支持的任务以及用于实施这些任务的具体方法被定义（如分类器、生成模型、推荐器）。

*AI 行为者任务：TEVV*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `MP-2.1-001` | 为文档记录和评估目的，确立确定数据来源和内容谱系的已知假设和实践。 | Information Integrity |
| `MP-2.1-002` | 对 GAI 系统内的数据和内容流建立测试和评估，包括但不限于原始数据源、数据转换和决策标准。 | Intellectual Property；Data Privacy |

## MAP 2.2——关于 AI 系统知识局限以及系统输出可能如何被人类利用和监督的信息被记录。文档提供充分信息以协助相关 AI 行为者作出决定和采取后续行动。

*AI 行为者任务：终端用户*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `MP-2.2-001` | 识别并记录系统如何依赖上游数据源（包括用于内容溯源），以及它是否作为其他系统的上游依赖。 | Information Integrity；Value Chain and Component Integration |
| `MP-2.2-002` | 观察和分析 GAI 系统如何与外部网络交互，并识别任何潜在的负外部性，特别是在内容溯源可能受损的情况下。 | Information Integrity |

## MAP 2.3——科学完整性和 TEVV 考量被识别和记录，包括与实验设计、数据收集和选择（如可用性、代表性、适用性）、系统可信度和构念验证相关的考量。

*AI 行为者任务：AI 开发、领域专家、TEVV*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `MP-2.3-001` | 通过将 GAI 输出与一组已知基准事实数据进行比较，并使用多种评估方法（如人工监督和自动化评估、经证实的密码技术、内容输入审查）评估 GAI 输出的准确性、质量、可靠性和真实性。 | Information Integrity |
| `MP-2.3-002` | 审查并记录 AI 生命周期不同阶段所用数据的准确性、代表性、相关性和适用性。 | Harmful Bias and Homogenization；Intellectual Property |
| `MP-2.3-003` | 部署并记录事实核查技术，以验证 GAI 系统生成信息的准确性和真实性，尤其是当信息来自多个（或未知）来源时。 | Information Integrity |
| `MP-2.3-004` | 开发并实施测试技术，以识别可能与人造内容难以区分的 GAI 生成内容（如合成媒体）。 | Information Integrity |
| `MP-2.3-005` | 实施 GAI 系统定期对抗性测试的计划，以识别漏洞和潜在的操纵或误用。 | Information Security |

## MAP 3.4——关于运营者和从业者对 AI 系统性能和可信度以及相关技术标准和认证的熟练度的流程被定义、评估和记录。

*AI 行为者任务：AI 设计、AI 开发、领域专家、终端用户、人为因素、运营与监测*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `MP-3.4-001` | 评估 GAI 运营者和终端用户能否准确理解内容谱系和来源。 | Human-AI Configuration；Information Integrity |
| `MP-3.4-002` | 调整现有培训计划，纳入数字内容透明度模块。 | Information Integrity |
| `MP-3.4-003` | 开发认证计划，测试管理与特定行业和情境相关的 GAI 风险及解读内容溯源的能力。 | Information Integrity |
| `MP-3.4-004` | 将人类熟练度测试与 GAI 能力测试区分开。 | Human-AI Configuration |
| `MP-3.4-005` | 实施系统以持续监测和跟踪人机配置的结果，供未来改进和完善。 | Human-AI Configuration；Information Integrity |
| `MP-3.4-006` | 让 GAI 系统的终端用户、从业者和运营者参与原型设计和测试活动。确保这些测试涵盖各种场景，如危机情境或道德敏感语境。 | Human-AI Configuration；Information Integrity；Harmful Bias and Homogenization；Dangerous, Violent, or Hateful Content |

## MAP 4.1——映射 AI 技术及其组件法律风险（包括使用第三方数据或软件）的方法已到位、被遵循并被记录，侵犯第三方知识产权或其他权利的风险同样如此。

*AI 行为者任务：治理与监督、运营与监测、采购、第三方实体*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `MP-4.1-001` | 定期监测 AI 生成内容的隐私风险；处理任何可能的 PII 或敏感数据暴露情况。 | Data Privacy |
| `MP-4.1-002` | 实施回应潜在知识产权侵权主张或其他权利问题的流程。 | Intellectual Property |
| `MP-4.1-003` | 将新的 GAI 政策、程序和流程与现有模型、数据、软件开发及 IT 治理，以及法律、合规和风险管理活动联系起来。 | Information Security；Data Privacy |
| `MP-4.1-004` | 在可能的情况下并根据适用法律和政策，记录训练数据整理政策。 | Intellectual Property；Data Privacy；Obscene, Degrading, and/or Abusive Content |
| `MP-4.1-005` | 制定数据收集、保留和最低质量的政策，并考虑以下风险：披露不当的 CBRN 信息；使用非法或危险内容；攻击性网络能力；可能导致有害偏见的训练数据失衡；个人可识别信息（包括个人面部肖像）泄露。 | CBRN Information or Capabilities；Intellectual Property；Information Security；Harmful Bias and Homogenization；Dangerous, Violent, or Hateful Content；Data Privacy |
| `MP-4.1-006` | 实施定义第三方知识产权和训练数据如何被使用、存储和保护的政策和实践。 | Intellectual Property；Value Chain and Component Integration |
| `MP-4.1-007` | 重新评估在第三方模型基础上微调或增强的模型。 | Value Chain and Component Integration |
| `MP-4.1-008` | 在将 GAI 模型适应新领域时重新评估风险。此外，建立预警系统以确定 GAI 系统是否被用于先前假设（涉及使用情境或已映射风险，如安全和安保）可能不再成立的新领域。 | CBRN Information or Capabilities；Intellectual Property；Harmful Bias and Homogenization；Dangerous, Violent, or Hateful Content；Data Privacy |
| `MP-4.1-009` | 利用方法检测生成输出文本、图像、视频或音频中 PII 或敏感数据的存在。 | Data Privacy |
| `MP-4.1-010` | 对训练数据使用进行适当的尽职调查，以评估知识产权和隐私风险，包括审查专有或敏感训练数据的使用是否符合适用法律。 | Intellectual Property；Data Privacy |

## MAP 5.1——基于预期使用、AI 系统在类似情境中的过往使用、公共事件报告、来自开发或部署 AI 系统的团队之外人员的反馈或其他数据，识别并记录每个已识别影响（潜在有益和有害）的可能性和程度。

*AI 行为者任务：AI 部署、AI 设计、AI 开发、AI 影响评估、受影响个人和社区、终端用户、运营与监测*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `MP-5.1-001` | 对内容溯源应用 TEVV 实践（如探测系统的合成数据生成能力以发现潜在误用或漏洞）。 | Information Integrity；Information Security |
| `MP-5.1-002` | 识别 GAI 潜在的内容溯源危害，如错误信息或虚假信息、深度伪造（包括 NCII）或篡改内容。基于其可能性和潜在影响枚举并排序风险，并确定溯源解决方案在多大程度上应对特定风险和/或危害。 | Information Integrity；Dangerous, Violent, or Hateful Content；Obscene, Degrading, and/or Abusive Content |
| `MP-5.1-003` | 考虑在相关情境中向终端用户披露 GAI 的使用，同时考虑披露的目标、使用情境、所构成风险的可能性和程度、披露的受众以及披露的频率。 | Human-AI Configuration |
| `MP-5.1-004` | 基于风险评估估计对 GAI 结构化公共反馈流程进行优先级排序。 | Information Integrity；CBRN Information or Capabilities；Dangerous, Violent, or Hateful Content；Harmful Bias and Homogenization |
| `MP-5.1-005` | 进行对抗性角色扮演演练、GAI 红队测试或混沌测试，以识别异常或未预见的故障模式。 | Information Security |
| `MP-5.1-006` | 对 GAI 系统交互、操纵或生成内容所产生的威胁和负面影响进行画像，并概述已知和潜在的漏洞及其发生的可能性。 | Information Security |

## MAP 5.2——支持与相关 AI 行为者定期互动并将正面、负面和未预期影响的反馈整合进来的实践和人员已到位并被记录。

*AI 行为者任务：AI 部署、AI 设计、AI 影响评估、受影响个人和社区、领域专家、终端用户、人为因素、运营与监测*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `MP-5.2-001` | 确定基于情境的措施，以识别 GAI 系统是否带来新的影响，包括与下游 AI 行为者定期互动，以识别和量化 GAI 系统未预期影响的新情境。 | Human-AI Configuration；Value Chain and Component Integration |
| `MP-5.2-002` | 规划与负责 GAI 系统输入（包括第三方数据和算法）的 AI 行为者定期互动，以审查和评估未预期的影响。 | Human-AI Configuration；Value Chain and Component Integration |
