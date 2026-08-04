# 通用法律词典（基础层）

适用于**所有**法律文件的英语法律术语和惯例，无论源语言或具体领域如何。本文件始终加载。此外，应根据文件类型加载一个或多个领域特定词典：

- `finance-banking.md` —— 融资协议、担保文件、质押、抵押、债券、贷款、银行业监管、银团贷款、AML/KYC、制裁、巴塞尔协议
- `corporate-ma-jv.md` —— 股权转让协议（SPA）、股东协议（SHA）、股东贷款、交易契据、披露函；合资协议（JVA）、联合体协议、共同投资协议；董事会决议、董事会纪要、股东决议；授权委托书和委托投票
- `ndas-service-agreements.md` —— 保密协议、保密约定；服务协议、SLA、外包、咨询、管理服务
- `energy-infrastructure.md` —— EPC/交钥匙合同、施工协议、O&M 协议、BOP；购电协议（PPA）、并网、承购、特许经营、可再生能源、电价
- `ip-it-technology.md` —— 专利、商标、版权、许可、研发、技术转让；SaaS 协议、软件许可、云服务、开发协议
- `public-procurement.md` —— 招标、特许经营、PPP/PFI、国家援助、欧盟采购指令
- `real-estate.md` —— 租赁、财产转让、地役权、分区、产权转移
- `litigation-settlement.md` —— 和解协议、放弃、弃权、争议解决、仲裁、民事/行政/刑事程序
- `transport-and-insurance.md` —— 租船合同、提单、Incoterms、运费、海商法；保险单、再保险合同、索赔、代位求偿、劳合社市场
- `trading-capital-markets.md` —— ISDA、衍生产品、回购、证券借贷、EMIR、MiFID
- `consumer-retail.md` —— 条款和条件、特许经营、分销、代理、消费者保护
- `employment.md` —— 雇佣合同、竞业禁止、遣散费、集体谈判、借调
- `taxes.md` —— CIT、PIT、增值税、转让定价、DAC6、支柱二、并购税务
- `permitting-environmental.md` —— EIA、IED/IPPC、REACH、CLP、废弃物、水、土壤、气候、CSRD/CSDDD

如果文件横跨多个领域（如作为并购过程一部分的 NDA），加载两个相关词典。

**关于按语言划分的子词典的说明。** 上面列出的英语参考词典中，`finance-banking.md` 和 `trading-capital-markets.md` 仍为两个独立文件。在按语言划分的子词典（`sub-lexicons/<语言>-<领域>.md`）中，两个领域合并为一个文件 `<语言>-finance-banking.md`，因为源语言侧词汇高度重叠。因此处理资本市场文件时：加载两个参考文件，但只加载单一按语言划分的 `<语言>-finance-banking.md`。

## 子词典

语言特定子词典（将源语言术语映射为本文件中的英语术语）存储于技能根目录，即 `sub-lexicons/<语言>-<领域>.md`（如 `sub-lexicons/italian-real-estate.md`）。如果源语言存在子词典，与本文件一起加载。子词典使用说明见主 SKILL.md。

---

## 合同订立与一般概念

| 正确英语术语 | 用法/含义 | 避免 |
|---|---|---|
| enter into (an agreement) | 订立合同的标准动词 | "stipulate"、"constitute" |
| create / grant (a right, a security interest) | 确立权利或担保权益的标准动词。注："establish a security interest"也可接受。 | "constitute (a right)"（直译） |
| representations and warranties | 一方对事实陈述和承诺的标准表述 | "declarations and warranties"、"declarations and guarantees" |
| undertakings (UK finance/LMA) / covenants (M&A/US) / obligations (FIDIC/construction) | 一方承诺履行的合同义务。使用与文件领域和起草传统匹配的术语。 | — |
| consideration | 交换的有价物；普通法概念。仅在适用英国法概念时使用。 | — |
| conditions precedent | 义务生效前必须满足的条件 | "suspensive conditions"（大陆法直译） |
| recitals | 合同的开头"鉴于"（whereas）部分 | 用"preambles"或"premises"作为条款标题 |
| now, therefore, | 序言与操作性条款之间的标准衔接 | "having established all the above" |

## 努力标准（Efforts and Endeavours）

这是最关键的翻译概念之一。英国法区分努力程度，而选择会实质性改变义务：

| 标准 | 含义 | 备注 |
|---|---|---|
| **best efforts** | 最高标准——必须尽一切所能，即使付出重大成本或不便 | 英式替代："best endeavours"。默认使用"best efforts"。 |
| **all reasonable efforts** | 中等——必须探索并穷尽所有合理行动方案 | 英式替代："all reasonable endeavours"。默认使用"all reasonable efforts"。 |
| **reasonable efforts** | 最低标准——必须采取一项合理行动方案，不必然穷尽所有选项 | 英式替代："reasonable endeavours"。默认使用"reasonable efforts"。 |

