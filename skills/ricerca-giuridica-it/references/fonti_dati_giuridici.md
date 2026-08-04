# 法律数据来源——访问与再利用地图

规范引用目录（`fonti_normative.md`）的技术配套文件：针对每个官方来源，如何访问（包括自动方式）、适用何种许可、有何再利用规则。供技能用于路由检索，并评估在文档语料库中合法获取什么。

- 目录更新日期：2026-07-17（新增条目：税务实体司法、AGCOM；此轮未重新核查旧条目）
- 一般规则：文书文本是自由的，编辑增值内容则否。任何获取前务必核查许可和使用条款。

---

## 1. 根本性不对称

法规（国家和欧盟）已解决：开放数据、API、可复用许可。判例则不然：免费可读，但没有官方的整体开放数据。意大利没有美国 Caselaw Access Project 或瑞士 OpenCaseLaw 的对应物。司法部未将判决作为开放数据发布。

实际后果：可以合法构建广泛且最新的法规语料库；无法合法构建广泛的判例语料库。判例只能针对自身议题做定向深入收集，而非广度收集。

---

## 2. 法规

| 层级 | 来源/端点 | 机器访问 | 许可 | 获取适宜性 |
|---|---|---|---|---|
| 宪法和宪法性法律 | Normattiva；判例见 cortecostituzionale.it | 同国家法规 | CC BY 4.0（Normattiva） | 高 |
| 国家法规 | dati.normattiva.it | REST API（含 OpenAPI）、Postman 配置、批量数据集 | CC BY 4.0 | 高 |
| 大区法律 | normattiva.it/legislazioneRegionale（联邦式引擎：转发至各区域议会和自治省数据库） | 联邦式网页检索；文本存于来源大区数据库。真正开放 API 的大区数据库示例：伦巴第，dati.lombardia.it/resource/abjw-hhay.json（Socrata，CC0），全文 HTML/XML 链接于 normelombardia.consiglio.regione.lombardia.it；2026-07-09 核实可用。2026-07-13 实机核查**未确认**可比的：艾米利亚-罗马涅（dati.emilia-romagna.it 是真正的 CKAN 门户，但没有大区法律数据集——只有在其他语境引用法律编号的行政数据）；托斯卡纳（raccoltanormativa.consiglio.regione.toscana.it 是可通过网页查询的档案，无 API/开放许可迹象）；威尼托（直接检查未发现开放的立法数据库）。其他大区须逐案核查：不得假定同样开放 | 公共文书；各区域数据库条件各异 | 中（来源分散，除伦巴第等已核实例外外无统一 API） |
| 国际条约 | ATRIO — atrio.esteri.it（MAECI 条约档案，双边和多边） | 按事项和时间线网页查询 | 机构数据，须注明来源 | 中 |
| 欧盟法律 | EUR-Lex / CELLAR | SPARQL、REST API、数据转储、SOAP 网络服务 | 按 Publications Office 政策再利用 | 高 |
| 欧盟企业登记和破产登记（跨境诉讼、债权回收、对外国对手方尽职调查） | e-Justice 门户——企业登记互连系统（BRIS，指令 2012/17/EU，条例 EU 2015/884）及互连破产登记（条例 EU 2015/848 第 25 条）：e-justice.europa.eu，"Business registers" 和 "Bankruptcy/insolvency registers" 栏目 | 免费网页检索，无须登录，按公司名称或代码查询，直接链接至 27 个国家登记处；核实可用（页面 2026 年更新） | 门户内容依决定 2011/833/EU 再利用（法律声明已核实）；各国家登记处的数据遵循来源登记的条款 | 中（联邦式访问点，非可获取的统一数据集） |
| 次级来源（条例） | gazzettaufficiale.it + 发布机关官方站点 | 网页查询 | 公共文书 | 中 |
| 惯例和习惯 | 商会省级惯例汇编（旧 R.D. 2011/1934），见于各 CCIAA 网站 | 按省网页/PDF 查询 | 商会公共文件，须注明来源 | 低（按省分散） |
| 立法准备工作 | senato.it 和 camera.it（法案程序、卷宗）；开放数据见 dati.camera.it（CC BY 4.0，已核实：许可从 CC BY-SA 3.0 变更以覆盖数据库特别权利）和 dati.senato.it（CC BY 3.0，页面已核实） | 网页查询；两个开放数据门户都要求浏览器 User-Agent（无任何请求头则返回 403，非站点不可达） | 公共文书 | 中 |
| 官方发布 | gazzettaufficiale.it | 网页查询 | 公共文书 | 中 |

