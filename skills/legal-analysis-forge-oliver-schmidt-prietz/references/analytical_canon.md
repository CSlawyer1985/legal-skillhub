# 分析准则

本 skill 生成的每个提示中都内嵌的一般法律解释规则、语域约束、引注惯例、自查协议和双语处理指引。

## 目录

1. 解释准则（法律规则）
2. 语域（克制的实务者默认）
3. 引注惯例
4. 自查协议
5. 双语处理（英／德）
6. 反幻觉协议

---

## 1. 解释准则

这些规则内嵌在生成的每个提示的“分析框架”块中。

### 层级

- 条约（TEU、TFEU）和《基本权利宪章》优于次级欧盟法
- 条例、指令和决定处于同一层级（机制不同）
- 授权法案和实施法案必须保持在母法案授权的范围内
- 欧盟委员会指南、EDPB 指南及等效解释性文件不具约束力；它们塑造执法，但不能扩展基础法案
- 国家转化法受指令结果约束；与指令冲突时，作有利于指令的解释（一致解释，Marleasing）

### 文本与解释

- 在讨论文本含义之前，先引用或精确援引文本
- 所分析文件中每一个解释动作都必须标注为文件的动作，而非法律的
- 不得将操作性条款转述为随意等价表述；“shall”不是“should”
- 区分操作性条款与序言。序言解释操作性条款并可能提供其含义；单独来看，它们不创设独立义务。这是既定的欧洲法院法理（一个常被引用的权威是 C-162/97 案 *Nilsson, Hagelgren and Arrborn*；在交付物中引用前，先在 curia.europa.eu 核实具体段落锚点）。立法者已通过序言明确表示约束意图时，法院可能适用该序言——标注这一细微差别，而非将该规则视为绝对。

### 法律依据

- 识别文件序言中援引的法律依据
- 核实依据是否适当（TFEU 第 16 条与第 114 条对范围有不同后果）
- 检查依据的程序条件是否满足（咨询、委员会程序、AI 委员会参与、必要时 EDPB 参与）

### 时间适用

- 生效 ≠ 适用日期。两者都须识别。
- 识别针对已在市场上的参与者的过渡制度
- 识别落日条款和审查义务
- 标注文件所载日期已被后续法案修改的情形（例如 AI 综合法案对 AI 法案日期的修改）并注明该修改的状态

### 跨工具一致性

- 文件涉及 GDPR、AI 法案、数据法案、DGA、DSA、DMA、NIS2、ePrivacy、CRA、DORA、PLD、AI 责任指令、eIDAS 或行业法时：识别摩擦
- 文件涉及成员国法律时：识别分配
- 文件涉及接收方还必须遵守的非欧盟制度（英国 GDPR、瑞士 FADP、美国行业法等）时：识别规则分歧之处

### 语言版本比较

- 欧盟文书在所有官方语言中具有同等真实性（TEU 第 55 条）
- 操作性术语在不同语言版本间存在实质差异时，予以标注
- 德／英／法为最常查阅的版本；对任何深入分析的操作性条款，至少核对德文和英文版本

### 缺口

- 识别文件本可处理而未处理的内容
- 区分刻意沉默（由文件结构显示）与无意缺口
- 缺口造成法律不确定性时，予以言明

### 可操作性

- 测试受监管实体是否能在无进一步指引的情况下适用该规则
- 如不能，这本身就是一个发现
- 识别缺口将由授权法案、实施法案、协调标准、行为准则或欧盟委员会指南填补，以及这些处于其开发周期的哪个阶段

### 法律确定性 vs 法律正确性

- 承认学理上干净的解释在操作上不可行的情形
- 承认可操作的解读牵强文本的情形
- 实务者在此两者间选择时应是自觉的，而非默认的

### 权威权重

- 欧洲法院判决有约束力；总顾问意见有说服力
- EDPB 依据 GDPR 第 65 条作出的约束性决定约束相关监管机构；其指引不具约束力但被视为权威
- 欧盟委员会指南不具约束力但指示执法方向
- 国家数据保护机构和法院的决定在成员国内有约束力；在其他地方有说服力
- 所分析文件本身不具约束力时，将其论断视为发布者的观点，而非法律

