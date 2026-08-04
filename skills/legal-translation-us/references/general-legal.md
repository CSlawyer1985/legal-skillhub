# 通用法律词典（基础层）

适用于**所有**法律文件的英文法律术语和惯例，无论源语言或具体领域。本文件始终加载。此外，应根据文件类型加载一个或多个领域特定词典：

- `finance-banking.md`——融资协议、担保文件、质押、抵押、债券、贷款、银行监管、银团贷款、AML/KYC、制裁、巴塞尔
- `corporate-ma-jv.md`——SPA、SHA、股东贷款、交易契据、披露函；JVA、联合体协议、共同投资协议；董事会决议、董事会会议记录、股东决议；授权委托书和代理
- `ndas-service-agreements.md`——保密协议、保密约定；服务协议、SLA、外包、咨询、托管服务
- `energy-infrastructure.md`——EPC/交钥匙合同、施工协议、运维（O&M）协议、BOP；PPA、并网、承购、特许经营、可再生能源、电价
- `ip-it-technology.md`——专利、商标、版权、许可、研发、技术转让；SaaS 协议、软件许可、云服务、开发协议
- `public-procurement.md`——招标、特许经营、PPP/PFI、国家援助、欧盟采购指令
- `real-estate.md`——租赁、不动产转让、地役权、分区、产权转移
- `litigation-settlement.md`——和解协议、责任解除、放弃、争议解决、仲裁、民事/行政/刑事程序
- `transport-and-insurance.md`——租船合同、提单、Incoterms、运费、海商法；保险单、再保险条约、索赔、代位求偿、劳合社市场
- `trading-capital-markets.md`——ISDA、衍生品、回购、证券借贷、EMIR、MiFID
- `consumer-retail.md`——条款与条件、特许经营、分销、代理、消费者保护
- `employment.md`——雇佣合同、竞业限制、遣散、集体谈判、借调
- `taxes.md`——企业所得税、个人所得税、增值税、转让定价、DAC6、支柱二、并购税务
- `permitting-environmental.md`——EIA、IED/IPPC、REACH、CLP、废弃物、水、土壤、气候、CSRD/CSDDD

如果一份文件横跨多个领域（例如作为并购流程一部分的保密协议），则同时加载两个相关词典。

**关于各语言子词典的说明。** 上述英文参考词典中，`finance-banking.md` 和 `trading-capital-markets.md` 仍是两个独立文件。在各语言子词典（`sub-lexicons/<语言>-<领域>.md`）中，两个领域合并为单一文件 `<语言>-finance-banking.md`，因为源语言侧词汇重叠严重。因此在处理资本市场文件时：加载两个参考文件，但只加载单一的各语言 `<语言>-finance-banking.md`。

## 子词典

各语言子词典（将源语言术语映射为本文件中的英文术语）存储在技能根目录的 `sub-lexicons/<语言>-<领域>.md`（如 `sub-lexicons/italian-real-estate.md`）。如存在源语言的子词典，请与本文件一同加载。子词典使用说明见主 SKILL.md。

---

## 合同订立与一般概念

| 正确英文术语 | 用法/含义 | 避免 |
|---|---|---|
| enter into (an agreement) | 订立（协议）的标准动词 | "stipulate"、"constitute" |
| create / grant (a right, a security interest) | 创设权利或担保权益的标准动词。注："establish a security interest" 也可接受。 | "constitute (a right)"（直译自大陆法） |
| representations and warranties | 一方对事实的陈述和承诺的标准表述 | "declarations and warranties"、"declarations and guarantees" |
| undertakings (UK finance) / covenants (M&A/US) / obligations (FIDIC/construction) | 一方承诺履行的合同承诺。使用与文件领域和起草传统相匹配的术语。 | — |
| consideration | 交换的有价之物；普通法概念。仅在适用英国法概念时包含。 | — |
| conditions precedent | 义务生效前必须满足的条件 | "suspensive conditions"（大陆法直译） |
| recitals | 合同的引言"鉴于"部分 | 将"preambles"或"premises"用作条款标题 |
| now, therefore, | 引言之"鉴于"与执行条款之间的标准过渡语 | "having established all the above" |

