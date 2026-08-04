# 荷兰语——金融与银行子词典

> **适用范围。** 本子词典在单个按语言划分的文件中涵盖两个紧密相关的领域：**金融与银行**（主要）和**交易与资本市场**。两者在此合并，因为其词汇高度重叠（债务工具、证券、交易所监管），且译者通常同时需要两者。两个跨语言的英语参考词典仍保持拆分：分别见 `references/finance-banking.md` 和 `references/trading-capital-markets.md`。

根据翻译经验自动生成。将荷兰语的金融、银行和证券法术语映射为正确的英语对应词。涵盖融资协议、担保文件、荷兰担保权益（质押/抵押）、Wft 监管的银行业、AML/KYC 以及荷兰法下的银团/项目融资概念。

## 融资协议核心术语

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| kredietovereenkomst | facility agreement / credit agreement | |
| leningsovereenkomst | loan agreement | |
| geldleningsovereenkomst | money-loan agreement | 民法典第 7:129 条 |
| rekening-courantkrediet | current account facility / overdraft | |
| revolverend krediet | revolving credit facility / RCF | |
| termijnkrediet | term loan | |
| faciliteit | facility | |
| tranche | tranche | |
| opname / trekking | drawdown / drawing / utilisation | |
| opnameverzoek / trekkingsverzoek | utilisation request / drawdown request | |
| beschikbaarheidsperiode | availability period / commitment period | |
| opnameperiode | drawdown period | |
| hoofdsom | principal amount | |
| rente | interest | |
| rentevaste periode | interest period | |
| variabele rente | floating rate | |
| vaste rente | fixed rate | |
| rentemarge | margin / spread | |
| referentierente | reference rate | |
| EURIBOR | EURIBOR | |
| risk-free rate (RFR) | risk-free rate / RFR | LIBOR 退出后的过渡（€STR、SONIA、SOFR） |
| terugbetaling / aflossing | repayment | |
| vervroegde aflossing | prepayment / early repayment | |
| aflossingsschema | repayment schedule / amortisation schedule | |
| bulletaflossing | bullet repayment | |
| annuïtaire aflossing | annuity repayment | |
| lineaire aflossing | linear / straight-line repayment | |
| vervaldag / vervaldatum | due date / maturity date | |
| einddatum / eindvervaldag | final maturity date | |
| opeisbaarheid | acceleration / falling due | |
| versnelde opeising | acceleration | |
| verzuim / default | default | 交叉参考荷兰民法典第 6:81 条的 verzuim 概念 |
| opeisingsgrond / grond voor opeising | event of default | |
| voorwaardelijk verzuim | potential event of default | |
| kredietnemer / leningnemer | borrower | |
| kredietgever / geldgever | lender / finance provider | |
| agent | agent / facility agent | |
| security agent / zekerhedenagent | security agent / security trustee | 荷兰担保通常采用平行债务结构，因为荷兰法不承认信托 |
| arrangeur | arranger | |
| mandated lead arranger (MLA) | mandated lead arranger / MLA | |
| syndicaat | syndicate | |
| syndicering | syndication | |
| consortium | consortium | |
| primaire syndicering / secundaire markt | primary syndication / secondary market | |
| overdracht van rechten | transfer of rights | |
| contractsoverneming | assumption of contract / novation | 民法典第 6:159 条——需要所有当事方配合 |
| subparticipatie | sub-participation | |