大陆法系通常有单一、不分层的注意标准（如理性人标准或"勤勉商人"标准）。翻译此类概念时，根据语境和义务的分量确定最接近的英语标准。如有疑问，使用"reasonable efforts"（负担最轻的标准）并标注供审查律师复核。

当用户要求美式英语输出时，通篇使用"efforts"。当用户要求英式英语输出时，仍默认使用"efforts"，但注明"endeavours"是传统的英式替代。产出的文件应保持一致——同一文件中不得混用"efforts"和"endeavours"。

## 样板条款/一般条款

| 正确英语术语 | 用法/含义 | 避免 |
|---|---|---|
| miscellaneous | 一般/样板条款的首选标题（英式）。"General Provisions"或"General"也可接受。 | "final provisions" |
| governing law and jurisdiction | 法律选择和争议法院的标准标题。可拆分为独立的"Governing Law"和"Jurisdiction"或"Dispute Resolution"条款。 | "applicable law and competent court"（直译） |
| dispute resolution | 合同包含仲裁、调解或专家裁定条款（与法院管辖并列或替代）时的标准标题 | — |
| service of process | 向一方送达法律文件的机制 | "election of domicile"（大陆法直译） |
| severability | 处理条款部分无效的条款 | 用"partial invalidity"、"partial nullity"作标题 |
| amendment (UK) / modification (US) | 对协议的修改。英式起草默认使用"amendment"。 | — |
| notices | 规定正式通知如何送达的条款 | 用"communications"、"contact details"作标题 |
| waiver | 放弃权利；在英国法下区别于"release"或"discharge" | — |
| assignment | 将协议项下的权利/义务转让给第三方 | — |
| successors and assigns | 原当事人之后受约束者的标准表述 | "successors and those who acquired title" |
| entire agreement | 声明合同是双方之间完整协议的条款 | — |
| counterpart | 协议的每一份签署副本 | "exemplar"、"specimen" |
| forms part of (this Agreement) | 说明附件或附录被纳入的标准方式 | "integral part"（直译） |
| order of precedence | 确立冲突时哪份文件优先的条款 | "conflict of provisions"、"prevalence" |
| freedom from encumbrances | 确认资产不受第三方权利负担 | "absence of charges" |

## 常见条款标题与概念

这些几乎出现在所有合同类型中：

| 正确英语术语 | 用法/含义 | 避免 |
|---|---|---|
| term and termination | 管辖合同存续期间和终止的条款的标准标题 | "duration and withdrawal" |
| force majeure | **标准定义**——超出当事人控制的不可预见事件（自然灾害、战争、大流行病、恐怖主义、政府行为），在合同明确约定时免除履行义务。英国普通法不默示不可抗力原则；它完全取决于合同条款。保留法语术语"force majeure"——被视为英语法律术语。领域变体：保险和运输中通常更窄、常为穷尽列举；能源/EPC中通常与救济事件制度配对（FIDIC）；IT/SaaS中通常排除经济困难和劳资行动。 | "act of God"（过时，且更窄——限于自然力量）；"unforeseeable event"（不精确）；frustration（不同的英国普通法理论，适用于无不可抗力条款时） |
| limitation of liability | 对一方责任的合同上限或排除 | "limitation of damages" |
| liability cap | 协议项下累计责任的最高总额 | — |
| indemnity (UK) / indemnification (US) | 赔偿损失义务。英式起草默认使用"indemnity"。 | — |
| confidentiality | 施加保密义务的条款的标准标题 | 用"secrecy"、"non-disclosure"作为更宽泛协议中的条款标题 |
| without prejudice | 权利保留；不放弃任何未明确放弃的权利 | — |
| notwithstanding | 优先效力用语——"notwithstanding Clause X"意为"尽管第 X 条如此规定" | — |
| subject to | 条件用语——"subject to Clause X"意为"以第 X 条为条件/受其限定" | — |
| material adverse change (MAC) / material adverse effect (MAE) | 对业务、资产或财务状况的重大负面变化或影响 | — |

## 诚信（Good Faith）

"诚信"在普通法和大陆法系法域中分量截然不同。英国法没有一般默示诚信义务（尽管这正在演变，且特定的诚信义务可以合同约定）。在大多数大陆法系中，诚信是普遍存在且强制性的原则。翻译大陆法系的"诚信"条款时，忠实译为"good faith"——但要意识到，阅读译本的英国律师可能会与大陆法系律师有不同的理解。不得添加或删除源文本中没有的诚信义务。

## 人、实体与角色

| 正确英语术语 | 用法/含义 | 避免 |
|---|---|---|
| person | 除非另行定义，包括自然人和法人实体 | "subject"（直译） |
| third party | 非协议当事人的任何人 | — |
| competent authority | 拥有相关权力的政府机构或监管机关 | — |
| assets | 一方拥有的财产和权利（商业语境） | "patrimony"、"heritage"（直译） |
| estate | 死者或破产实体的财产（仅继承/破产语境） | 在商业语境中使用"estate" |

