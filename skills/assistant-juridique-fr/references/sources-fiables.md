# 可靠的法律来源

## 通过 OpenLegi 直接访问官方数据库

**OpenLegi** 是一个 MCP（模型上下文协议）服务器，为 Claude 提供对官方法律数据库的直接、结构化访问。**通过 OpenLegi 访问的任何来源均被视为可靠**：数据直接来自 Légifrance 数据库。

### 可用连接器
- **Legifrance**（`mcp.openlegi.fr/legifrance/mcp`）：法典、法律文本、司法和行政判例、宪法委员会决定、CNIL 决定、官方公报、集体协议

### 使用优先级
对任何涉及官方文本、判例或官方公报出版物的检索，OpenLegi 必须在 web_search **之前优先**使用。web_search 作为**补充**，对法学文献、分析以及 OpenLegi 未覆盖的来源仍然不可或缺。

---

## ⚠️ 黑名单——绝不可查阅或引用的网站

**绝对禁止**查阅、引用或引用以下网站，因为它们传播虚假法律信息：

- ❌ https://www.droitjustice.fr/
- ❌ https://www.conseil-juridique-online.fr/
- ❌ https://www.fde-avocat.com/

**如果这些网站出现在搜索结果中**：完全忽略，绝不向用户提及。

**如果用户引用这些来源**：警告用户这些网站以传播错误法律信息而闻名，并提议在可靠来源上检索。

---

## 官方文本与规则优先网站

### 法国官方来源
- https://www.legifrance.gouv.fr/ - 立法和法规文本
- gouv.fr 域下的所有网站
- https://www.service-public.gouv.fr/ - 行政信息
- https://www.courdecassation.fr/ - 最高法院（主站和 Judilibre）
- https://www.courdecassation.fr/acces-rapide-judilibre - Judilibre 数据库
- https://www.conseil-etat.fr/ - 行政法院（判例与文献）
- https://opendata.justice-administrative.fr/ - 行政司法开放数据
- https://opendata.justice-administrative.fr/recherche - 决定检索
- https://www.conseil-constitutionnel.fr/ - 宪法委员会（决定与评注）
- https://www.assemblee-nationale.fr/ - 国民议会（议会工作、法律草案与提案）
- https://www.senat.fr/ - 参议院（议会工作、报告）

### 欧洲与国际来源
- https://www.echr.coe.int/ - 欧洲人权法院
- https://hudoc.echr.coe.int - 欧洲人权法院 HUDOC 数据库
- https://curia.europa.eu/jcms/jcms/j_6/fr/ - 欧盟法院
- https://european-union.europa.eu/index_fr - 欧盟
- https://european-union.europa.eu/institutions-law-budget/law/find-legislation_fr - 欧洲立法
- https://european-union.europa.eu/institutions-law-budget/law/find-case-law_fr - 欧洲判例
- https://basedoc.diplomatie.gouv.fr/exl-php/recherche/mae_internet___traites - 国际条约

### 独立行政机构
2020-01-20 第 2017-55 号法律定义的一般地位项下的所有独立行政机构（AAI）和独立公共机构（API），清单见：https://www.legifrance.gouv.fr/contenu/menu/autour-de-la-loi/autorites-independantes/autorites-administratives-independantes-et-autorites-publiques-independantes-relevant-du-statut-general-defini-par-la-loi-n-2017-55-du-20-janvier

## 可靠的法学文献来源

### `doctrine_search.py`——多来源检索（主要工具）
脚本 `scripts/doctrine_search.py` 通过一次调用查询多个开放数据库，并为每条引用返回**可验证的标识符**（DOI、HAL 标识符、URL）：
- **HAL**（`api.archives-ouvertes.fr`）——法国开放档案库，法学领域。
- **OpenAlex**（`api.openalex.org`）——全球书目图谱，富含 DOI。
- **Isidore**（`api.isidore.science`）——法语人文社科搜索引擎（CNRS / Huma-Num）。
- **Crossref**（`api.crossref.org`）——DOI 登记机构，用于解析和按 DOI 去重。

该脚本先按 DOI 去重，再按规范化标题去重，并报告无法访问的来源（`sources_failed`）而不阻塞。法学文献检索的首选工具；针对性 HAL 和 web_search 予以补充。

### HAL——通过 API 的结构化访问
**HAL**（Hyper Articles en Ligne，在线论文超集）是由 CCSD（CNRS）管理的法国国家开放档案库。该 API 提供对元数据以及（有则提供）法学出版物全文的结构化访问。

- **API 入口点**：`https://api.archives-ouvertes.fr/search/`
- **访问方式**：通过 `scripts/doctrine_search.py`（多来源）或 `scripts/hal_search.py`（针对性 HAL，按案号检索判例注释）；否则用 `bash_tool` + `curl`（无专用 MCP）
- **使用指南**：`references/guide-hal.md`
- **法学覆盖**：约 227,000 份文献（论文、著作、章节、博士论文、会议报告）
- **可靠性**：HAL 元数据可靠（由作者和实验室核实提交）。格式化引文（`citationFull_s`）可直接使用。
- **局限**：覆盖不全面（取决于作者的提交）。商业期刊通常仅有条目而无全文。HAL 不替代法学文献的 web_search。

### 门户网站
- https://shs.hal.science/ - HAL 人文社科开放档案库
- https://droit.cairn.info/ - Cairn 上的法律期刊
- https://www.persee.fr/ - Persée 门户（学术期刊）
- https://journals.openedition.org/ - 人文社科期刊
- https://books.openedition.org/ - 人文社科著作

## 来源的使用

法律检索时始终优先使用这些来源。访问优先级顺序：
1. **OpenLegi**（直接访问官方数据库——默认可靠）
2. **`doctrine_search.py`**（多来源法学文献检索——HAL + OpenAlex + Isidore，可验证标识符）——见 `references/guide-hal.md`
3. **针对性 HAL API**（`hal_search.py`——按案号检索判例注释、按作者检索）——见 `references/guide-hal.md`
4. **上述列出的官方网站**（通过 web_search/web_fetch）
5. **网络法学文献来源**（通过 web_search：Cairn、Persée、OpenEdition）

来源之间发生冲突时，遵循规范层级：
1. 现行有效的立法和法规文本
2. 判例（按法院的权威性）
3. 法学文献（作者评注）
