# Persée OAI-PMH——完整参考

## 概述

Persée 是法国科学期刊回溯性馆藏的数字化和在线传播项目。它提供超过 80 万份全文文献的开放获取，其中包括许多历史法学期刊。

程序化访问通过 OAI-PMH 协议（开放档案倡议元数据收割协议）进行。

**OAI 基础 URL**：https://oai.persee.fr/oai

## 对法学研究的意义

- **回溯性馆藏**：自 19 世纪起的法学期刊文章
- **全文**：免费开放获取
- **OCR 质量**：已数字化并校正的文本
- **URL 稳定性**：永久标识符

## OAI-PMH 协议——基本查询

### 1. 识别仓库

```bash
curl "https://oai.persee.fr/oai?verb=Identify"
```

### 2. 列出馆藏（Sets）

```bash
curl "https://oai.persee.fr/oai?verb=ListSets"
```

返回可用馆藏/期刊的完整列表。

### 3. 列出元数据格式

```bash
curl "https://oai.persee.fr/oai?verb=ListMetadataFormats"
```

可用格式：
- `oai_dc`：简单 Dublin Core（推荐）
- `mets`：METS（更详细）

### 4. 列出某馆藏的全部记录

```bash
curl "https://oai.persee.fr/oai?verb=ListRecords&metadataPrefix=oai_dc&set=NOM_COLLECTION"
```

### 5. 获取特定记录

```bash
curl "https://oai.persee.fr/oai?verb=GetRecord&metadataPrefix=oai_dc&identifier=IDENTIFIANT"
```

## 主要法学馆藏

以下是 Persée 中与法律相关的馆藏（set 名称）：

| Set | 期刊 | 大致时段 |
|-----|-------|----------------------|
| `revue_rfsp` | 法国政治学评论 | 1951-2004 |
| `revue_ridc` | 国际比较法评论 | 1949-2014 |
| `revue_ride` | 国际经济法评论 | 1987-2014 |
| `revue_adef` | 法律与政治科学年鉴 | 历史性 |
| `revue_rcdip` | 国际私法评论 | 1934-2005 |
| `revue_lgdj` | LGDJ 各类出版物 | 不定 |
| `revue_reco` | 经济评论 | 1950-2014 |
| `revue_rfas` | 法国社会事务评论 | 1967-2014 |
| `revue_pop` | 人口 | 1946-2014 |

注：完整列表通过 `ListSets` 获取。set 的确切名称可能变化——始终用 ListSets 查询核实。

## OAI-PMH 响应结构（Dublin Core）

```xml
<OAI-PMH>
  <ListRecords>
    <record>
      <header>
        <identifier>oai:persee:article/ridc_0035-3337_2023_num_75_1_21250</identifier>
        <datestamp>2023-06-15</datestamp>
        <setSpec>revue_ridc</setSpec>
      </header>
      <metadata>
        <oai_dc:dc>
          <dc:title>文章标题</dc:title>
          <dc:creator>姓, 名</dc:creator>
          <dc:subject>比较法</dc:subject>
          <dc:description>文章摘要...</dc:description>
          <dc:publisher>比较立法协会</dc:publisher>
          <dc:date>2023</dc:date>
          <dc:type>article</dc:type>
          <dc:format>application/pdf</dc:format>
          <dc:identifier>https://www.persee.fr/doc/ridc_0035-3337_2023_num_75_1_21250</dc:identifier>
          <dc:language>fr</dc:language>
          <dc:rights>free</dc:rights>
        </oai_dc:dc>
      </metadata>
    </record>
  </ListRecords>
</OAI-PMH>
```

## 按日期过滤

OAI-PMH 支持时间过滤：

```bash
# 自某日期起新增/修改的文档
curl "https://oai.persee.fr/oai?verb=ListRecords&metadataPrefix=oai_dc&set=revue_ridc&from=2020-01-01"

# 某日期之前新增/修改的文档
curl "https://oai.persee.fr/oai?verb=ListRecords&metadataPrefix=oai_dc&set=revue_ridc&until=2000-12-31"

# 在某日期范围内
curl "https://oai.persee.fr/oai?verb=ListRecords&metadataPrefix=oai_dc&set=revue_ridc&from=1990-01-01&until=2000-12-31"
```

