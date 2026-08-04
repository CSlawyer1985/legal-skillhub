# 可靠法律来源

## 通过 OpenLegi 直接访问官方数据库

**OpenLegi** 是一个 MCP（模型上下文协议）服务器，为 Claude 提供对官方法律数据库的直接、结构化访问。**凡经 OpenLegi 访问的来源均视为可靠**：数据直接来自 Legifrance 数据库。

### 可用连接器
- **Legifrance**（`mcp.openlegi.fr/legifrance/mcp`）：法典、法律文本、司法和行政判例、宪法委员会决定、CNIL 决定、官方公报、集体协议

### 使用优先级
对任何涉及官方文本、判例或官方公报发布物的检索，OpenLegi 必须在 web_search **之前优先**使用。web_search 作为**补充**对于学说、分析及 OpenLegi 未覆盖的来源仍不可或缺。

---

## 通过 LegalDataHunter 访问外国法和比较法

**LegalDataHunter** 是一个 MCP 服务器，可访问覆盖90多个国家、超过600万份法律文件。它在三个命名空间提供混合检索（语义 + 关键词）：`case_law`、`legislation`、`doctrine`。

### 使用方式
- **比较检索**：`LegalDataHunter:search`，带国家、法域、日期过滤
- **外国引用解析**：`LegalDataHunter:resolve_reference`
- **来源发现**：`LegalDataHunter:discover_sources`、`LegalDataHunter:discover_countries`
- 使用指南：`references/guide-legaldatahunter.md`

### 可靠性
LegalDataHunter 的来源来自国家和国际官方数据库。按来源（官方 vs. 二手）系统性地标注可靠性等级。

---

## 黑名单——绝不查阅或引用的网站

**绝对禁止**查阅、引用或援引以下网站，因其传播虚假法律信息：

- https://www.droitjustice.fr/
- https://www.conseil-juridique-online.fr/
- https://www.fde-avocat.com/

**如这些网站出现在检索结果中**：完全忽略，绝不可向用户提及。

**如用户引用这些来源**：警告用户这些网站以传播错误法律信息著称，并建议在可靠来源上检索。

---

## 官方文本与规则优先网站

### 法国官方来源
- https://www.legifrance.gouv.fr/ ——立法和行政法规文本
- gouv.fr 域下的所有网站
- https://www.service-public.gouv.fr/ ——行政信息
- https://www.courdecassation.fr/ ——最高法院（主站和 Judilibre）
- https://www.courdecassation.fr/acces-rapide-judilibre ——Judilibre 数据库
- https://www.conseil-etat.fr/ ——最高行政法院（判例和文档）
- https://opendata.justice-administrative.fr/ ——行政司法开放数据
- https://opendata.justice-administrative.fr/recherche ——决定检索
- https://www.conseil-constitutionnel.fr/ ——宪法委员会（决定和评注）
- https://www.assemblee-nationale.fr/ ——国民议会（议会工作、法律草案和提案）
- https://www.senat.fr/ ——参议院（议会工作、报告）

### 欧洲和国际来源
- https://www.echr.coe.int/ ——欧洲人权法院
- https://hudoc.echr.coe.int ——欧洲人权法院 HUDOC 数据库
- https://curia.europa.eu/jcms/jcms/j_6/fr/ ——欧盟法院
- https://european-union.europa.eu/index_fr ——欧盟
- https://european-union.europa.eu/institutions-law-budget/law/find-legislation_fr ——欧洲立法
- https://european-union.europa.eu/institutions-law-budget/law/find-case-law_fr ——欧洲判例
- https://basedoc.diplomatie.gouv.fr/exl-php/recherche/mae_internet___traites ——国际条约

### 独立行政机构
列于 https://www.legifrance.gouv.fr/contenu/menu/autour-de-la-loi/autorites-independantes/autorites-administratives-independantes-et-autorites-publiques-independantes-relevant-du-statut-general-defini-par-la-loi-n-2017-55-du-20-janvier 的所有独立行政机构

## 可靠学说来源

### `doctrine_search.py`——多源检索（主要工具）
脚本 `scripts/doctrine_search.py` 一次调用即查询多个开放数据库，并为每条引用返回一个**可验证标识符**（DOI、HAL 标识符、URL）：
- **HAL**（`api.archives-ouvertes.fr`）——法国开放档案库，法学领域。
- **OpenAlex**（`api.openalex.org`）——全球文献图谱，富含 DOI。
- **Isidore**（`api.isidore.science`）——法语人文社科搜索引擎（CNRS / Huma-Num）。
- **Crossref**（`api.crossref.org`）——DOI 注册机构，用于按 DOI 解析和去重。

脚本先按 DOI 去重，再按规范化标题去重，并在不阻塞的情况下提示无法连接的来源（`sources_failed`）。它是学说检索的首选工具；定向 HAL 检索（`hal_search.py`）和 web_search 作为补充。

### HAL——经 API 的结构化访问
**HAL**（Hyper Articles en Ligne）是法国国家开放档案库，由 CCSD（CNRS）管理。API 可结构化访问元数据，并在可用时访问法学出版物的全文。

- **API 入口**：`https://api.archives-ouvertes.fr/search/`
- **访问方式**：经 `scripts/doctrine_search.py`（多源）或 `scripts/hal_search.py`（定向 HAL、按案号查判例注释）
- **使用指南**：`references/guide-hal.md`
- **法学覆盖**：约227,000份文档（论文、著作、章节、学位论文、会议发言）
- **可靠性**：HAL 元数据可靠（由作者和实验室核实的存储）。格式化引用（`citationFull_s`）可直接使用。
- **局限**：覆盖非穷尽（取决于作者存储）。商业期刊往往只有题录而无全文。HAL 不替代 web_search 的学说检索。

### 网页门户
- https://shs.hal.science/ ——HAL 人文社科开放档案库
- https://droit.cairn.info/ ——Cairn 上的法律期刊
- https://www.persee.fr/ ——Persée 门户（学术期刊）
- https://journals.openedition.org/ ——人文社科期刊
- https://books.openedition.org/ ——人文社科著作

## 来源使用

法律检索时始终优先使用这些来源。访问优先顺序：
1. **OpenLegi**（直接访问官方数据库——默认可靠）
2. **`doctrine_search.py`**（多源学说检索——HAL + OpenAlex + Isidore，可验证标识符）——见 `references/guide-hal.md`
3. **定向 HAL API**（`hal_search.py`——按案号查判例注释、按作者检索）
4. **LegalDataHunter**（外国法和比较法——90多个国家）——见 `references/guide-legaldatahunter.md`
5. **上文所列官方网站**（经 web_search/web_fetch）
6. **网页学说来源**（经 web_search：Cairn、Persée、OpenEdition）

来源冲突时，遵循规范层级：
1. 现行有效的立法和行政法规文本
2. 判例（按法院权威性）
3. 学说（作者评注）
