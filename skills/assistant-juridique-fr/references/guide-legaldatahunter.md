# LegalDataHunter 指南——欧盟法、欧洲人权公约法与外国/比较法

## ⚠️ 强制性可用性核验

**在任何使用之前**，核验 MCP 是否已启用。如 `LegalDataHunter:*` 工具在会话中不可用：
- **Cowork**：插件菜单 → 核验 LegalDataHunter 已安装并启用
- **Chat**：联系 Christophe Quézel-Ambrunaz 以启用
- 如不可用：告知用户，改用 web_search 检索官方站点（curia.europa.eu、hudoc.echr.coe.int、外国司法机关官方站点）。在交付物中注明该限制。

**绝不要因 MCP 不可用而阻塞执行**——使用 web_search 回退。

## 使用范围

LegalDataHunter 是以下任何问题的**优先** MCP：
- **欧盟法**：欧盟法院判例、欧盟普通法院、最新欧盟规范性文本——代码 `EU`
- **《欧洲人权公约》法**：欧洲人权法院判例——代码 `CoE`
- **外国法**（其他国家的法律体系）——国家 ISO 代码
- **比较法**（法律体系的对照）
- **外国引用的解析**

**⚠️ 不要用于法国法。** OpenLegi 是任何法国来源的优先工具。LegalDataHunter 也涵盖法国（代码 `FR`，约 230 万份文件），但 OpenLegi 在该范围内更全面、更可靠、集成更好。例外：OpenLegi 不可用时。

## 主要国家代码

| 范围 | 代码 | 覆盖 | 说明 |
|---|---|---|---|
| 欧盟法 | `EU` | 欧盟法院、欧盟普通法院、最新 EUR-Lex、DGComp、EPO…… | 见下文时间限制 |
| 欧洲人权公约 / 欧洲委员会 | `CoE` | HUDOC（97K 份决定，1960-2026）、《欧洲社会宪章》 | 欧洲人权公约的主要来源 |
| 德国 | `DE` | 重要 | case_law、legislation |
| 英国 | `UK` | 重要 | case_law、legislation |
| 美国 | `US` | 重要 | case_law、legislation |
| 意大利 | `IT` | 重要 | case_law、legislation |
| 比利时 | `BE` | 重要 | case_law、legislation |
| 瑞士 | `CH` | 重要 | case_law、legislation |
| 西班牙 | `ES` | 重要 | case_law、legislation |
| 国际 | `INTL` | 30 个来源，国际法庭 | 国际法院、国际刑事法院等 |

完整清单：`LegalDataHunter:discover_countries`

## ⚠️ 已知时间限制——须在任何相关交付物中注明

| 来源 | 时间覆盖 | 影响 |
|---|---|---|
| `EU/CURIA`（欧盟法院判例） | 仅 **2015-2026**（9,383 份决定） | 对 2015 年前的欧盟法院判决：在 curia.europa.eu 上 web_search 回退 |
| `EU/EUR-Lex`（欧盟合并立法） | 仅 **2024-2026**（5,001 份文件） | 对 2024 年前的欧盟文本：在 eur-lex.europa.eu 上 web_search |
| `CoE/HUDOC`（欧洲人权法院） | **1960-2026**（97K 份决定） | 覆盖完整——无实际限制 |

**欧盟法的优先级规则：**
1. **最新欧盟法院判例（2015 年后）** → `LegalDataHunter:search`（`country: "EU"`，`namespace: "case_law"`）
2. **2015 年前的欧盟法院判例** → 在 curia.europa.eu 上 web_search
3. **欧盟规范性文本（条例、指令）** → 首先用 web_search 检索 EUR-Lex（覆盖更广）；对最新文书（2024 年后）以 LegalDataHunter 补充

## 可用工具（7 个）

### 1. `LegalDataHunter:search`
**主要用途**：语义 + 关键词混合检索。

**参数**：
- `query`（必填）：检索词（可用英语和国家语言）
- `namespace`：`case_law` | `legislation` | `doctrine`
- `country`：国家代码（如 `EU`、`CoE`、`DE`、`GB`）
- `court_tier`：司法机关层级（`supreme`、`appellate`、`first_instance`）
- `date_from`、`date_to`：时间界限（ISO 格式）
- `language`：结果语言
- `limit`：结果数量（默认：10）

### 2. `LegalDataHunter:get_document`
**用途**：获取按 ID 识别的文件的全文。