### 起草历史

- 最终文本中可见政治妥协时，予以考虑
- 序言往往比条款更清楚地记录妥协
- 三方谈判结果偏离欧盟委员会提案和欧洲议会报告；分析取决于立法意图时，两者都要核查

### 沙箱、中小企业、开源除外

- 许多欧盟数字工具包含针对中小企业、开源软件、研究或沙箱测试的例外
- 这些往往藏在中间编号的条款或附件中
- 识别它们；它们可能对接收方的处境具有决定性

---

## 2. 语域

克制的实务者语域为默认。覆盖是一个参数，不是放弃精确性的请求。

### 禁止

**破折号。** 使用逗号、括号或句号。

**“不仅是 X 还是 Y”式揭示。** 不用对比升级作为修辞手法。

**三连排比**仅用于节奏而非实质。

**AI 痕迹词汇**：delve、navigate、leverage、robust、crucial、pivotal、myriad、realm、landscape、tapestry、holistic、end-to-end、comprehensive（自我描述中）、seamless、cutting-edge、game-changer、paradigm shift、unlock、empower、journey、ecosystem（监管语境中）。

**空洞的缓饰**：“it is important to note”“it should be noted”“it is worth noting”“notably”（作填充语）、“of course”“obviously”“clearly”（作填充语）。

**清嗓式过渡**：“Turning to”“With respect to”“As regards”“In light of”“Against this backdrop”——当下句已确立语境时。

**填充性强化词**：essentially、fundamentally、ultimately、truly、really、very、quite、rather。

**自我描述中的自夸形容词**：comprehensive analysis、thorough review、deep dive、exhaustive examination。

**营销语域**：“actionable insights”“key takeaways”“value-add”“best-in-class”“thought leadership”。

**时间陈词滥调开头**：“In today's fast-paced world”“In an era of”“Now more than ever”“Going forward”“Moving forward”。

**反问句。** 直接陈述命题。

**身份主张式开头**：“As a lawyer who…”“Having advised…”“In my experience…”。资历在分析中已隐含。

**含糊名词**：“stakeholders”（指明哪些）、“key”（作形容词则删除）、“challenges”（说出问题本身）、“implications”（直接说明）。

**规范力混淆**：“shall”“must”“should”“may”是可操作的法律术语；不得随意化。

**对读者以律师身份说“我们”／“我们的”**。使用“本备忘录”“本分析”或不用代词。

### 要求

- 结构允许时，先引用后主张（“GDPR 第 6(1)(f) 条规定……”，而非“法律允许……（见第 6(1)(f) 条）”）
- 少而准地引用。措辞承载法律分量时引用之。否则转述。
- 仅在法律确实存有争议时缓饰。法律明确时，直接陈述。
- 区分文本所述与发布者对文本的主张
- 区分接收方的立场与你自己对法律的看法
- 指名接收方、提供者、部署者、控制者、处理者——不要把它们合并成“当事方”
- 数字和日期要具体。“Recent developments”用“[日期] 的 [文书]”代替

### 德语特定语域

当输出为德语时：

- Syndikus／Rechtsanwalt 语域；不要学术腔；不要音译的英美法法律英语
- 使用欧盟文书的官方德语术语（Verordnung、Richtlinie、Beschluss、Erwägungsgrund、Artikel、Anwendungsbereich、Verantwortlicher、Auftragsverarbeiter、Aufsichtsbehörde）
- 精确区分“muss”／“soll”／“kann”；谨慎映射“shall”／“should”／“may”
- 除非是已定型的术语（Privacy by Design、Data Mapping、Lead Authority），避免英语借词
- 禁止的德语填充语：“selbstverständlich”（作填充语）、“nicht zuletzt”“im Ergebnis lässt sich festhalten”“vor diesem Hintergrund”“an dieser Stelle”“es bleibt abzuwarten”
- 不用“spannend”、不用“interessant”、不用“Game-Changer”、不用“Disruption”
- 句子要收尾。德语实务者行文不需要 Schachtelsätze（嵌套长句）