基础来源——宪法、《民法典》（1942 年 3 月 16 日 R.D. 第 262 号）、《刑法典》（1930 年 10 月 19 日 R.D. 第 1398 号）、程序法典、统一文本——已在 `fonti_normative.md` 中连同引用信息和现行效力状态编目。权威且最新的文本始终是 Normattiva。

---

## 3. 判例

| 法院 | 来源/端点 | 访问 | 再利用 | 备注 |
|---|---|---|---|---|
| 最高法院（Cassazione） | SentenzeWeb（italgiure.giustizia.it/sncass） | 免费网页检索，无须注册：全文，支持 AND/OR/NOT 布尔运算、引用信息、法律引用、ECLI、分庭/年份筛选；无 API | 公共文书，无批量再利用许可 | 定向收集，无批量；*.giustizia.it 证书标准抓取器无法验证 |
| CED 裁判要旨及其他法院 | ItalgiureWeb 保留区（italgiure.giustizia.it） | 免费登录但限特定人群：法官、公共行政机关及登记于 Cassa Forense 的律师（合作协议，经 cassaforense.it 激活） | 个人使用，不可再分发 | "按类别"来源：获授权的律师可核实 Rv 编号；不可用于语料库 |
| 民事实体（Merito） | Banca Dati di Merito / BDP（bdp.giustizia.it） | 免费但非匿名：SPID/CIE/CNS；全文 + 摘要，2016 年起约 350 万份裁判文书 | 公共文书；大规模编辑性再利用须专门协议 | **排除家庭、未成年人和身份状态**；无 API：向用户提供说明 |
| 行政司法（国务委员会、大区行政法院 TAR、西西里行政司法委员会 CGARS） | giustizia-amministrativa.it，"Decisioni e pareri" 栏目 | 网页检索，全文免费 | 公共文书 | 行政诉讼和采购 |
| 行政司法，开放数据 | OpenGA（openga.giustizia-amministrativa.it） | CKAN 门户，标准 API，裁判文书和活动数据集 | **声明 CC BY 4.0**（在资源层面经 API `package_show`/RDF-DCAT 导出核实；单个数据集的 HTML 页面误导性地显示"未指明许可"——经 API 核实，勿看页面组件） | 唯一有明确开放许可的司法门户 |
| 统一专利法院 | UPC — unifiedpatentcourt.org/en/decisions-and-orders | 浏览器自由查询；自动抓取返回 403 | 公开裁判文书，须注明来源 | 备选：检索 `site:unifiedpatentcourt.org` |
| 宪法法院 | cortecostituzionale.it，"Ricerca pronunce" 栏目 | 网页检索，全文带 ECLI 标识符 | 公共文书 | 作为检索种子也可参见 LAWSUIT 数据集（§5） |
| 审计法院 | banchedati.corteconti.it | 网页检索 | 公共文书 | 会计管辖权、公共资金责任、地方实体 |
| 税务司法（实体） | bancadatigiurisprudenza.giustiziatributaria.gov.it（税务司法司，MEF） | 公开网页检索，无须登录：全文和高级筛选；自动抓取返回 403（2026-07-17 核实），备选 `site:giustiziatributaria.gov.it` 或姊妹门户 dgt.mef.gov.it | 公共文书，未声明批量再利用许可 | 2021 年起一审和二审判决，已假名化；区别于国家税务裁判要旨汇编（§4，非完整汇编） |
| 欧盟法院（CJEU） | curia.europa.eu（InfoCuria）；判决也见于 EUR-Lex | 网页检索；EUR-Lex 有 API | 按 Publications Office 政策再利用 | 以 ECLI/CELEX 引用 |
| 欧洲人权法院（ECtHR） | HUDOC（hudoc.echr.coe.int） | 网页检索 | 欧洲委员会版权，自由查询和引用 | 《欧洲人权公约》 |
| 欧洲人权法院，判决执行 | HUDOC-EXEC（hudoc.exec.coe.int）——判决执行司 | 免费网页检索，无须登录；可按国家、主题、监督状态、试点判决筛选；经实际浏览核实（69,654 条结果，其中意大利 9,310 条，截至 2026-07-17） | 推定与 HUDOC 相同（欧洲委员会版权，自由查询和引用）——未逐条重新核查子域特定法律声明 | 行动计划/报告、部长委员会依《欧洲人权公约》第 46 条的决定和决议 |

