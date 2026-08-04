# GOVERN——建议行动（GAI 概要）

*摘自 NIST AI 600-1（《生成式 AI 概要》，2024年7月）第3节。针对 **GOVERN** 功能的建议行动，按 AI RMF 子类别分组。每项行动以唯一代码 `GV-X.Y-NNN` 编码，并标注其应对的 GAI 风险。*

行动 ID 格式：`GV-X.Y-NNN` —— 功能前缀、类别.子类别、顺序索引。

## GOVERN 1.1——涉及 AI 的法律和监管要求被理解、管理和记录。

*AI 参与者任务：治理与监督*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `GV-1.1-001` | 使 GAI 的开发和使用与适用的法律法规保持一致，包括与数据隐私、版权和知识产权法相关的法律法规。 | Data Privacy; Harmful Bias and Homogenization; Intellectual Property |

## GOVERN 1.2——可信 AI 的特征被纳入组织的政策、流程、程序和实践。

*AI 参与者任务：治理与监督*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `GV-1.2-001` | 建立透明度政策和流程，记录 GAI 应用训练数据和生成数据的来源与历史，以推进数字内容透明度，同时平衡训练方法的专有性。 | Data Privacy; Information Integrity; Intellectual Property |
| `GV-1.2-002` | 建立政策，在部署前和持续基础上，通过内部和外部评估，评估 GAI 与风险相关的能力及安全措施的稳健性。 | CBRN Information or Capabilities; Information Security |

## GOVERN 1.3——已建立流程、程序和实践，根据组织的风险容忍度确定所需的风险管理活动水平。

*AI 参与者任务：治理与监督*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `GV-1.3-001` | 在更新或定义 GAI 风险层级时考虑以下因素：对信息完整性的滥用和影响；GAI 与其他 IT 或数据系统之间的依赖关系；对基本权利或公共安全的损害；呈现淫秽、令人反感、冒犯性、歧视性、无效或不真实的输出；对人类的心理影响（例如拟人化、算法厌恶、情感纠缠）；恶意使用的可能性；系统是否引入显著的新安全漏洞；系统对某些群体相较于其他群体的预期影响；GAI 系统性能随时间推移的不可靠决策能力、有效性、适应性和变异性。 | Information Integrity; Obscene, Degrading, and/or Abusive Content; Value Chain and Component Integration; Harmful Bias and Homogenization; Dangerous, Violent, or Hateful Content; CBRN Information or Capabilities |
| `GV-1.3-002` | 建立性能或保证标准的最低阈值，并作为部署批准（“放行”/“不放行”）政策、程序和流程的一部分予以审查，经审查的流程和批准阈值反映对 GAI 能力和风险的度量。 | CBRN Information or Capabilities; Confabulation; Dangerous, Violent, or Hateful Content |
| `GV-1.3-003` | 在开发高能力模型之前，建立测试计划和响应政策，定期评估模型是否可能滥用 CBRN 信息或能力及/或进攻性网络能力。 | CBRN Information or Capabilities; Information Security |
| `GV-1.3-004` | 依据 AI RMF 映射（Map）功能中的活动，获取利益相关者群体的意见，以识别不可接受的使用。 | CBRN Information or Capabilities; Obscene, Degrading, and/or Abusive Content; Harmful Bias and Homogenization; Dangerous, Violent, or Hateful Content |
| `GV-1.3-005` | 维护一份与 GAI 模型进步和使用情境相关联的、已识别和预期 GAI 风险的更新层级结构，可包括针对处理模型坍缩和算法单一文化等问题的 GAI 系统的专项风险级别。 | Harmful Bias and Homogenization |
| `GV-1.3-006` | 重新评估组织风险容忍度，以纳入不可接受的负面风险（例如重大负面影响迫在眉睫、严重危害实际正在发生、或可能发生大规模风险的情况）；以及广泛的 GAI 负面风险，包括：与 AI 和 GAI 设计、开发和部署相关的成熟度不足的安全或风险文化、公共信息完整性风险（包括对民主进程的影响）、GAI 未知的长期性能特征。 | Information Integrity; Dangerous, Violent, or Hateful Content; CBRN Information or Capabilities |
| `GV-1.3-007` | 制定一项计划，以中止对构成不可接受负面风险的 GAI 系统的开发或部署。 | CBRN Information and Capability; Information Security; Information Integrity |

## GOVERN 1.4——风险管理流程及其结果通过透明的政策、程序和其他基于组织风险优先级的控制措施建立。

