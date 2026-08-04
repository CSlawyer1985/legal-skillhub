# HAL API——完整参考

## 概述

HAL（Hyper Articles en Ligne，在线文献库）是法国多学科开放存档。它收录法国及法语区研究的科学出版物（文章、学位论文、会议报告等）。

**基础 URL**：https://api.archives-ouvertes.fr

## 主要端点：检索

```
GET https://api.archives-ouvertes.fr/search/
```

## 检索参数

### 必填参数

- **q**：检索查询
  - Solr/Lucene 语法
  - 可以包含特定字段（例如 `title:contrat`）

### 格式参数

- **wt**：输出格式
  - `json`（推荐）
  - `xml`
  - `csv`
  
### 分页参数

- **rows**：结果数量（默认：10，最大：10000）
- **start**：起始位置（默认：0）

### 过滤参数

- **fq**：过滤器（filter query）
  - `domain_s:shs.droit` - 法律领域
  - `docType_s:ART` - 文章
  - `docType_s:THESE` - 学位论文
  - `publicationDateY_i:[2020 TO *]` - 自 2020 年起
  - `language_s:fr` - 法语

### 排序参数

- **sort**：排序字段
  - `publicationDateY_i desc` - 日期降序
  - `producedDateY_i desc` - 制作日期
  - `score desc` - 相关度

### 字段选择参数

- **fl**：要返回的字段（逗号分隔）
  - 默认：所有字段
  - 建议：指定以减小大小

## 法律领域

```
domain_s:shs.droit              # 法律（一般）
domain_s:shs.droit.civil        # 民法
domain_s:shs.droit.public       # 公法
domain_s:shs.droit.prive        # 私法
domain_s:shs.droit.inter        # 国际法
domain_s:shs.droit.euro         # 欧洲法
```

## 文档类型

```
docType_s:ART          # 文章
docType_s:THESE        # 学位论文
docType_s:HDR          # 研究指导资格（Habilitation à Diriger des Recherches）
docType_s:COMM         # 会议报告
docType_s:COUV         # 著作章节
docType_s:OUV          # 著作
docType_s:REPORT       # 报告
docType_s:UNDEFINED    # 未定义类型
```

## 主要字段

### 标识
- **halId_s**：HAL 标识符
- **docid**：文档 ID
- **uri_s**：HAL URI
- **doiId_s**：DOI

### 基本元数据
- **title_s**：标题（数组）
- **authFullName_s**：作者全名
- **authIdHal_s**：作者 HAL 标识符
- **abstract_s**：摘要（数组，多语言）

### 日期
- **publicationDateY_i**：出版年份
- **producedDateY_i**：制作年份
- **modifiedDateY_i**：修改年份

### 分类
- **domain_s**：科学领域
- **docType_s**：文档类型
- **language_s**：语言

### 出版
- **journalTitle_s**：期刊名称
- **journalPublisher_s**：期刊出版者
- **volume_s**：卷（通常缺失——缺失时不要虚构）
- **issue_s**：期号（通常缺失——缺失时不要虚构）
- **page_s**：页码（通常缺失——缺失时不要虚构）
- **bookTitle_s**：著作名称
- **conferenceTitle_s**：会议名称

> **注意**：volume_s、issue_s 和 page_s 字段在 HAL 中很少填写。如缺失，使用 CrossRef（通过 DOI）获取这些元数据。绝不虚构这些数据。

### 文件
- **fileMain_s**：主文件
- **files_s**：文件列表

## 查询示例

### 1. 简单检索
```bash
curl "https://api.archives-ouvertes.fr/search/?q=contrat%20de%20travail&wt=json&rows=10"
```

### 2. 仅法律文章
```bash
curl "https://api.archives-ouvertes.fr/search/?q=licenciement&fq=domain_s:shs.droit&fq=docType_s:ART&wt=json&rows=20"
```

### 3. 近期学位论文
```bash
curl "https://api.archives-ouvertes.fr/search/?q=*&fq=domain_s:shs.droit&fq=docType_s:THESE&fq=publicationDateY_i:[2020%20TO%20*]&wt=json&sort=publicationDateY_i%20desc&rows=15"
```

