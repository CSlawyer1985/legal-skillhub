---
name: recherche-doctrine
description: "在法国、欧洲和国际法律学术数据库中进行学术研究。当用户请求检索学说文章、学位论文、学术著作或大学法律出版物——包括比较法——时使用本技能。主要来源：ISIDORE（CNRS 社会科学聚合器，包括 Cairn.info、Persée、OpenEdition）、HAL（法国开放存档）、OpenAlex（全球开放数据库，2.5 亿+ 作品）、Semantic Scholar、CrossRef、Persée（直接 OAI）和 CORE。覆盖法语区**和**国际法律学术，内置用于比较法的双语工作流。以下请求也触发：注释书目、研究现状、法律文献综述、作者检索、引文核验、文献计量分析。"
---

# 法律学说检索——v2（法国法与比较法）

面向律师、研究者和博士生的多来源学术检索技能。专为法国学说**和**比较法（内置法语/英语双语检索）设计。

## 来源架构

### 第一层——法语区来源（优先）

| 来源 | 覆盖 | 访问 | 主要用途 |
|--------|-----------|-------|----------------|
| **ISIDORE**（CNRS） | 500 万+ 人文社科文献，聚合 HAL/Cairn/Persée/OpenEdition | 开放 API | 法语区主要检索 |
| **HAL** | 法国开放存档、全文 | 开放 API | 针对性补充、按作者/实验室检索 |
| **Persée OAI** | 回溯馆藏、历史法律期刊 | OAI-PMH | 经典学说、旧馆藏 |

### 第二层——国际来源（比较法）

| 来源 | 覆盖 | 访问 | 主要用途 |
|--------|-----------|-------|----------------|
| **OpenAlex** | 2.5 亿+ 作品、全球开放获取 | 开放 API | 国际检索、文献计量、引用 |
| **Semantic Scholar** | 2 亿+ 文章、语义 AI | API（无密钥 1 请求/秒） | 英语学说、有影响力文章 |
| **CrossRef** | 1.5 亿+ DOI、编辑元数据 | 开放 API | 引文核验、高质量元数据 |
| **CORE** | 全球最大开放获取聚合器 | API（建议使用密钥） | 开放获取补充 |

## 关键规则：书目元数据完整性

**绝不编造、猜测或推断**以下书目信息：
- 卷号 / 册号
- 期刊号 / 期号
- 页码（首页和末页）
- 精确日期（月、日）——只报告 API 返回的内容
- DOI 编号

**基本原则**：如果 API 未返回某个字段（卷、期、页），**不要**将其包含在参考文献中。一条不完整但准确的参考文献，价值远远超过一条完整但虚假的参考文献。

**编辑元数据的可靠来源**（按顺序）：
1. **CrossRef**：卷/期/页的唯一可靠来源（数据由出版商提供）
2. **DOI**：如果有 DOI，**始终**通过 CrossRef 解析以获取完整元数据
3. **HAL / ISIDORE / OpenAlex**：标题、作者、年份、期刊可靠——但通常**没有**卷/期/页

**强制核验工作流**：
- 每次 ISIDORE/HAL/OpenAlex 检索后，如果结果中有 DOI，通过 CrossRef（`https://api.crossref.org/works/DOI`）解析 DOI 以获取卷、期和页
- 如果没有 DOI 且卷/期/页缺失，明确说明：`[卷/期/页不可用——请在来源上核实]`
- 绝不从 DOI 重建页码（例如：不要从 `rdli.095.0045` 推断"第 45 页"）

## 检索工作流

### 指导原则

始终根据所请求的检索类型调整策略：

- **纯法国检索** → 先用 ISIDORE，HAL 补充
- **比较法** → 并行检索法语（ISIDORE）+ 英语（OpenAlex/Semantic Scholar）
- **作者检索** → HAL（法国作者）+ OpenAlex（国际作者）
- **书目核验** → 优先 CrossRef（出版商数据）
- **历史学说** → 回溯馆藏用 Persée OAI
- **研究现状 / 文献综述** → 所有来源，比较综合

### 第 1 步：分析请求

任何检索之前，识别：
1. **目标语言/法域**：仅法国法？比较法？国际法？
2. **时期**：近期学说（5 年）？历史？无限制？
3. **文献类型**：文章？学位论文？所有类型？
4. **所需深度**：快速结果（5-10 条）还是穷尽（50+ 条）？

### 第 2 步：法语区检索（ISIDORE + HAL）