## 担保权益（荷兰法）

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| zekerheid / zekerheidsrecht | security / security interest / security right | |
| goederenrechtelijke zekerheid | proprietary security | |
| persoonlijke zekerheid | personal security / guarantee | |
| pandrecht | right of pledge | 民法典第 3:236 条（占有型）和第 3:237 条（非占有型） |
| vuistpand | possessory pledge | 资产转移给质权人；民法典第 3:236 条 |
| stil pandrecht / bezitloos pandrecht | non-possessory pledge / silent pledge | 民法典第 3:237 条——登记或公证契据；资产仍由出质人占有 |
| openbaar pandrecht | disclosed pledge | 通知债务人（就债权而言） |
| eerste pandrecht / tweede pandrecht | first-ranking pledge / second-ranking pledge | |
| verpanding | pledging | |
| pandakte | deed of pledge | |
| hypotheek | mortgage | 就不动产（房地产、船舶、飞机）设定；民法典第 3:260 条 |
| eerste hypotheek | first-ranking mortgage | |
| bankhypotheek | bank mortgage / all-moneys mortgage | 担保对银行的所有现有和未来债务——荷兰标准做法 |
| krediethypotheek | credit mortgage | 担保特定信贷关系 |
| vestigen (van een pandrecht/hypotheek) | to create / grant (a pledge / mortgage) | |
| notariële akte | notarial deed | 抵押所必需；非占有型质押建议采用 |
| registratie van pandakte | registration of pledge deed | 非占有型质押向税务机关登记 |
| executie | enforcement / realisation | 违约时出售担保资产 |
| openbare verkoop / executieverkoop | public auction / forced sale | |
| onderhandse verkoop | private sale | 经法院批准（民法典第 3:251 条）或按约定 |
| parate executie | summary enforcement / self-enforcement | 担保债权人无需判决即可强制执行 |
| borgtocht | surety / guarantee (personal) | 民法典第 7:850 条——保证人提供的人保 |
| particuliere borgtocht | consumer surety | 依民法典第 7:857 条受特别形式要求约束 |
| garantie / concerngarantie | guarantee / corporate guarantee / group guarantee | |
| bankgarantie | bank guarantee | 抽象的或有条件的；通常为见索即付 |
| afroepgarantie / on-demand garantie | on-demand guarantee | |
| achterstelling | subordination | |
| achterstellingsovereenkomst | subordination agreement / deed of subordination | |
| intercrediten overeenkomst | intercreditor agreement / ICA | |
| parallel debt | parallel debt | 荷兰法不承认信托——担保债权人通过平行债务向担保代理人确立地位 |
| accessoriteit | accessoriness | 荷兰担保具有从属性——取决于被担保债权的存在（因此采用平行债务予以规避） |
| pluraliteit van rechthebbenden | multiple beneficiaries | 促成平行债务结构的问题 |
| derdenbeslag | third-party attachment / garnishment | |
| rangorde van schuldeisers | creditor ranking | |
| preferente schuldeiser | preferred / preferential creditor | |
| concurrente schuldeiser | unsecured / ordinary creditor | |
| bodemrecht (fiscus) | bottom right (tax authority) | 税务机关对经营场所内"底层物品"的法定留置权——在某些情况下优先于非占有型质押 |
| bodemvoorrecht / bodemzaakbegrip | bottom privilege / bottom assets | 荷兰特有的税务留置权概念——为外国读者作注释 |

## 提款条件与承诺条款

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| opschortende voorwaarden (conditions precedent) | conditions precedent | |
| documentaire voorwaarden | documentary conditions | |
| opschortende voorwaarden voorafgaand aan iedere trekking | conditions precedent to each utilisation | |
| verklaringen en garanties | representations and warranties | |
| herhaling (van verklaringen) | repetition (of representations) | |
| affirmatieve convenants | affirmative covenants / undertakings | |
| negatieve convenants | negative covenants | |
| financiële convenants | financial covenants | |
| leverage ratio | leverage ratio / net debt to EBITDA | |
| interest cover ratio (ICR) | interest cover ratio | |
| debt service cover ratio (DSCR) | debt service cover ratio | |
| loan to value (LTV) | loan-to-value ratio | |
| gearing ratio | gearing ratio | |
| verplichte betalingen / mandatory prepayment | mandatory prepayment | |
| vrijwillige vervroegde aflossing | voluntary prepayment | |
| cash sweep | cash sweep | |
| illegality | illegality | |
| material adverse change (MAC) / wezenlijke negatieve wijziging | material adverse change / MAC | |
| cross default / kruiselings verzuim | cross-default | |
| cross acceleration | cross-acceleration | |
| change of control / wijziging van zeggenschap | change of control | |
| negative pledge / negatieve pandverklaring | negative pledge | |

## 银行业监管（Wft 与反洗钱）

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| Wet op het financieel toezicht (Wft) | Financial Supervision Act | 荷兰审慎监管和行为监管的核心法律 |
| Besluit prudentieel toezicht financiële groepen Wft | Financial Groups Prudential Supervision Decree | |
| De Nederlandsche Bank (DNB) | Dutch Central Bank | 审慎监管机构（与 AFM 构成双峰监管） |
| Autoriteit Financiële Markten (AFM) | Authority for the Financial Markets | 行为/市场监管机构 |
| vergunning (Wft) | Wft licence / authorisation | |
| kredietinstelling | credit institution | |
| bank (in de zin van de Wft) | bank (within the meaning of the Wft) | |
| beleggingsonderneming | investment firm | |
| financiële dienstverlener | financial service provider | |
| geschiktheid en betrouwbaarheid | suitability and integrity | 对高管进行适任与诚信测试 |
| toetsing / geschiktheidstoets | suitability test / assessment | |
| gedragstoezicht | conduct supervision | |
| prudentieel toezicht | prudential supervision | |
| zorgplicht | duty of care | 荷兰金融服 务提供者对消费者的增强注意义务 |
| bijzondere zorgplicht | special / enhanced duty of care | 判例法衍生——最高法院关于咨询和衍生产品的判例 |
| know your customer (KYC) / cliëntenonderzoek | customer due diligence | |
| vereenvoudigd cliëntenonderzoek | simplified due diligence | |
| verscherpt cliëntenonderzoek | enhanced due diligence | |
| ultimate beneficial owner (UBO) / uiteindelijk belanghebbende | ultimate beneficial owner / UBO | |
| UBO-register | UBO register | 由商会（KvK）维护 |
| politically exposed person (PEP) | politically exposed person / PEP | |
| Wwft | AML/CFT Act | 《防止洗钱和恐怖主义融资法》 |
| ongebruikelijke transactie | unusual transaction | Wwft 术语——触发向荷兰金融情报机构（FIU-Nederland）报告 |
| melding ongebruikelijke transactie | report of unusual transaction | 向 FIU-Nederland（金融情报机构）报告 |
| FIU-Nederland | FIU Netherlands | |
| sanctiewet | Sanctions Act | 1977 年《制裁法》实施联合国/欧盟制裁 |
| sanctielijsten | sanctions lists | |
| verplichte identificatie | mandatory identification | |
| risicogebaseerde benadering | risk-based approach | |