## 公司识别信息

| 正确英语术语 | 用法/含义 | 避免 |
|---|---|---|
| registered office | 公司的官方法定地址 | — |
| principal place of business | 主要运营地点 | "operating office"（直译） |
| tax identification number | 税务用途的唯一识别号 | "tax code"（直译） |
| VAT registration number | 增值税识别号 | 用"VAT number"作为定义术语 |
| companies register / trade register | 公司信息备案的公共登记簿 | 与维护该登记簿的机构混淆 |
| share capital | 公司已发行股份的面值 | — |
| articles of association (UK) / by-laws (US) | 标准定义见 corporate-ma-jv.md。 | — |
| casting vote | 主席为打破平局行使的决定性表决权 | "double vote" |

## 交叉引用惯例

| 要素 | 正确英语 | 避免 | 备注 |
|---|---|---|---|
| 内部章节 | Clause（英式）/ Section（美式） | Article（用于内部引用） | "Article"适用于立法和公司章程/附则 |
| 子项 | paragraph | subsection、comma | — |
| 附件 | Schedule（英式）或 Annex（欧盟/国际） | — | 与源文件的惯例一致；Appendix 也可接受 |
| 引言陈述 | Recital | Preamble、Whereas clause | — |
| 文件中更早/更晚 | above / below | "that precedes" / "that follows" | — |
| 自我引用 | this Deed / this Agreement | "the present deed"、"the present agreement" | — |

## 当事人引用

- 一致使用定义中的当事人名称："the Grantor"、"the Borrower"（带"the"且首字母大写）
- 在定义中，被定义的术语不带"the"
- **"hereby"** 是法律英语中表达现在时施为性行为的标准方式（如"the Grantor hereby pledges"）

## 保留的拉丁语术语

这些拉丁语术语在英语法律文件中是惯例用法，不应翻译：

inter alia、mutatis mutandis、pari passu、pro rata、bona fide、vis-à-vis、de facto、de jure、prima facie、sui generis、et seq.、ibid.、supra、infra、ad hoc、ab initio、ultra vires、intra vires、per se、in rem、in personam、lex loci、locus standi、pro forma、ex parte、inter vivos、mortis causa、ipso facto、sine die

## 语法与风格

从任何源语言译为英语法律语体时，适用以下规则：

- **"Shall"与"will"/"must"**：英式法律英语传统上用"shall"施加义务（"the Borrower shall repay"）。现代简明英语起草和部分美国实务偏好"will"或"must"。与源文件预期受众的起草惯例匹配。如果源文件来自魔圈所或顶尖城市律所语境，预期使用"shall"。如果用户无偏好，英式默认"shall"，美式默认"will"或"must"。
- **形容词位置**：英语将形容词置于名词之前（"existing and future plants"，而非"plants existing and future"）。
- **冠词**：英语一致使用冠词（"the Borrower"，而非仅"Borrower"）。
- **不定冠词**："an Event"、"an Enforcement Event"（而非"a Event"）。
- **被动结构**：许多源语言过度使用被动语态；在英语中更自然的场合转为主动语态。
- **句子长度**：如果有助于清晰，可将非常长的源语言句子拆分为两个英语句子，前提是保留法律含义。
- **双重否定**：英语中简化（"cannot not" → "must" / "shall necessarily"）。
- **列举中的词序**：确保自然的英语顺序（"all existing and future receivables"，而非"receivables existing and future"）。

## 日历惯例——强制性（所有源语言）

英语翻译中的所有日期必须为完整公历（西历）形式：`29 November 2017`、`1 April 2023`、`15 March 1989`。许多法律体系以非公历日历起草日期；在出现在英语输出中之前，将每个此类日期转换为其公历对应日期。

法律文件中常见的日历：

- **日本**——年号制（和暦）：令和 / Reiwa、平成 / Heisei、昭和 / Showa、大正 / Taisho、明治 / Meiji。
- **中华民国（台湾）**——民国纪年（民國）。民国 + 1911 ＝ 公历。
- **泰国**——佛历（พ.ศ. / B.E.）。B.E. − 543 ＝ 公历。
- **回历/伊斯兰历**——A.H.（ھ）。太阴历；换算并非简单——使用换算表或可信的换算器。
- **韩国檀纪**——现代法律起草中罕见。檀纪 − 2333 ＝ 公历。
- **希伯来历创世纪元**——A.M.。现代法律起草中罕见。

**规则（严格）：将每个日期转换为公历。** 不要在输出中保留源语言的年号名称，即使括号内也不保留。英语文件必须读起来如同通篇以公历起草——不得出现 `Reiwa 5`、`Heisei 29`、`Minguo 110`、`B.E. 2566`、`A.H. 1445`。

