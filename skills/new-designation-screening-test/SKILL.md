---
name: new-designation-screening-test
description: "生成一个测试条目电子表格——来自 OFAC、OFSI 和欧盟制裁清单的新指定名称及这些名称的有意变体——以验证制裁筛查系统能捕获新指定，并已调到正确的模糊度阈值。每当用户要求制裁清单更新测试数据、筛查回归测试数据、筛查 QA、模糊匹配校准或想核验其筛查清单是否最新时使用本技能。即使用户没有明确说'screening'也触发——如'test my sanctions list'、'check our SDN coverage'、'is my list up to date'或'build me a regression set from the latest designations'等短语也应调用本技能。"
metadata:
  author: "Amir Fadavi"
  license: "mit"
  version: "2026-05-07"
---

# 新指定筛查测试生成器

本技能生成一个电子表格，合规团队可以将其运行通过其制裁筛查系统，以同时验证两件事：

1. **覆盖**——筛查清单是最新的（捕获最近一次指定中添加的名称）。
2. **模糊调优**——筛查引擎已调到能捕获现实的名称变体（转写、换位、字母表替换），而不仅仅是精确字符串。

输出中的每行都是一个测试条目：一个指定名称或其有意变体，外加分析师解读命中（或未命中）所需的元数据。

## 何时运行

当用户要求以下内容时运行：
- 新指定测试数据 / 筛查回归集
- 验证其制裁清单是否最新
- 模糊匹配校准测试集
- 任何匹配"test my screening"或"check our [SDN/OFSI/EU] coverage"的内容

如果用户未指定回溯窗口，默认前 7 天。如果他们说"since last run"并提供了先前的日期，使用该日期。

## 工作流

### 第 1 步——从三大监管机构拉取近期指定

| 监管机构 | 来源 | 要捕获的内容 |
|---|---|---|
| OFAC | `https://ofac.treasury.gov/recent-actions` | SDN 清单或行业/非 SDN 清单的增补。排除修订、移除、FAQ 更新和重新发布的一般许可。 |
| OFSI | `https://www.gov.uk/government/publications/the-uk-sanctions-list` 以及匹配的 OFSI 公告 PDF（见下方子程序） | 仅标记为 **"Added"（新增）** 的条目——排除 **"Amended"（修订）** 和 **"Removed"（移除）**。 |
| EU | 两个来源配合使用：(1) `https://data.europa.eu/apps/eusanctionstracker/`——欧盟制裁跟踪器；页面中部列出最近指定的个人和实体，用于识别窗口内增补。(2) *官方公报*中的相关理事会实施条例（如第 20 个俄罗斯一揽子计划的 (EU) 2026/509 号条例），通过 EUR-Lex 访问——这是标识符、地址、指定理由和列名引用的规范性法律来源。 | CFSP 综合金融制裁清单上的新条目。 |

#### OFSI 子程序

英国制裁清单页面告诉您清单已变更以及变更日期。您需要的被指定人详情（标识符、指定理由、监管机构发布的名称变体）位于匹配的 OFSI 公告 PDF 中，该 PDF 作为单独文件发布。

**始终展开完整的变更日志。**`https://www.gov.uk/government/publications/the-uk-sanctions-list` 上的"Updates to this page"部分默认折叠。可见部分不完整；窗口内条目可能位于折线下方。每次阅读日志前，点击 **"show all updates"**（或展开 `#full-publication-update-history` 锚点）。

工作流：

1. 打开 `https://www.gov.uk/government/publications/the-uk-sanctions-list#full-publication-update-history` 并展开"show all updates"，使每个条目都可见。
2. 阅读回溯窗口内的每个条目。识别列出 **"Added"** 的条目——排除仅为变体、行政修订、更正或撤销的条目。注明日期和所点名的制裁计划。
3. 对于每个有增补的计划，网络搜索 `OFSI notice [计划名称] [日] [月] [年]`（如 `OFSI notice Sudan 29 April 2026`）并定位匹配的 PDF。URL 以 `https://assets.publishing.service.gov.uk/media/...` 开头，后跟公告名称。
4. 确认 PDF 的发布日期与变更日志条目匹配。如果该计划有多份公告，只有与窗口内日期关联的那份才是正确来源。
5. 解析公告。PDF 本身说明每个条目是 **Addition（新增）**、**Variation（变体）** 还是 **Removal（移除）**。**只拉取"Additions"下的条目。**对每项增补捕获：主要名称、唯一 ID、制度名称、施加的制裁、出生日期、出生城镇/国家、所有国籍、所有护照、国民身份证、地址、职务、指定来源（英国 / 联合国）、指定日期以及任何联合国参考编号（如 SDi.011）。
6. 如果英国正在实施联合国安理会列名，在 `identifiers` 列注明联合国参考编号，并检查 OFAC 是否有同一人——跨监管机构的转写差异会产生有用的测试行（见分类中的 `cross_regulator_variant`）。