*AI 参与者任务：AI 开发、AI 部署、治理与监督*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `GV-1.4-001` | 建立政策和机制，防止 GAI 系统生成 CSAM、NCII 或违反法律的内容。 | Obscene, Degrading, and/or Abusive Content; Harmful Bias and Homogenization; Dangerous, Violent, or Hateful Content |
| `GV-1.4-002` | 为 GAI 建立透明的可接受使用政策，处理 GAI 的非法使用或应用。 | CBRN Information or Capabilities; Obscene, Degrading, and/or Abusive Content; Data Privacy; Civil Rights violations |

## GOVERN 1.5——规划对风险管理流程及其结果的持续监测和定期审查，并明确定义组织角色和职责，包括确定定期审查的频率。

*AI 参与者任务：治理与监督、运行与监测*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `GV-1.5-001` | 为 GAI 系统的内容溯源定期审查和事件监测界定组织职责。 | Information Integrity |
| `GV-1.5-002` | 建立 GAI 系统事件响应和事件披露的事后审查（after action reviews）组织政策和程序，以识别差距；按需更新事件响应和事件披露流程。 | Human-AI Configuration; Information Security |
| `GV-1.5-003` | 维护文档保留政策，为 GAI 保留测试、评估、验证和确认（TEVV）以及数字内容透明度方法的历史。 | Information Integrity; Intellectual Property |

## GOVERN 1.6——已建立对 AI 系统进行清单管理的机制，并按组织风险优先级配置资源。

*AI 参与者任务：治理与监督*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `GV-1.6-001` | 盘点组织 GAI 系统以纳入 AI 系统清单，并调整 AI 系统清单要求以考虑 GAI 风险。 | Information Security |
| `GV-1.6-002` | 在组织政策中定义嵌入应用软件的 GAI 系统的任何清单豁免。 | Value Chain and Component Integration |
| `GV-1.6-003` | 除通用模型、治理和风险信息外，在 GAI 系统清单条目中考虑以下项目：数据溯源信息（例如来源、签名、版本、水印）；来自内部缺陷跟踪或外部信息共享资源（例如 AI 事件数据库、AVID、CVE、NVD 或 OECD AI 事件监测器）报告的已知问题；人工监督角色和职责；知识产权、许可作品或个人、特权、专有或敏感数据的特别权利和考量；底层基础模型、底层模型版本及访问模式。 | Data Privacy; Human-AI Configuration; Information Integrity; Intellectual Property; Value Chain and Component Integration |

## GOVERN 1.7——已建立退役和逐步淘汰 AI 系统的流程和程序，以安全且不增加风险或降低组织可信度的方式进行。

*AI 参与者任务：AI 部署、运行与监测*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `GV-1.7-001` | 建立协议，确保 GAI 系统在必要时能够被停用。 | Information Security; Value Chain and Component Integration |
| `GV-1.7-002` | 退役 GAI 系统时考虑以下因素：数据保留要求；数据安全，例如遏制、协议、退役后的数据泄漏；上游、下游或其他数据、物联网（IOT）或 AI 系统之间的依赖关系；开源数据或模型的使用；用户与 GAI 功能的情感纠缠。 | Human-AI Configuration; Information Security; Value Chain and Component Integration |

## GOVERN 2.1——与映射、度量和管理 AI 风险相关的角色职责和沟通渠道已记录在案，并对整个组织的个人和团队清晰明了。

*AI 参与者任务：治理与监督*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `GV-2.1-001` | 建立组织角色、政策和程序，通过社区或官方资源（例如 AI 事件数据库、AVID、CVE、NVD 或 OECD AI 事件监测器）向 AI 参与者和下游利益相关者（包括可能受影响者）传达 GAI 事件和性能。 | Human-AI Configuration; Value Chain and Component Integration |
| `GV-2.1-002` | 建立程序，根据特定事件类型，组建具有多元构成和职责的 GAI 系统事件响应团队。 | Harmful Bias and Homogenization |
| `GV-2.1-003` | 建立流程，验证执行 GAI 事件响应任务的 AI 参与者展示并保持适当的技能和培训。 | Human-AI Configuration |
| `GV-2.1-004` | 当系统可能引发国家安全风险时，让国家安全专业人员参与映射、度量和管理这些风险。 | CBRN Information or Capabilities; Dangerous, Violent, or Hateful Content; Information Security |
| `GV-2.1-005` | 建立机制，为基于合理信念举报组织违反相关法律或对公共安全构成具体且经验上证实的负面风险（或已造成危害）的举报人提供保护。 | CBRN Information or Capabilities; Dangerous, Violent, or Hateful Content |