---

## 3-bis. 裁判要旨：哪些免费可得、哪些没有

免费裁判要旨和立场来源的层级，自最权威者起：

1. **宪法法院官方裁判要旨**——cortecostituzionale.it，"Ricerca sulle massime"：意大利唯一完整免费的官方裁判要旨汇编（自 1956 年起）。要旨检索界面有反机器人保护：浏览器自由访问，自动访问不行。
2. **欧盟法院摘要/裁判要旨**——收集于 InfoCuria（curia.europa.eu，高级检索 20+ 字段，运算符 `*`、`_`、引号、空格=AND、逗号=OR、`!`=EXCEPT）和 EUR-Lex（CELEX 6 部门，含学说注释；API 和批量免费，须先注册；站点阻止非浏览器抓取）。
3. **裁判要旨办公室的汇编和报告**——cortedicassazione.it（超过 440 份免费 PDF：月度民事和刑事汇编、年度、专题、关于分歧和新法规的报告；引用 Rv 编号）以及 **IPZS 裁判要旨门户**（portaledelmassimario.ipzs.it：2010-2024 年度汇编，在线全文）。权威立场但非官方裁判要旨：引用汇编和底层判决。
4. **实体判决数据库（Banca Dati di Merito）摘要**——民事实体自动生成的准裁判要旨（SPID，自 2016 年起，排除家庭/未成年）。
5. **带 Rv 编号的 CED 裁判要旨**——不公开：仅 ItalgiureWeb（按类别：Cassa Forense 律师、法官、公共行政机关）或商业数据库。只有所取回语境中出现 Rv 编号时才可引用。
6. **由全文生成的裁判要旨**——工作草稿，绝无权威性（见技能规则）。

免费无法实现的：可查询的完整 CED 裁判要旨；引证检索（核实某一立场是否仍有效）；实体案件的编辑性裁判要旨；跨合法性+实体+宪法+欧盟的统一检索（需编排 4-5 个独立引擎）。

---

## 4. 行政实践

再利用列有三种状态：**已核实宽松（明确）** = 已核查网站法律声明，明确声明允许引用或复制；**推定宽松（公共文书）** = 未核查特定法律声明，依据 §6 一般原则（公共文书文本自由，L. 633/1941 第 5 条）；**已核实限制性** = 网站明确声明超出引用的限制（禁止转储、禁止再版、保留所有权利）。

