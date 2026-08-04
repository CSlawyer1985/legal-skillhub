# Semantic Scholar API——完整参考

## 概述

Semantic Scholar 是一个由 AI 驱动的免费学术搜索引擎，覆盖所有学科 2 亿多篇科学文章。对英语国际法律学说特别有用。

**基础 URL**：https://api.semanticscholar.org/graph/v1

## 身份验证

- **无 API 密钥**：1 次请求/秒
- **有 API 密钥**：更高的限制（免费）
- **申请密钥**：https://www.semanticscholar.org/product/api

**使用 API 密钥：**
```bash
curl -H "x-api-key: YOUR_API_KEY" "https://api.semanticscholar.org/..."
```

## 主要端点

### 1. 批量检索（推荐）
```
GET /paper/search/bulk
```

性能最佳，支持排序和高级运算符。

**参数：**
- `query`：搜索词（必填）
- `fields`：要返回的字段（逗号分隔）
- `limit`：结果数量（最大：100）
- `offset`：分页偏移量
- `year`：按年份过滤（如 `2020-2024`）
- `publicationTypes`：出版物类型
- `fieldsOfStudy`：研究领域
- `sort`：排序（`citationCount:desc`、`publicationDate:desc`）

**示例：**
```bash
curl "https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=employment%20law&fields=paperId,title,authors,year,abstract,url,citationCount&limit=20&year=2020-2024"
```

### 2. 标准检索
```
GET /paper/search
```

更简单但功能较少。

### 3. 论文详情
```
GET /paper/{paper_id}
```

获取特定文章的完整详情。

## 可用字段

### 基本字段
- **paperId**：唯一标识符
- **title**：标题
- **abstract**：摘要
- **year**：出版年份
- **url**：Semantic Scholar URL
- **externalIds**：外部标识符（DOI、ArXiv 等）

### 作者
- **authors**：作者列表
  - `authorId`：作者 ID
  - `name`：全名
  - `affiliations`：隶属机构

### 指标
- **citationCount**：引用次数
- **influentialCitationCount**：有影响力的引用
- **referenceCount**：参考文献数量

### 出版物
- **venue**：出版地点（期刊、会议）
- **publicationDate**：出版日期
- **publicationTypes**：类型（期刊、会议等）

### 关系
- **citations**：引用此论文的文章
- **references**：被引用的文章
- **fieldsOfStudy**：研究领域

## 法律领域推荐字段

```
fields=paperId,title,authors,year,abstract,venue,publicationDate,citationCount,url,externalIds,fieldsOfStudy,publicationTypes
```

## 检索运算符

### 布尔运算符
- **AND**：以空格分隔的词（隐含）
  - `employment law` = employment AND law
- **OR**：使用 `|`
  - `employment | labor law`
- **NOT**：使用 `-`
  - `employment law -criminal`

### 精确短语
```
"employment contract"
```

### 分组
```
(employment | labor) law
```

### 组合示例
```
"labor law" (France | UK) -criminal
```

## 按领域过滤（fieldsOfStudy）

与法律相关的领域：
- `Law`
- `Political Science`
- `Sociology`
- `Economics`
- `Business`

**示例：**
```bash
curl "https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=contract%20law&fields=title,authors,year&fieldsOfStudy=Law&limit=20"
```

## 出版物类型

- `JournalArticle`
- `Conference`
- `Review`
- `Book`
- `BookSection`

## 实用示例

### 1. 简单检索——劳动法
```bash
curl "https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=employment%20law&fields=title,authors,year,abstract,citationCount,url&limit=20&fieldsOfStudy=Law"
```

### 2. 带引用的近期检索
```bash
curl "https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=labor%20rights&fields=title,authors,year,citationCount,url&year=2020-2024&sort=citationCount:desc&limit=20"
```

### 3. 精确短语 + 年份过滤
```bash
curl "https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=\"employment%20contract\"&fields=title,authors,year,abstract,url&year=2022-2024&limit=15"
```

### 4. 法律比较
```bash
curl "https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=comparative%20labor%20law%20(France%20|%20UK)&fields=title,authors,year,abstract,url&fieldsOfStudy=Law&limit=20"
```

### 5. 使用 API 密钥（更高的速率限制）
```bash
curl -H "x-api-key: YOUR_KEY" \
  "https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=employment%20discrimination&fields=title,authors,year,url&limit=50"
```

## JSON 响应结构

