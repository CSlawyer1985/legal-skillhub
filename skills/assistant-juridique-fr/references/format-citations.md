# 法律引用规范

规范参考：SNE RefLex 2022 编写指南
https://reflex.sne.fr/sites/default/files/guide/Guide-de-redaction-SNE-RefLex-2022-03-18.pdf

## 任何引用都必须附 Légifrance 链接

交付物中引用的任何法国判例或规范性引用，都必须附有指向 Légifrance 官方来源的超链接。该规则是根本性的（见 `references/principes-cardinaux.md`）；此处在其形式层面重申。

按引用类型区分的预期 Légifrance URL 模式：

| 引用类型 | URL 模式 | 示例 |
|---|---|---|
| 司法判例（最高法院、上诉法院、司法法院） | `https://www.legifrance.gouv.fr/juri/id/JURITEXT…` | `https://www.legifrance.gouv.fr/juri/id/JURITEXT000007043704`（最高法院全体会议，2000 年 2 月 25 日，第 97-17.378 号，*Costedoat*） |
| 行政判例（最高行政法院、行政上诉法院、行政法庭） | `https://www.legifrance.gouv.fr/ceta/id/CETATEXT…` | `https://www.legifrance.gouv.fr/ceta/id/CETATEXT000018259414`（最高行政法院，全体会议，2007 年 2 月 8 日，第 287110 号，*Gardedieu*） |
| 宪法委员会决定 | `https://www.legifrance.gouv.fr/jorf/id/JORFTEXT…` 或委员会网站专页 |（URL 从检索工具响应中提取） |
| CNIL 决定 | `https://www.legifrance.gouv.fr/cnil/id/CNILTEXT…` |（URL 从 `OpenLegi:rechercher_decisions_cnil` 响应中提取） |
| 法典条文 | `https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI…` | `https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006437058`（《民法典》第 1242 条） |
| 法律条文和合并文本（LODA） | `https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI…` 或 `…/loda/id/LEGITEXT…` |（URL 从 `OpenLegi:rechercher_dans_texte_legal` 响应中提取） |
| 官方公报发布的文本 | `https://www.legifrance.gouv.fr/jorf/id/JORFTEXT…` | `https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000051782996`（2025 年 6 月 23 日第 2025-568 号法律） |
| 官方公报条文 | `https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI…` | `https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000051783004`（第 2025-568 号法律第 3 条） |
| 集体协议（KALI） | `https://www.legifrance.gouv.fr/conv_coll/id/KALITEXT…` |（URL 从 `OpenLegi:rechercher_conventions_collectives` 响应中提取） |

对非法国来源，适用相应的官方 URL：

| 引用类型 | URL 模式 |
|---|---|
| 欧洲人权法院（HUDOC） | `https://hudoc.echr.coe.int/fre?i=…` 或 `…/eng?i=…` |
| 欧盟法院（Curia） | `https://curia.europa.eu/juris/document/document.jsf?docid=…` |
| 欧盟文本（EUR-Lex） | `https://eur-lex.europa.eu/eli/…` 或 `…/legal-content/…` |