| 事项 | 来源/端点 | 访问 | 再利用 |
|---|---|---|---|
| 税务 | 税务局（Agenzia delle Entrate）"Normativa e prassi" + def.finanze.it | 已发布的 PDF/HTML 文件 | 推定宽松（公共文书），须注明来源 |
| 采购、解释性行为 | ANAC anticorruzione.it（决议、意见、指南、示范招标文件） | 已发布文件 | 推定宽松（公共文书） |
| 采购、招标数据 | dati.anticorruzione.it/opendata（BDNCP） | CSV/JSON/OCDS 批量、经 PDND 的 API | 已核实宽松（明确）：开放数据（交易数据，非法律文本） |
| 劳动、监察 | INL ispettorato.gov.it（通知、说明、意见） | 已发布文件 | 推定宽松（公共文书） |
| 劳动、解释请求（interpelli） | lavoro.gov.it，"Interpelli" 栏目（D.lgs. 124/2004 第 9 条） | 已发布文件 | 推定宽松（公共文书） |
| 社保 | INPS，"Circolari、Messaggi e Normativa" 栏目 | 已发布文件 | 推定宽松（公共文书） |
| 隐私 | Garante gpdp.it（裁决、DocWeb 数据库） | 网页检索 | 推定宽松（公共文书），须注明 doc web 编号 |
| 隐私、欧盟层面 | EDPB edpb.europa.eu（指南、意见） | 已发布文件 | 已核实宽松（明确）：注明出处再利用 |
| 银行监管 | 意大利央行（法规和监管立场、处罚） | 网页档案 + PDF，按关键词/年份检索 | **已核实限制性**：文书文本可引用，但网站版权声明明确：禁止大规模再版 |
| 保险 | IVASS（条例、致市场函件） | 按年份档案 + 关键词检索 | **已核实限制性**：同意大利央行，文书文本可引用，禁止转储 |
| 金融 | CONSOB（公报、监管） | 公报全文检索 | **已核实限制性**：官方文书可引用，但网站和数据库声明"保留所有权利" |
| 反洗钱 | UIF uif.bancaditalia.it（异常指标、范本、Quaderni 系列） | 已发布文件 | 推定宽松（公共文书） |
| 欧盟金融监管机关 | EBA（Interactive Single Rulebook、Q&A）、ESMA（Document Library）、EIOPA（Solvency II Rulebook） | 网页检索 + PDF，无须登录 | 已核实宽松（明确）：注明出处获准复制（法律声明已核实）；衍生作品须声明修改 |
| 竞争和消费 | AGCM（裁决高级检索） | 浏览器自由访问；**整个域名对抓取返回 403**：备选 `site:agcm.it` 或 PDF 公报 | 推定宽松（公共文书） |
| 通信和媒体 | AGCOM agcom.it/provvedimenti（编号决议 n. XXX/YY/CONS 或 /CSP；与上述 AGCM 是不同机关，勿混淆两个域名） | 自由网页检索，可按名称/类型/编号/年份/机关筛选；自动抓取可达（2026-07-17 核实，与 AGCM 域名不同） | 推定宽松（公共文书） |
| 教育 | MIM mim.gov.it/web/guest/normativa（通知、法令、命令） | 按类型/主题/日期筛选，无全文：备选 `site:` | 推定宽松（公共文书） |
| 移民 | 内政部、公民自由司（通知）；国家庇护委员会 | 自由查询，仅日期筛选：备选 `site:` | 推定宽松（公共文书） |
| 地方实体 | 内政部、DAIT——内政和领土事务司（dait.interno.gov.it/pareri）：地方行政官员资格、依 D.lgs. 235/2012 的当选障碍事由 | 按主题领域和年份自由网页检索，2000 年起 2,704 份意见；自动抓取可达（2026-07-17 核实，无反机器人） | 推定宽松（公共文书）；未找到特定法律声明 |
| 欧盟国际保护 | EUAA euaa.europa.eu + COI 门户 coi.euaa.europa.eu | 公开，按国家高级检索 | 已核实宽松（明确）：注明出处获准复制（法律声明） |

**商业数据库**（DeJure、Pluris、OneLegale）：订阅访问；许可禁止提取和转存内容。在任何情况下都不是获准的获取来源。

---

## 4-bis. ADR 决定与集体合同

| 来源 | 端点 | 访问 | 再利用 |
|---|---|---|---|
| ABF——银行金融仲裁员 | arbitrobancariofinanziario.it/decisioni/ricerca-avanzata | 免费检索，无须登录：2010 年起决定，按事项/年份/文本 | 决定可注明来源引用；站点 © 意大利央行限制性，禁止转储 |
| ACF——金融争议仲裁员 | acf.consob.it/decisioni-del-collegio | 自由查询：2017 年起决定 | 决定可注明来源引用；须核查 consob.it 的限制性法律声明（§4，"保留所有权利"）是否延伸至子域 acf.consob.it，或该子域是否有自身条款（待核查） |
| 消费者 ADR | MIMIT 名册（国家 ADR 机构）；欧盟名册见 consumer-redress.ec.europa.eu；ConciliaWeb AGCOM（电信，SPID）；ARERA 调解服务（能源/水/废弃物） | 自由查询；程序经数字身份 | 机构数据，须注明来源 |
| 欧洲 ODR 平台 | **自 2025 年 7 月 20 日起停运**（条例 EU 2024/3228） | — | 不要再路由至 ec.europa.eu/consumers/odr |
| CCNL、国家档案 | CNEL cnel.it/Archivio-Contratti | 按行业自由检索；依 L. 936/1986 第 17 条存放的认证文本 | 注明来源获准复制（页面声明） |
| CCNL、开放数据 | cnel.it/Archivio-Contratti-Collettivi/Contratti-Open-Data | 直接下载，开放格式，URL 稳定 | **IODL 2.0**：注明出处可含商业再利用 |
| CCNL 公共部门 | ARAN aranagenzia.it（按板块合同、适用立场） | 浏览器自由访问；抓取返回 403：备选 `site:aranagenzia.it` | 机构文件可注明来源引用 |