## 金融文件中的荷兰起草惯例

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| Partijen komen overeen | The Parties agree | |
| Kredietnemer verbindt zich jegens Kredietgever | Borrower undertakes to Lender | |
| onverwijld | without delay / forthwith | |
| op eerste verzoek | on first demand | |
| hoofdelijk en ondeelbaar / hoofdelijk aansprakelijk | jointly and severally / joint and several liability | 民法典第 6:6 条 |
| pari passu | pari passu | |
| gelijke rang | equal ranking / pari passu | |
| toerekening van betalingen | application of payments | |
| compensatie / verrekening | set-off | 民法典第 6:127 条 |
| schuldvergelijking | set-off (tax/traditional term) | |
| bruto-/netto-bedrag | gross / net amount | |
| gross-up | gross-up | |
| bronbelasting | withholding tax | |
| vrijwaring voor belastingen | tax indemnity / tax gross-up | |
| yield protection | yield protection / increased costs | |
| break costs / vergoeding bij vervroegde aflossing | break costs | |
| hoofdelijk debiteur | joint and several debtor | |
| borg | surety | 狭义——民法典第 7:850 条下的个人保证人 |
| regres | recourse / indemnity | |
| subrogatie | subrogation | 民法典第 6:150 条 |

## 破产与重组（金融语境）

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| faillissement | bankruptcy | 适用于公司和个人 |
| faillissementsaanvraag | petition for bankruptcy | |
| faillissementsvonnis | bankruptcy order / adjudication | |
| curator | trustee in bankruptcy | |
| rechter-commissaris | supervisory judge | 监督破产管理人 |
| boedel | insolvency estate | |
| boedelschuld | estate claim | 优先于破产前债权 |
| preferente vordering | preferential claim | |
| bevoorrechte vordering | privileged claim | |
| separatist | separatist | 可以如同无破产一样强制执行的担保债权人——质权人/抵押权人 |
| afkoelingsperiode | cooling-off period | 破产中强制执行被暂停的短暂期间（2+2 个月） |
| surseance van betaling | suspension of payments | 类似债务人自行管理式的暂停付款程序；正被 WHOA 取代 |
| WHOA — Wet homologatie onderhands akkoord | Dutch Scheme | 法院确认的债务重组方案；可约束异议债权人 |
| akkoord | composition / scheme of arrangement | 在破产、暂停付款或 WHOA 中 |
| homologatie | court confirmation | |
| herstructurering | restructuring | |
| pre-insolventie akkoord | pre-insolvency composition | |
| paulianeus | fraudulent / avoidable | 民法典第 3:45 条（撤销之诉）和《破产法》第 42 条 |
| pauliana | actio pauliana | 撤销损害债权人利益的交易 |
| klasseindeling | class composition | WHOA 类别 |
| dwangakkoord | cram-down / enforced composition | WHOA 跨类别强制执行 |
| aandeelhoudersakkoord (WHOA) | shareholder class (WHOA) | |

## 译者注