## 努力标准（Efforts and Endeavours）

这是最关键的翻译概念之一。英国法区分努力程度等级，选择会实质性地改变义务：

| 标准 | 含义 | 说明 |
|---|---|---|
| **best efforts** | 最高标准——必须尽一切所能，即使付出重大成本或不便 | 英式替代："best endeavours"。默认用"best efforts"。 |
| **all reasonable efforts** | 中等——必须探索并穷尽所有合理行动方案 | 英式替代："all reasonable endeavours"。默认用"all reasonable efforts"。 |
| **reasonable efforts** | 最低标准——必须采取一项合理行动方案，不必然穷尽所有选项 | 英式替代："reasonable endeavours"。默认用"reasonable efforts"。 |

大陆法系通常只有单一、不分等级的注意标准（如理性人标准，或"勤勉商人"标准）。翻译此类概念时，根据上下文和义务的分量判断最接近哪个英文标准。如有疑问，用"reasonable efforts"（最不繁重的标准）并提请审查律师注意。

在美式英文输出（默认）中，始终使用"efforts"。在英式英文输出（应请求）中，仍默认"efforts"，但注明"endeavours"是传统的英式替代。产出文件应保持一致——不得在同一文件中混用"efforts"和"endeavours"。

## 样板/杂项条款

| 正确英文术语 | 用法/含义 | 避免 |
|---|---|---|
| miscellaneous | 一般/样板条款的首选标题。"General Provisions"或"General"也可接受。 | "final provisions" |
| governing law and jurisdiction | 法律选择与争议法院的标准标题。可分为独立的"Governing Law"和"Jurisdiction"或"Dispute Resolution"条款。 | "applicable law and competent court"（直译） |
| dispute resolution | 合同在法院管辖之外或同时包含仲裁、调解或专家裁定条款时的标准标题 | — |
| service of process | 向一方送达法律文书的机制 | "election of domicile"（大陆法直译） |
| severability | 处理条款部分无效的条款 | 将"partial invalidity"、"partial nullity"用作标题 |
| amendment / modification | 对协议的变更。两者均可接受；"amendment"在美式和英式法律英语中均更常见。除非文件语境需要"modification"，默认用"amendment"。 | — |
| notices | 规定正式通信交付方式的条款 | 将"communications"、"contact details"用作标题 |
| waiver | 权利的放弃；在英国法下区别于"release"或"discharge" | — |
| assignment | 将协议项下权利/义务转让给第三方 | — |
| successors and assigns | 原始当事方之后受约束者的标准表述 | "successors and those who acquired title" |
| entire agreement | 声明合同是当事方之间完整协议的条款 | — |
| counterpart | 协议的每一份签署副本 | "exemplar"、"specimen" |
| forms part of (this Agreement) | 表述附件或附表被纳入的标准化说法 | "integral part"（直译） |
| order of precedence | 规定冲突时哪个文件优先的条款 | "conflict of provisions"、"prevalence" |
| freedom from encumbrances | 确认资产不受第三方权利负担 | "absence of charges" |

## 常见条款标题与概念

这些几乎出现在所有合同类型中：

