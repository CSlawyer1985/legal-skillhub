# 瑞士法律来源层级

本文件为瑞士法律 AI 工作流对来源类型进行分类。目的不是对每个具体来源作绝对排名，而是防止 AI 助手混淆官方权威、发现基础设施、开放数据、商业研究产品和次级评述。

## 第 1 层——官方基础法律

优先用于法律文本、生效日期、修订和条约状态。

- Fedlex：https://www.fedlex.admin.ch/en/home
- 官方汇编 / Amtliche Sammlung / Recueil officiel / Raccolta ufficiale
- 分类或系统汇编 / Systematische Rechtssammlung / Recueil systématique / Raccolta sistematica
- 通过 Fedlex 发布的联邦条约
- 官方州法门户
- 相关时使用官方市镇/地方法律门户

处理方式：支配性基础来源，须经语言/版本/日期核验。

## 第 2 层——官方判例

用于司法解释、指导性判决、程序实践和法院特定学理。

- 联邦最高法院：https://www.bger.ch/
- 联邦行政法院：https://www.bvger.ch/
- 联邦刑事法院：https://www.bstger.ch/
- 联邦专利法院：https://www.bundespatentgericht.ch/
- 州法院门户

处理方式：官方判例来源。核验判决属于指导性判决、已公开判决、未公开/匿名化判决还是下级法院判决。

## 第 3 层——官方立法材料

用于立法意图、改革追踪、征求意见历史和议会状态。

- 《联邦公报》/ Bundesblatt / Feuille fédérale / Foglio federale：通过 Fedlex
- Curia Vista：https://www.parlament.ch/en/ratsbetrieb/curia-vista
- 《官方公报》：https://www.parlament.ch/en/ratsbetrieb/amtliches-bulletin
- 征求意见程序材料：通过 Fedlex 和 admin.ch

处理方式：除非已颁布，否则不是可操作的法律规则，但对解释和改革追踪很重要。

## 第 4 层——官方监管与监督机关材料

用于行业解释、监管期望、执法立场、指南、通函和许可背景。

- FINMA：https://www.finma.ch/
- FDPIC / EDÖB：https://www.edoeb.admin.ch/en
- COMCO / WEKO：https://www.weko.admin.ch/
- SECO：https://www.seco.admin.ch/
- Swissmedic：https://www.swissmedic.ch/
- 联邦税务局 / ESTV：https://www.estv.admin.ch/
- 联邦通信办公室 / BAKOM-OFCOM：https://www.bakom.admin.ch/
- fedpol / MROS：https://www.fedpol.admin.ch/

处理方式：仔细归类为约束性条例、通函、指南、执法报告、建议、常见问题或软法/自律材料。

## 第 5 层——登记簿和法律状态来源

用于法律状态事实：存在性、注册、公告、所有权/状态通知、破产/公告事件、知识产权注册。

- Zefix：https://www.zefix.ch/
- 《瑞士商业公报》/ SHAB / SOGC：https://www.shab.ch/
- 各州商事登记簿
- Swissreg / IPI：https://www.swissreg.ch/
- 债务执行和破产公告来源
- 可访问的不动产登记簿来源

处理方式：登记簿/法律状态事实的证据，不替代法律分析。

## 第 6 层——开放发现和 AI 就绪层面

用于搜索、元数据、引用图谱、API、批量数据和跨来源发现。

- OpenCaseLaw：https://opencaselaw.ch/
- LexFind：https://www.lexfind.ch/
- Entscheidsuche：https://entscheidsuche.ch/
- opendata.swiss：https://opendata.swiss/en
- Fedlex-JOLux：https://swiss.github.io/fedlex-jolux/

处理方式：对发现和机器工作流有用。尽可能针对官方来源核验支配性命题。

## 第 7 层——学理与专家权威

在核验官方法律、判例和监管实践之后，用于学理评述、专著、教科书、专家意见和学术著作。学理有助于构建解释结构并识别争议，但仅具**说服力而非约束力**。优先署名著作（如评注、专著、学术文章），而非仅列姓名。核验版本日期、语言和出版背景。学理可能在德文、法文和意大利文学术界之间以及各州之间存在分歧。

示例：

- 评注（如 **Basler Kommentar**、**Berner Kommentar**、**Commentaire romand**）
- 特定领域的专著、手册和教科书（如刑法、宪法、税法、公司法、数据保护）
- 已发表的专家意见和法律报告

处理方式：说服性权威。使用学理理解法律的结构、标准解释和学理争议。未经官方来源确认，不得将学理作为支配性法律引用。按领域划分的指南见 `resources/doctrine-and-expert-authority-map.md`。

## 第 8 层——次级导向

用于导向、教学、背景和研究扩展。这些来源提供总体概览、研究指导和法律文化背景，但不构成基础或学理权威。

- GlobaLex 瑞士研究指南
- 美国国会图书馆《在线法律指南》：瑞士
- UZH / 法律数据科学中心法律数据资源
- **sui generis** 开放获取期刊
- 大学法律研究指南
- 瑞士法的开放学术入门
- 律所注释、通讯、博客文章和实务评述

处理方式：次级。这些资源对广泛导向和发现进一步来源有帮助，但不具权威性。任何法律主张均须对照官方来源和学理核验。

## 第 9 层——商业或需登录的法律研究产品

在用户有权访问且专业研究完整性需要时使用。

- Swisslex
- Lawsearch / Weblaw
- Legalis
- 私营法律 AI 和研究平台
- 律所知识库

处理方式：强大的研究工具，但应与免费/开放公共基础设施分开归类，并避免暗示可公开访问。

## 来源状态标签

在输出中使用这些标签。选择最能反映每个引用来源法律地位的标签。如需体现学理细微差别，可扩展或细化。

- `official-primary-law`（官方基础法律）
- `official-case-law`（官方判例）
- `official-legislative-material`（官方立法材料）
- `official-regulator-material`（官方监管材料）
- `official-register-legal-state`（官方登记簿法律状态）
- `official-cantonal-or-communal`（官方州或市镇）
- `open-data-or-machine-readable`（开放数据或机器可读）
- `free-discovery-layer`（免费发现层）
- `doctrine-or-expert-authority`（学理或专家权威）
- `secondary-orientation`（次级导向）
- `commercial-or-login-based`（商业或需登录）
- `soft-law-or-self-regulation`（软法或自律）
- `unknown-or-unverified-status`（状态未知或未核验）