**始终从 ISIDORE 开始**——它聚合了大部分法语区来源。

```bash
# ISIDORE 基本检索
curl "https://api.isidore.science/resource/search?q=TERMES_FR&output=json&replies=20"

# 带法律筛选
curl "https://api.isidore.science/resource/search?q=TERMES_FR&type=http://isidore.science/ontology%23article&discipline=http://purl.org/dc/terms/subject/law&output=json&replies=20&sort=date"
```

如果结果不足或需要按作者/机构检索，用 HAL 补充：

```bash
curl "https://api.archives-ouvertes.fr/search/?q=TERMES_FR&fq=domain_s:shs.droit&fl=halId_s,title_s,authFullName_s,abstract_s,publicationDateY_i,uri_s,doiId_s,journalTitle_s,volume_s,issue_s,page_s,fileMain_s&wt=json&rows=20&sort=publicationDateY_i%20desc"
```

> 完整参数文档见 `references/hal_api.md` 和 `references/isidore_api.md`。

### 第 3 步：国际检索（如果比较法或扩展）

**OpenAlex**（国际优先推荐——法律覆盖优于 Semantic Scholar）：

```bash
# 带法律筛选的检索
curl "https://api.openalex.org/works?search=TERMES_EN&filter=topics.domain.id:https://openalex.org/domains/2,publication_year:2020-2025&sort=relevance_score:desc&per_page=20"

# 按特定法律概念检索
curl "https://api.openalex.org/works?search=TERMES_EN&filter=concepts.id:C138885662&per_page=20"
```

> OpenAlex 中的 `C138885662` 概念对应"法律"。高级筛选和法律概念见 `references/openalex_api.md`。

**Semantic Scholar**（补充，主要用于引用指标）：

```bash
curl "https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=TERMES_EN&fields=paperId,title,authors,year,abstract,venue,citationCount,url,externalIds&fieldsOfStudy=Law&limit=20&year=2020-2025"
```

> 完整文档见 `references/semantic_scholar_api.md`。

### 第 4 步：通过 CrossRef 核验和充实（强制性）

**此步骤是系统性的，而非可选的。**CrossRef 是编辑元数据（卷、期、页）的唯一可靠来源。

**对于每个有 DOI 的结果**（通过 ISIDORE、HAL 或 OpenAlex 找到）：

```bash
# 解析 DOI——获取卷、期、页、精确日期
curl "https://api.crossref.org/works/10.xxxx/yyyy"
```

提取并补充：`volume`、`issue`、`page`、`published.date-parts`。

**对于无 DOI 的结果**，尝试按标题 + 作者进行 CrossRef 检索：

```bash
# 书目检索以找到 DOI 和元数据
curl "https://api.crossref.org/works?query.bibliographic=AUTEUR+TITRE_PARTIEL&rows=3"
```

**如果 CrossRef 未返回任何内容**：将卷/期/页字段在参考文献中留空并明确说明。

> 按类型、日期、出版商的筛选见 `references/crossref_api.md`。

### 第 5 步：历史学说（如相关）

**Persée OAI**——用于法律期刊的回溯馆藏：

```bash
# 可用法律馆藏列表
curl "https://oai.persee.fr/oai?verb=ListSets"

# 在特定馆藏中检索
curl "https://oai.persee.fr/oai?verb=ListRecords&metadataPrefix=oai_dc&set=revue_rfsp"
```

> 法律馆藏和导航见 `references/persee_oai.md`。

## 特殊工作流：比较法

对于比较检索，使用双语同义词表在两种语言中并行执行检索。

### 双语同义词表——常见法律术语

| Français | English |
|----------|---------|
| Contrat de travail | Employment contract |
| Licenciement | Dismissal / Termination |
| Licenciement abusif | Unfair dismissal / Wrongful termination |
| Période d'essai | Probationary period / Trial period |
| Négociation collective | Collective bargaining |
| Convention collective | Collective agreement |
| Représentant du personnel | Employee representative |
| Comité social et économique | Works council |
| Harcèlement moral | Workplace bullying / Moral harassment |
| Harcèlement sexuel | Sexual harassment |
| Discrimination | Discrimination |
| Rupture conventionnelle | Negotiated termination |
| Temps de travail | Working time |
| Salaire minimum | Minimum wage |
| Droit de grève | Right to strike |
| Transfert d'entreprise | Transfer of undertaking (TUPE) |
| Responsabilité civile | Civil liability / Tort liability |
| Responsabilité contractuelle | Contractual liability |
| Obligation de sécurité | Duty of care / Safety obligation |
| Protection des données | Data protection |
| Propriété intellectuelle | Intellectual property |
| Droit de la consommation | Consumer law |
| Droit des sociétés | Company law / Corporate law |
| Procédure civile | Civil procedure |
| Voies de recours | Remedies / Appeals |