对三大监管机构的每项新条目捕获：
- 所列主要名称
- 监管机构发布的所有别名 / 化名
- 实体类型（个人、实体、船舶、航空器）
- 制裁计划 / 主管机关
- 指定日期
- 标识符：出生日期、出生地、国籍/司法辖区、地址、护照 / 国民身份证 / 税号 / IMO 编号 / 航空器机尾号
- 来源 URL（直接链接到列名或公告页面，而非仅首页）

#### 默认范围：仅个人和实体

默认情况下，**从测试集中排除船舶和航空器**。金融交易中的大多数制裁筛查针对付款叙述、受益人姓名和相对方实体——而非船舶登记册或飞机机尾号。以船舶和航空器名称种子的通用筛查测试，对典型合规团队（银行、金融科技、专业服务公司）产生的是噪音多于信号。

船舶和航空器筛查*确实*重要，对于：
- 贸易融资和信用证业务
- 船舶和飞机融资
- 海事和航空保险
- 航运、货运代理和物流公司
- 港口运营商和燃油供应服务

如果用户特别要求船舶或航空器测试数据，使用相同的列模式为这些实体类型生成**单独的电子表格**——不要将其并入默认输出。文件名建议：`screening-test-vessels-YYYY-MM-DD.xlsx` 或 `screening-test-aircraft-YYYY-MM-DD.xlsx`。

在交付默认输出的回复中，简要注明船舶/航空器已被排除，并说明可按需提供单独数据集。

#### 数量控制

对每个单独的监管行动（单个 OFAC 近期行动页面、单个 OFSI 公告、单个欧盟理事会实施条例）分别应用此规则，**在从总体中移除船舶和航空器之后**，除非用户要求它们。按行动应用，而非合并的跨监管机构总数。

- **行动中 5 个或更少的增补** → 全部采用。
- **超过 5 个增补** → 抽取 **5 个随机条目加总数的 10%**（向上取整）。例如，120 名被指定人的欧盟一揽子计划 → 5 + ⌈12⌉ = 17 个条目；30 名被指定人的 OFAC 行动 → 5 + 3 = 8 个条目。

抽样时，尽可能按 `entity_type`（个人与实体）和计划对随机抽取进行分层，使样本不会意外地一边倒。在回复中说明选择了哪些条目、排除后的总人数，以及其余条目可按需提供。

### 第 2 步——每个名称生成 6-8 个变体，按失败模式分类

每个变体必须标记其测试的失败模式，使分析师可以将由此产生的命中/未命中模式解读为关于其筛查工具的诊断信息。从下方分类中为每个名称选择 6-8 种模式，偏向与该名称来源和结构最相关的模式（如转写和文字替换对阿拉伯/波斯/俄语/中文名称至关重要；法律形式变体对实体最重要）。

#### 变体分类

| # | 模式 | 测试内容 | 示例："Mohammad Reza Hosseini" |
|---|---|---|---|
| 1 | **换位** | 词序处理 | "Hosseini Mohammad Reza"；"Hosseini, Mohammad Reza" |
| 2 | **首字母 / 缩写** | 部分字符串匹配 | "M. R. Hosseini"；"Mohammad R. Hosseini" |
| 3 | **空格与标点** | 分词边界情况 | "Mohammad-Reza Hosseini"；"MohammadReza Hosseini"；"Mohammad  Reza Hosseini"（双空格） |
| 4 | **变音符号与特殊字符剥离** | Unicode 规范化 | "Hosseini" → "Hoseyni"；"José" → "Jose"；"Ḥusayn" → "Husayn" |
| 5 | **转写漂移** | 语音拼写变体——对阿拉伯、波斯、俄语、中文名称至关重要 | "Mohammad" → "Muhammad" / "Mohammed" / "Mohamed" / "Muhamad" |
| 6 | **文字替换** | 非拉丁文字处理——以母语文字呈现名称（阿拉伯文、西里尔文、中文、波斯文、希伯来文） | "محمد رضا حسینی" |
| 7 | **常见拼写错误 / 错字** | 单字符错误和相邻键换位 | "Hossieni"；"Mohammed Rezza" |
| 8 | **尊称与头衔处理** | 前缀噪音——Sheikh、Dr.、Hajji、Sayyid、Mr.、Mullah | "Sheikh Mohammad Reza Hosseini" |
| 9 | **截断** | 省略中间名、后缀或多个名字中的一个 | "Mohammad Hosseini"（省略 "Reza"） |
| 10 | **跨监管机构变体** | 同一个人被 OFAC / OFSI / EU / UN 以不同方式呈现。当所列之人以不同拼写出现在多个清单上时，每个拼写是单独测试行，标记为 `cross_regulator_variant`，强度为 `strong`。这对以单一模糊阈值筛查多个清单的公司至关重要。 | 同一家族 OFSI "DAGALO" 与 OFAC "DAGLO" |

