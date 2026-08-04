# 更新日志

`nuremberg-tokyo` skill 的所有重要变更均记录在本文件中。

格式遵循 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)，本 skill 遵循 [语义化版本](https://semver.org/spec/v2.0.0.html)。

## [1.0.1] — 2026-06-02

### 修复
- IMTFE 被告表（`references/defendants-and-judges.md`、`references/citation-format.md`）：将冈田（Takasumi Oka）的军衔更正为**海军中将**。已对照 UVA IMTFE 数字馆藏核验。

## [1.0.0] — 初始发布

### 新增
- `SKILL.md` —— 入口文件，将**IMT**（1945-46）、依照管制委员会第 10 号法律进行的十二场后续**NMT**审判（1946-49）以及**IMTFE**（1946-48）整合为单一 skill；先核验后回答的纪律、标准工作流、四大经典陷阱（IMT/NMT、纽伦堡/东京、宪章术语、多数意见与个别意见）、基础文本清单、含约 15 个第一层来源的来源层级、引用格式概览、审计模式、实体学理指引、敏感语境指引
- `references/foundational-texts.md` —— 《伦敦协定》（82 U.N.T.S. 280）及作为附件的 IMT 宪章；管制委员会第 10 号法律及其第 II(1)(c) 条；麦克阿瑟 1946 年 1 月 19 日特别公告和《东京宪章》（第 5 条 A/B/C 级、第 6 条责任）；IMTFE 程序规则（1946 年 4 月 25 日）；联合国大会 1946 年 12 月 11 日第 95(I) 号决议；联合国大会 1947 年 11 月 21 日第 177(II) 号决议；国际法委员会 1950 年纽伦堡原则
- `references/authoritative-sources.md` —— 全面的第一层 / 第二层 / 绝不可作为权威的来源层级。第一层涵盖：三部官方出版的审判记录（蓝皮书系列 42 卷、绿皮书系列 15 卷、Pritchard-Zaide 版 IMTFE 记录 22-27 卷）；权威数字档案（耶鲁大学 Avalon 项目、哈佛大学纽伦堡审判项目、斯坦福大学 IMT Taube 档案、弗吉尼亚大学 IMTFE 数字馆藏、国际刑事法院法律工具数据库、JACAR、联合国视听图书馆）；机构典藏（美国国会图书馆、NARA、帝国战争博物馆、胡佛研究所、和平宫图书馆）；以及专门大学馆藏（Creighton Delaney 东京文件、夏威夷大学 WCDI、康涅狄格大学 Dodd 文件、北达科他州、Jackson Center）。第二层涵盖纽伦堡研究院、USHMM、纽伦堡主要学术评述（Taylor、Harris、Smith、Conot、Heller、Schabas、Kelsen）和东京主要学术评述（Minear、Totani、Boister-Cryer、Röling-Cassese、Tanaka-McCormack-Simpson）
- `references/citation-format.md` —— 五种引用模式（宪章条款、IMT 判决、NMT 案件、带强制性的多数意见与个别意见区分的 IMTFE 判决、纽伦堡原则）；变音符号表（22 名 IMT 被告、28 名 IMTFE 被告）；IMT 的四项指控；IMTFE 的 A/B/C 级；犯罪组织认定
- `references/verification-workflow.md` —— 针对 IMT/NMT 和 IMTFE 引用分别设置的备用检索阶梯；采集字段；核验级别匹配；**四大经典陷阱**的明确列举；翻译纪律（纽伦堡的英/法/德/俄文；东京的英/日文）
- `references/foundational-texts.md`（上文已述）
- `references/jurisprudence-map.md` —— 十四个按主题划分的部分，涵盖 IMT、NMT 和 IMTFE 的学理：法庭合法性（*nullum crimen* 法不溯及既往）、危害和平罪、战争罪、危害人类罪（含 IMT/管制委员会第 10 号法律/IMTFE 在武装冲突关联要件上的分歧）、犯罪组织学说、个人刑事责任、不豁免（含通向 2025 年 7 月 25 日 *Mayaleh* / *Al-Assad* 案的脉络）、上级命令、共谋（含 IMT/IMTFE 学理分歧）、指挥官责任、裕仁天皇不起诉、Pal 反对意见、纽伦堡原则以及十二个 NMT 案件
- `references/defendants-and-judges.md` —— 专门参考：22 名 IMT 被告（含变音符号、职务、判决）；IMT 四项指控；犯罪组织认定；28 名 IMTFE 被告（含职务和判决）；裕仁天皇不起诉；A/B/C 级；11 名 IMTFE 法官及其个别意见；IMT 和 IMTFE 首席检察官
- `examples/example-verification.md` —— 端到端核验一处纽伦堡引用（IMT 判决中著名的"人，而非抽象实体"段落）和一处东京引用（Pal 关于侵略战争的反对意见）
- `examples/example-audit.md` —— 三个审计示例，分别说明陷阱 1（经 Einsatzgruppen 案混淆 IMT/NMT）、陷阱 2（混淆纽伦堡/东京宪章条款编号）和陷阱 4（将 Pal 反对意见归于"法庭"）

### v1.0.0 的 skill 范围
- 涵盖**IMT**（纽伦堡四国国际军事法庭，1945-46）、**十二场后续 NMT**审判（纽伦堡美国军事法庭，依据管制委员会第 10 号法律，1946-49）以及**IMTFE**（远东国际军事法庭，东京，1946-48），整合为单一 skill
- 采用与本仓库 `icc`、`eccc` 和 `icty-ictr-irmct` skill 相同的先核验后回答方法论，并针对纽伦堡 + 东京语料库及其多个权威档案进行了调整
- 将战后法庭定位为学理母体——《罗马规约》、ICTY/ICTR 规约、《ECCC 法》以及危害人类罪、不豁免、上级命令和个人责任的现代表述均源于此
- 精确区分 IMT 与 IMTFE，以其在后殖民法律学术中应有的严肃态度对待 Pal 反对意见和裕仁天皇不起诉问题，并为 IMTFE 提供明确的 A/B/C 级术语指引

### 已知限制
- 其他同期审判（以色列的艾希曼审判；法兰克福奥斯维辛审判；德国的 Demjanjuk 审判；横滨、马尼拉、新加坡、哈巴罗夫斯克及其他亚太地点的 B/C 级审判；殖民地对日本 B/C 级战犯的审判）**不在**本 skill 覆盖范围内，需要另行分析
- 蓝皮书系列、绿皮书系列和 Pritchard-Zaide 卷册中的具体页码定位留待运行时核验——不同版本和译本之间页码不同（蓝皮书系列有英/法/德/俄文；Pritchard-Zaide 为英文）
- 22 名 IMT 被告和 28 名 IMTFE 被告表格记录一审结果；此后的赦免、减刑及数十年间幸存者的结局不在此详述
- Pal 反对意见原稿打字稿超过 1,000 页；Pritchard-Zaide 压缩版在第 21 卷。具体章节页码应针对用户持有的版本核验
- 上海交通大学出版社的东京审判可全文检索数据库是第一层资源，但仅限订阅——无订阅的用户应依赖 UVA、ICC 法律工具、JACAR 和 Pritchard-Zaide
