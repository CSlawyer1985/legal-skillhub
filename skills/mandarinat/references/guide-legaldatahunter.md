# LegalDataHunter 指南——欧盟法、欧洲人权公约和外国/比较法

## ⚠️ 强制可用性核验

**在任何使用之前**，核验 MCP 是否已激活。如会话中 `LegalDataHunter:*` 工具不可用：
- **Cowork**：插件菜单 → 核验 LegalDataHunter 已安装并激活
- **Chat**：联系 Christophe Quézel-Ambrunaz 以激活
- 如不可用：告知用户，切换到使用官方网站（curia.europa.eu、hudoc.echr.coe.int、外国法院官方网站）的 web_search。在交付物中标明该限制。

**绝不要因 MCP 不可用而阻止执行**——使用 web_search 后备方案。

## 使用范围

LegalDataHunter 是以下任何问题的**优先** MCP：
- **欧盟法律**：CJUE 判例、欧盟法院、近期欧盟规范性文本——代码 `EU`
- **《欧洲人权公约》法律**：欧洲人权法院判例——代码 `CoE`
- **外国法律**（另一国家的法律体系）——国家 ISO 代码
- **比较法**（法律体系的对照）
- **外国引用的解析**

**⚠️ 不要用于法国法律。** OpenLegi 是任何法国来源的优先工具。LegalDataHunter 也涵盖法国（代码 `FR`，约 230 万份文件），但 OpenLegi 在此范围内更完整、更可靠、集成更好。例外：OpenLegi 不可用时。

## 主要国家代码

| 范围 | 代码 | 覆盖 | 备注 |
|---|---|---|---|
| 欧盟法律 | `EU` | CJUE、欧盟法院、近期 EUR-Lex、DGComp、EPO… | 见下文时间限制 |
| 欧洲人权公约 / 欧洲委员会 | `CoE` | HUDOC（97,000 份决定，1960-2026）、《欧洲社会宪章》 | CEDH 的主要来源 |
| 德国 | `DE` | 重要 | case_law、legislation |
| 英国 | `UK` | 重要 | case_law、legislation |
| 美国 | `US` | 重要 | case_law、legislation |
| 意大利 | `IT` | 重要 | case_law、legislation |
| 比利时 | `BE` | 重要 | case_law、legislation |
| 瑞士 | `CH` | 重要 | case_law、legislation |
| 西班牙 | `ES` | 重要 | case_law、legislation |
| 国际 | `INTL` | 30 个来源，国际法庭 | 国际法院、国际刑事法院等 |

完整列表：`LegalDataHunter:discover_countries`

## ⚠️ 已知时间限制——须在任何相关交付物中提及

| 来源 | 时间覆盖 | 影响 |
|---|---|---|
| `EU/CURIA`（CJUE 判例） | **仅 2015-2026**（9,383 份决定） | 对 2015 年之前的 CJUE 判决：在 curia.europa.eu 上使用 web_search 后备 |
| `EU/EUR-Lex`（欧盟合并立法） | **仅 2024-2026**（5,001 份文件） | 对 2024 年之前的欧盟文本：在 eur-lex.europa.eu 上使用 web_search |
| `CoE/HUDOC`（欧洲人权法院） | **1960-2026**（97,000 份决定） | 完整覆盖——无实际限制 |

**欧盟法律的优先规则：**
1. **近期 CJUE 判例（2015+）** → `LegalDataHunter:search`（`country: "EU"`，`namespace: "case_law"`）
2. **2015 年之前的 CJUE 判例** → 在 curia.europa.eu 上使用 web_search
3. **欧盟规范性文本（条例、指令）** → 优先在 EUR-Lex 上使用 web_search（覆盖更广）；对非常近期（2024+）的法规以 LegalDataHunter 作补充

## 可用工具（7 个）

### 1. `LegalDataHunter:search`
**主要用途**：语义 + 关键词混合检索。

**参数**：
- `query`（必填）：检索词（英语和国家语言均可用）
- `namespace`：`case_law` | `legislation` | `doctrine`
- `country`：国家代码（如 `EU`、`CoE`、`DE`、`GB`）
- `court_tier`：法院层级（`supreme`、`appellate`、`first_instance`）
- `date_from`、`date_to`：时间范围（ISO 格式）
- `language`：结果语言
- `limit`：结果数量（默认：10）

### 2. `LegalDataHunter:get_document`
**用途**：获取由其 ID 识别的文件的完整文本。