### 3. `LegalDataHunter:resolve_reference`
**用途**：解析外国法律引用（如"BVerfG, 1 BvR 1585/13"）。
**参数**：`reference`（引用文本）、`country`（可选）。

### 4. `LegalDataHunter:discover_countries`
**用途**：列出可用国家及文件数量。

### 5. `LegalDataHunter:discover_sources`
**用途**：列出特定国家的可用来源。
**参数**：`country_code`（必填）。

### 6. `LegalDataHunter:get_filters`
**用途**：获取特定国家和命名空间的可用过滤器。

### 7. `LegalDataHunter:report_source_issue`
**用途**：报告来源问题。

## 检索策略

### 欧洲人权法院判例（CoE）

```
LegalDataHunter:search
  query: "[法律问题，英文或法文]"
  country: "CoE"
  namespace: "case_law"
```
如结果不足：尝试不带 `namespace` 过滤器，或用英文改写。

### 欧盟法院判例（EU）

```
LegalDataHunter:search
  query: "[法律问题]"
  country: "EU"
  namespace: "case_law"
```
⚠️ 仅覆盖 2015-2026 年。对更早的判决：在 curia.europa.eu 上 web_search。

### 欧盟立法（条例、指令）

优先 web_search EUR-Lex（eur-lex.europa.eu）——`EU/EUR-Lex` 仅覆盖 2024-2026 年。
对最新文书（2024 年后）补充：
```
LegalDataHunter:search
  query: "[文本标题或对象]"
  country: "EU"
  namespace: "legislation"
```

### 双边比较检索（法国 vs. X 国）

1. 用一般术语识别问题（建议英文）
2. `search` 使用 `country` = 目标国家，`namespace` = `case_law` 或 `legislation`
3. 用法国法（OpenLegi）就同一问题进行比较
4. 综合趋同与分歧

### 多国检索（比较全景）

1. `discover_countries` 识别具有相关来源的国家
2. 对每个选定国家：用相同术语 `search`
3. 按法律家族组织（罗马-日耳曼、普通法、混合）

### 外国引用的解析

1. 用引用的确切文本 `resolve_reference`
2. 如失败：用可识别的要素 `search`
3. 如仍为否定：web_search，然后注明该引用未能解析

## 与检索序列的集成（SKILL.md 第 3 节）

- **第 2 步（最高司法判例）**：LegalDataHunter 用于欧盟法院（`EU`）和欧洲人权法院（`CoE`）
- **第 5 步（外国/比较法）**：LegalDataHunter 用于第三方国家

**触发模式：**
- 欧盟法院问题 → `search`（country: `EU`）+ 如早于 2015 年则在 curia.europa.eu 上 web_search 回退
- 欧洲人权法院问题 → `search`（country: `CoE`）
- 欧盟规范性文本问题 → 首先 web_search EUR-Lex，LegalDataHunter 补充（2024 年后）
- 他国法律问题 → `search`（country: ISO 代码）
- 比较分析 → 多国序列

## 引用格式

**欧洲人权法院：**
```
CEDH, [审判庭], [日期], req. n° [编号], [案件名称]
例：CEDH, Gr. Ch., 29 avr. 2002, req. n° 2346/02, Pretty c. Royaume-Uni
```

**欧盟法院：**
```
CJUE, [审判庭], [日期], aff. [C-XX/XX], [案件名称]
例：CJUE, Gr. Ch., 5 juin 2018, aff. C-210/16, Wirtschaftsakademie Schleswig-Holstein
```

**外国法（一般规则）：**
```
[司法机关], [日期], [国内引用]
```
普通法：`[案件名称] [年份] [汇编] [页码]`

始终注明原籍国，并在相关时注明标题或所确立原则的翻译。

## 错误处理

| 情形 | 行动 |
|---|---|
| MCP 不可用 | 告知用户；改用 web_search 检索官方站点 |
| 2015 年前的欧盟法院判决 | web_search curia.europa.eu——在交付物中注明 |
| 2024 年前的欧盟文本 | web_search eur-lex.europa.eu——在交付物中注明 |
| 国家不可用 | `discover_countries`，建议相同传统的邻国 |
| 0 结果 | 用英文改写，放宽过滤器，其他命名空间 |
| 文件不完整 | `get_document` 获取全文，否则注明限制 |
| 引用未解析 | 用部分要素 `search`，然后 web_search |
