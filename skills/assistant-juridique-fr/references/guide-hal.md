# 使用 HAL API 进行学说检索的指南

## 概述

HAL（Hyper Articles en Ligne）是法国国家开放存档库，由 CCSD（CNRS）管理。API 无需认证即可查询数据库。

- **入口**：`https://api.archives-ouvertes.fr/search/`
- **语法**：Apache Solr
- **法律领域**：`1.shs.droit`（约 227,000 份文件）
- **推荐访问方式**：`scripts/doctrine_search.py`（HAL + OpenAlex + Isidore 多源，经 Crossref 按 DOI 去重，可验证引用的标识符）——**学说检索的首选工具**。`scripts/hal_search.py` 用于针对性 HAL 查询（通过 `--pourvoi` 按上诉编号检索判例注释，通过 `--author` 按作者检索）。最后手段：`bash_tool` + `curl` 直接访问 API（模式见下）。

## 特征与局限

### 优势
- 结构化元数据（作者、期刊、年份、关键词）
- 预格式化引用（`citationFull_s`）
- 永久链接（`uri_s`）
- 可获得的开放获取全文（`fileMain_s`）
- 覆盖范围可观：法律领域约 148,000 篇文章、约 30,000 个章节、约 8,700 部著作

### 应牢记的局限
- **覆盖不穷尽**：HAL 只收录作者自行提交的出版物。商业期刊（Dalloz、LexisNexis、LGDJ）往往只有题录而无全文
- **无全文检索**：检索针对元数据（标题、摘要、关键词），而非文章内容
- **提交偏差**：不同实验室和作者的覆盖情况参差不齐
- **结论**：HAL 是 web_search 的极佳**补充**，绝不是替代品

## 标准查询模式（法律学说）

```bash
curl -s "https://api.archives-ouvertes.fr/search/?q=(title_t:(TERMES) OR abstract_t:(TERMES) OR keyword_t:(TERMES))&fq=domain_s:1.shs.droit&fq=docType_s:(ART OR OUV OR COUV OR COMM OR DOUV OR THESE OR HDR)&sort=producedDate_tdate desc&rows=10&wt=json&fl=halId_s,title_s,authFullName_s,producedDateY_i,journalTitle_s,uri_s,docType_s,citationFull_s,abstract_s,keyword_s,fileMain_s,submitType_s"
```

### 必填参数

| 参数 | 值 | 作用 |
|---|---|---|
| `q` | 多字段查询 | 检索词 |
| `fq=domain_s` | `1.shs.droit` | 限定法律领域 |
| `fq=docType_s` | `(ART OR OUV OR COUV OR COMM...)` | 学术文献类型 |
| `sort` | `producedDate_tdate desc` | 最新优先 |
| `rows` | `10`（推荐默认） | 结果数量 |
| `wt` | `json` | 响应格式 |
| `fl` | 字段列表 | 要返回的字段 |

### 特殊字符编码

带重音字符须进行 URL 编码：
- `é` → `%C3%A9`
- `è` → `%C3%A8`
- `ê` → `%C3%AA`
- `à` → `%C3%A0`
- 空格 → `%20`

Solr 特殊字符须以 `\` 转义：`+ - && || ! ( ) { } [ ] ^ " ~ * ? : \`

## 检索策略

### 1. 主题检索（主要用法）

组合标题 + 摘要 + 关键词：

```bash
q=(title_t:(responsabilité civile) OR abstract_t:(responsabilité civile) OR keyword_t:(responsabilité civile))
```

**提示**：限用 2-4 个有意义的词。Solr 引擎默认应用 AND——词太多 = 0 结果。

### 2. 按作者检索

```bash
q=authLastName_t:Bénabent
# 或用于复姓作者：
q=authLastName_t:Quézel-Ambrunaz
```

### 3. 判例注释检索（按上诉编号）

```bash
q=title_t:"21-12345"
```

之所以有效，是因为许多作者在上诉注释的标题中包含上诉编号。

### 4. 按法律期刊检索

```bash
fq=journalTitle_t:"Recueil Dalloz"
fq=journalTitle_t:"Gazette du Palais"
fq=journalTitle_t:"Revue trimestrielle de droit civil"
```

### 5. 时间检索

最近 N 年的学说：
```bash
fq=producedDateY_i:[2023 TO 2026]
```

近期学说（最近 6 个月）：
```bash
fq=producedDate_tdate:[NOW-6MONTHS/DAY TO NOW/DAY]
```

### 6. 仅检索开放获取全文

```bash
fq=submitType_s:file
```

此时 `fileMain_s` 字段将包含 PDF 的 URL。

### 7. 精确短语检索

使用引号：
```bash
q=title_t:"préjudice d'anxiété"
```

### 8. 跨学科检索（扩大领域）

对处于法律与其他学科交界处的主题（法律与经济、法律与哲学等）：
```bash
fq=domain_s:(1.shs.droit OR 0.shs)
```

结果不足时，最后手段是移除领域过滤器。

## 返回字段（fl）

### 必备字段（始终请求）

| 字段 | 类型 | 说明 |
|---|---|---|
| `halId_s` | string | 唯一 HAL 标识符 |
| `title_s` | string[] | 文件标题 |
| `authFullName_s` | string[] | 作者全名 |
| `producedDateY_i` | int | 出版年份 |
| `journalTitle_s` | string | 期刊名 |
| `uri_s` | string | HAL 永久 URL |
| `docType_s` | string | 文件类型（ART、OUV、COUV、COMM、THESE、HDR） |
| `citationFull_s` | string | **完整格式化引用**（非常有用） |

### 补充字段（如相关则请求）

