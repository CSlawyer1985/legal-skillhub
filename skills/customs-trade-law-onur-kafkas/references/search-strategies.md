# 检索策略——所有数据源的查询模式

本文件包含经过验证和整理的贸易与海关数据检索模式。在所有工作流中的 `web_search` 和 `web_fetch` 调用中使用这些模式。

---

## 1. HTS 归类查询

### 现行 HTS 批量 JSON 发现（修订感知工作所必需）

在依赖批量 JSON、GRI 6 层级、税率字段或第 99 章脚注之前，先遵循 `references/hts-data-sources.md`。首先通过 Data.gov 目录元数据发现最新 JSON；不要将修订特定的 USITC URL 硬编码为主要来源。

现行 Data.gov 目录 API 模式：

```text
web_fetch("https://catalog.data.gov/search?q=Harmonized+Tariff+Schedule+of+the+United+States+{current_year}&per_page=10")
```

记录：
- Data.gov 目录 URL
- 目录检查 / 收获日期（如有）
- 选定的 `HTS Revision N (JSON)` 标题
- JSON 下载 URL
- 分析日期
- 所用 HTS 修订版

如 Data.gov 不可用，使用：

```text
web_fetch("https://www.usitc.gov/tata/hts/archive/index.htm")
web_fetch("https://www.usitc.gov/harmonized_tariff_information")
```

辅助工具：

```text
python3 scripts/resolve-latest-hts-json.py --year {current_year}
```

### USITC REST API（用于实时关键词/税率查询）
```
web_fetch("https://hts.usitc.gov/reststop/search?keyword={TERM}")
```
- 返回：最多 100 个税目，JSON 格式
- 字段：htsno、description、indent、general、special、other、footnotes、units
- **不包含**章/部分注释——仅品目/子目数据
- 对关键词进行 URL 编码
- 尝试多个关键词变体以获得最佳覆盖

REST 结果可用于候选发现，但不能替代已记录的现行 HTS 修订版进行层级敏感的 GRI 6 分析。

### 批量 JSON（用于层级导航）

- 使用从 Data.gov 或后备来源选定的 JSON URL。
- 返回：HTS 行项目的完整扁平数组。
- 使用 `scripts/hts-hierarchy-builder.py` 转换为可导航的树。
- 如用户上传 JSON 文件，记录文件名，如修订版/日期不明则询问其来源。

### 章 PDF（用于章/部分注释）
```
web_fetch("https://hts.usitc.gov/reststop/file?release=currentRelease&filename=Chapter+{N}")
```
- 返回：二进制 PDF——建议用户下载
- 章注释、部分注释和总注释的**唯一来源**
- 对 GRI 1 分析至关重要

### 网页检索后备
```
web_search("{product name} HTS classification HTSUS")
web_search("{product function} tariff heading chapter {XX}")
web_search("HTSUS {heading number} {product description}")
web_search("HTS chapter {N} notes {relevant note topic}")
```

---

## 2. CROSS 裁定检索

### 主要方法——直接 CROSS 检索 URL
```
web_fetch("https://rulings.cbp.gov/search?term={product+keywords}&collection=ALL&commodityGrouping=ALL&sortBy=DATE_DESC&pageSize=30&page=1")
```
- 返回：按日期排序的现行裁定（最新在前）
- 对搜索词进行 URL 编码（空格用 `+`）
- 调整 `collection`：`ALL`（默认）、`HQ`（仅总部）、`NY`（仅纽约）
- 调整 `pageSize`（最大 30）和 `page` 进行分页

### 单个裁定获取
```
web_fetch("https://rulings.cbp.gov/ruling/{RULING_ID}")
```
- 返回：完整裁定文本，包括产品描述、归类、推理和状态
- 用于达到**已核验**证据质量

### 布尔检索模式（在 `term` 参数中支持）
- AND：`keyboard AND bluetooth AND 8471`
- OR：`smartwatch OR "smart watch" OR "wrist computer"`
- AND NOT：`keyboard AND NOT piano`
- NEAR：`essential NEAR character`（查找邻近的术语）
- 通配符：`comput*`（匹配 computer、computing、computation）
- 精确短语：`"essential character"`

### 裁定检索策略
1. 从宽开始：`web_fetch` 使用产品关键词、`collection=ALL`、`sortBy=DATE_DESC`
2. 按品目收窄：在搜索词中加入 4 位品目
3. 聚焦 HQ 裁定：设置 `collection=HQ` 获取权威总部裁定
4. 获取单个裁定：`web_fetch("https://rulings.cbp.gov/ruling/{ID}")` 获取全文
5. 检查撤销：在裁定文本中查找撤销/修改通知

---

## 3. CIT/CAFC 法院判决

来源**并非**同等。遵循此严格优先级顺序：

