# ISIDORE API —— 完整参考

## 概览

ISIDORE 是 CNRS 的人文与社会科学（SHS）研究数据聚合器。它自动采集并丰富以下来源的元数据：
- HAL（开放存档）
- Cairn.info（SHS 期刊）
- Persée（回溯馆藏）
- OpenEdition（期刊和图书）
- theses.fr
- 以及 5000 多个其他来源

**基础 URL**：https://api.isidore.science

## 主要端点

### 1. 资源检索
```
GET https://api.isidore.science/resource/search
```

**必填参数：**
- `q`：检索词

**可选参数：**
- `output`：格式（`json` 或 `xml`，默认：xml）
- `replies`：结果数量（默认：10，最大：100）
- `page`：页码
- `lang`：语言（`fr`、`en`、`es`）
- `type`：文献类型（URI）
- `discipline`：学科（URI）
- `facet`：要返回的方面
- `sort`：排序（`score` 或 `date`）

**完整示例：**
```bash
curl "https://api.isidore.science/resource/search?q=contrat%20travail&type=http://isidore.science/ontology%23article&discipline=http://purl.org/dc/terms/subject/law&output=json&replies=20&sort=date"
```

### 2. 自动补全
```
GET https://api.isidore.science/resource/suggest
```

**参数：**
- `q`：词的开头
- `replies`：建议数量（默认：10）

**示例：**
```bash
curl "https://api.isidore.science/resource/suggest?q=droit%20trav&replies=5"
```

### 3. 词表检索
```
GET https://api.isidore.science/vocabulary/search
```

用于查找叙词表的规范化术语。

## 文献类型（URIs）

法律领域的主要类型：

```
http://isidore.science/ontology#article            # 期刊文章
http://isidore.science/ontology#thesis             # 论文
http://isidore.science/ontology#book               # 专著
http://isidore.science/ontology#chapter            # 专著章节
http://isidore.science/ontology#report             # 报告
http://isidore.science/ontology#conference_paper   # 会议论文
http://isidore.science/ontology#working_paper      # 工作文件
```

## 学科（URIs）

法律领域：

```
http://purl.org/dc/terms/subject/law              # 法律（一般）
http://aurehal.archives-ouvertes.fr/subject/shs.droit    # 法律（HAL）
```

## JSON 响应结构

```json
{
  "response": {
    "numFound": 1234,
    "docs": [
      {
        "uri": "...",
        "title": ["Titre de l'article"],
        "creator": ["Nom, Prénom", "Autre auteur"],
        "date": ["2023"],
        "publisher": ["Nom éditeur"],
        "source": ["Nom de la revue"],
        "abstract": ["Résumé..."],
        "type": ["http://isidore.science/ontology#article"],
        "discipline": ["http://purl.org/dc/terms/subject/law"],
        "language": ["fra"],
        "identifier": ["DOI:10.xxxx/yyyy"],
        "access_URL": ["https://..."]
      }
    ]
  }
}
```

## 重要字段

- **uri**：ISIDORE 唯一标识符
- **title**：标题（数组）
- **creator**：作者（数组）
- **date**：出版日期（数组）
- **abstract**：摘要
- **identifier**：标识符（DOI、HAL ID 等）
- **access_URL**：文献访问 URL
- **source**：出版来源
- **type**：文献类型
- **discipline**：学科
- **language**：语言

## 检索运算符

ISIDORE 支持布尔运算符：

- **AND**：`contrat AND travail`
- **OR**：`contrat OR emploi`
- **NOT**：`contrat NOT commercial`
- **"精确短语"**：`"contrat de travail"`
- **截断**：`travail*`（travail、travailleur 等）

## 实用示例

### 简单检索
```bash
curl "https://api.isidore.science/resource/search?q=licenciement&output=json&replies=10"
```

### 仅期刊文章
```bash
curl "https://api.isidore.science/resource/search?q=responsabilité%20civile&type=http://isidore.science/ontology%23article&output=json"
```

### 近期论文（使用布尔运算符）
```bash
curl "https://api.isidore.science/resource/search?q=droit%20numérique&type=http://isidore.science/ontology%23thesis&output=json&sort=date"
```

### 按作者和主题检索
```bash
curl "https://api.isidore.science/resource/search?q=creator:Dupont%20AND%20droit%20travail&output=json"
```

## 速率限制

- 无记录的严格限制
- 建议合理使用（< 10 次请求/秒）
- 无需身份验证

## 语义丰富

ISIDORE 自动丰富元数据：
- 叙词表术语（Rameau 等）
- 指向人物/组织的链接
- 如相关，地理位置
- 文献之间的关系

这些丰富改善了检索质量。

## 使用建议

1. **从简单开始**：先基础检索，再细化
2. **使用 output=json**：更易于解析
3. **按类型过滤**：根据需要使用 article、thesis
4. **分页**：使用 `page` 浏览结果
5. **按日期排序**：使用 `sort=date` 获取近期出版物

## 聚合数据来源

ISIDORE 特别采集：
- HAL-SHS
- Cairn.info
- Persée
- OpenEdition Journals
- OpenEdition Books
- Gallica（BnF）
- Erudit
- theses.fr
- Calenda
- Hypothèses
- 以及数以千计的其他机构存储库

## 官方文档

https://isidore.science/api
https://documentation.huma-num.fr/isidore/