- **Pandrecht**：始终译为"pledge"——对动产和债权的担保。不要单独使用"security interest"（过于笼统）。区分"possessory pledge"（占有型质押，vuistpand）与"non-possessory pledge"（非占有型质押，stil pandrecht/bezitloos pandrecht）——后者是商业融资中的主导形式。
- **Hypotheek**：对已登记财产（房地产、船舶、飞机）的抵押。英语翻译中绝不使用"hypothec"（那是大陆法系术语）。也不得将 hypotheek 译为"pledge"。
- **Parallel debt（平行债务）**：荷兰法担保交易的关键概念。荷兰法要求担保债权人必须是债权持有人（从属性），因此银团融资采用平行债务机制：每名贷款人的债权由担保代理人对借款人的债权镜像对应，担保担保该平行债务。英语中保留"parallel debt"不译。
- **Bodemrecht / bodemvoorrecht**：荷兰税法的一个特例：税务机关（Belastingdienst）对债务人经营场所内的"底层物品"（bodemd-goederen，即在债务人场所内的动产）享有法定留置权，可优先于非占有型质押。译为"bottom right"或"bottom privilege"并加注释；外国读者需要这一警示。
- **Bank mortgage / bankhypotheek**：荷兰市场标准做法——抵押担保银行对债务人的所有现有和未来债权，而不仅是一笔特定贷款。首次出现时注明。
- **Notariële akte**：公证契据——抵押所必需，（可选但通常如此）非占有型质押也采用。在荷兰，这是由民法公证人主持签署的契据。不要与美国式公证（仅见证）混淆。
- **Verzuim / ingebrekestelling**：荷兰法要求正式违约通知（ingebrekestelling）才能在某些救济（损害赔偿、解除）可用前将债务人置于违约状态（verzuim）。合同通常放弃这一要求——翻译中予以保留（"without prior notice of default"）。民法典第 6:82 条。
- **DNB 和 AFM**：荷兰"双峰"模式——DNB 是审慎监管机构，AFM 是行为监管机构。首次出现时拼出全称：De Nederlandsche Bank（DNB）和 Autoriteit Financiële Markten（AFM）。
- **Wft 术语**：《金融监管法》（Wet op het financieel toezicht）是荷兰实施 CRD/CRR、MiFID、偿付能力指令等欧盟指令的伞形法律。"Financial Supervision Act"是官方译名；简称保留"Wft"。
- **Zorgplicht**：荷兰银行和金融顾问承担的注意义务可能超出合同法要求。在著名的最高法院判例中，这被称为"bijzondere zorgplicht"（特别注意义务）。译为"duty of care"，将"special/enhanced duty of care"保留给判例法理论。
- **Achterstelling vs subordinatie**：荷兰语对从属（subordination）使用"achterstelling"；"subordinatie"很少见。两者均译为"subordination"。
- **WHOA**：2021 年荷兰《庭外债务重组方案确认法》——首次出现时使用"WHOA"或"Dutch Scheme"并附全称。不要译为"Act on Confirmation of Private Composition"（过于直译）。类似于英国的 scheme of arrangement 和美国破产法第 11 章的强制批准。
- **Surseance van betaling**：荷兰历史上的暂停付款程序。技术上仍然有效，但实务中基本已被 WHOA 取代。译为"suspension of payments"或"moratorium"。
- **Separatist**：在荷兰破产中，指可以"如同无破产一样"强制执行的担保债权人（质权人/抵押权人）——不要译为"separatist"（英语中有政治含义）。首次使用时用"separatist creditor"并加注释，或描述为"具有独立强制执行权的担保债权人"。
- **"Verklaringen en garanties"**：英语"representations and warranties"的直译借词。直接译为"representations and warranties"。不要使用"declarations and guarantees"（会误导——"guarantee"有特定的信用支持含义）。
- **"Opeisbaar"**：到期应付（并可按要求强制执行）。区别于仅"due"——opeisbaarheid 触发加速权。
- **"Jegens" vs "tegenover"**：两者均表示"towards"——jegens 更具正式/法律语体。根据语境两者均译为"to"或"towards"。
- **"Rentevast" vs "vaste rente"**：rentevast＝利率固定期（特定计息期）；vaste rente＝固定利率（相对于浮动利率）。区别翻译。
- **比利时荷兰语金融文件**：使用《比利时民法典》和《经济法法典》的条文；比利时质押法已由 2013 年《质押法》（2018 年起生效）大幅改革。主要区别：比利时动产质押可在国家质押登记簿登记；抵押法结构与荷兰类似，但采用比利时特有的优先权规则。比利时文件应标注交叉核对。

---

## 交易与资本市场——荷兰语

根据翻译经验自动生成。将荷兰语的交易、资本市场、证券和上市公司术语映射为正确的英语对应词。荷兰资本市场法主要由《金融监管法》（Wft）、欧盟法规（MiFID II/MiFIR、《招股说明书条例》、MAR、CSDR、EMIR、SFDR、SFTR、CSRD）以及民法典第二编第 9 章（年度账目）和第 8 章（大公司治理）驱动。

