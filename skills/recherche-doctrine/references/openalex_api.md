# OpenAlex API——完整参考

## 概览

OpenAlex 是一个开放、免费的文献数据库，索引超过 2.5 亿项科学著作。它是 Microsoft Academic Graph 的继任者，由 OurResearch 维护。因其国际覆盖范围和开放的引文数据，对比较法研究尤为有用。

**基础 URL**：https://api.openalex.org

## 对比较法研究的优势

- **全球覆盖**：2.5 亿+ 著作，涵盖所有语言
- **开放数据**：无需 API 密钥，元数据无付费墙
- **开放引文**：完整免费的引文图谱
- **富集概念**：按主题/领域自动分类
- **归属数据**：识别作者的机构和所在国家
- **开放获取访问**：可获取时直接链接至 OA 版本

## 主要端点

### 1. 著作检索（Works）

```
GET https://api.openalex.org/works?search=TERMES
```

**关键参数：**
- `search`：全文检索（标题、摘要、全文）
- `filter`：可组合的过滤器（见"过滤器"一节）
- `sort`：结果排序
- `per_page`：结果数量（默认：25，最大：200）
- `page`：页码
- `select`：返回字段（优化）
- `mailto`：用于"礼貌池"访问的邮箱（推荐，速率限制更高）

**完整示例：**
```bash
curl "https://api.openalex.org/works?search=employment%20law%20comparative&filter=topics.domain.id:https://openalex.org/domains/2,publication_year:2020-2025,type:article&sort=relevance_score:desc&per_page=20&mailto=votre@email.fr"
```

### 2. 作者检索

```
GET https://api.openalex.org/authors?search=NOM
```

用于查找研究者的完整档案及其全部出版物。

```bash
curl "https://api.openalex.org/authors?search=dupont%20droit%20travail&per_page=5&mailto=votre@email.fr"
```

### 3. 来源检索（期刊）

```
GET https://api.openalex.org/sources?search=NOM_REVUE
```

```bash
curl "https://api.openalex.org/sources?search=revue%20droit%20travail&per_page=5&mailto=votre@email.fr"
```

### 4. 概念/主题检索

```
GET https://api.openalex.org/topics?search=TERME
```

```bash
curl "https://api.openalex.org/topics?search=labor%20law&per_page=10&mailto=votre@email.fr"
```

## 法律研究过滤器

### 按领域（Topics）

OpenAlex 使用层级主题系统：Domain > Field > Subfield > Topic（领域 > 学科 > 子学科 > 主题）。

```
# "Social Sciences" 领域（包含法律）
filter=topics.domain.id:https://openalex.org/domains/2

# 专门针对 "Law" 子学科
filter=topics.subfield.id:https://openalex.org/subfields/3308
```

**与法律相关的领域和子学科：**
- `domains/2`：Social Sciences
- `subfields/3308`：Law
- `subfields/3312`：Sociology and Political Science
- `subfields/3301`：Social Sciences (general)

### 按概念（旧系统，仍可用）

```
# "Law" 概念（ID: C138885662）
filter=concepts.id:C138885662

# "Labour law" 概念（ID: C107457646）  
filter=concepts.id:C107457646

# "Employment" 概念（ID: C162324750）
filter=concepts.id:C162324750

# "Comparative law" 概念（ID: C2776548165）
filter=concepts.id:C2776548165
```

### 按日期

```
filter=publication_year:2024
filter=publication_year:2020-2025
filter=from_publication_date:2023-01-01
```

### 按文献类型

```
filter=type:article
filter=type:book
filter=type:book-chapter
filter=type:dissertation
filter=type:review
```

### 按语言

```
filter=language:fr        # 法语
filter=language:en        # 英语
filter=language:de        # 德语
```

### 按开放获取

```
filter=is_oa:true                    # 仅 OA
filter=open_access.oa_status:gold    # Gold OA
filter=open_access.oa_status:green   # Green OA
```

### 按作者国家

```
filter=authorships.countries:FR      # 归属法国的作者
filter=authorships.countries:GB      # 归属英国的作者
filter=authorships.countries:US      # 归属美国的作者
```

### 过滤器组合

过滤器用逗号组合（逻辑 AND）：

```bash
# 法律文章、法国作者、2020 年以来、开放获取
curl "https://api.openalex.org/works?search=labor%20law&filter=concepts.id:C138885662,authorships.countries:FR,publication_year:2020-2025,is_oa:true&sort=cited_by_count:desc&per_page=20"
```

## 结果排序

```
sort=relevance_score:desc       # 相关度（与 search 一起使用时的默认）
sort=cited_by_count:desc        # 被引最多
sort=publication_date:desc      # 最新
sort=publication_date:asc       # 最早
```

## JSON 响应结构（Works）

