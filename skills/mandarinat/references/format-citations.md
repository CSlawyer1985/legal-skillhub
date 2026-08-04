# 法律引用规范

规范性参考：SNE RefLex 2022 起草指南
https://reflex.sne.fr/sites/default/files/guide/Guide-de-redaction-SNE-RefLex-2022-03-18.pdf

## 任何引用均须附 Légifrance 链接

在交付物中引用的任何法国判例或规范性引用，都必须附有指向 Légifrance 官方来源的超链接。该规则是基础性的（见 `references/principes-cardinaux.md`）；此处就其形式维度予以重申。

按引用类型预期的 Légifrance URL 模式：

| 引用类型 | URL 模式 | 示例 |
|---|---|---|
| 司法判例（最高法院、上诉法院、司法法院） | `https://www.legifrance.gouv.fr/juri/id/JURITEXT…` | `https://www.legifrance.gouv.fr/juri/id/JURITEXT000007043704`（Cass. ass. plén., 25 févr. 2000, n° 97-17.378, *Costedoat*） |
| 行政判例（国政院、行政上诉法院、行政法院） | `https://www.legifrance.gouv.fr/ceta/id/CETATEXT…` | `https://www.legifrance.gouv.fr/ceta/id/CETATEXT000018259414`（CE, ass., 8 févr. 2007, n° 287110, *Gardedieu*） |
| 宪法委员会决定 | `https://www.legifrance.gouv.fr/jorf/id/JORFTEXT…` 或委员会网站专用页面 | （URL 从检索工具的回答中提取） |
| CNIL 决定 | `https://www.legifrance.gouv.fr/cnil/id/CNILTEXT…` | （URL 从 `OpenLegi:rechercher_decisions_cnil` 的回答中提取） |
| 法典条文 | `https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI…` | `https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006437058`（art. 1242 C. civ.） |
| 法律与合并文本条文（LODA） | `https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI…` 或 `…/loda/id/LEGITEXT…` | （URL 从 `OpenLegi:rechercher_dans_texte_legal` 的回答中提取） |
| 发布于《官方公报》的文本 | `https://www.legifrance.gouv.fr/jorf/id/JORFTEXT…` | `https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000051782996`（2025 年 6 月 23 日第 2025-568 号法律） |
| 《官方公报》条文 | `https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI…` | `https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000051783004`（第 2025-568 号法律第 3 条） |
| 集体协议（KALI） | `https://www.legifrance.gouv.fr/conv_coll/id/KALITEXT…` | （URL 从 `OpenLegi:rechercher_conventions_collectives` 的回答中提取） |

对于非法国来源，适用相应的官方 URL：

| 引用类型 | URL 模式 |
|---|---|
| 欧洲人权法院（HUDOC） | `https://hudoc.echr.coe.int/fre?i=…` 或 `…/eng?i=…` |
| 欧盟法院（Curia） | `https://curia.europa.eu/juris/document/document.jsf?docid=…` |
| 欧盟文本（EUR-Lex） | `https://eur-lex.europa.eu/eli/…` 或 `…/legal-content/…` |

