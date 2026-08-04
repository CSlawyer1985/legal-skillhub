---
name: sanctions-screening
description: 全球制裁筛查智能引擎。对公司/个人进行全球制裁匹配、出口管制检查，覆盖 100+ 名单，生成含证据截图合规报告。默认执行变体确认；若用户明确给出一个或多个名称并要求只按这些名称搜索，则必须严格使用该名称集合，禁止自动扩展变体。
---

# 全球制裁筛查智能引擎

## 架构概览

```
三层筛查 + 法律影响分析 + 专业 PDF 报告

用户输入实体名
      │
      ▼
┌─────────────────┐
│ 第一层：初筛      │ ← OpenSanctions API (/match 端点)
│ (第三方聚合)      │    覆盖 100+ 全球制裁名单
└────────┬────────┘
         │ 命中？
    ┌────┴────┐
    │ 否      │ 是
    ▼         ▼
  清除    ┌────────────────┐
          │ 第二层：官方校验  │ ← 浏览器直连 10+ 官方网站
          │ (政府官网)       │    截图取证 + 时间戳
          └────────┬───────┘
                   ▼
          ┌────────────────┐
          │ 第三层：情报搜索  │ ← Tavily API (28 个受信源)
          └────────┬───────┘
                   ▼
          ┌────────────────┐
          │ 法律影响分析     │ ← 参见 references/legal_implications.md
          └────────┬───────┘
                   ▼
          ┌────────────────┐
          │ PDF 专业报告     │ ← scripts/generate_report.py (Edge Headless)
          └────────────────┘
```

> **关键原则：** OpenSanctions 是第三方聚合数据，仅用于初筛。即使初筛未命中，也会生成官方校验计划（防止 API 故障导致漏报）。

## 🔴🔴🔴 强制执行工作流（含路径确认） 🔴🔴🔴

> **最高优先级指令：** 当用户要求对某实体进行制裁筛查时，**必须先完成「阶段 0：路径确认」，获得用户明确回复后，才能执行任何脚本。禁止跳过路径确认直接运行命令。** 路径确认完毕后，阶段 1-4 必须全部自动执行，不得中途停下来询问用户。

### 阶段 0：意图识别 + 搜索模式确认 ⛔ 必须先完成，禁止跳过

**这是整个工作流中唯一一次交互暂停点。在用户回复之前，禁止执行任何 python 命令。**

收到筛查请求后，**你自己先做两件事**：

**（1）判断实体类型**：根据用户输入的名称，用你的知识判断是公司还是个人。

**（2）先判断搜索模式，再决定是否生成变体**：

#### 模式 A：全量变体模式（默认）

如果用户只是说“筛查华为 / Huawei / 大疆 / DJI”，**没有明确限制只搜一个字符串**，则进入默认模式：自动生成搜索变体。**🔴 你必须覆盖以下所有类别，通常至少生成 8-10 个变体。禁止只生成 2-3 个就交差。**（部分网站对大小写敏感，所以大小写变体必不可少）：

- 英文简称，**含大小写变体**（如 "DJI"、"dji"、"Dji"）
- 英文全名（如 "SZ DJI Technology Co., Ltd."）
- 英文通用名（如 "DJI Technology"）
- 中文全名（如 "深圳市大疆创新科技有限公司"）
- 中文简称（如 "大疆"、"大疆创新"）
- 拼音/音译变体（如 "dajiang"）
- 常见缩写（如 "HW" 代表华为）
- 已知重要子公司（如 "DJI Europe B.V."、"HiSilicon"）

然后**向用户展示变体列表 + 自然语言说明，请求确认**：

