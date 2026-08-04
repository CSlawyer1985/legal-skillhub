# HTS 数据来源与修订协议

## 目的

凡 HTS 数据支撑归类、GRI 6 层级、关税税率、第 99 章引用、配额注释或来源时效声明时，使用本协议。

目标不仅是获取 JSON 文件。目标是证明使用了哪个 HTS 修订版、如何选择的，以及是否可能存在更新的来源。

## 来源优先级

### 1. Data.gov 目录元数据

Data.gov 是 HTS 批量 JSON 的首选发现点，因为其目录记录列出了当年数据集和可用的修订版本分发。

发现模式：

1. 在 Data.gov 中检索 `Harmonized Tariff Schedule of the United States`。
2. 优先选择与当前日历年匹配的数据集标题。
3. 检查数据集的 `distribution`（分发）列表。
4. 选择最高的当年 `HTS Revision N (JSON)` 分发。
5. 如无当年修订版，选择当年的 `HTS Basic Edition (JSON)`。
6. 记录 Data.gov 目录页、来源落地页（如有）、目录检查或采集日期（如可用）、所选修订版标题和 JSON 下载 URL。

现行 API 指引由 Data.gov 记录于 `https://resources.data.gov/catalog-api/`。Data.gov 已警告其 API 基础 URL 可能随 API 在 `api.data.gov` 中迁移而改变，因此不要将单一 API 主机视为永久。实施时，优先使用可配置的基础 URL，并在 API 行为变化时回退到人工可读的目录页。

辅助脚本：

```text
python3 scripts/resolve-latest-hts-json.py
python3 scripts/resolve-latest-hts-json.py --year 2026
python3 scripts/resolve-latest-hts-json.py --json
```

辅助脚本非权威性。它解析并打印目录元数据；法律分析仍必须记录并从所选来源进行推理。

### 2. USITC HTS 档案

如 Data.gov 不可用或不完整，使用 USITC HTS 档案：

```text
https://www.usitc.gov/tata/hts/archive/index.htm
```

选择当前年份和最高的可用修订版 JSON。记录 Data.gov 不可用或不完整，并指明所用档案页。

### 3. USITC 现行 HTS / 发布页

如档案无法使用，使用 USITC 现行 HTS 或发布页：

```text
https://hts.usitc.gov/
https://www.usitc.gov/harmonized_tariff_information
```

这是税率核查和章节文件的回退方案。如无法核验批量 JSON 修订版，记录该限制。

## 必需的 HTS 来源记录

在归类、关税、第 99 章和合规交付物中包括此紧凑块：

```text
HTS 来源记录
- 目录/来源 URL：{Data.gov 目录 URL 或回退 URL}
- 来源落地 URL：{USITC/来源页（如提供）}
- 目录检查 / 采集：{日期或“不可用”}
- 所选 HTS 版本：{如，2026 HTS 修订版 7（JSON）}
- JSON 下载 URL：{URL}
- 所用 HTS 修订版：{修订版标识符}
- 分析日期：{日期}
- 来源限制：{无 / 使用回退 / API 不可用 / 备注}
```

## 选择规则

- 不要将修订版特定的 USITC 文件 URL 硬编码为主要来源。
- 将修订版 URL 视为通过目录元数据发现的产物。
- 当存在当年修订版时，不要假定“基础版”即为现行版本。
- 如有更新的当年修订版可用，不要按过时层级比较两个候选子目。
- 如当年元数据内部不一致，说明不一致，并在批量 JSON 可确认之前使用实时 USITC REST 加现行章节文件。

## HTS JSON 模式

USITC 批量 JSON 是扁平列表。预期字段包括：

| 字段 | 用途 |
|---|---|
| `htsno` | HTS 编号。空行可能是标签或分组标题。 |
| `indent` | 层级深度。GRI 6 同级比较所必需。 |
| `description` | 该行的法律/统计描述。 |
| `superior` | 层级标签指示符。将 `true`、`"true"` 和 `"True"` 均视为真。 |
| `units` | 数量单位。可能为数组或为空。 |
| `general` | 第 1 栏一般税率。 |
| `special` | 特别计划税率字符串和计划代码。 |
| `other` | 第 2 栏税率。 |
| `footnotes` | 脚注，包括可能的第 99 章引用。 |
| `quotaQuantity` | 配额或数量元数据（存在时）。 |
| `additionalDuties` | 附加关税元数据（存在时）。 |
| `addiitionalDuties` | 观察到的拼写错误；视为与 `additionalDuties` 等效。 |

## 层级规则

- 空 `htsno` 行不是可丢弃行。它们可能承载定义层级的标签。
- `superior: true` 行是分组标签。
- `indent` 控制父子关系。
- GRI 6 比较仅在相同父项下、相同缩进层级的子目之间进行。
- 批量 JSON 可用时，使用 `scripts/hts-hierarchy-builder.py` 进行本地层级探索。

## 第 99 章交叉引用审查

在提出关税或贸易救济结论之前：

1. 检查目标 HTS 行及其父行的 `footnotes`。
2. 检查 `additionalDuties` 和 `addiitionalDuties`。
3. 在所选 JSON 中检索引用的第 99 章子目。
4. 对照官方 USTR、联邦公报、USITC、商务部或公告来源核实现行状态。
5. 记录生效日期、到期日期、排除项和未解决的歧义。