**链接来源** —— 链接**从检索工具**（OpenLegi、LegalDataHunter 等）针对当前会话中该引用的回答中**提取**。绝不由记忆或类推重建。任何重建均被禁止（见 `references/principes-cardinaux.md》，“禁止事项”一节）。

**核验** —— 在 COWORK 和 CHAT_CU 模式下，交付前对全部 URL 运行 `scripts/verify_links.py`（见 `references/checklist-pre-livraison.md`）。

## 判例

### 最高法院
```
Cass. [分庭], [日] [缩写月] [年], n° [XX-XX.XXX]
```
- 分庭：civ. 1re、civ. 2e、civ. 3e、com.、soc.、crim.
- 庄严合议：Ass. plén.、Ch. mixte
- 缩写月：janv.、févr.、mars、avr.、mai、juin、juill.、août、sept.、oct.、nov.、déc.
- 预期 Légifrance 链接：`JURITEXT` 模式（见上表）。
- 示例：
  - `Cass. civ. 1re, 12 juill. 2023, n° 21-12.345`
  - `Cass. Ass. plén., 9 mai 1984, n° 79-16.612`

### 国政院
```
CE, [组成], [日] [缩写月] [年], n° [XXXXXX]
```
- 组成：Ass.、Sect.、ss-sect.
- 预期 Légifrance 链接：`CETATEXT` 模式。
- 示例：`CE, Ass., 8 févr. 2007, n° 287110, Gardedieu`

### 宪法委员会
```
Cons. const., [日] [缩写月] [年], n° [XXXX-XXX] [QPC/DC/LP/etc.]
```
- 预期链接：Légifrance 页面（`JORFTEXT`）或宪法委员会网站专用页面。
- 示例：`Cons. const., 16 janv. 1982, n° 81-132 DC, Nationalisations`

### 上诉法院
```
CA [城市], [分庭], [日] [缩写月] [年], n° RG [XX/XXXXX]
```
- 预期 Légifrance 链接：`JURITEXT` 模式（决定已公布时）。
- 示例：`CA Paris, pôle 2, ch. 3, 15 mars 2024, n° RG 22/04567`

### 司法法院
```
TJ [城市], [日] [缩写月] [年], n° RG [XX/XXXXX]
```

### 欧洲人权法院
```
CEDH, [日] [缩写月] [年], [名称 c/ 国家], n° [XXXXX/XX]
```
- 预期链接：HUDOC URL。
- 示例：`CEDH, 7 juill. 1989, Soering c/ Royaume-Uni, n° 14038/88`

### 欧盟法院
```
CJUE, [日] [缩写月] [年], [名称], aff. [C-XXX/XX]
```
- 预期链接：Curia URL。

## 规范性文本

### 法典条文
```
Art. [编号] [缩写法典]
Art. L. [编号] [缩写法典]
Art. R. [编号] [缩写法典]
```
- 常用法典：C. civ.、C. pén.、C. com.、C. trav.、C. consom.、CPC、CPP、CJA、CGCT、CSP、CSS。
- 预期 Légifrance 链接：`LEGIARTI` 模式（codes/article_lc）。
- **文本最近被修改时注明适用版本**：`Art. [编号] [缩写法典], dans sa rédaction issue de [法律/条例/法令] du [日期]`。
- 示例：
  - `Art. 1240 C. civ.`
  - `Art. L. 1234-5 C. trav.`
  - `Art. R. 421-1 CJA`
  - `Art. 1242 al. 4 C. civ., dans sa rédaction issue de la loi n° 2025-568 du 23 juin 2025`

### 法律
```
Loi n° [年-NNN] du [日] [月] [年] [短标题]
```
- 预期链接：`JORFTEXT` 模式（原始文本）或 `LEGITEXT`（合并版本）。
- 示例：`Loi n° 2016-1547 du 18 nov. 2016 de modernisation de la justice du XXIe siècle`
- 近期示例：`Loi n° 2025-568 du 23 juin 2025 visant à renforcer l'autorité de la justice à l'égard des mineurs délinquants et de leurs parents`（`https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000051782996`）

### 条例
```
Ord. n° [年-NNN] du [日] [月] [年]
```
- 示例：`Ord. n° 2016-131 du 10 févr. 2016 portant réforme du droit des contrats`

### 法令
```
Décr. n° [年-NNN] du [日] [月] [年]
```

## 学说

> **强制性可核验标识符。** 任何学说引用都必须通过检索（`scripts/doctrine_search.py`、`scripts/hal_search.py`、对可识别来源的 web_search）找到，并带有**可核验标识符**：DOI（形式 `https://doi.org/10.xxxx/...`）、HAL 标识符/URL（`https://hal.science/hal-XXXXXXXX`），或公认数据库（Cairn、Persée、OpenEdition、Dalloz）的 URL。有 DOI 时，在引用末尾注明；否则注明数据库 URL。无可核验标识符的学说引用标记为“（未核验引用）”或删除。书目格式整理可由 `scripts/format_citation.py`（类型化 JSON 输入）辅助，并由 `scripts/generate_bibliography.py` 汇编。

### 期刊文章
```
[姓氏] [名字首字母]., « [文章准确标题] », [缩写期刊] [年], p. [X]
```
- 示例：`BRUN Ph., « La responsabilité du fait des choses », RTD civ. 2023, p. 45`
- 常用期刊：RTD civ.、RTD com.、D.、JCP G、JCP E、AJDA、RFDA、RDC、Gaz. Pal.、Dr. soc.、RJS、RLDC、RCA

### 著作
```
[姓氏] [名字首字母]., [著作标题], [出版社], [年], [第 2 版起注明版本]
```
- 示例：`TERRÉ F., SIMLER Ph. et LEQUETTE Y., Droit civil. Les obligations, Dalloz, 2024, 13e éd.`

### 博士论文
```
[姓氏] [名字首字母]., [标题], thèse [大学], [年]
```

### 集体著作中的篇章
```
[姓氏] [名字首字母]., « [篇章标题] », in [著作标题], [主编], [出版社], [年], p. [X]
```

### 判例评注与观察
```
[姓氏] [名字首字母]., note sous [法院], [日期], [期刊] [年], p. [X]
```

## 报告与机构文件
```
[作者/机构], [标题], [日期或年份]
```
- 示例：`Cour des comptes, Rapport annuel 2024, févr. 2024`

## 尾注中链接的整合

每条尾注引用都必须依上表附上指向官方来源的超链接。预期形式：

> Cass. ass. plén., 25 févr. 2000, n° 97-17.378, *Costedoat*, *https://www.legifrance.gouv.fr/juri/id/JURITEXT000007043704*。

> Art. 1242 al. 4 C. civ., dans sa rédaction issue de la loi n° 2025-568 du 23 juin 2025, *https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006437058*。

缺少链接使注释不合规：此时引用依 `references/checklist-pre-livraison.md` 的程序处理（删除、非人称改写或注明“待核验”）。

## RefLex 指南允许的变体

RefLex 指南保留一定的自由度。主要变体：

| 要素 | 变体 A | 变体 B |
|---|---|---|
| 作者名字 | `BRUN Ph.` | `Brun (Ph.)` |
| 多位作者 | `TERRÉ F., SIMLER Ph. et LEQUETTE Y.` | `F. Terré, Ph. Simler et Y. Lequette` |
| 期刊名称 | 缩写（`RTD civ.`） | 全称（`Revue trimestrielle de droit civil`） |
| 标题引号 | « … » | "…" |

关键在于同一文档内的**一致性**。变体选择属于作者。对任务 10（统一化），检测多数使用的变体，然后在系统性应用前请求确认。

## 确定度代码（用于任务 9 和 10）

| 代码 | 含义 |
|---|---|
| 🟢 | 所有识别要素齐备（日期+编号+法院/系列）+有效的 Légifrance 链接 |
| 🟡 | 一个要素不确定或待确认，或缺少 Légifrance 链接 |
| 🟠 | 两个要素缺失或近似 |
| 🔴 | 引用极不完整、规范化属推测、Légifrance 链接缺失或无法核验 |