> 🏢 我判断 **「<用户输入>」** 是 **公司/法人实体**（如果判断错了请纠正）。
>
> 🔍 我拟使用以下变体对 10 个全球制裁源进行全量筛查。每个变体都会分别在各网站搜索框搜索并截图取证，因为部分制裁网站对大小写敏感，所以会覆盖大写、小写、首字母大写等多种形式。
>
> | # | 搜索变体 | 说明 |
> |---|---------|------|
> | 1 | DJI | 英文简称-大写（主搜索词） |
> | 2 | dji | 英文简称-小写 |
> | 3 | SZ DJI Technology Co., Ltd. | 英文注册全名 |
> | 4 | DJI Technology | 英文通用名 |
> | 5 | 大疆 | 中文简称 |
> | 6 | 大疆创新 | 中文常用名 |
> | 7 | 深圳市大疆创新科技有限公司 | 中文注册全名 |
> | 8 | dajiang | 拼音变体 |
> | 9 | DJI Europe B.V. | 已知子公司 |
>
> 📂 报告默认输出：
> - PDF（最终交付）：`<Skill根目录>/<实体名>_sanctions_report.pdf`
> - HTML（在线浏览）：`<Skill根目录>/<实体名>_sanctions_report.html`
>
> 请确认：回复**「确认」**开始筛查。你也可以告诉我需要**增加**或**删除**哪些变体（增加的变体同样会走完整筛查流程）。

#### 模式 B：用户指定名称集合模式（用户明确要求时）

如果用户明确表达以下意思之一，**必须进入“用户指定名称集合模式”，禁止自动生成变体，禁止再展示 8-10 个变体表**：

- “只筛这个名字”
- “只筛这几个名字”
- “单个名称 / 两个名称 / 三个名称 / 四个名称 / 多个名称”
- “exact name / exact string / exact names”
- “不要变体”
- “仅搜索 `huawei`”
- “只查 `DJI` 和 `dji`，不要扩展”
- “只查这 4 个名字，不要自动补全”

此时你只能使用用户明确给定的名称集合进行搜索，**不能自动补全全名、中文名、拼音、大小写变体、子公司**。用户给 1 个就搜 1 个，给 2 个就搜 2 个，给 N 个就搜 N 个。

此时请改为发送下面这种确认文案：

> 🏢 我判断 **「<用户输入>」** 是 **公司/法人实体**（如果判断错了请纠正）。
>
> 🔍 你要求执行**用户指定名称集合筛查**。我将只使用你明确给出的这些名称在全部制裁源中搜索，**不会自动扩展任何变体**（不补全全名、别名、中文名、拼音、子公司或大小写变体）。
>
> 本次将使用的名称集合（1-N 个，严格按你提供的列表执行）：
> | # | 名称 |
> |---|------|
> | 1 | `<名称1>` |
> | 2 | `<名称2>` |
> | 3 | `<名称3>` |
> | 4 | `<名称4>` |
>
> 📂 报告默认输出：
> - PDF（最终交付）：`<Skill根目录>/<实体名>_sanctions_report.pdf`
> - HTML（在线浏览）：`<Skill根目录>/<实体名>_sanctions_report.html`
>
> 请确认：回复**「确认」**开始按上述**名称集合**执行筛查；如果你希望改回全量变体模式，请直接说明。

**等待用户回复后**，你需要做以下准备（对全流程生效）：

```
实体类型  → 公司 → screen_entity 用 --type LegalEntity，browser_verify 用 --type Entity
         → 个人 → screen_entity 用 --type Person，browser_verify 用 --type Individual

搜索策略  → 全量变体模式：变体列表中第一个英文简称作为主搜索词（--entity 参数）
         → 全量变体模式：其余所有变体通过 --extra-variants 传入
         → 全量变体模式：🔄 脚本会在每个源上，用每个变体分别搜索+截图+取证（全量覆盖）
         → 用户指定名称集合模式：若只有 1 个名称，给 screen_entity.py 和 browser_verify.py 都加 --exact-name-only
         → 用户指定名称集合模式：若有 2-N 个名称，主名称作为 entity，其余名称通过 --extra-variants 传入
         → 用户指定名称集合模式：只搜索用户明确给出的名称集合，不自动生成任何变体
         → 每源结果自动合并：最严重状态优先，截图和匹配记录汇总

报告路径  → 默认路径，或用户指定的路径
```

> 🔴 **严格执行用户确认的变体列表**：如果用户回复中修改了变体列表（删除某些、只保留某些、或新增某些），你**必须严格按用户确认后的最终列表执行**，不要自行补充被用户删掉的变体（如全名）。用户说"只看 DJI 和 dji"，那就只传 DJI 和 dji，不要偷偷加回全名。

