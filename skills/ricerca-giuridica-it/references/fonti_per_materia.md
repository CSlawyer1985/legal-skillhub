# 按实务领域分类的免费来源最小套装

针对每个实务领域，列出来源最小套装：官方且可自由访问的规范性文件、实务/主管机关、判例和决定。规范性文件的出处见 `fonti_normative.md`；访问条件、许可和横向复用规则见 `fonti_dati_giuridici.md`。

- 核验日期：2026-07-06（所有 URL 均通过 fetch 或 curl 核验）；2026-07-17 新增的条目（§§19-21）于同日单独核验。
- 规则：不使用任何付费来源；免费登录但限于某类用户的来源标注“（按类别）”；阻止自动访问的网站标注“（反机器人：回退用 `site:` 搜索或向用户提供说明）”。

---

## 1. 民事（共同基础）[全覆盖]

- 规范性文件：民法典、程序法典、法律总则（preleggi）——Normattiva。
- 合法性（最高法院）：SentenzeWeb（民事全文，布尔 AND/OR/NOT，可按分庭/年份/规范引用过滤）。
- 实体裁判：Banca Dati di Merito / BDP（bdp.giustizia.it）——2016 年起民事含摘要，**需要 SPID/CIE/CNS**（按类别：向用户提供说明）；不含家庭、未成年人和人格身份案件。
- 损害赔偿计算：《米兰表格》（tribunale-milano.giustizia.it，免费 PDF）。
- 裁判取向：最高法院判例汇编处（Ufficio del Massimario）的民事综述（§ Massime 见 `fonti_dati_giuridici.md`）。

## 2. 刑事 [部分覆盖]

- 规范性文件：刑法典、刑事诉讼法典（c.p.p.）、狱政制度、毒品综合法（T.U. stupefacenti）——Normattiva。
- 合法性（最高法院）：SentenzeWeb（刑事档案，过滤器与民事相同）；判例汇编处的刑事综述。
- 上级法院：宪法法院；欧洲人权法院（CEDU）经 HUDOC；欧盟法院（CGUE）经 InfoCuria。
- 免费期刊（编辑内容，仅限引用）：Sistema Penale（CC BY-NC-ND 4.0）、Giurisprudenza Penale、Diritto Penale Contemporaneo 2010-2019 档案（CC BY-NC 4.0）。
- **结构性缺口：** 刑事实体裁判没有任何结构化的免费来源（BDP 仅限民事）。必须始终声明这一点。

## 3. 行政 [全覆盖]

- 规范性文件：第 241/1990 号法律、行政诉讼法典（c.p.a.）、地方实体综合法、公共就业综合法——Normattiva。
- 判例：giustizia-amministrativa.it（国政院 CdS、地方行政法院 TAR、西西里行政司法委员会 CGARS，全文免费）；OpenGA（openga.giustizia-amministrativa.it）——开放数据 **CC BY 4.0**，CKAN API。
- 审计法院：banchedati.corteconti.it。

## 4. 税务 [全覆盖]

- 规范性文件：TUIR（所得税综合法）、增值税综合法、登记税综合法、《纳税人章程》——Normattiva。
- 实务：意大利税务局（Agenzia delle Entrate）“Normativa e prassi”；def.finanze.it（经济和财政文件）。
- 判例：税务判例国家汇编（Massimario nazionale della giurisprudenza tributaria，def.finanze）；最高法院税务分庭经 SentenzeWeb；判例汇编处的税务综述。

## 5. 劳动与社会保障 [全覆盖]

- 规范性文件：《劳动者章程》、Jobs Act、第 81/2015 号立法法令、第 81/2008 号安全综合法——Normattiva。
- 实务：INL（国家劳动监察局，通函和说明，ispettorato.gov.it）；劳工部依第 124/2004 号立法法令第 9 条的答复（interpelli）；INPS“通函、消息和规范性文件”；INAIL（inail.it，规范性文件和通函部分）处理工伤和职业病——已核验可自由查阅，未明确声明复用许可（推定为许可，属公文书）。
- **CCNL（全国集体劳动合同）：** CNEL 国家档案（cnel.it/Archivio-Contratti）——依第 936/1986 号法律第 17 条的官方来源，文本由各方存交；cnel.it/Archivio-Contratti-Collettivi/Contratti-Open-Data 上有 **IODL 2.0 开放数据**数据集（注明出处可含商业复用）。
- 公共就业：ARAN（aranagenzia.it）——分部门的 CCNL 和适用取向（反机器人：回退 `site:aranagenzia.it`）。
- 判例：最高法院劳动分庭经 SentenzeWeb；实体裁判经 BDP（SPID）。