**注意**：`from` 和 `until` 按 Persée 中的上线/修改日期过滤，而非文章原始出版日期。

## 分页（resumptionToken）

对大型馆藏，OAI-PMH 使用令牌系统：

```bash
# 第一页
curl "https://oai.persee.fr/oai?verb=ListRecords&metadataPrefix=oai_dc&set=revue_ridc"
# → 返回 <resumptionToken>TOKEN_VALUE</resumptionToken>

# 后续页
curl "https://oai.persee.fr/oai?verb=ListRecords&resumptionToken=TOKEN_VALUE"
```

令牌在每页结果末尾返回。当其为空时，所有结果已遍历完毕。

## 文章直接访问

Persée URL 遵循可预测的格式：

```
https://www.persee.fr/doc/REVUE_ISSN_ANNEE_num_VOL_NUM_PAGEID
```

示例：
```
https://www.persee.fr/doc/ridc_0035-3337_2023_num_75_1_21250
```

## Persée REST API（补充）

除 OAI-PMH 外，Persée 通过 data.persee.fr 提供 REST 访问：

```bash
# 在 Persée 数据中搜索（SPARQL 端点）
curl "https://data.persee.fr/sparql?query=SELECT+*+WHERE+{?s+?p+?o}+LIMIT+10&format=json"
```

SPARQL 端点更灵活但更复杂。对大多数用途，OAI-PMH 已足够。

## 实用示例

### 1. 探索国际比较法评论

```bash
# RIDC 的首批文章
curl "https://oai.persee.fr/oai?verb=ListRecords&metadataPrefix=oai_dc&set=revue_ridc"
```

### 2. 获取特定文章

```bash
curl "https://oai.persee.fr/oai?verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:persee:article/ridc_0035-3337_2023_num_75_1_21250"
```

### 3. 列出所有可用馆藏

```bash
curl "https://oai.persee.fr/oai?verb=ListSets" | grep -i "droit\|juridique\|law"
```

## XML 响应解析

OAI-PMH 响应为 XML。在 bash 中解析：

```bash
# 使用 xmllint（如可用）
curl "https://oai.persee.fr/oai?verb=ListRecords&metadataPrefix=oai_dc&set=revue_ridc" | \
  xmllint --xpath '//dc:title/text()' -

# 使用 Python
python3 -c "
import xml.etree.ElementTree as ET
import urllib.request
url = 'https://oai.persee.fr/oai?verb=ListRecords&metadataPrefix=oai_dc&set=revue_ridc'
response = urllib.request.urlopen(url).read()
root = ET.fromstring(response)
ns = {'dc': 'http://purl.org/dc/elements/1.1/', 'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/'}
for record in root.iter('{http://www.openarchives.org/OAI/2.0/}record'):
    title = record.find('.//dc:title', ns)
    creator = record.find('.//dc:creator', ns)
    if title is not None:
        print(f'{creator.text if creator is not None else \"?\"} - {title.text}')
"
```

## 局限

- **OAI-PMH 协议**：为收割而设计，非全文检索
- **无关键词搜索**：遍历馆藏，而非在其中搜索
- **回溯性馆藏**：无近期出版物（出版方禁运）
- **XML 格式**：比 JSON 更难解析
- **吞吐量**：顺序分页，无并行检索

如需在 Persée 中进行关键词搜索，优先使用索引 Persée 的 ISIDORE。

## 何时使用 Persée OAI 与 ISIDORE

| 需求 | 推荐工具 |
|--------|-----------------|
| 关键词搜索 | ISIDORE（索引 Persée） |
| 遍历完整馆藏 | Persée OAI |
| 访问文章的详细元数据 | Persée OAI |
| 特定期刊的历史学说 | Persée OAI |
| 宽泛主题检索 | ISIDORE |

## 资源

- **Persée 门户**：https://www.persee.fr
- **技术文档**：https://www.persee.fr/entrepot-oai
- **SPARQL 端点**：https://data.persee.fr