| 正确英文术语 | 用法/含义 | 避免 |
|---|---|---|
| term and termination | 管辖合同期限和终止的条款的标准标题 | "duration and withdrawal" |
| force majeure | **权威定义**——当事方无法控制的不可预见事件（自然灾害、战争、疫情、恐怖主义、政府行为），在合同明示规定时免除履行义务。英国普通法不默示不可抗力原则；完全取决于合同条款。保留法语术语"force majeure"——被视为英国法的专门术语。领域变体：在保险和运输中，通常更窄且往往穷尽列举；在能源/EPC 中，通常与救济事件制度（FIDIC）配对；在 IT/SaaS 中，往往排除经济困难和劳资行动。 | "act of God"（过时，且更窄——仅限于自然力量）；"unforeseeable event"（不精确）；frustration（独立的英国普通法原则，适用于无不可抗力条款时） |
| limitation of liability | 对一方责任的合同上限或排除 | "limitation of damages" |
| liability cap | 协议项下的最高累计责任 | — |
| indemnification / indemnity | 赔偿损失义务。美式起草默认"indemnification"；英式起草默认"indemnity"。 | — |
| confidentiality | 施加保密义务的条款的标准标题 | 将"secrecy"、"non-disclosure"用作更广泛协议内的条款标题 |
| without prejudice | 权利保留；不放弃任何未明示放弃的权利 | — |
| notwithstanding | 优先语言——"notwithstanding Clause X"意为"尽管第 X 条如此规定" | — |
| subject to | 条件语言——"subject to Clause X"意为"以第 X 条为条件 / 受第 X 条限制" | — |
| material adverse change (MAC) / material adverse effect (MAE) | 对业务、资产或财务状况的重大不利变化或影响 | — |

## 诚实信用（Good Faith）

"Good faith"在普通法系和大陆法系中的分量差异极大。在英国法中，不存在一般的默示诚信义务（尽管这一点正在演变，且特定诚信义务可通过合同约定）。在大多数大陆法系，诚信是一项普遍且强制性的原则。翻译大陆法的"good faith"条款时，忠实地译为"good faith"——但要注意，阅读译文的英国律师可能以与大陆法律师不同的方式理解它。不得增加或删除源文本中没有的诚信义务。

## 人、实体与角色

| 正确英文术语 | 用法/含义 | 避免 |
|---|---|---|
| person | 包括自然人和法律实体，除非另有定义 | "subject"（直译） |
| third party | 非协议当事方的任何人 | — |
| competent authority | 拥有相关权力的政府机构或监管机关 | — |
| assets | 一方拥有的财产和权利（商业语境） | "patrimony"、"heritage"（直译） |
| estate | 死者或破产实体的财产（仅限继承/破产语境） | 在商业语境中使用"estate" |

## 公司标识

| 正确英文术语 | 用法/含义 | 避免 |
|---|---|---|
| registered office | 公司的官方法定地址 | — |
| principal place of business | 主要运营地点 | "operating office"（直译） |
| tax identification number | 税务目的的唯一个人标识符 | "tax code"（直译） |
| VAT registration number | 增值税标识符 | 将"VAT number"用作定义术语 |
| companies register / trade register | 公司信息存档的公共登记簿 | 与维护该登记簿的机构混淆 |
| share capital | 公司已发行股份的面值 | — |
| articles of association (UK) / by-laws (US) | 见 corporate-ma-jv.md 中的权威定义。 | — |
| casting vote | 主席行使的打破平局的决定性投票 | "double vote" |

## 交叉引用惯例

| 要素 | 正确英文 | 避免 | 说明 |
|---|---|---|---|
| 内部章节 | Section（美国默认）/ Clause（英国） | Article（用于内部引用） | "Article"适用于立法和章程/细则 |
| 小节 | paragraph | subsection、comma | — |
| 附件 | Schedule（英国）或 Annex（欧盟/国际） | — | 与源文件惯例一致；Appendix 也可接受 |
| 引言陈述 | Recital | Preamble、Whereas clause | — |
| 文件中前后 | above / below | "that precedes" / "that follows" | — |
| 自我指称 | this Deed / this Agreement | "the present deed"、"the present agreement" | — |

## 当事方引用

- 一致使用定义的当事方名称："the Grantor"、"the Borrower"（带"the"并大写）
- 在定义中，被定义的术语不带"the"
- **"hereby"**是法律英语中表达现在时完成行为的标准方式（如"the Grantor hereby pledges 出让人特此出质"）

## 应保留的拉丁语术语