## 6. 银行、保险和金融 [全覆盖]

- 规范性文件：银行综合法（T.U.B.）、金融综合法（T.U.F.）——Normattiva；欧盟框架逐条参见：EBA Interactive Single Rulebook（CRR/CRD/PSD2/DORA/MiCA）、EIOPA Solvency II Single Rulebook。
- 银行监管：意大利央行（Banca d'Italia）——监管规范性文件（Circ. 285/2013 等）、监管取向、制裁决定（网站版权声明较严：安全复用限于各别文书文本并注明引用）。
- 保险：IVASS——规章和市场信函（按年归档，可按关键词检索）。
- 金融：CONSOB——公报（决议、通告、制裁）和监管部分（TUF、规章、ESMA 取向）。
- 反洗钱：UIF（uif.bancaditalia.it）——异常指标（2023 年 5 月 12 日规定）、异常行为模式、《Quaderni》。
- 欧盟机关：EBA Single Rulebook Q&A；ESMA Document Library（约 7,000 份文件，注明引用并须声明修改后可复用）；EIOPA（注明“Source: EIOPA”后可复用）。
- **ADR 决定：** ABF——金融银行仲裁员（arbitrobancariofinanziario.it）：2010 年起决定，可按事项/年份/文本免费高级检索；ACF——金融争议仲裁员（acf.consob.it）：2017 年起决定。价值：ADR 取向，非判例；引用时注明。

## 7. 公司法 [全覆盖]

- 规范性文件：民法典第五编、T.U.F.、公有资本公司综合法——Normattiva。
- 公证员取向（编辑内容受保护，自由查阅，仅限注明来源的引用）：米兰公证委员会公司委员会决议（Massime della Commissione Società del Consiglio Notarile di Milano，约 230 条，系统索引）；意大利东北三区公证人委员会公司取向（Orientamenti societari del Comitato Triveneto dei Notai）。
- 会计：OIC 会计准则（fondazioneoic.eu）——PDF 免费，但除查阅和引用外禁止复用（编辑权保留）。
- 判例：最高法院经 SentenzeWeb；实体裁判经 BDP 和 ilcaso.it（免费层级）。

## 8. 企业危机 [全覆盖]

- 规范性文件：《企业危机与破产法典》（第 14/2019 号立法法令）、破产法（依时间适用范围）——Normattiva。
- 判例和材料：Diritto della Crisi（dirittodellacrisi.it，ANVUR 期刊，裁定全文免费）；IL CASO.it（按法院的实体裁判，1996 年起，免费层级）；Unijuris（破产观察站，乌迪内大学）；最高法院经 SentenzeWeb。
- 复用说明：这些期刊发布的裁定是可引用的公文书；编辑部摘要和注释受保护。
- 过度负债（消费者、小微企业主）：危机组成机构公开登记册（第 3/2012 号法律、第 202/2014 号部长令）位于 crisisovraindebitamento.giustizia.it（giustizia.it 上的落地页已核验可访问）——**登记册子域阻止一切自动抓取**（已用 WebFetch、带浏览器 User-Agent 的 curl、真实浏览测试：全部失败，模式与仓库中已知的其他 `*.giustizia.it` 域一致，如 SentenzeWeb）：真实来源，但只能由终端用户通过人工浏览器核验，不能用于自动检索路由。

## 9. 家庭与未成年人 [部分覆盖]