## 市场基础设施与参与者

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| financiële markten | financial markets | |
| gereglementeerde markt | regulated market | MiFID II——Euronext Amsterdam |
| multilateral trading facility (MTF) | multilateral trading facility | |
| organised trading facility (OTF) | organised trading facility | |
| beursnotering | listing | |
| Euronext Amsterdam | Euronext Amsterdam | 荷兰主要证券交易所 |
| effectenbeurs | securities exchange | |
| beheerder / beursbeheerder | market operator | |
| beleggingsonderneming | investment firm | MiFID 监管实体 |
| beleggingsdienstverlener | investment service provider | |
| beleggingsadviseur | investment adviser | |
| vermogensbeheerder | asset manager / portfolio manager | |
| beleggingsinstelling | investment fund / collective investment undertaking | |
| beheerder van een beleggingsinstelling | AIFM / UCITS manager | |
| bewaarder / depositary | depositary | |
| effectenclearinginstelling | CCP / clearing house | |
| effectenafwikkelsysteem | settlement system | CSDR 监管 |
| centraal effectenbewaarbedrijf (CSD) | central securities depository | |
| Euroclear Nederland | Euroclear Nederland | 荷兰中央证券存管机构 |
| tussenpersoon / intermediair | intermediary | |
| gekwalificeerde belegger / professionele belegger | qualified investor / professional investor | |
| retail investor | retail investor | |

## 监管机构与监管框架

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| Wet op het financieel toezicht (Wft) | Financial Supervision Act | |
| AFM (Autoriteit Financiële Markten) | Authority for the Financial Markets | 行为监管机构 |
| DNB (De Nederlandsche Bank) | Dutch Central Bank | 审慎监管机构 |
| ESMA | ESMA | 欧洲证券和市场管理局 |
| EBA | EBA | 欧洲银行管理局 |
| EIOPA | EIOPA | |
| ECB / Europese Centrale Bank | ECB | 银行业监管（SSM） |
| SRB / Single Resolution Board | SRB | 银行处置 |
| AP (Autoriteit Persoonsgegevens) | Dutch DPA | |
| ACM | ACM | 消费者与市场管理局 |
| financieel toezicht | financial supervision | |
| twin peaks-model | twin-peaks model | 荷兰监管架构 |
| vergunning | licence / authorisation | |
| Wft-vergunning | Wft authorisation | |
| MiFID-vergunning | MiFID authorisation | |
| paspoort-regeling | passporting regime | 欧盟跨境活动 |
| branche | branch | |
| dienstverrichting | cross-border provision of services | |

## 业务行为与投资者保护

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| zorgplicht | duty of care | 更宽泛的荷兰一般注意义务 |
| ken-uw-cliënt (KYC) | know your client | |
| cliëntacceptatie / CDD | customer due diligence | |
| Wwft (Wet ter voorkoming van witwassen en financieren van terrorisme) | AML Act | |
| Sanctiewet | Sanctions Act | |
| geschiktheid / passendheid | suitability / appropriateness | MiFID II 的适当性 vs 适合性 |
| execution-only | execution-only | |
| niet-complexe instrumenten | non-complex instruments | |
| complex product | complex product | |
| provisieverbod | ban on commissions / inducements | Wft 第 86b 条及以下——全面禁止收受产品提供方的佣金 |
| KID / PRIIP KID | KID / PRIIP KID | 关键信息文件 |
| ESMA-productinterventies | ESMA product interventions | 二元期权、差价合约 |
| best execution | best execution | MiFID II 第 27 条 |
| belangenconflicten | conflicts of interest | |
| cliëntcategorisatie | client categorisation | |

## 招股说明书与公开发行

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| prospectus | prospectus | 欧盟《招股说明书条例》(EU) 2017/1129 |
| prospectusplicht | prospectus obligation | |
| particulier bod / private placement | private placement | |
| uitgifte van effecten | issue of securities | |
| uitgevende instelling / emittent | issuer | |
| eerste notering / IPO | initial public offering / IPO | |
| vervolgemissie / SPO | secondary offering | |
| rights issue / claimemissie | rights issue | |
| accelerated bookbuild (ABB) | accelerated bookbuild | |
| bookrunner | bookrunner | |
| onderschrijvingsovereenkomst / onderwriting | underwriting agreement | |
| overtoewijzingsoptie / greenshoe | over-allotment option / greenshoe | |
| stabilisatieperiode | stabilisation period | 《委员会授权条例》2016/1052 |
| lockup / lock-up | lock-up agreement | |
| pricing statement | pricing statement | |
| prospectussamenvatting | prospectus summary | |
| verrichtingsnota / wertpapierbeschrijving | securities note | |
| registratiedocument | registration document | |
| EU Growth-prospectus | EU Growth prospectus | |
| universal registration document (URD) | URD | |
| goedkeuring AFM | AFM approval | |
| passporting van prospectus | prospectus passporting | 在整个欧洲经济区 |
| vrijstellingen | exemptions | 《招股说明书条例》第 1(4) 条和第 3(2) 条 |
| gekwalificeerde beleggers | qualified investors | |
| minder dan 150 natuurlijke personen/rechtspersonen | fewer than 150 persons | 私募安全港 |