| 字段 | 类型 | 说明 |
|---|---|---|
| `abstract_s` | string[] | 摘要（如可得） |
| `keyword_s` | string[] | 关键词 |
| `fileMain_s` | string | 主文件（PDF）URL |
| `submitType_s` | string | `file`（全文）或 `notice`（仅元数据） |
| `files_s` | string[] | 所有关联文件列表 |

## 文件类型（docType_s）

与法律学说相关的类型：

| 代码 | 说明 | 用途 |
|---|---|---|
| `ART` | 期刊文章 | ⭐ 主要来源 |
| `COUV` | 著作章节 | 祝贺文集、论著中的贡献 |
| `OUV` | 著作/专著 | 教材、已出版论文、论著 |
| `COMM` | 会议报告 | 研讨会论文集 |
| `DOUV` | 著作主编 | 主编的集体著作 |
| `THESE` | 博士论文 | 深入研究 |
| `HDR` | 指导研究资格 | 工作综述 |

## 推荐引用格式

以 `citationFull_s` 为基础，然后附加 HAL 链接：

```
[HAL 格式化引用]
Disponible sur HAL : [uri_s]
```

如全文可得（`submitType_s == "file"`）：
```
[HAL 格式化引用]
Disponible en accès ouvert : [fileMain_s]
```

## 0 结果时的扩大策略

1. **减少词数**：从 4 个词减为 2 个
2. **改为 OR**：`q=title_t:(terme1 OR terme2)` 而非隐含的 AND
3. **移除领域过滤器**：去掉 `fq=domain_s:1.shs.droit`（部分法律文章被归类到经济、哲学等领域）
4. **扩大类型**：增加 `OTHER`、`REPORT`、`BLOG`
5. **仅检索标题**：有时单独使用 `title_t` 比多字段组合更有效
6. **使用截断**：`responsab*` 可捕获 responsabilité/responsable/responsabilisation

## 结果过多时的细化策略

1. **按年份过滤**：`fq=producedDateY_i:[2020 TO 2026]`
2. **按类型过滤**：仅限 `ART` 期刊文章
3. **精确短语检索**：短语加引号
4. **与作者组合**：增加 `fq=authLastName_t:NOM`

## 各使用场景的典型查询

### 深入法律检索（检索任务）
宽泛主题检索 + 近期学说时间过滤：
```bash
curl -s "https://api.archives-ouvertes.fr/search/?q=(title_t:(clause%20abusive) OR abstract_t:(clause%20abusive) OR keyword_t:(clause%20abusive))&fq=domain_s:1.shs.droit&fq=docType_s:(ART OR OUV OR COUV OR COMM OR THESE)&sort=producedDate_tdate desc&rows=15&wt=json&fl=halId_s,title_s,authFullName_s,producedDateY_i,journalTitle_s,uri_s,docType_s,citationFull_s,abstract_s,fileMain_s,submitType_s"
```

### 学说跟踪（法律监测任务）
某主题最近 2 年的学说：
```bash
curl -s "https://api.archives-ouvertes.fr/search/?q=(title_t:(RGPD%20données%20personnelles) OR abstract_t:(RGPD%20données%20personnelles) OR keyword_t:(RGPD))&fq=domain_s:1.shs.droit&fq=producedDateY_i:[2024 TO 2026]&fq=docType_s:(ART OR OUV OR COUV OR COMM)&sort=producedDate_tdate desc&rows=10&wt=json&fl=halId_s,title_s,authFullName_s,producedDateY_i,journalTitle_s,uri_s,docType_s,citationFull_s,fileMain_s,submitType_s"
```

### 某法律条文的参考文献（条文分析任务）
条文编号 + 主题的组合：
```bash
curl -s "https://api.archives-ouvertes.fr/search/?q=(title_t:(1240%20code%20civil) OR title_t:(responsabilité%20civile%20extracontractuelle))&fq=domain_s:1.shs.droit&fq=docType_s:(ART OR OUV OR COUV OR THESE)&sort=producedDate_tdate desc&rows=10&wt=json&fl=halId_s,title_s,authFullName_s,producedDateY_i,journalTitle_s,uri_s,docType_s,citationFull_s,fileMain_s,submitType_s"
```

### 判例注释（按上诉编号）
```bash
curl -s "https://api.archives-ouvertes.fr/search/?q=title_t:\"21-19.900\"&fq=domain_s:1.shs.droit&rows=10&wt=json&fl=halId_s,title_s,authFullName_s,producedDateY_i,journalTitle_s,uri_s,docType_s,citationFull_s,fileMain_s,submitType_s"
```

## 错误处理

| 情形 | 动作 |
|---|---|
| curl 超时（>10 秒） | 改用仅 web_search |
| HTTP 5xx 错误 | 重试一次，然后改用 web_search |
| 0 结果 | 应用扩大策略，然后 web_search |
| 结果不相关 | 细化查询，核验检索词 |

## HAL / web_search 互补性

| 方面 | HAL | web_search |
|---|---|---|
| 结构化元数据 | ✅ 优秀 | ❌ 参差不齐 |
| 格式化引用 | ✅ `citationFull_s` | ❌ 不可用 |
| 免费全文 | ✅ 如可得 | ❌ 常有付费墙 |
| 商业期刊覆盖 | ❌ 部分（仅题录） | ✅ 更好 |
| Cairn/Persée 上的学说 | ❌ 未覆盖 | ✅ 有 |
| 法律博客文章 | ❌ 罕见 | ✅ 有 |
| 链接可靠性 | ✅ 永久链接 | ⚠️ 参差不齐 |
| 按上诉编号检索 | ✅ 在标题中 | ✅ 更广 |

**黄金法则**：始终并行使用两个来源，以获得最优的学说覆盖。