对于**实体**，将相关模式替换为法律形式变体（"LLC" / "L.L.C." / "Ltd" / "Limited" / "Co." / "Company"）、拉丁/母语文字互换、长名称缩写以及常见所有权前缀变更（俄罗斯实体的 "OAO" / "OOO" / "PJSC"；"JSC" / "Public Joint Stock Company" 等）。

对于**船舶**，变化 "M/V"、"M.V." 或 "MV" 周围的空格；测试带和不带 "IMO" 前缀以及带/不带空格的 IMO 编号；如监管机构列出曾用名，包含它。

对于**航空器**，变化机尾号格式（带/不带破折号；带/不带前导国家代码）。

### 第 3 步——为每个变体标记预期匹配强度

使分析师知道他们的筛查工具*应该*做什么：

- **exact（精确）**——变体与监管机构发布的字符串（主要名称或所列别名）相同。正确加载的筛查清单必须捕获它。此处失败意味着清单过时或未加载。
- **strong（强）**——编辑距离近（1-2 个字符变化、大小写、空格、变音符号）。在典型模糊阈值（约 85% 以上）应被捕获。
- **moderate（中）**——转写变体、尊称噪音、换位。在中等阈值（约 70-85%）应被捕获。
- **weak（弱）**——文字替换、重度截断、多模式组合。测试模糊度的上限或筛查工具的转写 / 非拉丁支持。

### 第 4 步——构建电子表格

使用 `xlsx` 技能生成单工作表工作簿。每个测试条目一行：每个原始名称产生一个 `exact` 行加 6-8 个变体行，因此一次包含 5 名新被指定人的典型运行产生 35-45 行。

列，按此顺序：

| # | 列 | 说明 |
|---|---|---|
| 1 | `original_name` | 监管机构列出的主要名称 |
| 2 | `variation` | 实际输入筛查的测试字符串 |
| 3 | `variation_type` | 来自分类（`exact`、`transposition`、`transliteration` 等） |
| 4 | `expected_match_strength` | `exact` / `strong` / `moderate` / `weak` |
| 5 | `entity_type` | `Individual` / `Entity` / `Vessel` / `Aircraft` |
| 6 | `source_list` | `OFAC SDN` / `OFAC Non-SDN` / `OFSI` / `EU CFSP` |
| 7 | `program` | 如 `RUSSIA-EO14024`、`SDGT`、`IRAN-HR`、`RUS`（英国）、`2014/145/CFSP`（欧盟） |
| 8 | `designation_date` | YYYY-MM-DD |
| 9 | `aliases_aka` | 按发布的以分号分隔的别名 |
| 10 | `dob_or_incorporation` | 个人的出生日期；实体的注册日期（列出时） |
| 11 | `pob_or_place_of_incorporation` | 出生地（个人）或注册地（实体） |
| 12 | `nationality_or_jurisdiction` | 国籍或司法辖区 |
| 13 | `address` | 所列地址，分号分隔 |
| 14 | `identifiers` | 带标签且竖线分隔，如 `Passport: A12345 \| National ID: 1234567890 \| IMO: 9876543` |
| 15 | `regulator_url` | 指向特定列名或公告页面的链接 |

文件名：`screening-test-YYYY-MM-DD.xlsx`（使用运行技能的日期）。

应用最少格式：加粗标题行、冻结顶行、自动调整列宽。不要添加公式——此文件是扁平数据集，而非模型。

## 交付前的输出检查清单

- [ ] 每个原始名称有 1 个 `exact` 行加 6-8 个变体行
- [ ] 每个变体有 `variation_type` 和 `expected_match_strength`
- [ ] 当名称有非拉丁来源时，每个名称至少有一个文字替换行
- [ ] 船舶和航空器从默认输出中排除（或者，如果请求了单独数据集，船舶包含 IMO，航空器包含机尾号）
- [ ] `regulator_url` 链接到特定列名或公告，而非监管机构首页
- [ ] 标题行加粗并冻结
- [ ] 无空行、无合并单元格
- [ ] 回复注明船舶/航空器排除并提供单独数据集

## 边界情况

- **同一个人跨多个监管机构拼写不同。**当 OFAC、OFSI 和欧盟都以略有不同的拼写或出生日期指定同一个人时，将每个拼写作为带其来源清单的单独行包含——那种分歧*就是*测试。
