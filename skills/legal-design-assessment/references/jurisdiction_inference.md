# 法域推断——参考

当审计到达 SKILL.md 工作流第 2 步时加载。

## 为何重要

法定重复支柱（第 7 步）需要知道哪部成文法可能被重复。其他支柱对法域不敏感。将法域推断视为**概率性**而非确定性——给出明确置信度并相应标示发现。

## 要使用的信号，大致按权重递减

### 1. 准据法条款

最强的单一信号。以相关语言查找：

- **英语。** "This Agreement is governed by the laws of [X]"（本协议受 [X] 法律管辖）；"shall be construed in accordance with the laws of [X]"（应按 [X] 法律解释）；"the laws of England and Wales"（英格兰和威尔士法律）；"the laws of the State of New York"（纽约州法律）；"the laws of the Commonwealth of Australia"（澳大利亚联邦法律）；"the federal laws of Canada"（加拿大联邦法律）。
- **法语。** "Le présent contrat est régi par le droit français"（本合同受法国法律管辖）；"soumis au droit belge"（受比利时法律管辖）；"régi par le droit suisse"（受瑞士法律管辖）；"régi par les lois du Grand-Duché de Luxembourg"（受卢森堡大公国法律管辖）；"régi par le droit du Québec"（受魁北克法律管辖）。
- **德语。** "Dieser Vertrag unterliegt dem Recht der Bundesrepublik Deutschland"（本合同受德意志联邦共和国法律管辖）；"unterliegt österreichischem Recht"（受奥地利法律管辖）；"unterliegt schweizerischem Recht unter Ausschluss des UN-Kaufrechts"（受瑞士法律管辖，排除联合国货物销售公约）；"es gilt liechtensteinisches Recht"（适用列支敦士登法律）。

如存在准据法条款且无歧义，法域置信度为**高**。

### 2. 法院地/管辖权条款

当准据法不明确或有歧义时，专属法院地条款是次强信号："the courts of [X]"（[X] 法院）、"les tribunaux de [X]"（[X] 法院）、"ausschließlicher Gerichtsstand ist [X]"（专属管辖地为 [X]）。注意法院地与准据法可能不同；如不同，法域由准据法条款决定实体法、由法院地条款决定程序。法定重复审查以实体法为准。

### 3. 正文中的成文法引用

即使没有准据法条款，对具名成文法或法典的具体引用也能锚定法域。清点：

- **法国 / 比利时 / 瑞士（法语区）/ 卢森堡 / 魁北克。** "Code civil"（民法典）（FR、BE、LU、QC 使用不同的民法典）、"Code de la consommation"（消费者法典）（FR、BE、LU）、"Code du travail"（劳动法典）、"Code monétaire et financier"（货币与金融法典）、"Code de commerce"（商法典）、"LCD"（《联邦反不正当竞争法》，CH）、"Code des obligations" 或 "CO"（债法典，CH）、"Loi du 8 décembre 1992"（1992 年 12 月 8 日法律，BE，数据保护前身）。
- **德国 / 奥地利 / 瑞士（德语区）/ 列支敦士登。** BGB（DE）、HGB（DE）、AGG（DE）、UWG（DE/AT）、AGBG（AT）、KSchG（AT）、OR（CH，《债法典》，与法语 CO 对应）、DSG（CH，《数据保护法》）、ABGB（AT，《奥地利普通民法典》）、PGR（LI，《人法与公司法》）。
- **英格兰和威尔士 / 苏格兰 / 北爱尔兰。**《2015 年消费者权利法》、《1979 年货物销售法》、《1977 年不公平合同条款法》、《2006 年公司法》、《2018 年数据保护法》、《2010 年平等法》。
- **美国（联邦和州）。** UCC（州法，各异）、《谢尔曼法》、《联邦贸易委员会法》、CCPA / CPRA（加利福尼亚）、州消费者保护成文法。"U.S.C." 引用为联邦法。
- **加拿大。**《魁北克民法典》（CCQ）→ 魁北克；《货物销售法》→ 普通法省份；PIPEDA → 联邦。
- **澳大利亚 / 新西兰。**《澳大利亚消费者法》、《2010 年竞争与消费者法》（联邦）；《1993 年消费者保障法》（NZ）。
- **爱尔兰。**《2022 年消费者权利法》。

如至少两条不同引用指向同一法域且无矛盾信号，成文法引用以**高**置信度解析到某一法域。