---

## 5. 开放与研究数据集（待评估，非官方）

作为检索种子使用，须对覆盖范围、更新、来源以及数据集原始来源声明的**许可**进行强制审计（绝不接受"开放"之类的笼统标签）。它们不是权威来源。

| 数据集 | 内容 | 声明许可 | 用途 |
|---|---|---|---|
| italian-legal-corpus（Hugging Face） | 意大利法律、欧盟法律、司法裁判文书；公共领域文本 | 汇编 CC BY 4.0 | 广泛种子；须核查哪些裁判文书及时间远近 |
| LAWSUIT | 1956-2022 年 14,000 份宪法法院判决，附专家撰写的裁判要旨 | **CC BY-SA 3.0 IT**（已核实：与来源相同的许可，即宪法法院的开放数据） | 非常适合宪法法院，也是裁判要旨撰写的范例；不是最高法院 |
| Italia Corpus（github.com/ahmeabd/italia-corpus） | 意大利立法 Markdown 版，每日从 Normattiva 更新 | **MIT**（生成代码，经 GitHub API 核实）；立法文本依 L. 633/1941 第 5 条仍属公共领域 | 现成的 Normattiva 摄入替代方案；须核查完整性 |
| Italian Civil Code（A. Simeri，HF） | 结构化《民法典》及交叉引用 | **Apache 2.0**（经 Hugging Face API 核实） | 有助于条文结构和引用 |

注：这些数据集覆盖法规和宪法法院。最高法院则仍部分覆盖或缺失：广泛且最新的最高法院语料库只能通过 SentenzeWeb 定向收集构建。

---

## 6. 法律约束摘要

- 文书文本（法律、判决）：自由（L. 633/1941 第 5 条）。
- 编辑内容（编辑性裁判要旨、评论、注释、词典）：受保护。
- 数据库本身：制作者的特别权利（L. 633/1941 第 102-bis 条），禁止提取实质部分，无论由谁执行、无论是否转售。
- Normattiva：CC BY 4.0，注明出处再利用。
- EUR-Lex：按 Publications Office 政策再利用。
- 判决：公共文书，但无整体批量再利用许可。针对自身议题的定向收集可接受；广泛判决语料库的再分发则不可。对同一数据库（如 SentenzeWeb）在时间上累积多个定向收集，仍受制于禁止反复、系统性地提取或再利用即使非实质部分的规则，当该行为与数据库的正常管理相悖或损害制作者时（L. 633/1941 第 102-bis 条）：时间上的重复不是规避大规模提取禁令的漏洞。
- Italgiure 保留区：登记律师的个人使用，不可再分发。
- 商业数据库：许可禁止转存，无论去向何处。

---

## 7. 获取的操作规则（不要做什么）

- 不要构建或运行针对商业数据库或 Italgiure 的大规模提取器。
- 不要复制他人的编辑性裁判要旨（Giuffrè、Wolters Kluwer、裁判要旨办公室）：判决全文是自由的，编辑性裁判要旨是受保护的作品。如需裁判要旨，从完整文本生成并作为草稿处理。
- 不要将生成的裁判要旨当作可引用内容：始终引用底层判决。
- 不要以激进或自动化的方式超出使用条款强行访问机构网站（SentenzeWeb、def.finanze、Banca Dati di Merito）。
- 不要将在同一来源上随时间累积定向收集视为规避大规模提取禁令的合法方式：即使小批量，系统性重复仍被禁止（L. 633/1941 第 102-bis 条）。

---

## 8. 维护

- 多时效版本：管理适用于特定日期的规范版本是最严重的技术风险。Normattiva 经 API 提供，但完整的按时间适用开放数据目前仅覆盖最近 5 年。
- 引用：只引用所取回语境中的内容，附可核实的引用信息。
- 引证检索缺失：没有任何免费来源能说明某判决是否仍为有效法律。没有付费数据库则无法弥补此限制。
- 编码：许多第三方 PDF 和网页不是 UTF-8（常见 Windows-1252）。须规划规范化。
- 最终核查：对会产生后果的使用（公共行政机关、招标、文书），输出必须始终与官方来源核对。