以下拉丁语术语是英文法律文件的惯用表达，不应翻译：

inter alia、mutatis mutandis、pari passu、pro rata、bona fide、vis-à-vis、de facto、de jure、prima facie、sui generis、et seq.、ibid.、supra、infra、ad hoc、ab initio、ultra vires、intra vires、per se、in rem、in personam、lex loci、locus standi、pro forma、ex parte、inter vivos、mortis causa、ipso facto、sine die

## 语法与风格

从任何源语言翻译为英文法律语域时，适用以下规则：

- **"Shall" vs "will"/"must"**：传统法律英语用"shall"施加义务（"the Borrower shall repay"）；这是英国法律起草的规范，在美国法律起草中仍是主导惯例。现代简明英语起草（Bryan Garner、联邦法院风格指南）偏好"will"或"must"。与源文件预期受众的起草惯例相匹配。如果源文件来自魔圈所、顶级伦敦金融城或顶级华尔街律所语境，"shall"是预期用法。如果用户无偏好，默认用"shall"——它在美式和英式法律英语中读起来都正确。仅在用户明确要求简明英语起草时才使用"will"/"must"。
- **形容词位置**：英文形容词置于名词之前（"existing and future plants"，不是"plants existing and future"）。
- **冠词**：英文一致使用冠词（"the Borrower"，而非仅"Borrower"）。
- **不定冠词**："an Event"、"an Enforcement Event"（不是"a Event"）。
- **被动结构**：许多源语言过度使用被动语态；在英文读起来更自然的地方改为主动语态。
- **句长**：如有助于清晰，可将源语言的长句拆分为两个英文句子，前提是法律含义得以保留。
- **双重否定**：英文中简化（"cannot not" → "must" / "shall necessarily"）。
- **列举中的词序**：确保自然的英文语序（"all existing and future receivables"，不是"receivables existing and future"）。

## 日历惯例——强制（所有源语言）

英文译文中的所有日期必须为完整公历（西历）形式：`29 November 2017`、`1 April 2023`、`15 March 1989`。许多法域的起草使用非公历纪年；在英文输出中出现之前，将每个此类日期换算为公历对应日期。

法律文件中常见的纪年：

- **日本**——年号制（和暦）：令和 / Reiwa、平成 / Heisei、昭和 / Showa、大正 / Taisho、明治 / Meiji。
- **中华民国（台湾）**——民国纪年（民國）。民国 + 1911 = 公历。
- **泰国**——佛历（พ.ศ. / B.E.）。B.E. − 543 = 公历。
- **回历/伊斯兰历**——A.H.（ھ）。太阴历；换算不简单——使用换算表或可信换算工具。
- **韩国檀君纪年**——现代法律起草中罕见。檀君 − 2333 = 公历。
- **希伯来历创世纪年**——A.M.。现代法律起草中罕见。

**规则（严格）：将每个日期换算为公历。** 不得在输出中保留源语言的年号名称，即使是括号注也不保留。英文文件必须读起来像全程以公历起草——不出现 `Reiwa 5`、`Heisei 29`、`Minguo 110`、`B.E. 2566`、`A.H. 1445`。

各语言年号对照表、换算细节和占位符处理（如未填写日期格中的日文`〇`），见相应的 `<语言>-general-legal.md` 子词典。

## 美式 vs 英式英语

默认使用**美式英语**拼写和惯例。仅在用户指定或文件语境明确要求时使用英式英语（如适用英国法或面向英国受众的文件）。

需保持一致的关键差异：

| 美式英语（默认） | 英式英语（应请求） |
|---|---|
| favor, honor, color | favour, honour, colour |
| organize, recognize | organise, recognise |
| program | programme（但软件用 program） |
| defense、license（名词）、practice（名词） | defence、licence（名词）、practise（动词） |
| Section | Clause |
| Exhibit / Schedule | Schedule |
| closing | completion |
| amendment（也可用 "modification"） | amendment |
| indemnification | indemnity |
| best efforts | best endeavours（传统英式）/ best efforts |
| while | whilst（传统） |