### 3. `LegalDataHunter:resolve_reference`
**用途**：解析外国法律引用（如「BVerfG, 1 BvR 1585/13」）。
**参数**：`reference`（引用文本）、`country`（可选）。

### 4. `LegalDataHunter:discover_countries`
**用途**：列出可用国家及文件数量。

### 5. `LegalDataHunter:discover_sources`
**用途**：列出给定国家的可用来源。
**参数**：`country_code`（必填）。

### 6. `LegalDataHunter:get_filters`
**用途**：获取国家和命名空间的可用筛选器。

### 7. `LegalDataHunter:report_source_issue`
**用途**：报告来源问题。

## 检索策略

### 欧洲人权法院判例（CoE）

```
LegalDataHunter:search
  query: "[英语或法语的法律问题]"
  country: "CoE"
  namespace: "case_law"
```
如结果不足：尝试不带 `namespace` 筛选器，或用英语改写。

### CJUE 判例（EU）

```
LegalDataHunter:search
  query: "[法律问题]"
  country: "EU"
  namespace: "case_law"
```
⚠️ 仅覆盖 2015-2026。对较早判决：在 curia.europa.eu 上使用 web_search。

### 欧盟立法（条例、指令）

优先使用 EUR-Lex（eur-lex.europa.eu）上的 web_search——`EU/EUR-Lex` 仅覆盖 2024-2026。
对非常近期（2024+）的法规作补充：
```
LegalDataHunter:search
  query: "[文本标题或主题]"
  country: "EU"
  namespace: "legislation"
```

### 双边比较检索（法国 vs. X 国）

1. 以一般性术语界定问题（建议英语）
2. 以 `country` = 目标国、`namespace` = `case_law` 或 `legislation` 进行 `search`
3. 就同一问题与法国法律（OpenLegi）比较
4. 综合趋同与分歧

### 多国检索（比较全景）

1. `discover_countries` 识别拥有相关来源的国家
2. 对每个选定国家：以相同术语进行 `search`
3. 按法律家族组织（罗马日耳曼、普通法、混合）

### 外国引用解析

1. 以引用精确文本进行 `resolve_reference`
2. 如失败：以可识别要素进行 `search`
3. 如仍为否定：web_search，然后说明该引用无法解析

## 与检索序列的整合（SKILL.md 第 3 节）

- **第 2 步（最高法院判例）**：对 CJUE（`EU`）和 CEDH（`CoE`）使用 LegalDataHunter
- **第 5 步（外国/比较法）**：对第三国使用 LegalDataHunter

**触发模式：**
- 关于 CJUE 的问题 → `search`（country: `EU`）+ 如早于 2015 则 fallback web_search curia.europa.eu
- 关于 CEDH 的问题 → `search`（country: `CoE`）
- 关于欧盟规范性文本的问题 → 优先 web_search EUR-Lex，LegalDataHunter 作补充（2024+）
- 关于另一国法律的问题 → `search`（country: ISO 代码）
- 比较分析 → 多国序列

## 引用格式

**CEDH：**
```
CEDH, [分庭], [日期], req. n° [编号], [案件名称]
例：CEDH, Gr. Ch., 29 avr. 2002, req. n° 2346/02, Pretty c. Royaume-Uni
```

**CJUE：**
```
CJUE, [分庭], [日期], aff. [C-XX/XX], [案件名称]
例：CJUE, Gr. Ch., 5 juin 2018, aff. C-210/16, Wirtschaftsakademie Schleswig-Holstein
```

**外国法律（一般规则）**：
```
[法院], [日期], [国家参考]
```
对普通法：`[案件名称] [年份] [判例集] [页码]`

始终指明原产国，如相关，指明标题或所确立原则的翻译。

## 错误处理

| 情形 | 行动 |
|---|---|
| MCP 不可用 | 告知用户；切换到使用官方网站的 web_search |
| 2015 年之前的 CJUE 判决 | web_search curia.europa.eu——在交付物中提及 |
| 2024 年之前的欧盟文本 | web_search eur-lex.europa.eu——在交付物中提及 |
| 国家不可用 | `discover_countries`，建议同传统相邻国家 |
| 0 个结果 | 用英语改写、放宽筛选器、换命名空间 |
| 文件不完整 | `get_document` 获取完整文本，否则说明限制 |
| 引用未解析 | 以部分要素 `search`，然后 web_search |