---

### 阶段 1：API 初筛（自动）

从 Skill 根目录运行：

```bash
# screen_entity.py 用官方全名 + LegalEntity/Person
python scripts/screen_entity.py "<官方全名>" --type <LegalEntity|Person> -o <report>.md

# 用户只给 1 个名称
python scripts/screen_entity.py "huawei" --type LegalEntity --exact-name-only -o <report>.md

# 用户明确只给 2 个名称
python scripts/screen_entity.py "Huawei" --type LegalEntity --extra-variants "huawei" -o <report>.md

# 用户明确给 4 个名称
python scripts/screen_entity.py "Huawei" --type LegalEntity --extra-variants "huawei" "HUAWEI" "Huawei Technologies" -o <report>.md
```

此步骤自动执行：OpenSanctions 初筛 + Tavily 情报搜索 + 生成浏览器校验计划。
**🔴 禁止使用 `--no-intel` 参数** — Tavily 情报搜索是第三层核心环节，必须执行。
**完成后立即进入阶段 2，不要停下来向用户报告中间结果。**

### 阶段 2：官方网站浏览器校验（自动）

> 🚫 **禁止自己写浏览器脚本。** 直接运行已封装好的 `scripts/browser_verify.py`。
> 🚫 **禁止裁减源列表。** 不要加 `--sources` 参数，必须一次性跑完全部 10 个官方源。

**命令模板（❗ 注意：主搜索词是最短常用名，不是全名）**：

```bash
# 公司示例（用户输入"大疆"或"dji"）
# ❗ --entity 用最短常用名 "DJI"（会在每个网站搜索框搜索）
# ❗ --extra-variants 只放用户确认的变体
# ❗ --api-report 传入阶段 1 的报告路径（嵌入 OpenSanctions 交叉验证）
python scripts/browser_verify.py "DJI" \
  --type Entity \
  --extra-variants "dji" \
  -o screenshots/ \
  --report DJI_sanctions_report.html \
  --api-report DJI_api_report.md

# 用户只给 1 个名称
python scripts/browser_verify.py "huawei" \
  --type Entity \
  --exact-name-only \
  -o screenshots/ \
  --report huawei_sanctions_report.html \
  --api-report huawei_api_report.md

# 用户明确只给 2 个名称
python scripts/browser_verify.py "Huawei" \
  --type Entity \
  --extra-variants "huawei" \
  -o screenshots/ \
  --report Huawei_sanctions_report.html \
  --api-report Huawei_api_report.md

# 用户明确给 4 个名称
python scripts/browser_verify.py "Huawei" \
  --type Entity \
  --extra-variants "huawei" "HUAWEI" "Huawei Technologies" \
  -o screenshots/ \
  --report Huawei_sanctions_report.html \
  --api-report Huawei_api_report.md

# 个人示例（用户输入"张三"）
python scripts/browser_verify.py "Zhang San" \
  --type Individual \
  --extra-variants "张三" "ZHANG SAN" "zhang san" \
  -o screenshots/ \
  --report ZhangSan_sanctions_report.html \
  --api-report ZhangSan_api_report.md
```

**关键说明**：
- **第一个参数（entity）用最短常用英文名**（如 "DJI"、"Huawei"）
- 默认模式下，`--extra-variants` — 官方全名/中文名/其他别名。🔄 **每个变体都会在每个源上全量搜索+截图+取证**
- 用户指定名称集合模式下，`--extra-variants` — 用户明确给出的其余名称（可传 1-N 个）；**只搜索用户给出的列表，不自动扩展**
- `--exact-name-only` — 只搜索输入的单个名称，**禁止自动扩展任何变体**
- `--type Entity|Individual` — 对应阶段 0 用户回答
- `--report <路径>` — 直接输出 HTML 报告

> ⚠️ **重要：不要加 `--sources` 参数！** 默认会自动校验全部 10 个官方源（OFAC、BIS CSL、DoD 1260H、SAM.gov、FCC、UK、UN、EU、AU、CA）。