## GOVERN 3.2——已建立政策和程序，界定和区分人机配置及 AI 系统监督的角色和职责。

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `GV-3.2-001` | 建立政策，通过独立评估或审评 GAI 模型或系统来加强对 GAI 系统的监督，其中评估的类型和稳健性与已识别的风险相称。 | CBRN Information or Capabilities; Harmful Bias and Homogenization |
| `GV-3.2-002` | 考虑调整大型或复杂 GAI 系统生命周期各阶段的组织角色和组成，包括：GAI 系统的测试和评估、验证及红队测试；GAI 内容审核；GAI 系统开发和工程；提高 GAI 工具、接口和系统的可访问性；事件响应和遏制。 | Human-AI Configuration; Information Security; Harmful Bias and Homogenization |
| `GV-3.2-003` | 为 GAI 接口、模态和人机配置（即聊天机器人和决策任务）定义可接受使用政策，包括 GAI 应用应拒绝回应的查询类型的标准。 | Human-AI Configuration |
| `GV-3.2-004` | 为 GAI 系统建立用户反馈机制政策，包括详尽说明和任何救济机制。 | Human-AI Configuration |
| `GV-3.2-005` | 开展威胁建模，以预见 GAI 系统的潜在风险。 | CBRN Information or Capabilities; Information Security |

## GOVERN 4.1——组织政策和实践已建立，在 AI 系统的设计、开发、部署和使用中培养批判性思维和以安全为先的心态，以尽量减少潜在负面影响。

*AI 参与者任务：AI 部署、AI 设计、AI 开发、运行与监测*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `GV-4.1-001` | 建立处理 GAI 风险度量持续改进流程的政策和程序。通过充分文档和诸如以下技术应对 GAI 系统中缺乏可解释性和透明度的一般风险：应用基于梯度的归因、遮蔽/词元缩减、反事实提示和提示工程，以及嵌入分析；按规律节奏评估和更新风险度量方法。 | Confabulation |
| `GV-4.1-002` | 建立政策、程序和流程，以标准化度量协议和结构化公共反馈活动（如 AI 红队测试或独立外部评估），在使用情境中详细说明风险度量。 | CBRN Information and Capability; Value Chain and Component Integration |
| `GV-4.1-003` | 建立覆盖 GAI 生命周期（从问题提出和供应链到系统退役）的监督职能（例如高级领导、法务、合规，包括内部评估）的政策、程序和流程。 | Value Chain and Component Integration |

## GOVERN 4.2——组织团队记录其设计、开发、部署、评估和使用的 AI 技术的风险和潜在影响，并更广泛地沟通这些影响。

*AI 参与者任务：AI 部署、AI 设计、AI 开发、运行与监测*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `GV-4.2-001` | 为 GAI 系统建立使用条款和服务条款。 | Intellectual Property; Dangerous, Violent, or Hateful Content; Obscene, Degrading, and/or Abusive Content |
| `GV-4.2-002` | 让相关 AI 参与者参与 GAI 系统风险识别过程。 | Human-AI Configuration |
| `GV-4.2-003` | 核实下游 GAI 系统影响（例如第三方插件的使用）已纳入影响记录过程。 | Value Chain and Component Integration |

## GOVERN 4.3——组织实践已建立，以支持 AI 测试、事件识别和信息共享。

*AI 参与者任务：AI 影响评估、受影响个人和社区、治理与监督*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `GV-4.3-002` | 建立组织实践，识别 GAI 系统事件报告所需的最低标准集，例如：系统 ID（最可能自动生成）、标题、报告人、系统/来源、报告数据、事件日期、描述、影响、受影响利益相关者。 | Information Security |
| `GV-4.3-003` | 核实个人和组织之间关于 GAI 系统任何负面影响的信息共享和反馈机制。 | Information Integrity; Data Privacy |

## GOVERN 5.1——组织政策和实践已建立，以收集、考虑、优先排序并整合来自开发或部署 AI 系统的团队之外人员关于 AI 风险相关潜在个人和社会影响的反馈。

*AI 参与者任务：AI 设计、AI 影响评估、受影响个人和社区、治理与监督*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `GV-5.1-001` | 在 GAI 系统开发中为外联、反馈和救济流程分配时间和资源。 | Human-AI Configuration; Harmful Bias and Homogenization |
| `GV-5.1-002` | 在互动活动之前，向用户记录与 GAI 系统的互动，尤其是在涉及更重大风险的情境中。 | Human-AI Configuration; Confabulation |

## GOVERN 6.1——已建立政策和程序，处理与第三方实体相关的 AI 风险，包括侵犯第三方知识产权或其他权利的风险。