各语言的年号换算表、转换细节和占位符处理（如未填写日期单元格中的日文 `〇` 空白），见相应的 `<语言>-general-legal.md` 子词典。

## 英式与美式英语

欧洲法律文件默认使用**英式英语**拼写和惯例。仅当用户指定或文件语境明确要求（如受美国法管辖的文件）时使用美式英语。

需要一致维持的关键差异：

| 英式英语（默认） | 美式英语（应要求） |
|---|---|
| favour、honour、colour | favor、honor、color |
| organise、recognise | organize、recognize |
| programme（但：软件用 program） | program |
| defence、licence（名词）、practice（名词） | defense、license（名词）、practice（名词） |
| Clause | Section |
| Schedule | Exhibit |
| completion | closing |
| amendment | modification |
| indemnity | indemnification |
| best endeavours（传统英式）/ best efforts | best efforts |
| whilst（传统） | while |

产出英式英语输出时，全篇保持一致。不得混用英式和美式惯例。

## 封面页与行政性措辞

封面页、标题栏和签名栏是**读者最先看到的内容**。它们使用公式化的行政语言，特别容易产生直译腔——逐字翻译但在英语中读起来不自然的短语。始终将封面页作为独立英语文本重新阅读，并改写任何母语者不会写的结构。

| 正确英语 | 避免 | 备注 |
|---|---|---|
| authorised representative | "representative acting on behalf of the organisation" | 大陆法语言使用冗长结构；英语简洁 |
| Authorised signatory: [name] | "Authorised representative and signature: [name]" | 人是**signatory**（名词：签署人）；"signature"是纸上的签名标记。在封面页和签名栏中，指人时始终使用**signatory**。绝不写"authorised representative and signature"——这是从匈牙利语（"jogosult képviselő és aláírás"）和意大利语（"rappresentante autorizzato e firma"）的直接直译。正确形式："Authorised signatory"、"Signatory"、"Signed by" |
| Title: [Managing Director] | "Position: …" / "Function: …" / "Capacity: …" | 在英语签名栏中，签署人职务上方的标签始终是**"Title"**——绝不用"Position"、"Function"、"Capacity"或"Role"。无论源文本使用什么均适用：荷兰语 *Functie*、意大利语 *Qualifica*、法语 *Fonction*、德语 *Funktion* / *Stellung*、西班牙语 *Cargo*、葡萄牙语 *Cargo*、波兰语 *Stanowisko*、匈牙利语 *Beosztás*。全部译为"Title"。"Title:" 下方的值是高管的公司职务——"Managing Director"、"Director"、"Chief Executive Officer"、"Authorised Signatory"等。如果源文本给出 *Directeur* 等通用词，不要臆造职务——签署人为公司董事时，荷/法式 *directeur* 译为"Managing Director"；明显为董事会成员时译为"Director"。 |
| Application under Call [reference] | "for the grant application under the above Call" / "Application under the 'Call'..." / "for the grant application entitled" | **直接简洁。** 将征稿编号紧贴"Call"——不要使用"under the above Call"或"for the grant application under..."等含糊的关系从句。读者必须立即看到这是哪个征稿。如源文本还点名了项目名称，附上："Application under Call [reference] — [Programme name]"。绝不截断，绝不使用间接措辞。 |
| Applicant: [name] | "Applicant organisation: [name]" | 当实体名称已经一目了然时去掉"organisation" |
| signed by | "signed and authenticated by" | 除非适用特定的认证程序，"Authenticated"在英语中是赘余的 |
| on behalf of [entity] | "in the name and on behalf of [entity]" | 除非有意区分"in the name of"与"on behalf of"的法律含义 |
| [Title], dated [date] | "the [Title] bearing the date of [date]" | 大陆法文书中常见的冗长直译 |
| pursuant to | "on the basis of and pursuant to" | 二选一；不要堆叠 |
| duly authorised | "duly invested with powers" / "endowed with necessary powers" | 大陆法授权委托书语言的直译 |

**封面页完整性规则：** 封面页上的每个字段都必须**完整**翻译。绝不截断短语、省略编号或留下部分翻译的字段。封面页是读者最先看到的内容——不完整或截断的字段立即表明翻译质量差。翻译封面页后，将其作为独立英语重新阅读并核实：(a) 每个字段完整；(b) 无源语言残片残留；(c) 措辞是英语母语者会写的；(d) 该用"signatory"之处未用"signature"。

## 定义部分

当文件包含定义部分时：

- 定义必须**按英语定义术语的字母顺序重新排序**
- 源语言通常有不同的字母顺序——始终重新排序
- 多段落定义（含子项或示例）必须保持组合在一起
- 应用翻译后，使用随附的 `reorder_definitions.py` 脚本