- 规范性文件：民法典第一编、第 898/1970 号离婚法、第 184/1983 号收养法、第 76/2016 号 Cirinnà 法、Cartabia 改革——Normattiva。
- 判例：最高法院经 SentenzeWeb；宪法法院；欧洲人权法院（HUDOC，第 8 条）。
- 材料：AGIA——儿童与青少年保护局（指南、意见）；AIMMF（minoriefamiglia.org，公共内容）；损害赔偿用《米兰表格》。
- **结构性缺口：** BDP 排除家庭、未成年人和人格身份案件：家庭实体裁判没有免费来源。必须始终声明这一点。

## 10. 知识产权 [全覆盖]

- 规范性文件：《工业产权法典》（第 30/2005 号立法法令）、第 633/1941 号著作权法——Normattiva。
- 注册簿：UIBM 数据库（1989 年起意大利权利）；EUIPO eSearch plus（欧盟商标、外观设计）；TMview/DesignView（TMDN 聚合器）；EPO European Patent Register + Espacenet（反机器人：程序化访问用 OPS API，注册免费）；WIPO PATENTSCOPE 和 Global Brand Database。
- 判例和决定：EUIPO eSearch Case Law（申诉委员会、欧盟商标/外观设计判决）；EPO 申诉委员会（1979 年起决定，全文）；UPC——统一专利法院决定和命令（反机器人：回退 `site:unifiedpatentcourt.org`）；企业专门分庭经 BDP（SPID）。

## 11. 消费者法与竞争法 [全覆盖]

- 规范性文件：《消费法典》（第 206/2005 号立法法令）——Normattiva。
- 主管机关：AGCM——决定高级检索（垄断协议、滥用市场支配地位、不正当商业行为、不公平条款）；整个 agcm.it 域对自动抓取一律返回 403：回退 `site:agcm.it` 或 PDF 公报。
- ADR：MIMIT 的国家 ADR 机构名单；欧盟 ADR 机构名单（consumer-redress.ec.europa.eu）；AGCOM 的 ConciliaWeb（电信，SPID 访问）；ARERA 调解服务（能源、水、废弃物）；银行/投资用 ABF 和 ACF（§6）。
- **注意：** 欧盟 ODR 平台**已于 2025 年 7 月 20 日停用**（欧盟 2024/3228 号条例）：不要再路由到 ec.europa.eu/consumers/odr。

## 12. 房地产与建筑 [全覆盖]

- 规范性文件：《建筑综合法》（第 380/2001 号总统令）、征收综合法、民法典第三编——Normattiva。
- 不动产数据：意大利税务局 OMI 报价（按区域半年期，引用“Agenzia delle Entrate – OMI”）；OMI 出版物（不动产报告、统计）；地籍制图地理门户——**CC BY 4.0**，可查询 WMS/WFS 服务。
- 地籍查询和抵押登记查询：经 SPID/CIE/CNS 免费（按类别：向用户提供说明）。
- 判例：建筑/城市规划经 giustizia-amministrativa.it；民事经 SentenzeWeb 和 BDP。
- 全国公证委员会研究（notariato.it）：自由查阅，但法律声明**禁止复制**——仅可链接和简短注明来源的引用。

## 13. 隐私与数据保护 [全覆盖]

- 规范性文件：GDPR（欧盟 2016/679 号条例）经 EUR-Lex；《隐私法典》（第 196/2003 号立法法令）——Normattiva。
- 主管机关：Garante——决定在 DocWeb 数据库（gpdp.it，引用 doc web 编号）；EDPB——指南和意见。
- 判例：欧盟法院经 InfoCuria（该领域至关重要）；欧洲人权法院经 HUDOC；最高法院经 SentenzeWeb。

## 14. 合规与实体责任（231）[全覆盖]

- 规范性文件：第 231/2001 号立法法令、第 231/2007 号立法法令（反洗钱）、第 24/2023 号立法法令（举报）——Normattiva。
- 指引：Confindustria——第 231 号指引（2021 年版，经司法部批准；文件受保护，注明来源引用）；UIF——异常指标和模式；ANAC——举报指引（第 311/2023 号决议及后续）。
- 判例：最高法院经 SentenzeWeb（实体责任，刑事分庭）；判例汇编处综述。

## 15. 教育法 [全覆盖]