产出美式英文时，全文保持一致。不得混用美式和英式惯例。

## 封面页与行政性措辞

封面页、标题块和签署块是**读者最先看到的内容**。它们使用公式化的行政语言，特别容易产生直译腔——逐字翻译但在英文中读起来不自然的短语。始终将封面页作为独立的英文重新通读，并改写任何母语者不会写的结构。

| 正确英文 | 避免 | 说明 |
|---|---|---|
| authorized representative | "representative acting on behalf of the organization" | 大陆法语言使用冗长结构；英文简洁 |
| Authorized signatory: [name] | "Authorized representative and signature: [name]" | 人是**签署人**（signatory，名词：签名的人）；"signature"是纸上的签名。在封面页和签署块中，指人时始终用 **signatory**。切勿写"authorized representative and signature"——这是匈牙利语（"jogosult képviselő és aláírás"）和意大利语（"rappresentante autorizzato e firma"）的直接直译。正确形式："Authorized signatory"、"Signatory"、"Signed by" |
| Title: [Managing Director] | "Position: …" / "Function: …" / "Capacity: …" | 在英文签署块中，签署人角色上方的标签永远是 **"Title"**——绝不使用"Position"、"Function"、"Capacity"或"Role"。无论源语言用什么均如此：荷兰语 *Functie*、意大利语 *Qualifica*、法语 *Fonction*、德语 *Funktion* / *Stellung*、西班牙语 *Cargo*、葡萄牙语 *Cargo*、波兰语 *Stanowisko*、匈牙利语 *Beosztás*。全部译为"Title"。"Title:" 下的值是高管的公司职务——"Managing Director"、"Director"、"Chief Executive Officer"、"Authorized Signatory"等。如源语言只给出如 *Directeur* 的通用词，不要凭空捏造头衔——签署人为公司董事时对荷兰/法语风格 *directeur* 译为"Managing Director"，明显是董事会成员时译为"Director"。 |
| Application under Call [reference] | "for the grant application under the above Call" / "Application under the 'Call'..." / "for the grant application entitled" | **直接且简洁。** 将征集编号紧贴"Call"——不要使用"under the above Call"或"for the grant application under..."等含糊关系从句。读者必须立即看出是哪次征集。如源语言还给出计划名称，追加："Application under Call [reference] — [Program name]"（征集 [编号] 申请——[计划名称]）。绝不截断，绝不使用间接措辞。 |
| Applicant: [name] | "Applicant organization: [name]" | 当实体名称已使"organization"显而易见时省略它 |
| signed by | "signed and authenticated by" | 除非适用特定的认证程序，英文中"Authenticated"是多余的 |
| on behalf of [entity] | "in the name and on behalf of [entity]" | 除非有意区分"in the name of"和"on behalf of"的法律差异 |
| [Title], dated [date] | "the [Title] bearing the date of [date]" | 大陆法文书中常见的冗长直译 |
| pursuant to | "on the basis of and pursuant to" | 选一个；不要堆叠两者 |
| duly authorized | "duly invested with powers" / "endowed with necessary powers" | 大陆法授权委托书语言的直译 |

**封面页完整性规则：** 封面页上的每个字段必须**完整**翻译。绝不截断短语、漏掉编号或留下部分翻译的字段。封面页是读者最先看到的内容——不完整或被截断的字段立刻表明翻译质量差。翻译封面页后，将其作为独立英文重新通读并核验：(a) 每个字段完整，(b) 无源语言残片残留，(c) 措辞是英语母语者会写的，(d) 该用"signatory"处未用"signature"。

## 定义部分

当文件包含定义部分时：

- 定义必须**按英文定义术语的字母顺序重新排序**
- 源语言往往有不同的字母顺序——始终重新排序
- 多段定义（含子项或示例）必须保持成组
- 应用翻译后，使用随附的 `reorder_definitions.py` 脚本