此同义词表是指示性的。对于专业术语，将翻译调整为每个法律体系的精确法律语境。

### 比较检索策略

1. **翻译术语**，以上述同义词表为起点
2. **运行 ISIDORE**，使用法语术语 + "droit comparé" 或 "comparative"
3. **运行 OpenAlex**，使用英语术语 + Law 筛选
4. 如需引用指标，**运行 Semantic Scholar**
5. **综合**：按法域分组，识别双方的关键作者

## 输出格式

根据请求调整格式（快速结果与完整研究现状）。

### 标准格式（检索结果）

对每个结果，仅提供**API 实际返回的信息**：

```
[N]. 作者 (年份)。"完整标题"。期刊/来源，[第 X 卷，第 Y 期，第 Z-W 页——仅在可通过 CrossRef 或来源 API 获取时]。
    → 类型：文章 | 学位论文 | 著作 | 章节 | 会议报告
    → 来源：ISIDORE | HAL | OpenAlex | Semantic Scholar | CrossRef
    → 摘要：[如可用 2-3 行]
    → 访问：[直接 URL] | DOI：[如可用]
    → [引用数：N（如 OpenAlex/Semantic Scholar 提供该数据）]
    → [⚠ 元数据不完整：卷/期/页不可用——如相关]
```

**输出格式的严格规则：**
- 如果卷/期/页不是 API 返回的，**不要**包含它们。只写期刊名称和年份。
- 绝不默认写 `第 1 页` 或 `第 1 卷`——数据缺失不是 `1`。
- 如果 DOI 已通过 CrossRef 解析且完整元数据可用，包含它们。
- 在列表末尾注明完整度比率："Y 条参考文献中的 X 条拥有完整的编辑元数据（卷/页）。"

### 注释书目格式（如要求）

```
## 注释书目：[主题]

### 法国学说

[格式化的参考文献]
↳ 评注：对所提问题的相关性、学说立场、主要贡献。

### 国际 / 比较学说

[格式化的参考文献]
↳ 评注：比较相关性、所处理的法体系、方法论。

### 综合
[学说趋势分析、识别出的缺口、研究方向]
```

## 引用格式

提供适合语境的格式。有疑问时，使用法国法律期刊格式。

**绝对规则**：只填写实际拥有的字段。API 中缺失的字段在引用中也是缺失的。绝不通过推断、近似或编造来补全。

**法国法律期刊格式：**
> 姓. 名， "文章标题"， *期刊名称* 年份[, 第 X 卷][, 第 Y 期][, 第 Z 页]。
> *（方括号表示条件字段：仅当信息由 CrossRef 或其他 API 返回时才包含）*

**APA 7 格式：**
> 姓, 名. (年份). 文章标题. *期刊名称*[, *卷*(期), 页码]. https://doi.org/xxx

**芝加哥格式（脚注）：**
> 名 姓, "文章标题", *期刊名称* [卷, 期] (年份)[: 页码]。

**不完整但诚实的参考文献示例：**
> J. DUPONT， "Le licenciement pour motif personnel"， *Revue de droit du travail* 2023 [卷/期/页：请查源——DOI：10.xxxx/yyyy]

## 最佳实践

### 检索策略

1. **法语区学说从 ISIDORE 开始**（覆盖约 80% 的需求）
2. **HAL 补充**用于针对性检索（作者、机构、全文）
3. **国际用 OpenAlex**——比 Semantic Scholar 覆盖更好且数据开放
4. **Semantic Scholar 补充**——对引用指标和语义检索有用
5. **书目用 CrossRef**——可靠的出版商数据、DOI 解析
6. **历史用 Persée**——法国期刊的回溯馆藏

### 请求优化

- ISIDORE/HAL 使用**法语术语**，OpenAlex/Semantic Scholar 使用**英语**
- 引号内**精确短语**：`"contrat de travail"`、`"unfair dismissal"`
- **组合运算符**：`(licenciement OR rupture) AND jurisprudence`
- 近期学说**按日期筛选**，有影响力学说按引用筛选
- 对于比较法，始终**用两种语言**检索