## 市场行为（MAR）

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| Marktmisbruikverordening (MAR) | Market Abuse Regulation | (EU) 596/2014 |
| voorwetenschap | inside information | |
| handel met voorwetenschap | insider dealing | |
| marktmanipulatie | market manipulation | |
| openbaarmaking van voorwetenschap | disclosure of inside information | |
| uitstel van openbaarmaking | delayed disclosure | |
| insiderlijst | insider list | |
| managerstransacties | managers' transactions | 管理人员（PDMR）交易 |
| closed periods | closed periods | 围绕业绩公告期间 |
| gesloten periode | closed period | |
| transactiemelding | transaction reporting | |
| STOR-melding | STOR | 可疑交易和指令报告 |
| benchmarkverordening | Benchmark Regulation | (EU) 2016/1011 |

## 收购与要约

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| Wet openbare biedingen (incorporated in Wft and BOB) | Public Offers Act | 实施欧盟《收购指令》 |
| Besluit openbare biedingen Wft (BOB) | Public Offers Decree | |
| openbaar bod | public / tender offer | |
| vrijwillig bod | voluntary offer | |
| verplicht bod | mandatory offer | 在控制 30% 表决权时触发 |
| partieel bod | partial offer | |
| biedingsbericht | offer memorandum | |
| biedprijs | offer price | |
| equitable price | equitable price | 强制要约价格标准 |
| certain funds | certain funds | 必须证明融资确定性 |
| bod in contanten / bod in aandelen | cash offer / share exchange offer | |
| werknemersraadpleging | employee consultation | SER 并购准则 |
| SER Fusiegedragsregels | SER Merger Code | 荷兰社会与经济理事会 |
| Stichting Autoriteit Financiële Markten als biedingstoezichthouder | AFM as takeover supervisor | |
| standstill | standstill | 不收购股份的义务 |
| break fee / reverse break fee | break fee | |
| fiduciary-out / uitgangsrecht | fiduciary-out | |
| squeeze-out | squeeze-out | 民法典第 2:92a 条（公司） / 第 2:359c 条（与要约相关） |
| sell-out | sell-out right | 收购达 95% 时少数股东强制卖出的权利 |
| biedprocedure | offer procedure | |
| gestanddoening | declaration unconditional | 要约成为有约束力 |
| naloopperiode | post-acceptance period | |
| deal protection | deal protection | |
| position statement | position statement | 目标公司董事会对要约的回应 |

## 上市公司治理与披露

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| Corporate Governance Code / Nederlandse Corporate Governance Code | Dutch Corporate Governance Code | "遵循或解释"；由监督委员会（Monitoring Commissie）监督 |
| monitoring commissie | Monitoring Committee | |
| one-tier board | one-tier board | |
| two-tier board | two-tier board | 管理委员会 + 监事会 |
| RvB (Raad van Bestuur) | Management Board | |
| RvC (Raad van Commissarissen) | Supervisory Board | |
| executive directors | executive directors | |
| non-executive directors | non-executive directors | |
| independent commissioners | independent supervisory directors | |
| CEO / CFO | CEO / CFO | 保留英语 |
| voorzitter / president-commissaris | chair / chair of supervisory board | |
| remuneratiecommissie | remuneration committee | |
| auditcommissie | audit committee | |
| selectie- en benoemingscommissie | selection and appointment committee | |
| beloningsbeleid | remuneration policy | 有约束力的表决；SRD II |
| beloningsverslag | remuneration report | 咨询性表决 |
| jaarrekening | annual accounts | |
| jaarverslag / bestuursverslag | annual report / management report | |
| accountantsverklaring | auditor's report | |
| controlverklaring | audit opinion | |
| publicatie jaarcijfers | publication of annual figures | |
| halfjaarbericht | half-year report | |
| trading update / kwartaalbericht | trading update / quarterly report | |
| financiële kalender | financial calendar | |
| ad-hoc publicatie | ad-hoc publication | 依 MAR |