此脚本自动完成：
- 访问全部 10 个官方制裁搜索网站；默认模式下用**全名 + 所有变体**逐一搜索
- 若启用“用户指定名称集合模式”，则**只搜索用户明确给出的 1-N 个名称**，无论是 1 个、2 个、4 个还是更多
- **分页截图**：如果搜索结果有多页，逐页翻页截图
- **PDF 逐页截图 + 精确高亮**：DoD 1260H 等 PDF 名单，逐页 PageDown + PyMuPDF 黄色高亮
- **XLSX 下载分析**：澳大利亚 DFAT 名单下载 XLSX，pandas 分析后渲染截图
- 截图取证并保存到指定目录
- 输出汇总结果表（命中/清除/需人工确认）

**首次使用需安装依赖：**

```bash
pip install playwright
python -m playwright install chromium
```

**完成后立即进入阶段 2.5，不要停下来向用户报告中间结果。**

### 阶段 2.5：误中审查（自动，禁止跳过）

> 🔴🔴🔴 **此步骤必须在撰写报告之前完成，绝对禁止跳过。**
> 跳过此步骤将导致报告包含大量虚假命中，质量不可接受。

**你必须按顺序执行以下操作**：

**步骤 1**：读取审查指南（完整的判断规则在这里）：
```
read_file: references/false_positive_check.md
```

**步骤 2**：**无需手动操作** — FP 分析已在 `browser_verify.py` 报告生成阶段**自动完成**：
1. 报告生成时自动调用 OpenSanctions API 获取交叉验证数据
2. 核心清单（ofac, bis_csl, dod_1260h, sam, uk, un）的 HIT → **一律标记为确认命中**
3. 泛化清单（eu, au, ca）的 HIT 自动检查：
   - ISO 国家代码碰撞 →  疑似误中
   - OpenSanctions 无该清单佐证 → 🟡 疑似误中
   - EU regime 列表泛化 →  疑似误中
4. 报告 HTML 中的侧栏图标、汇总表、源 section 标题、Evidence List badge、Executive Summary 数字**全部自动更新**

> ⚠️ **禁止**：不要手动写脚本修改报告 HTML 中的 badge/icon/数字。所有 FP 标记已在生成阶段完成。
> 如需调整判断规则，修改 `browser_verify.py` 中的 `SOURCE_TO_OS_DATASETS`、`CORE_HIT_SOURCES`、`FP_CANDIDATE_SOURCES` 配置。

**步骤 3**：检查报告中的判断结果，如有异议直接反馈给用户。

**完成后立即进入阶段 3。**


### 阶段 3：撰写完整证据报告（自动）

将阶段 1、阶段 2、**阶段 2.5 的误中判断**全部整合为一份完整的 Markdown 证据报告。报告必须包含：

1. **报告头部**：筛查编号、时间、实体信息、风险评级
2. **法律影响分析**：读取 `references/legal_implications.md` 模板，针对每个**确认命中**的清单给出法律影响
3. **OpenSanctions 初筛结果**：匹配实体、命中名单、匹配分数
4. **官方校验证据**：每个源的校验结果 + 截图内嵌 + **🟡 误中标注**（如有）
5. **情报摘要**：Tavily 新闻搜索结果
6. **管理层底线结论**：参考 `references/legal_implications.md` 中的 Executive Action Plan 模板
7. **证据清单**：所有截图和数据文件的汇总表

**完成后立即进入阶段 4，不要停下来向用户报告中间结果。**

### 阶段 4：交付最终报告（自动）

`browser_verify.py` 已自动生成专业 HTML 报告和 PDF 报告（PDF 默认始终生成，可用 `--no-pdf` 跳过）。

**报告交付时，你必须在回复中附上以下内容（不可省略）**：

1. **PDF 报告文件路径**（最终交付物，自动通过 Playwright 从 HTML 渲染，含页眉页脚页码）
2. **HTML 报告文件路径**（在线浏览版，含侧栏目录、截图、交叉验证、误中标注）

3. **🧠 误中分析结论**（阶段 2.5 结果）——逐个 HIT 列出判断和理由：

