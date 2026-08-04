# CrossRef API——完整参考

## 概述

CrossRef 是科学出版物 DOI（数字对象标识符）的官方登记处。它包含超过 1.5 亿条出版物的元数据，由出版商直接提供。是书目核实和编辑质量元数据的参考来源。

**基本 URL**：https://api.crossref.org

## 对法律研究的优势

- **出版商数据**：元数据由出版商直接提供（可靠性高）
- **DOI 解析**：通过 DOI 直接访问文章的元数据
- **法律覆盖**：大量法律期刊被收录
- **免费**：开放 API，无需认证
- **引文**：引文计数（通过 OpenCitations）

## 主要端点

### 1. 著作检索

```
GET https://api.crossref.org/works?query=TERMES
```

**参数：**
- `query`：一般检索
- `query.title`：仅标题检索
- `query.author`：按作者检索
- `query.bibliographic`：组合书目检索
- `query.container-title`：按期刊名称检索
- `filter`：过滤器（见过滤器一节）
- `sort`：排序（`relevance`、`published`、`is-referenced-by-count`）
- `order`：顺序（`asc`、`desc`）
- `rows`：结果数（默认：20，最大：1000）
- `offset`：分页偏移
- `select`：要返回的字段

### 2. DOI 解析

```
GET https://api.crossref.org/works/DOI
```

```bash
# 示例：解析 DOI
curl "https://api.crossref.org/works/10.3917/rdli.095.0045"
```

### 3. 期刊检索

```
GET https://api.crossref.org/journals?query=NOM_REVUE
```

### 4. 期刊的著作

```
GET https://api.crossref.org/journals/ISSN/works?query=TERMES
```

## 过滤器

### 按日期

```
filter=from-pub-date:2020,until-pub-date:2025
filter=from-pub-date:2023-01-01
```

### 按类型

```
filter=type:journal-article
filter=type:book-chapter
filter=type:dissertation
filter=type:book
filter=type:monograph
filter=type:proceedings-article
```

### 按可用性

```
filter=has-abstract:true          # 有摘要
filter=has-full-text:true         # 有全文
filter=has-references:true        # 有参考文献
```

### 按许可／开放获取

```
filter=license.url:http://creativecommons.org/licenses/by/4.0/
```

### 按 ISSN（特定期刊）

```
filter=issn:1234-5678
```

### 按出版商

```
filter=publisher-name:Dalloz
filter=publisher-name:LGDJ
filter=publisher-name:Cairn
```

### 过滤器组合

过滤器用逗号组合：

```bash
curl "https://api.crossref.org/works?query=droit+travail+licenciement&filter=from-pub-date:2020,type:journal-article,has-abstract:true&sort=relevance&rows=20"
```

## JSON 响应结构

```json
{
  "status": "ok",
  "message-type": "work-list",
  "message": {
    "total-results": 456,
    "items": [
      {
        "DOI": "10.3917/rdli.095.0045",
        "type": "journal-article",
        "title": ["Le licenciement pour motif personnel"],
        "author": [
          {
            "given": "Jean",
            "family": "Dupont",
            "ORCID": "https://orcid.org/0000-0001-2345-6789",
            "affiliation": [{"name": "Université de Rouen"}]
          }
        ],
        "container-title": ["Revue de droit du travail"],
        "published": {
          "date-parts": [[2023, 6]]
        },
        "volume": "95",
        "page": "45-62",
        "abstract": "<jats:p>Résumé de l'article...</jats:p>",
        "URL": "http://dx.doi.org/10.3917/rdli.095.0045",
        "ISSN": ["1234-5678"],
        "is-referenced-by-count": 12,
        "references-count": 35,
        "publisher": "Dalloz",
        "subject": ["Law"],
        "language": "fr"
      }
    ]
  }
}
```

### 关于摘要的说明

CrossRef 的摘要通常是 JATS XML 格式。通过删除标签提取文本：

```
<jats:p>Texte du résumé...</jats:p>  →  Texte du résumé...
```

## 实用示例

### 1. 劳动法一般检索

```bash
curl "https://api.crossref.org/works?query=droit+travail+licenciement&filter=type:journal-article,from-pub-date:2020&sort=relevance&rows=15"
```

### 2. 按作者检索

```bash
curl "https://api.crossref.org/works?query.author=Dupont&query.bibliographic=droit+travail&filter=from-pub-date:2015&rows=20"
```

### 3. 特定期刊的出版物

```bash
# 按 ISSN
curl "https://api.crossref.org/journals/1234-5678/works?query=licenciement&sort=published&order=desc&rows=10"
```

### 4. 书目引用核实

```bash
# 标题＋作者＋年份组合检索
curl "https://api.crossref.org/works?query.bibliographic=Dupont+licenciement+abusif+2023&rows=5"
```

### 5. DOI 解析

```bash
curl "https://api.crossref.org/works/10.3917/rdli.095.0045"
```

## “礼貌池”（推荐）

为获得更好的吞吐量，在请求中包含邮箱：

```bash
curl "https://api.crossref.org/works?query=...&mailto=votre@email.fr"
```

或通过 User-Agent 头：
```bash
curl -H "User-Agent: MonApp/1.0 (mailto:votre@email.fr)" "https://api.crossref.org/works?query=..."
```

## 速率限制

- **无邮箱**：约 50 请求／秒（共享池，可能受限）
- **带 mailto**：更高的速率限制且优先
- **带 Crossref Plus 令牌**：更快（付费）

## 字段选择

为减小响应大小：

```
select=DOI,title,author,container-title,published,volume,page,abstract,URL,is-referenced-by-count,type,language
```

## CrossRef 上的法国法律期刊（示例）

许多法国法律期刊有 DOI 并被收录：
- Dalloz 期刊（经 CAIRN）
- LGDJ 期刊
- Lextenso 期刊
- 带 DOI 的大学期刊

查找特定期刊：
```bash
curl "https://api.crossref.org/journals?query=revue+droit+travail"
```

## 限制

- **覆盖**：取决于出版商的 DOI 分配
- **法国期刊**：覆盖不一（大型出版社更好）
- **全文**：无全文，仅元数据
- **摘要**：并非总是可用，存在时多为 JATS XML 格式
- **分类**：`subject` 字段往往含糊

## 资源

- **文档**：https://api.crossref.org/swagger-ui/index.html
- **指南**：https://www.crossref.org/documentation/retrieve-metadata/rest-api/