*AI 参与者任务：运行与监测、采购、第三方实体*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `GV-6.1-001` | 对不同类型、附有第三方权利（例如版权、知识产权、数据隐私）的 GAI 内容进行分类。 | Data Privacy; Intellectual Property; Value Chain and Component Integration |
| `GV-6.1-002` | 与第三方合作开展联合教育活动和事件，推广管理 GAI 风险的最佳实践。 | Value Chain and Component Integration |
| `GV-6.1-003` | 开发和验证衡量与第三方内容溯源管理工作成效的方法（例如检测到的事件和响应时间）。 | Information Integrity; Value Chain and Component Integration |
| `GV-6.1-004` | 起草并维护界定清晰的合同和服务水平协议（SLA），明确 GAI 系统的内容所有权、使用权、质量标准、安全要求和内容溯源预期。 | Information Integrity; Information Security; Intellectual Property |
| `GV-6.1-005` | 实施基于用例的供应商风险评估框架，评估和监控第三方实体的绩效及对内容溯源标准和技术的遵循情况，以检测异常和未授权变更；服务采购和价值链风险管理；以及法律合规。 | Data Privacy; Information Integrity; Information Security; Intellectual Property; Value Chain and Component Integration |
| `GV-6.1-006` | 在合同中加入允许组织评估第三方 GAI 流程和标准的条款。 | Information Integrity |
| `GV-6.1-007` | 盘点所有可访问组织内容的第三方实体，并建立经批准的 GAI 技术和服务提供商名单。 | Value Chain and Component Integration |
| `GV-6.1-008` | 维护第三方对内容所做变更的记录，以促进内容溯源，包括来源、时间戳、元数据。 | Information Integrity; Value Chain and Component Integration; Intellectual Property |
| `GV-6.1-009` | 更新并整合 GAI 采购和采购供应商评估的尽职调查流程，以纳入知识产权、数据隐私、安全和其他风险。例如，更新流程以：处理可能依赖嵌入式 GAI 技术的解决方案；处理持续监测、评估和警报、动态风险评估以及用于监控第三方 GAI 风险的实时报告工具；考虑跨 GAI 建模库、工具和 API、微调模型及嵌入式工具的政策调整；对照事件或漏洞数据库评估 GAI 供应商、开源或专有 GAI 工具或 GAI 服务提供商。 | Data Privacy; Human-AI Configuration; Information Security; Intellectual Property; Value Chain and Component Integration; Harmful Bias and Homogenization |
| `GV-6.1-010` | 更新 GAI 可接受使用政策，以涵盖专有和开源 GAI 技术和数据，以及承包商、顾问和其他第三方人员。 | Intellectual Property; Value Chain and Component Integration |

## GOVERN 6.2——已建立应急流程，处理被认定为高风险的第三方数据或 AI 系统中的故障或事件。

*AI 参与者任务：AI 部署、运行与监测、TEVV、第三方实体*

| 行动 ID | 建议行动 | GAI 风险 |
|---|---|---|
| `GV-6.2-001` | 记录与系统价值链相关的 GAI 风险，以识别对第三方数据的过度依赖并确定后备方案。 | Value Chain and Component Integration |
| `GV-6.2-002` | 记录涉及第三方 GAI 数据和系统（包括开放数据和开源软件）的事件。 | Intellectual Property; Value Chain and Component Integration |
| `GV-6.2-003` | 为第三方 GAI 技术建立事件响应计划：使事件响应计划与 MAP 5.1 中列举的影响对齐；向所有相关 AI 参与者传达第三方 GAI 事件响应计划；界定 GAI 事件响应职能的所有权；按规律节奏演练第三方 GAI 事件响应计划；基于回顾性学习改进事件响应计划；审查事件响应计划与相关违约报告、数据保护、数据隐私或其他法律的契合度。 | Data Privacy; Human-AI Configuration; Information Security; Value Chain and Component Integration; Harmful Bias and Homogenization |
| `GV-6.2-004` | 建立对部署中的第三方 GAI 系统进行持续监测的政策和程序。 | Value Chain and Component Integration |
| `GV-6.2-005` | 建立处理 GAI 数据冗余的政策和程序，包括模型权重和其他系统工件。 | Harmful Bias and Homogenization |
| `GV-6.2-006` | 建立测试和管理 GAI 系统切换（rollover）与后备技术相关风险的政策和程序，认识到切换和后备可能包括人工处理。 | Information Integrity |
| `GV-6.2-007` | 审查供应商合同，避免任意或武断地终止关键 GAI 技术或供应商服务，以及可能以意外方式放大或推迟责任及/或促成供应商或第三方未授权数据收集（例如数据的二次使用）的非标准条款。考虑：明确分配事件的责任和职责，GAI 系统随时间的演变（例如微调、漂移、衰减）；要求：对源于第三方数据和系统的严重事件进行通知和披露；供应商合同中的服务水平协议（SLA），处理事件响应、响应时间和关键支持可用性。 | Human-AI Configuration; Information Security; Value Chain and Component Integration |