### 错误处理和替代方案

如果某个 API 无响应：
1. 检查请求语法
2. 用简化术语重试
3. 切换到替代来源（ISIDORE ↔ HAL、OpenAlex ↔ Semantic Scholar）
4. 告知用户失败情况和实际查阅的来源

### 质量、归属和书目完整性

- **始终**提供访问 URL 和 DOI
- **始终**注明每个结果的来源
- **始终**通过 CrossRef 解析 DOI 以补充卷/期/页
- **绝不**编造 API 未返回的卷号、页码、期号或精确日期
- **绝不**从标识符推断元数据（例如：不要从 DOI 提取页码）
- **优先**有全文的结果
- **注明**结果仅可通过订阅获取时（Cairn、LGDJ 等）
- **核验**来源之间的重复（同一篇文章可能出现在 ISIDORE 和 OpenAlex 中）
- **明确说明**结果末尾元数据的完整度水平

## 使用示例

**示例 1：简单主题检索**
```
用户："帮我找一些关于劳动法试用期的最新文章"
→ ISIDORE："période d'essai droit travail"，文章筛选，按日期排序
→ 呈现 15-20 条最新结果
```

**示例 2：比较检索**
```
用户："我想找关于英法比较法中不当解雇的学说"
→ ISIDORE："licenciement abusif droit comparé" + "unfair dismissal"
→ OpenAlex："unfair dismissal French British comparative"
→ Semantic Scholar："wrongful termination comparative labor law France UK"
→ 按法域分组综合
```

**示例 3：作者检索**
```
用户："X 在劳动法方面有哪些出版物？"
→ HAL：authFullName_t:"Nom" + domain_s:shs.droit
→ OpenAlex：filter=authorships.author.display_name:Nom
→ 呈现完整按时间排序列表
```

**示例 4：研究现状**
```
用户："给我做一份劳动法中远程办公的研究现状"
→ ISIDORE + HAL（法语）："télétravail" + 法律筛选
→ OpenAlex（国际）："telework remote work employment law"
→ 带趋势综合的注释书目
```

**示例 5：引文核验**
```
用户："你能核验这条参考文献吗：Dupont, RDT 2023, p. 45"
→ CrossRef：query="Dupont" + 期刊名筛选 + 日期
→ HAL：作者 + 期刊检索
→ 确认或纠正该参考文献
```

## 详细参考

每个 API 的完整技术文档：
- **ISIDORE**：`references/isidore_api.md`
- **HAL**：`references/hal_api.md`
- **OpenAlex**：`references/openalex_api.md`
- **Semantic Scholar**：`references/semantic_scholar_api.md`
- **CrossRef**：`references/crossref_api.md`
- **Persée OAI**：`references/persee_oai.md`

## 已知限制

- **ISIDORE**：每月更新（可能遗漏非常新的出版物）
- **HAL**：主要覆盖法国；卷/期/页字段很少填写
- **OpenAlex**：法语区法律覆盖有限（英语区最佳）；响应中**没有**卷/期/页
- **Semantic Scholar**：无 API 密钥时严格限速（1 请求/秒）；**没有**卷/期/页
- **CrossRef**：无全文，但卷/期/页的**唯一**可靠来源
- **Persée**：仅回溯馆藏（无进行中的出版物）
- **Cairn.info**：无直接 API——仅通过 ISIDORE（元数据）或机构订阅访问
- **Dalloz、LGDJ、LexisNexis**：本技能无法访问专有数据库

## 需避免的幻觉陷阱（关键提醒）

这些错误最常见，对学术信誉损害最大：

| 错误 | 示例 | 为什么严重 |
|--------|---------|---------------------|
| 编造页码 | 无来源的"第 45 页" | 无法核验，误导读者 |
| 编造卷号 | 无来源的"第 12 卷" | 该期刊可能没有第 12 卷 |
| 从 DOI 推断 | DOI `...095.0045` → "第 45 页" | DOI 是标识符，不是页码代码 |
| 补充日期 | API 返回 2023 → 写"2023 年 6 月" | 月份未知 |
| 编造 ISSN/ISBN | 提供 API 未返回的编号 | 可能对应另一本期刊 |
| 幻觉期刊名称 | API 说"Dr. soc."却写"《社会法》" | 缩写可能对应其他内容 |

**黄金法则：对某个元数据有疑问时，不要包含它，并注明缺失的信息。**