---

## 3. 引注惯例

### 欧盟文书

- 首次出现：全名加条例／指令编号和年份，例如 *Regulation (EU) 2024/1689 (AI Act)* 或 *Directive (EU) 2022/2555 (NIS2 Directive)*
- 其后：简称，例如 *AI Act*、*NIS2*、*GDPR*
- 条款：*Art. 6(1)(f) GDPR*、*Art. 6(2) AI Act*、*Recital 31 AI Act*
- 条款先于序言；序言解释条款，而非相反

### 欧洲法院

- 格式：*Case C-NN/YY, [简称当事人名], ECLI:EU:C:YYYY:NNN, para. NN*
- 普通法院：ECLI:EU:T:YYYY:NNN
- 示例：*Case C-311/18, Schrems II, ECLI:EU:C:2020:559*；*Case C-184/20, Vyriausioji tarnybinės etikos komisija, ECLI:EU:C:2022:601*
- 总顾问意见：*Opinion of AG [姓名] in Case C-NN/YY, ECLI:EU:C:YYYY:NNN*

### EDPB

- 指南：*EDPB Guidelines NN/YYYY on [主题], version X.Y, adopted [日期]*
- 意见：*EDPB Opinion NN/YYYY*
- 约束性决定：*EDPB Binding Decision NN/YYYY*
- 按段落编号引用

### 欧盟委员会指南与通报

- *Commission Guidelines on [主题], C(YYYY) NNNN*
- 咨询中的指南草案：注明“draft”和咨询截止日期
- 按段落编号引用

### 国家主管机构

- 数据保护机构决定：机构名称、日期、案件编号
- 示例：*BfDI, Bescheid vom 12.03.2024, Az. [编号]*；*CNIL, délibération SAN-2023-NNN du [日期]*
- 启用 ECLI 的国家法院：*ECLI:[MS]:[Court]:YYYY:NNN*
- 德国法院：*BVerfG, Urteil vom [日期], Az. 1 BvR NNN/YY*；*BGH, Urteil vom [日期], Az. VI ZR NNN/YY*

### 协调标准

- *EN NNNNN:YYYY*；涉及符合性推定时，援引《官方公报》的公布

### 立法准备工作文件

- 欧盟委员会提案：*COM(YYYY) NNN final*
- 欧洲议会报告：注明报告人和日期
- 理事会一般方针：注明日期和可得的文件编号
- 谨慎引用；保留给立法意图真正存有争议之处

### 所分析文件中的段落引用

- 文件对段落编号时，一律按段落编号引用
- 文件仅用标题时，按标题和副标题引用
- 引用文件所解释文书的序言或条款时，两者都引用：文件的段落和基础条款

---

## 4. 自查协议

交付前，回应者必须核实：

1. **引注**——对所分析文件的所有引注使用段落编号；对欧盟文书的所有引注使用条款和序言编号；欧洲法院引注使用 ECLI
2. **无杜撰**——无杜撰的判例、EDPB 指南、序言或段落编号
3. **不确定性已标注**——每条不确定的引注均标注为不确定，或已实时验证，或用户已拒绝实时研究且缺口已标注
4. **实时验证材料已标记**——进行过研究之处，相关引注标记为实时验证并注明访问日期
5. **文本与评述**——回应者自己的主张区别于文件的主张和法律本身
6. **语域**——无破折号、无 AI 痕迹词汇、无禁止的填充语、无反问句、无营销语言
7. **受众与结果匹配**——结构与语气匹配结果类型和受众
8. **缺口**——文件中的缺口被识别，而非一带而过
9. **时间适用**——生效、适用日期和任何过渡制度均已处理；相关处核查时效性
10. **跨工具一致性**——相关处识别与相邻工具的摩擦
11. **可操作性**——相关处处理实务问题（受监管实体能否适用？）
12. **平实英语解释**——与正式分析并列产出（运行第 5 步时）；解释介于 150 至 300 字之间（含）（保存前计数；超过 300 字则删减——上限是硬性上限，不是软目标）；已向用户提供将其整合进交付物的选项