## 股东权利与股东积极主义

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| algemene vergadering | general meeting | |
| stemgerechtigd | entitled to vote | |
| registratiedatum | record date | 会议前 28 天（民法典第 2:119 条） |
| agenderingsrecht | right to add agenda items | 对 BV/NV 的持股门槛为 3% |
| enquêterecht | right to inquiry proceedings | 民法典第 2:344 条及以下——在企业法庭（Ondernemingskamer）进行 |
| wanbeleid | mismanagement | 调查救济的检验标准 |
| onmiddellijke voorzieningen | immediate provisions | 企业法庭可以施加 |
| proxy-solicitation | proxy solicitation | |
| stemadviesbureaus (ISS, Glass Lewis) | proxy advisers | |
| shareholder engagement | shareholder engagement | SRD II 的驱动因素 |
| aandeelhoudersactivisme | shareholder activism | |
| 203 / responsetijd | response time | 荷兰公司治理准则——最长 180 天 |
| Stichting Continuïteit / preferred-share foundation | continuity foundation | 荷兰反收购手段 |
| Stichting Administratiekantoor (STAK) | trust-office foundation | 发行存托凭证 |
| depositary receipts / certificaten van aandelen | depositary receipts | |
| certificaathouders met vergaderrecht | receipt-holders with meeting rights | |
| prioriteitsaandelen | priority shares | 增强的表决/治理权 |
| golden share | golden share | 通常由政府持有 |

## 衍生产品、卖空与披露

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| derivaten | derivatives | |
| EMIR (EU) No 648/2012 | EMIR | 《欧洲市场基础设施条例》 |
| verplichte clearing | mandatory clearing | |
| risk mitigation | risk mitigation | |
| Shortsellingverordening | Short Selling Regulation | (EU) 236/2012 |
| short positie / netto short positie | short position / net short position | |
| meldingsplicht short position | short selling notification | 0.1% 阈值 |
| ongedekte short sale | uncovered short sale | |
| locate rule | locate rule | |
| substantial holding notification / Wft-melding | substantial holding notification | 阈值：3%、5%、10%、15%、20%、25%、30%、40%、50%、60%、75%、95%（民法典/Wft） |
| Wet melding zeggenschap | (historic) Significant Control Notification Act | 现已并入 Wft |
| SFTR | SFTR | 《证券融资交易条例》 |
| SFDR | SFDR | 《可持续金融披露条例》 |
| CSRD / ESRS | CSRD / ESRS | 《企业可持续发展报告指令》 |
| Taxonomy-verordening | Taxonomy Regulation | (EU) 2020/852 |

## 加密与数字资产

| 荷兰语 | 英语 | 备注 |
|---|---|---|
| MiCA-verordening | Markets in Crypto-Assets Regulation (MiCA) | (EU) 2023/1114 |
| crypto-activa | crypto-assets | |
| asset-referenced token (ART) | asset-referenced token | |
| e-money token (EMT) | e-money token | |
| utility token | utility token | |
| CASP (crypto-asset service provider) | CASP | |
| DLT / distributed ledger technology | DLT | |
| DLT Pilot Regime | DLT Pilot Regime | (EU) 2022/858 |
| tokenisatie | tokenisation | |
| witwasrisico crypto | AML risk in crypto | |

## 译者注