**链接的来源**——链接**从当前会话中为该项引用调用的检索工具（OpenLegi、LegalDataHunter 等）的响应中提取**。绝不凭记忆或类推重建。任何重建均被禁止（见 `references/principes-cardinaux.md》"禁止事项"一节）。

**核查**——在 COWORK 和 CHAT_CU 模式下，交付前对所有 URL 运行 `scripts/verify_links.py`（见 `references/checklist-pre-livraison.md`）。

## 判例

### 最高法院
```
Cass. [分庭]，[日] [缩写月] [年]，第 [XX-XX.XXX] 号
```
- 分庭：civ. 1re、civ. 2e、civ. 3e、com.、soc.、crim.
- 庄严组成：Ass. plén.（全体会议）、Ch. mixte（混合庭）
- 月份缩写：janv.、févr.、mars、avr.、mai、juin、juill.、août、sept.、oct.、nov.、déc.
- 预期 Légifrance 链接：`JURITEXT` 模式（见上表）。
- 示例：
  - `Cass. civ. 1re, 12 juill. 2023, n° 21-12.345`
  - `Cass. Ass. plén., 9 mai 1984, n° 79-16.612`

### 最高行政法院
```
CE, [组成]，[日] [缩写月] [年]，第 [XXXXXX] 号
```
- 组成：Ass.（全体会议）、Sect.（部门）、ss-sect.（分部门）
- 预期 Légifrance 链接：`CETATEXT` 模式。
- 示例：`CE, Ass., 8 févr. 2007, n° 287110, Gardedieu`

### 宪法委员会
```
Cons. const., [日] [缩写月] [年]，第 [XXXX-XXX] 号 [QPC/DC/LP/等]
```
- 预期链接：Légifrance 页面（`JORFTEXT`）或宪法委员会网站专页。
- 示例：`Cons. const., 16 janv. 1982, n° 81-132 DC, Nationalisations`

### 上诉法院
```
CA [城市]，[分庭]，[日] [缩写月] [年]，第 RG [XX/XXXXX] 号
```
- 预期 Légifrance 链接：`JURITEXT` 模式（决定已发布时）。
- 示例：`CA Paris, pôle 2, ch. 3, 15 mars 2024, n° RG 22/04567`

### 司法法院
```
TJ [城市]，[日] [缩写月] [年]，第 RG [XX/XXXXX] 号
```

### 欧洲人权法院
```
CEDH, [日] [缩写月] [年]，[姓名 c/ 国家]，第 [XXXXX/XX] 号
```
- 预期链接：HUDOC URL。
- 示例：`CEDH, 7 juill. 1989, Soering c/ Royaume-Uni, n° 14038/88`

### 欧盟法院
```
CJUE, [日] [缩写月] [年]，[名称]，aff. [C-XXX/XX]
```
- 预期链接：Curia URL。

## 规范性文本

### 法典条文
```
Art. [编号] [法典缩写]
Art. L. [编号] [法典缩写]
Art. R. [编号] [法典缩写]
```
- 常用法典：C. civ.（民法典）、C. pén.（刑法典）、C. com.（商法典）、C. trav.（劳动法典）、C. consom.（消费法典）、CPC（民事诉讼法典）、CPP（刑事诉讼法典）、CJA（行政司法法典）、CGCT（地方团体通则）、CSP（公共卫生法典）、CSS（社会保障法典）。
- 预期 Légifrance 链接：`LEGIARTI` 模式（codes/article_lc）。
- **提及适用版本**，当文本近期被修改时：`Art. [编号] [法典缩写], dans sa rédaction issue de [法律/命令/法令] du [日期]`（……，其文本来源于……）。
- 示例：
  - `Art. 1240 C. civ.`
  - `Art. L. 1234-5 C. trav.`
  - `Art. R. 421-1 CJA`
  - `Art. 1242 al. 4 C. civ., dans sa rédaction issue de la loi n° 2025-568 du 23 juin 2025`

### 法律
```
Loi n° [年份-编号] du [日] [月] [年] [短标题]
```
- 预期链接：`JORFTEXT` 模式（初始文本）或 `LEGITEXT`（合并版本）。
- 示例：`Loi n° 2016-1547 du 18 nov. 2016 de modernisation de la justice du XXIe siècle`
- 近期示例：`Loi n° 2025-568 du 23 juin 2025 visant à renforcer l'autorité de la justice à l'égard des mineurs délinquants et de leurs parents`（`https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000051782996`）

### 命令
```
Ord. n° [年份-编号] du [日] [月] [年]
```
- 示例：`Ord. n° 2016-131 du 10 févr. 2016 portant réforme du droit des contrats`

### 法令
```
Décr. n° [年份-编号] du [日] [月] [年]
```

## 学说

> **必须具有可核查标识符。** 任何学说引用都必须通过检索找到（`scripts/doctrine_search.py`、`scripts/hal_search.py`、对可识别来源的 web_search），并带有**可核查标识符**：DOI（形式 `https://doi.org/10.xxxx/...`）、HAL 标识符/URL（`https://hal.science/hal-XXXXXXXX`），或公认数据库的 URL（Cairn、Persée、OpenEdition、Dalloz）。存在 DOI 时，在引用末尾注明；否则注明数据库 URL。无可用可核查标识符的学说引用标注"（未核实的引用）"或删除。书目格式整理可由 `scripts/format_citation.py`（输入为类型化 JSON）辅助，并由 `scripts/generate_bibliography.py` 编译。

### 期刊文章
```
[姓] [名首字母]., « [文章确切标题] », [期刊缩写] [年], p. [X]
```
- 示例：`BRUN Ph., « La responsabilité du fait des choses », RTD civ. 2023, p. 45`
- 常用期刊：RTD civ.、RTD com.、D.、JCP G、JCP E、AJDA、RFDA、RDC、Gaz. Pal.、Dr. soc.、RJS、RLDC、RCA

### 著作
```
[姓] [名首字母]., [书名], [出版社], [年], [第 ≥2 版注明版本]
```
- 示例：`TERRÉ F., SIMLER Ph. et LEQUETTE Y., Droit civil. Les obligations, Dalloz, 2024, 13e éd.`

### 博士论文
```
[姓] [名首字母]., [标题], thèse [大学], [年]
```

### 集体著作的篇章
```
[姓] [名首字母]., « [篇章标题] », in [书名], [主编], [出版社], [年], p. [X]
```

### 判决评注与观察
```
[姓] [名首字母]., note sous [法院], [日期], [期刊] [年], p. [X]
```

## 报告与机构文件
```
[作者/机构], [标题], [日期或年份]
```
- 示例：`Cour des comptes, Rapport annuel 2024, févr. 2024`

## 尾注中链接的整合

每条尾注引用必须包含指向官方来源的超链接，符合上表。预期形式：

> Cass. ass. plén., 25 févr. 2000, n° 97-17.378, *Costedoat*, *https://www.legifrance.gouv.fr/juri/id/JURITEXT000007043704*。

> Art. 1242 al. 4 C. civ., dans sa rédaction issue de la loi n° 2025-568 du 23 juin 2025, *https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006437058*。

缺少链接使注释不合规：该引用随后按 `references/checklist-pre-livraison.md` 的程序处理（删除、非人称改写或注明"待核查"）。

## RefLex 指南允许的变体

RefLex 指南留有一些自由度。主要变体：

| 要素 | 变体 A | 变体 B |
|---|---|---|
| 作者名 | `BRUN Ph.` | `Brun (Ph.)` |
| 多位作者 | `TERRÉ F., SIMLER Ph. et LEQUETTE Y.` | `F. Terré, Ph. Simler et Y. Lequette` |
| 期刊标题 | 缩写（`RTD civ.`） | 全名（`Revue trimestrielle de droit civil`） |
| 标题引号 | « … » | "…" |

关键在于同一文档内的**一致性**。变体之间的选择属于作者。对任务 10（统一化），检测哪种变体占多数，然后在系统应用前请求确认。

## 确定性代码（用于任务 9 和 10）

| 代码 | 含义 |
|---|---|
| 🟢 | 所有识别要素齐全（日期 + 编号 + 法院/系列）+ Légifrance 链接有效 |
| 🟡 | 一个要素不确定或待确认，或 Légifrance 链接缺失 |
| 🟠 | 两个要素缺失或近似 |
| 🔴 | 引用非常不完整，规范化属推测性，Légifrance 链接缺失或无法核实 |