- 规范性文件：《教育综合法》（第 297/1994 号立法法令）、第 107/2015 号法律——Normattiva；MIM 规范性文件和通函（mim.gov.it/web/guest/normativa，可按类型/主题/日期过滤，无全文：回退 `site:mim.gov.it`）。
- CCNL：Istruzione e Ricerca 部门见 ARAN 和 CNEL 档案。
- 诉讼：giustizia-amministrativa.it（排名、竞聘、学校规模调整纠纷）；雇佣关系用最高法院劳动分庭。

## 16. 移民与国际保护 [全覆盖]

- 规范性文件：《移民综合法》（第 286/1998 号立法法令）、第 251/2007 号立法法令、第 25/2008 号立法法令——Normattiva（稳定的 URN-NIR 永久链接）。
- 实务：内政部公民自由与移民司通函（libertaciviliimmigrazione.dlci.interno.gov.it，仅日期过滤：回退 `site:`）；国家庇护权利委员会。
- 欧盟：EUAA（注明引用可复制）——Asylum Report、Country Guidance、Case Law Database；COI 门户（coi.euaa.europa.eu）获取来源国信息。
- 判例：最高法院经 SentenzeWeb；判例汇编处国际保护综述；欧洲人权法院经 HUDOC；欧盟法院经 InfoCuria。
- 行业汇编：ASGI 数据库（asgi.it/banca-dati，CC BY-NC-SA 4.0 许可：仅限注明出处的非商业复用；裁定本身仍为公文书）。

## 17. 律师职业道德 [部分覆盖]

- 规范性文件：律师职业法（2012 年 12 月 31 日第 247 号法律）——Normattiva（见 `fonti_normative.md`）；CNF 通过的《律师职业道德守则》，合并文本 PDF 发布在 consiglionazionaleforense.it/codice-deontologico-forense（不是 Normattiva 上的立法来源：行业自律规范，务必在网站核验最新修改，如关于合理报酬的第 25 条之二）。
- 主管机关：地区纪律委员会（CDD，依第 247/2012 号法律第 50 条起设立）一审；全国律师委员会（CNF）上诉审。
- **结构性缺口：** 未核验到任何公开免费、可检索的纪律判例数据库（仅 CNF 网站上有零散公告和通函）；不得假定其存在。

## 18. 政府采购 [全覆盖]

- 规范性文件：《公共合同法典》（2023 年 3 月 31 日第 36 号立法法令）——Normattiva；先前的第 50/2016 号和第 163/2006 号立法法令已废止，仅依时间适用范围相关（见 `fonti_normative.md`）。
- 实务：ANAC（anticorruzione.it）——决议、意见、指南、标准招标文件；公开招标数据在 dati.anticorruzione.it/opendata（BDNCP，CSV/JSON/OCDS 格式，经 PDND 提供 API）。
- 判例：诉讼经 giustizia-amministrativa.it；开放数据经 OpenGA（CC BY 4.0）。
- 仲裁：ANAC 公共合同仲裁庭（anticorruzione.it/en/arbitrati，依第 36/2023 号立法法令第 214 条）——裁决可下载 PDF，无职能角色的自然人数据已由来源方匿名化；已核验可自由访问。
- 程序：特别程序期限（采购程序，c.p.a. 第 120 条）见 `percorsi_processuali.md`。

## 19. 继承与家庭财产制度 [部分覆盖]

- 规范性文件：民法典第二编（继承）和第一编第六题（家庭财产制度）——Normattiva；继承和赠与税综合法（1990 年 10 月 31 日第 346 号立法法令）——出处已核验于 `fonti_normative.md`。
- 实务：意大利税务局——关于继承申报的通函和答复；全国公证委员会研究（notariato.it/ufficio-studi）：自由查阅但**禁止复制**——仅可链接和简短注明来源的引用（与 §12 相同复用制度）。
- 判例：最高法院经 SentenzeWeb；不属于家庭/人格身份排除范围时实体裁判经 BDP（SPID）（见 §1、§9）。
- **已声明缺口：** 没有具体的程序门禁（限定继承接受期限、放弃、扣减之诉）在 `percorsi_processuali.md` 中得到核验：引用前务必核验具体条文。

## 20. 环境与能源 [部分覆盖]