- **双峰模式（Twin-peaks model）**：2002 年以来的荷兰监管架构——DNB＝审慎监管机构（资本、偿付能力、治理）。AFM＝行为监管机构（分销、披露、市场诚信）。两个角色构成"双峰"——在英国/澳大利亚之外独一无二。"Autoriteit Financiële Markten"译为"Authority for the Financial Markets"或"AFM"；"De Nederlandsche Bank"译为"Dutch Central Bank"或"DNB"。
- **Wft（《金融监管法》）**：荷兰全面的金融服务监管法律。涵盖银行业、保险、投资公司、基金、招股说明书、收购、市场滥用。译为"Financial Supervision Act"；频繁使用时保留"Wft"并加注释。
- **重大持股通知**：荷兰阈值——3%、5%、10%、15%、20%、25%、30%、40%、50%、60%、75%、95%。向 AFM 和发行人通知。属于较严格的欧盟制度之一（许多成员国只采用部分阈值）。对并购和积极投资者投资者至关重要。
- **30% 强制要约阈值**：荷兰强制要约在 30% 表决权时触发（与某些其他法域并列欧盟最低）。"Verplicht bod"——一致译为"mandatory offer"，如受众不熟悉则标注 30% 阈值。
- **Stichting Continuïteit / 优先股基金会**：荷兰特有的反收购手段。基金会持有收购优先股的期权，稀释敌意竞购方的表决权。ASML、KPN、DSM、飞利浦等公司使用。译为"continuity foundation"或"protective foundation"；首次使用时保留"Stichting Continuïteit"并加注释。
- **STAK / Stichting Administratiekantoor**：信托办公室基金会——持有股份并发行存托凭证（"certificaten"）。常见于私募并购架构、家族企业、上市公司收购防御。凭证持有人可能有或没有会议权利。译为"trust-office foundation"并加注释。
- **Enquêteprocedure / Ondernemingskamer**：荷兰特有的股东救济。少数股东（通常持股 10% 以上或上市且市值 2 亿欧元以上）可以向企业法庭申请对公司事务进行调查。如认定"wanbeleid"（经营不善），法庭可施加影响深远的措施。常被战略性地用于并购争议（富通、荷兰银行、Delta Lloyd、联合利华）。译为"inquiry proceedings"或"enquête proceedings"并加注释。
- **荷兰公司治理准则（Dutch Corporate Governance Code）**：针对上市荷兰 NV 的"遵循或解释"准则。2022 年更新——增加了可持续性、多样性、文化条款。由监督委员会监督。译为"Dutch Corporate Governance Code"；标注版本日期。
- **Nederlandse Corporate Governance Code 回应期**：有争议的荷兰概念。准则允许董事会就股东的重大战略提案有 180 天的回应期。由股东积极主义推动。译为"response time"并加注释。
- **Provisieverbod**：荷兰禁止投资公司/顾问/抵押贷款经纪商收受产品提供方佣金（自 2013 年起，比 MiFID II 的诱导制度更广）。覆盖大多数零售金融产品。译为"commission ban"/"ban on inducements"。
- **SER Fusiegedragsregels**：社会与经济理事会并购准则——要求并购中与工会和职工委员会协商的程序性规则。不是成文法但具有准约束力。译为"SER Merger Code"。
- **MAR（《市场滥用条例》）**：直接适用的欧盟条例。荷兰语和英语范围相同。保留"MAR"缩略语；将"Marktmisbruikverordening"译为"Market Abuse Regulation"。
- **Biedingsbericht vs offer memorandum**：对 Euronext Amsterdam 上市公司公开发行，BOB（Wft 公开要约决定）要求提供要约备忘录（offer memorandum）。需要 AFM 批准。译为"offer memorandum"（英语市场标准用法）。
- **Gestanddoening**：要约人宣布要约无条件（最低接受率和其他条件已满足）时——不可撤销的承诺。译为"declaration unconditional"或"wholly unconditional declaration"；首次使用时为法律精确性保留荷兰语。
- **荷兰强制挤出框架**：两条路径——(1) 民法典第 2:92a 条公司强制挤出，任何股东持股达 95%；(2) 民法典第 2:359c 条与要约相关的强制挤出，公开发行后持股达 95%（更短更简化）。在企业法庭有不同的程序。译为"squeeze-out"并注明适用的民法典条文。
- **单层与双层董事会**：荷兰上市公司可选择任一种。双层（传统）＝管理委员会（RvB）和监事会（RvC）分立。单层（自 2013 年起）＝由执行董事和非执行董事组成的单一董事会。适用不同规则（尤其是利益冲突方面）。翻译中始终指明结构。
- **Structuurregime / structure regime（结构制度）**：对达到阈值的 NV（股本 1600 万欧元以上、设有职工委员会、100 名以上荷兰雇员）强制适用的大公司治理制度。监事会任命权从股东大会转移到自行补选（co-optation）；职工委员会拥有有约束力的提名权。荷兰特有制度。译为"structure regime"/"large company regime"并加注释。
- **Certain funds**：荷兰公开发行中使用的英语术语——竞购方必须在公告前证明已承诺资金。译为"certain funds"；保留英语。
- **Break fee / reverse break fee**：荷兰私有化交易中常见。受荷兰判例法限制（不得超过合理的交易成本/损害）。AFM 将其作为可能抑制竞争性要约的因素予以审查。译为"break fee"/"reverse break fee"。
- **投资公司的 Wwft 义务**：广泛的 AML/CDD 义务。咨询和执行服务中的关键触发点。译为"AML obligations"/"Wwft obligations"；频繁使用时保留 Wwft。
- **CSRD / ESRS / SFDR / Taxonomy**：欧盟可持续性报告框架，现已严重影响荷兰上市公司。欧盟文书名称直译；保留缩略语。
- **MiCA (2023/1114)**：适用于加密资产发行方/服务提供方；2024-2025 年分阶段适用。AFM/DNB 是荷兰的主管机关。译为"MiCA"/"Markets in Crypto-Assets Regulation"。
- **比利时资本市场**：比利时上市公司（Euronext Brussels）受《比利时公司和协会法典》以及 FSMA（行为） / NBB（审慎）监管。比利时收购阈值不同（视情况为 30% 或 50%）。比利时《2020 年公司治理准则》采取类似的"遵循或解释"方法。比利时文件应标注交叉核对。
- **Certificaten / depositary receipts（存托凭证）**：荷兰特有的工具。分离经济和治理权利。凭证持有人拥有经济权利；STAK 持有法定所有权并行使表决权。对每处存托凭证引用仔细标注。
- **Priority shares / prioriteitsaandelen（优先股）**：具有增强权利（有约束力的提名、对某些决议的否决权）的特别股份。曾经常见，自荷兰公司治理准则不鼓励以来已少见。在较老的结构中仍然相关。译为"priority shares"。