### 第 1 步：CIT 判决意见索引——识别判决
```
web_fetch("https://www.cit.uscourts.gov/content/slip-opinions-{YYYY}")
```
- 返回：结构化表格，含意见编号、案名、日期、案号、法官、管辖权代码
- 筛选管辖权代码 `1581(a)` = 归类案件

### 第 2 步：PDF 文本提取——意见文本的主要来源
```
bash: python3 scripts/cit-opinion-fetcher.py {slip-op-number}
```
- 示例：`python3 scripts/cit-opinion-fetcher.py 26-11`
- 从 `cit.uscourts.gov` 下载 PDF 并使用 pymupdf 提取全文
- 也接受完整 URL 或本地文件路径
- 这是意见文本的主要来源。始终先使用此方法，再使用后备方案。

### 第 3 步：后备来源——仅在 PDF 阅读器不可用时
```
web_search("site:law.justia.com Court International Trade {product} classification")
web_search("site:law.justia.com CIT {HTS heading} {year}")
```
- Justia 以可读格式索引完整案件文本
- 仅当直接 PDF 获取失败时作为后备使用

```
web_search("Court of International Trade {HTS heading} classification")
web_search("CIT {product type} classification {heading} GRI")
web_search("site:cit.uscourts.gov {product} classification")
```

### CAFC 上诉
```
web_search("CAFC {product type} HTS classification appeal")
web_search("Federal Circuit {heading} tariff classification")
web_search("Court of Appeals Federal Circuit customs classification {product}")
```

### CIT 判决筛选
- 管辖权 1581(a)：归类争议（主要关注）
- 管辖权 1581(c)：反倾销/反补贴税案件
- 管辖权 1581(i)：剩余管辖权
- 始终检查所引任何 CIT 判决的 CAFC 上诉状态

---

## 4. 第 99 章/贸易救济附加税

### 第 301 条（中国关税）
```
web_search("Section 301 tariff {HTS heading} China {current_year}")
web_search("USTR Section 301 list {product type} {current_year}")
web_search("9903.88 {HTS heading} Section 301")
web_search("Section 301 exclusion {product} {HTS heading} {current_year}")
```

### 第 232 条（钢铁/铝）
```
web_search("Section 232 tariff {product} {current_year}")
web_search("Section 232 steel aluminum tariff rate {current_year}")
web_search("Section 232 exclusion {product} {current_year}")
```

### 第 201 条（保障措施）
```
web_search("Section 201 safeguard tariff {product} {current_year}")
```

---

## 5. 反倾销/反补贴税命令

```
web_search("site:trade.gov antidumping duty order {product} {country}")
web_search("site:trade.gov countervailing duty order {product} {country}")
web_search("site:federalregister.gov AD/CVD order {product} {country}")
web_search("Commerce scope ruling {product} {country} AD/CVD")
web_search("ACCESS Commerce {product} {country} antidumping countervailing")
```

---

## 6. 原产地

### 标记规则
```
web_search("CBP country of origin marking {product type}")
web_search("19 CFR 134 substantial transformation {product}")
web_fetch("https://rulings.cbp.gov/search?term=country+of+origin+{product}&collection=ALL&commodityGrouping=ALL&sortBy=DATE_DESC&pageSize=30&page=1")
```

### FTA 原产地规则
```
web_search("USMCA rules of origin {HTS heading} tariff shift")
web_search("{FTA name} rules of origin {product type}")
web_search("CAFTA-DR origin {HTS chapter} rule")
```

### 《贸易协定法》（TAA）
```
web_search("TAA substantial transformation {product} {country}")
web_search("Trade Agreements Act designated country list {current_year}")
```

---

## 7. 补充来源

### 知情合规出版物
```
web_search("CBP informed compliance {product type}")
web_search("site:cbp.gov informed compliance classification {chapter}")
```

### 注释（世界海关组织）
```
web_search("WCO Explanatory Notes heading {XXXX}")
web_search("Harmonized System Explanatory Notes {heading} {product}")
```

### 《联邦公报》通知
```
web_search("Federal Register {topic} tariff {current_year}")
web_search("site:federalregister.gov customs {product} {current_year}")
```

---

## 检索策略提示

1. **始终以当前年份检索**以获取最新信息
2. **使用多个关键词变体**——贸易术语可能与日常用语不同
3. **优先直接来源访问**（HTS 用 Data.gov/USITC、裁定用 CROSS、法院用官方 CIT/CAFC 意见文本），而非一般网页检索
4. **交叉引用**多次检索的结果——没有单次检索能涵盖一切
5. **检查 HTS API 结果中的脚注**以获取第 99 章交叉引用（如"See 9903.88.15"）
6. **使用 Data.gov 批量 JSON 发现**进行修订感知的 HTS 层级；使用 REST 检索进行实时关键词和税率确认