### 4. 按作者检索
```bash
curl "https://api.archives-ouvertes.fr/search/?q=authFullName_t:\"Dupont\"&fq=domain_s:shs.droit&wt=json"
```

### 5. 在标题中检索
```bash
curl "https://api.archives-ouvertes.fr/search/?q=title_t:responsabilité&fq=domain_s:shs.droit&wt=json"
```

### 6. 带特定字段的检索
```bash
curl "https://api.archives-ouvertes.fr/search/?q=droit%20numérique&fq=domain_s:shs.droit&fl=halId_s,title_s,authFullName_s,publicationDateY_i,abstract_s,uri_s,doiId_s&wt=json&rows=20"
```

## JSON 响应结构

```json
{
  "response": {
    "numFound": 1234,
    "start": 0,
    "docs": [
      {
        "halId_s": "hal-01234567",
        "docid": "1234567",
        "uri_s": "https://hal.archives-ouvertes.fr/hal-01234567",
        "title_s": ["Titre de l'article"],
        "authFullName_s": ["Dupont, Jean", "Martin, Marie"],
        "abstract_s": ["Résumé en français...", "Abstract in English..."],
        "publicationDateY_i": 2023,
        "domain_s": ["shs.droit"],
        "docType_s": "ART",
        "language_s": ["fr"],
        "journalTitle_s": "Revue de droit du travail",
        "doiId_s": "10.1234/exemple",
        "fileMain_s": "https://hal.archives-ouvertes.fr/hal-01234567/document"
      }
    ]
  }
}
```

## Solr 检索运算符

### 布尔运算符
- **AND**：`contrat AND travail`
- **OR**：`contrat OR emploi`
- **NOT**：`contrat NOT commercial`
- **括号**：`(contrat OR emploi) AND travail`

### 字段检索
- **特定字段**：`title:contrat`
- **精确短语**：`title:"contrat de travail"`
- **通配符**：`travail*` 或 `tr?vail`

### 范围
- **日期范围**：`publicationDateY_i:[2020 TO 2024]`
- **自某日期起**：`publicationDateY_i:[2020 TO *]`
- **截至某日期**：`publicationDateY_i:[* TO 2024]`

## 建议返回字段（fl）

为减小响应大小：

```
fl=halId_s,docid,uri_s,title_s,authFullName_s,abstract_s,publicationDateY_i,domain_s,docType_s,language_s,journalTitle_s,volume_s,issue_s,page_s,doiId_s,fileMain_s
```

## 速率限制

- 无官方严格限制
- 建议合理使用
- 无需认证
- 免费服务

## 全文访问

- **fileMain_s**：主文件的 URL（如可用）
- **files_s**：所有文件的列表
- 并非所有文件都是开放获取
- 使用前核验许可

## 专业合集

### HAL-SHS
仅限人文社科：
```
fq=collCode_s:SHS
```

### 机构
按机构过滤：
```
fq=structure_t:"Université Paris 1"
```

## 使用建议

1. **始终指定 wt=json** 以便于解析
2. **过滤器优先使用 fq 而非 q**（性能更好）
3. **用 `fl` 限制返回字段** 以减小带宽
4. **组合多个 fq**：每个 fq 是独立过滤器
5. **对 URL 编码**：空格使用 %20 等
6. **分页前核验 numFound**

## 高效分页

浏览大量结果：

```bash
# 第 1 页（结果 0-19）
curl "https://api.archives-ouvertes.fr/search/?q=...&rows=20&start=0&wt=json"

# 第 2 页（结果 20-39）
curl "https://api.archives-ouvertes.fr/search/?q=...&rows=20&start=20&wt=json"

# 第 3 页（结果 40-59）
curl "https://api.archives-ouvertes.fr/search/?q=...&rows=20&start=40&wt=json"
```

## 限制

- 每次查询最多 10,000 条结果
- 仅元数据（全文情况不一）
- 持续更新但可能存在延迟
- 不保证文件可用性

## 附加资源

- 文档：https://api.archives-ouvertes.fr/docs
- 检索表单：https://hal.archives-ouvertes.fr/search
- 支持：hal-support@ccsd.cnrs.fr