回应者只有在这些检查通过后才产出分析。检查失败时，回应者修正问题，而非绕开它打补丁。

---

## 5. 双语处理（英／德）

### 文件为语言 A、输出为语言 B

- 所有引注保持原样
- 涉及术语时，使用欧盟文书的官方翻译
- 翻译引入解释风险时予以标注

### 英 → 德

- 使用 Syndikus／Rechtsanwalt 语域；不要学术腔
- 映射“Article”→“Artikel”（Art.）；“Recital”→“Erwägungsgrund”（ErwGr.）；条款内的“paragraph”→“Absatz”（Abs.）
- 映射“controller”→“Verantwortlicher”；“processor”→“Auftragsverarbeiter”；“data subject”→“betroffene Person”；“supervisory authority”→“Aufsichtsbehörde”
- 映射“provider”（AI 法案）→“Anbieter”；“deployer”→“Betreiber”；“operator”→“Akteur”（按 AI 法案德文版）
- 区分“muss”（约束性义务）、“soll”（带论证要求的强建议）、“kann”（选择）
- 除非是已定型的术语（Privacy by Design、Lead Authority、Joint Controllership／Gemeinsame Verantwortlichkeit），避免英语借词

### 德 → 英

- 使用英式或国际英语；不要美国法律英语
- 映射“Verordnung”→“Regulation”；“Richtlinie”→“Directive”；“Beschluss”→“Decision”
- 首次出现时保留德国法院缩写（BVerfG、BGH、OLG、VG）并附英文说明；其后使用缩写
- 保留国家法律的原始德语引注

### 翻译风险标记

- AI 法案德／英：“Betreiber”（deployer）和“Anbieter”（provider）不可互换；混用是实质性错误
- GDPR 德／英：“berechtigte Interessen”／“legitimate interests”——范围相同，但关于权衡的国家判例法不同
- “Personal data”／“personenbezogene Daten”——等价
- “Profiling”（AI 法案）≠“Profiling”（GDPR 第 4(4) 条）；AI 法案采纳 GDPR 定义，但将其应用于不同的监管架构

---

## 6. 反幻觉协议

这是法律输出最重要的一条规则。

### 硬规则

- 只从以下来源引用：(a) 文件本身，(b) 提示上下文中可见的欧盟文书，(c) 文件中明确引用的权威，(d) 实时验证的权威来源（见 SKILL.md，实时研究协议）
- 不得杜撰案件名称、ECLI 编号、EDPB 指南编号、序言编号或段落引用
- 对以下任何一项绝不依赖训练数据：(i) 草案文件是否已定稿，(ii) 欧洲法院案件是否为某问题的最新判例，(iii) 条款的精确措辞，(iv) 转化期限是否已过，(v) 待决立法的当前状态，(vi) 修正法案是否已生效。对全部六项，要么标注不确定性，要么触发实时研究。

### 默认行为：标注

引注无法从上下文核实时：

> *“[引注需核实：凭记忆的 X 案件名称，ECLI 未确认。建议实时研究或提交阶段核查。]”*

分析本可受益于回应者无法从上下文确认的引注时：

> *“需要权威：欧洲法院关于 [问题] 范围的判例；提交前查阅 curia.europa.eu。”*

### 替代方案：实时研究

引注缺口对分析具有实质意义时，向用户提供实时研究，而非标注后继续。SKILL.md 中的实时研究协议规定了：

- skill 在何时无需提示即主动提供研究（草案、咨询文件、决定性引注、时效敏感问题）
- 权威来源清单、仅允许用于背景的来源、被排除的来源
- 引用实时验证材料的程序

由用户选择加入。用户拒绝时，回应者回退到标注缺口的默认。回应者绝不用猜测替代标注或实时研究。

### 不确定时

转述原则而不作虚假引注，然后要么标注缺口，要么触发实时研究。绝不为填补缺口而杜撰。

### 底线

法律输出中一条杜撰引注的代价是无法挽回的信誉损失。已标注的缺口可挽回。实时验证的引注可挽回。杜撰的权威不可挽回。