```json
{
  "meta": {
    "count": 1234,
    "per_page": 20,
    "page": 1
  },
  "results": [
    {
      "id": "https://openalex.org/W1234567890",
      "doi": "https://doi.org/10.1234/example",
      "title": "Comparative Employment Law in France and the UK",
      "display_name": "Comparative Employment Law in France and the UK",
      "publication_year": 2023,
      "publication_date": "2023-06-15",
      "type": "article",
      "language": "en",
      "open_access": {
        "is_oa": true,
        "oa_status": "green",
        "oa_url": "https://hal.archives-ouvertes.fr/hal-01234567/document"
      },
      "authorships": [
        {
          "author": {
            "id": "https://openalex.org/A1234567",
            "display_name": "Jean Dupont",
            "orcid": "https://orcid.org/0000-0001-2345-6789"
          },
          "institutions": [
            {
              "id": "https://openalex.org/I12345",
              "display_name": "Université de Rouen Normandie",
              "country_code": "FR"
            }
          ]
        }
      ],
      "primary_location": {
        "source": {
          "id": "https://openalex.org/S1234567",
          "display_name": "Revue de droit du travail",
          "issn_l": "1234-5678",
          "type": "journal"
        }
      },
      "cited_by_count": 45,
      "abstract_inverted_index": { ... },
      "concepts": [
        {
          "id": "https://openalex.org/C138885662",
          "display_name": "Law",
          "score": 0.95
        }
      ],
      "topics": [
        {
          "id": "https://openalex.org/T12345",
          "display_name": "Employment Protection and Labor Markets",
          "subfield": { "display_name": "Law" },
          "field": { "display_name": "Social Sciences" },
          "domain": { "display_name": "Social Sciences" }
        }
      ]
    }
  ]
}
```

### 关于摘要的说明

OpenAlex 以 `abstract_inverted_index`（倒排索引）形式存储摘要。重建文本：

```python
# 倒排索引是一个字典：{词: [位置]}
# 按位置排序以重建文本
abstract_index = result.get("abstract_inverted_index", {})
if abstract_index:
    words = sorted(
        [(pos, word) for word, positions in abstract_index.items() for pos in positions],
        key=lambda x: x[0]
    )
    abstract_text = " ".join(word for _, word in words)
```

## 字段选择（优化）

为减小响应大小，使用 `select`：

```
select=id,doi,title,publication_year,authorships,primary_location,cited_by_count,open_access,language
```

## 分页

```bash
# 第 1 页
curl "https://api.openalex.org/works?search=...&per_page=50&page=1"

# 第 2 页
curl "https://api.openalex.org/works?search=...&per_page=50&page=2"
```

对大型结果集（>10,000 条结果），使用游标：

```bash
curl "https://api.openalex.org/works?filter=...&per_page=200&cursor=*"
# 然后使用 meta.next_cursor 的值获取下一页
```

## 速率限制

- **无邮箱**：约 10 请求/秒（共享池）
- **带 mailto**：约 100 请求/秒（礼貌池，推荐）
- **带 API 密钥**：更高限制（高级版，付费）

始终添加 `&mailto=votre@email.fr` 以获得更高吞吐量。

## 法律研究实用示例

### 1. 比较劳动法近期文献

```bash
curl "https://api.openalex.org/works?search=comparative%20labor%20law&filter=concepts.id:C138885662,publication_year:2020-2025&sort=cited_by_count:desc&per_page=20&mailto=user@example.fr"
```

### 2. 关于解雇的法国文章（法国作者）

```bash
curl "https://api.openalex.org/works?search=licenciement%20droit%20travail&filter=authorships.countries:FR,type:article&sort=publication_date:desc&per_page=20&mailto=user@example.fr"
```

### 3. 关于职场霸凌的论文

```bash
curl "https://api.openalex.org/works?search=harcelement%20moral%20workplace%20bullying&filter=type:dissertation&sort=publication_date:desc&per_page=15&mailto=user@example.fr"
```

### 4. 某机构的出版物

```bash
# 先查找机构 ID
curl "https://api.openalex.org/institutions?search=universite%20rouen&per_page=3"

# 然后检索其法律出版物
curl "https://api.openalex.org/works?filter=authorships.institutions.id:https://openalex.org/I[ID],concepts.id:C138885662&sort=publication_date:desc&per_page=20"
```

### 5. 关于 unfair dismissal 的被引最多文章

```bash
curl "https://api.openalex.org/works?search=%22unfair%20dismissal%22&filter=concepts.id:C138885662&sort=cited_by_count:desc&per_page=10&mailto=user@example.fr"
```

## 限制

- **摘要**：倒排索引格式（需要重建）
- **卷/期/页码**：OpenAlex 在标准响应中**不**返回这些字段。要获取卷、期和页码，须通过 CrossRef 解析 DOI。**绝不虚构**这些数据。
- **法语文献覆盖**：良好，但不如 ISIDORE 对法国文献全面
- **分类**：自动（可能遗漏部分被分类到别处的法律文章）
- **全文**：可获取时提供 OA 链接，否则仅元数据

## 资源

- **官方文档**：https://docs.openalex.org
- **API 演示环境**：https://api.openalex.org（可在浏览器中导航）
- **源代码**：https://github.com/ourresearch/openalex-api-tutorials