```json
{
  "data": [
    {
      "paperId": "abc123",
      "title": "Employment Law and Worker Rights",
      "authors": [
        {
          "authorId": "xyz789",
          "name": "John Smith"
        }
      ],
      "year": 2023,
      "abstract": "This paper examines...",
      "venue": "Harvard Law Review",
      "citationCount": 45,
      "url": "https://www.semanticscholar.org/paper/abc123",
      "externalIds": {
        "DOI": "10.1234/example",
        "ArXiv": "2301.12345"
      },
      "fieldsOfStudy": ["Law", "Political Science"],
      "publicationTypes": ["JournalArticle"]
    }
  ],
  "next": 20
}
```

## 分页

要浏览结果：

```bash
# 第 1 页（0-19）
curl "https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=...&offset=0&limit=20"

# 第 2 页（20-39）
curl "https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=...&offset=20&limit=20"

# 第 3 页（40-59）
curl "https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=...&offset=40&limit=20"
```

响应中的 `next` 字段指示下一页的偏移量。

## 结果排序

排序选项（`sort`）：
- `citationCount:desc`：被引最多者优先
- `citationCount:asc`：被引最少者优先
- `publicationDate:desc`：最新者优先
- `publicationDate:asc`：最早者优先

**示例：**
```bash
curl "https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=labor%20law&sort=citationCount:desc&limit=20"
```

## 访问外部标识符

`externalIds` 字段可包含：
- **DOI**：数字对象标识符
- **ArXiv**：ArXiv 标识符
- **PubMed**：PubMed ID
- **MAG**：微软学术图谱 ID
- **CorpusId**：Semantic Scholar 语料库 ID

对通过其他平台获取全文很有用。

## 速率限制

### 无 API 密钥
- 1 次请求/秒（100 次请求/分钟）
- 在所有未认证用户之间共享
- 高峰使用期可能受限

### 有 API 密钥
- 更高的限制（未公开说明）
- 请求不共享
- 更好的稳定性

### 申请提高限额
如需要更多：通过官方网站上的表单联系。

## 最佳实践

1. **始终使用批量检索**（而非标准检索）
2. **只指定必要的字段**
3. **法律检索用 `fieldsOfStudy=Law` 过滤**
4. **使用 `year` 过滤器**获取近期出版物
5. **按 `citationCount` 排序**获取有影响力的文章
6. **在 URL 中编码特殊字符**
7. **处理错误**（HTTP 429 = 速率限制）

## 局限性

- **覆盖范围**：主要是英语
- **全文**：并非始终可用（外部链接）
- **元数据**：质量因来源而异
- **速率限制**：无 API 密钥时受限
- **领域**：有时对理科比对人文社科更好

## 对比较法的优势

1. **广泛的国际覆盖**
2. **引用指标**用于评估影响力
3. **免费**且功能良好
4. **API 稳定**且文档完善
5. **智能语义检索**

## 资源

- **官方文档**：https://api.semanticscholar.org/api-docs/
- **申请 API 密钥**：https://www.semanticscholar.org/product/api
- **教程**：https://www.semanticscholar.org/product/api/tutorial
- **Postman 集合**：网站上提供

## 法律学说检索建议

1. **与 HAL/ISIDORE 结合**获取法语来源
2. **系统性地过滤 `fieldsOfStudy=Law`**
3. **使用运算符**进行精确检索
4. **按引用排序**以识别关键文章
5. **核验 DOI**以获取全文访问
6. **比较检索**：多国家使用 OR

## 错误处理

**HTTP 429**——请求过多
```
等待 1 秒后重试
如问题反复出现，获取 API 密钥
```

**HTTP 400**——无效请求
```
核验运算符语法
正确编码 URL
```

**HTTP 404**——未找到
```
核验端点
如按 ID 检索，核验 paperId
```

## 完整示例——法律比较检索

```bash
#!/bin/bash
# 比较检索：法国 vs 英国劳动法

API_KEY="your-api-key-here"

# 一般检索
curl -H "x-api-key: $API_KEY" \
  "https://api.semanticscholar.org/graph/v1/paper/search/bulk?\
query=comparative%20labor%20law%20(France%20OR%20UK%20OR%20\"United%20Kingdom\")&\
fields=paperId,title,authors,year,abstract,venue,citationCount,url,externalIds&\
fieldsOfStudy=Law&\
year=2015-2024&\
sort=citationCount:desc&\
limit=30"
```

此类检索是对 ISIDORE/HAL 的补充，可获得国际视角。