```markdown
## 🧠 AI 合规分析师误中判断

| 源 | 判断 | 理由 |
|----|------|------|
| [源名] | 🔴 确认命中 | [命中记录全名与搜索实体一致的证据] |
| [源名] | 🟡 疑似误中 | [具体误中模式：如 ISO 碰撞/类型不匹配/部分匹配] |
```

3. **综合风险等级**（排除疑似误中后的判断）
4. **建议**

## 环境与依赖

### 依赖安装

脚本仅使用 Python 标准库 + 1 个第三方包。如缺少则安装：

```bash
# 核心依赖（仅 markdown 是第三方包）
pip install markdown

# 可选：澳大利亚 DFAT XLSX 分析需要
pip install pandas openpyxl
```

### 工作目录

**所有脚本必须从 Skill 根目录执行**（`scripts/` 之间有相互导入依赖）。

### API Key

在 Skill 根目录创建 `.env`（可参考 `.env.example`），脚本启动时由 `env_loader` 自动加载。

- **OPENSANCTIONS_API_KEY**：OpenSanctions 聚合初筛（必填，用于 match / 交叉验证）
- **TAVILY_API_KEYS**：逗号分隔的多个 Tavily key，配额耗尽时自动轮换（推荐）
- **TAVILY_API_KEY**：单 key 备选

## 法律影响分析

对每个命中清单，报告中必须包含法律影响分析和咨询建议。模板参见 `references/legal_implications.md`。

结构：
1. **法律影响 (Legal Impact):** 引用具体法规/行政令号
2. **审批政策 (Licensing Policy):** 推定拒绝/逐案审查等
3. **咨询建议 (Advisory):** 面向客户的具体行动建议
4. **管理层底线结论 (Executive Action Plan):** 总结性决策建议

## 中文实体名处理

中文实体名在**默认模式**下须自动转换为多种搜索变体：
- 中文原名 → 拼音变体 → 英文商号 → 常用别名
- 例：`大疆` → `dji`, `SZ DJI Technology`, `Da Jiang Innovations`

变体生成逻辑在 `scripts/fuzzy_match.py` 中实现。若用户明确要求只按给定名称集合筛查，则**不要调用这套自动扩展逻辑**。

## 报告解读

### 风险等级

| 评分 | 等级 | 含义 | 行动建议 |
|------|------|------|---------|
| 56-80 | 🛑 CRITICAL | 极高风险 | 立即停止交易 |
| 36-55 | 🔴 HIGH | 高风险 | 升级审批 + 法律意见 |
| 20-35 | 🟠 MEDIUM | 中风险 | 增强尽职调查 |
| 8-19 | 🟡 LOW | 低风险 | 持续监控 |
| 0-7 | 🟢 CLEAR | 清除 | 正常推进 |

## 参考文档

详细信息参见 `references/` 目录：

- **us_lists_coverage.md** — 美国 5 大核心清单 + 13 个 CSL 子清单完整覆盖指南
- **legal_implications.md** — 各清单法律影响分析模板和咨询意见模板
- **country_risk_tiers.md** — 国家/地区风险分级表
- **red_flags_checklist.md** — BIS "Know Your Customer" 红旗检查清单

## 脚本索引

| 脚本 | 用途 |
|------|------|
| `screen_entity.py` | 核心筛查引擎（三层架构） |
| `official_verify.py` | 官方政府网站直连校验（生成浏览器操作指令） |
| `generate_report.py` | 专业 PDF 报告生成（封面页 + 证据内嵌 + Chrome/Edge Headless） |
| `opensanctions_search.py` | OpenSanctions API 查询 |
| `tavily_search.py` | Tavily 情报搜索 |
| `batch_screen.py` | 批量筛查 |
| `fuzzy_match.py` | 模糊匹配和中文名变体生成 |
| `risk_scorer.py` | 8 维度风险评分引擎 |

## 免责声明

- 本工具仅供参考，不构成法律意见
- OpenSanctions 为第三方聚合数据，命中结果需通过官方源校验
- 制裁名单持续更新，筛查报告建议有效期不超过 7 天
- 最终合规决策应咨询具有执业资格的律师或合规专家