- 规范性文件：《环境法典》（2006 年 4 月 3 日第 152 号立法法令）——Normattiva，出处已核验于 `fonti_normative.md`。
- 许可：MASE 的 VIA-VAS-AIA 国家门户（va.mite.gov.it）——已决程序和进行中程序；**截至 2026-07-17 交互式服务因网络安全要求核验暂时停用**（网站上有明确横幅），但内容仍可只读查阅：使用时核验状态。
- 技术数据：ISPRA（isprambiente.gov.it）——环境报告和数据。
- 能源：ARERA（arera.it）——监管决议（与 §11 已登记的 ADR 服务台区分）；GSE（gse.it）处理 FER 激励——**复用许可未核验**：作为可引用的公文书处理，不假定可大规模复用。
- 判例：诉讼经 giustizia-amministrativa.it（见 §3）。

## 21. 体育法 [仅路由]

- 规范性文件：体育管辖权划分，2003 年 10 月 17 日第 280 号法律（第 220/2003 号法令之转换）——**出处引用前务必在 Normattiva 核验**，尚未列入 `fonti_normative.md`。
- 实务/自律规范：CONI《体育司法法典》（coni.it）——自律规范文书，非国家立法来源：务必在网站核验现行版本。
- 决定：CONI 体育保障委员会（coni.it/it/attivita-istituzionali/collegio-di-garanzia-dello-sport/giudizi.html）——裁判档案；直接抓取在测试中出错（仓库已登记的机构门户常见反机器人模式）：使用时核验档案的可访问性和连续性。
- **已声明缺口：** 未核验任何联邦部门判例（如 FIGC 体育司法）：不得假定其可免费获取。

## 22. 第三部门 [部分覆盖]

- 规范性文件：《第三部门法典》（2017 年 7 月 3 日第 117 号立法法令）——Normattiva，出处已核验于 `fonti_normative.md`；依第 102 条的明示和延迟废止：务必核验单条规定的具体现行效力。
- 登记册：RUNTS——国家第三部门统一登记册（servizi.lavoro.gov.it/runts，劳动部）——查询登记组织，公开免费；已核验无需登录可查阅。首页未明确复用法律声明：作为可引用的公文书处理，不作为整体获取的数据集。
- 实务：劳动部第三部门通函（lavoro.gov.it，与 §5 已引用的同一来源）。
- **已声明缺口：** 未核验任何部门特定判例；诉讼依事项归入一般民事或行政（见 §1、§3），据此路由。

## 23. 运输法 [仅路由]

- 规范性文件：部门规范（铁路、港口、机场）在 Normattiva 上按文书分散——**引用前务必逐项核验出处**，尚未列入 `fonti_normative.md`。
- 主管机关：运输监管局——ART（autorita-trasporti.it/ricerca-avanzata）处理基础设施准入、公共服务义务、费率方面的决议、意见、咨询和报告；已核验无需登录可自由查阅，可按年份/文书类型/运输方式过滤；除网站一般版权外无明确复用许可（推定为许可，公文书）。
- 判例：涉及授权决定时诉讼经 giustizia-amministrativa.it（见 §3）。
- **已声明缺口：** 海事/航运法（航海法典、海岸警卫队、港口系统管理局）已探索但尚未纳入本目录：16 个港口系统管理局的来源分散在各自门户上，无统一索引，路由用户前务必逐一核验。

---

## 横向缺口（相关时必须声明）

1. **带 Rv 编号的最高法院判例汇编：** 公众无法免费访问；免费替代见 `fonti_dati_giuridici.md` 的 § Massime；向 Cassa Forense 注册的律师可免费访问 ItalgiureWeb（按类别）。
2. **Citator：** 没有任何免费来源能说明某判例是否已被超越；通过交叉检索和判例汇编处冲突报告重建。
3. **刑事实体裁判**和**家庭/未成年人实体裁判：** 没有结构化的免费来源。
4. **统一跨库检索：** 免费不存在；按路由规则路由到多个不同引擎。
5. **程序化访问：** API 仅 Normattiva、EUR-Lex、OpenGA（CKAN）、EPO OPS、CNEL 数据集可用；许多机构网站阻止自动抓取——务必预留回退（`site:` 或向用户提供说明）。