### 4. 货币、地址和登记标识符

较弱的信号，组合时有用：

- **货币。** GBP → 英国；CHF → 瑞士 / 列支敦士登；USD → 美国（州仍待确定）；CAD → 加拿大；AUD → 澳大利亚；NZD → 新西兰。EUR 为多法域——单独绝不定论。
- **邮政地址格式。** 德国邮政编码为 5 位；法国 5 位带地区前缀；比利时 4 位；瑞士 4 位；英国字母数字（如 SW1A 1AA）；美国 5 或 9 位 ZIP；加拿大字母数字（如 K1A 0B1）。
- **登记标识符。** SIREN/SIRET（FR）；BCE / KBO（BE）；IDE / UID（CH）；HRB / HRA / Amtsgericht 参考（DE）；FN（AT）；Companies House 编号（UK）；EIN（US）；ABN（AU）；NZBN（NZ）。
- **电话国家代码。** +33 FR；+32 BE；+41 CH；+49 DE；+43 AT；+423 LI；+352 LU；+44 UK；+1 US/CA。

在提升置信度前组合多个弱信号。德国两个地址 + EUR + HRB 编号，即使没有准据法条款也是**高**置信度德国。

### 5. 拼写惯例

有用的决胜因素，绝非首要：

- **英语。** -ize / -ization → 偏向美国；-ise / -isation → 英国 / 英联邦。"Color" / "colour"；"judgment"（美国、英国法律）/ "judgement"（英国一般）。注意英国法律起草即使在非法律语境也常用不带 e 的 "judgment"——不要过度解读。
- **法语。** 比利时法语用 "septante" / "nonante"（法国法语用 "soixante-dix" / "quatre-vingt-dix"）——罕见但决定性。瑞士法语亦然。魁北克法语更自由地使用英语外来词。
- **德语。** 奥地利德语有自己的法律词汇（行政法语境中用 "Erkenntnis" 而非 "Urteil"；用 "Pönale" 而非 "Vertragsstrafe"）。瑞士德语法律起草使用标准德语时通常无法区分，但注意处处 "ß" → "ss"（瑞士惯例）。

### 6. 文档类型元数据

标题为 "CGU"（Conditions Générales d'Utilisation，使用条款）的文件更可能是法国法语；"CGV" 亦然。"AGB" → 德国 / 奥地利 / 瑞士。"T&Cs" / "Terms of Use" → 英国或美国。"EULA" → 通常为美国。这些至多是弱信号。

## 置信度——何时分配何种

- **高。** 存在准据法条款且无歧义，**或**两个或以上独立强信号（成文法引用 + 地址 + 登记 ID）全部一致且无矛盾信号。
- **中。** 一个强信号与弱信号一致，**或**多个弱信号一致。大多数无明示准据法条款的跨境 B2B 合同位于此处。
- **低。** 信号冲突（如德国当事人 + 法国成文法引用），**或**仅有弱信号可用，**或**文件合理可能依多个法域起草且有歧义。
- **未知。** 无可用信号。

## 报告中对每个置信度如何处理

- **高** → 法定重复支柱全权重；支柱发现自信地引用相关成文法。
- **中** → 法定重复支柱全权重，但发现表述为「可能重述[法域][成文法]——请核验」。
- **低** → 法定重复权重减半；将 5 个百分点按比例重新分配到其他支柱。发现表述为 `未核验——取决于法域`。
- **未知** → 完全跳过法定重复支柱；将其 10 分按比例重新分配。在报告第 11 节注明跳过。

## 多法域文件

有些文件对不同部分适用不同法域（如纽约法律下的主协议附各成员国当地消费者法的欧盟特定附录）。此时：

1. 识别各部分及其各自法域。
2. **按部分**在其各自法域下运行法定重复支柱。
3. 报告单一综合的语言/可读性/结构/隐藏条件/视觉评分（这些不依赖法域）和按部分的法定重复评分。
4. 综合评分的置信度由最弱部分决定。

## 此处不做的事

- 不就法律冲突选择提供建议——这是本 skill 之外的实体法律问题。
- 不主张准据法条款可执行——仅将其存在作为信号记录。
- 如文本信号冲突，不只依语言推断法域。语言设定默认法域池（EN → 英语法域；FR → 法语法域；DE → 德语法域），而非答案。
