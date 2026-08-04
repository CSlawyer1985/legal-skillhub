---
name: 法律周报
description: "用户说「生成法律周报」「帮我筛法院公众号文章」「法律简报」「案例入库」时触发。从四个法院公众号（上海一中院/二中院/山东高法/中国应用法学）文章中用可解释的 k-NN 评分引擎（八判据驱动）筛出 10 条精品周报，其余实务文章全量入库 IMA 知识库做 RAG。临时法律热点查询走 legal-hot，不要用本 skill。"
author: "社区贡献者"
agent_created: true
version: 3.1.0
load: on_demand
---

# 法律周报自动化 · Legal Weekly Briefing

## 全局禁令（Agent 铁律）

> 以下规则在整个 skill 执行期间**必须遵守**。违反任一条 = 交付阻断。

| 场景 | 必须遵守 | 不应发生 |
|------|---------|---------|
| IMA 知识库 | 仅限用户自建个人 KB，使用前确认归属 | 不应指引订阅/加入/接受邀请非自建 KB |
| KB_ID | 用 `YOUR_KNOWLEDGE_BASE_ID` 占位符；用户提供后先确认「是自建的吗？」再写入 | 不应提供或暗示任何具体 KB_ID（含示例） |
| HTML 交付 | 仅用 `render_html.py` 渲染（`#f8f7f5` / `#1a1a2e` 浅色简报风） | 不应自造深色翻页幻灯片或其他替代样式 |
| 交付验证 | 每次修改后必须跑 `python3 scripts/verify.py`，23 项全通过 | 不应跳过验证或仅凭人眼判断 |
| 候选数据 | 每条候选必须含 `abstract` + `recommend` | 不应构建缺少必填字段的 candidates.jsonl |
| session.json | 仅本地使用，`.gitignore` 已排除 | 不应分享/提交到 Git/发送到任何服务器 |
| 样式修改 | 需要改样式时先问用户确认 | 不应擅自改动配色/布局/交互 |
| 适配流程 | 用户说「配置法律周报」→ 必须按适配向导 4 问引导 | 不应跳过适配向导给通用配置 |
| 内容发现路径 | 启动时检测双通道（微信读书登录态 → 元宝登录态），确定路径后明确告知用户 | 不应静默降级到 WebSearch 而不告知路径变化及影响 |
| 候选摘要 | 每条候选 `abstract` 必须非空。MP 路径取 `digest`；WebSearch 路径取 snippet → WebFetch → 占位文本 **三级回退** | 不应产出 abstract 为空的候选条目 |

---

## 执行前置检查（Agent 启动时强制，先于一切内容发现）

> 每次「生成本周法律周报」请求，Agent 必须先跑此检查，再开始任何操作。

### 三层通道可用性检测

> 2026-07-29 微信关闭 MP 跨号接口后，内容发现走「微信读书搜一搜（主）+ 元宝（补）」双通道。TokenHub API 已验证无公众号内容，仅保留代码兼容。

| 层 | 条件 | 检查方式 | 缺失影响 |
|----|------|---------|---------|
| L1 微信读书 | `~/.config/weread_state.json` 存在且含非空 `wr_vid` | 脚本 `preflight_channels()` | ✗ → 降级 L2 |
| L2 元宝 | `~/.config/yuanbao_state.json` 存在且有 cookies | 同上 | ✗ → 降级 L3 |
| L3 TokenHub | `~/.config/tencentcloud/tokenhub_api_key` 存在 | 同上 | ✗ → 降级 WebSearch（⚠️ 已验证无公众号内容，仅保留代码兼容） |

Agent 输出要求（任一通道缺失时，在回复中明确声明）：

```
⚠️ 自动发现通道缺失（缺少: <具体缺什么>），将降级至 <下一可用通道>。
影响：① 文章链接可能来自转载站而非微信原文 ② 摘要是搜索结果片段而非原文节选。
如需要主通道，请先完成配置（见 references/weread-setup-guide.md / yuanbao-setup-guide.md）。
```

### 摘要生成三级回退

根据内容发现路径选择摘要来源。**每条候选的 abstract 字段必须非空**：

| 优先级 | 路径 | 来源 | 失败处理 |
|--------|------|------|---------|
| 1 | 微信读书（L1） | 搜索结果 `digest` 字段 | 若疑似文末片段 → 回退到 3 |
| 2 | 元宝反查（L2）/ WebSearch | 回答摘要 / 搜索 snippet | 若空 → 回退到 3 |
| 3 | WebSearch 无 snippet | WebFetch 文章页面，取正文前 200 字 | 若失败 → 回退到 4 |
| 4 | 全部失败 | `abstract` = "摘要获取失败，请点击原文查看" | — |

> ⚠️ **L1 digest 质量陷阱（2026-08-01 实测）**：微信读书搜索的 `digest` 对部分文章会抓到**文末片段或法条引用段**（"来稿经编校后…""投稿须知…""关注我们…"等引导语，以及《民法典》第X条、《最高法…解释》等法条原文开头）。判断规则：digest 以"来稿/投稿/点击/长按/关注/扫描/更多信息"等文末特征词开头，或以《法条名》第X条句式开头（法条引用段）→ 视为质量差，回退到 WebFetch 取正文前 200 字（案情/问题引入段）。

`recommend` 字段：始终由 Agent 基于标题和可用摘要做律师视角的实务价值判断（≥30 字）。

> ⚠️ **recommend 缺失纪律（2026-08-01 实测）**：L1 微信读书抓取只有 5 字段（title/url/publish_time/digest/_source），**不含 recommend**。全自动模式跑 pipeline 前，Agent 必须为每条法律候选补写 recommend——漏补则周报条目无推荐理由（渲染时整段消失）。判据：这条对律师办案有什么用（裁判规则/举证要点/抗辩思路/调解策略），写不出就说明该条不该进精选。

---

## 第一性原理

同一批法院公众号文章，走三层分流：

> **Tier 1 · 精读区**：k-NN 评分引擎挑 10 条精品 → 律师主动阅读
> **Tier 2 · 雷达区 + IMA**：低分≠消失，legal 未进精读的前 8 条进「其他领域速览」（雷达区）防闭门造车；score ≥ 6.5 法院源条目全量入库 IMA 做 RAG
> **Tier 3 · 噪音**：非 legal 源 + 非 court 源 + 未进 AI 精读的条目，自然落选

精读解决"本周重点看什么"，雷达区解决"执业圈外还有什么在动"，IMA 解决"以后能找到什么"。三层共享内容发现层，在评分环节分叉。

**核心交付模式**：「配置一次，每周自动推送」——依赖外部调度层（WorkBuddy Automation / GitHub Actions cron）定时触发。

---

## 分级架构

```
Level 0 · 5 分钟快速体验（零配置，零依赖）
  └─ 预置 10 条示范候选 → demo.py → 演示周报 MD+HTML

Level 1 · 纯评分引擎（零外部依赖）
  └─ 用户提供候选 URL 列表 → k-NN 评分排序 → 周报 MD+HTML

Level 2 · + IMA 知识库（需 IMA 账号）
  └─ Level 1 + ima_importer.py → 分类 → import_urls → 全量入库

Level 3 · + 自动发现（需微信读书账号 + 元宝账号）
  └─ 微信读书搜一搜（主）→ 元宝反查（补）双通道拉取四账号文章（TokenHub 已验证无内容，仅保留兼容）
```

---

## 快速开始

**生成演示周报**：在 WorkBuddy 对话中说「帮我用 legal-weekly-briefing 生成一份演示周报」。AI 自动运行 `demo.py`，生成 MD + HTML 两份文件。

**生成真实周报**：对话中说「帮我生成本周法律周报」。AI 自动搜索 → 构建候选 → 评分排序 → 交付。

**配置自己的周报**：对话中说「帮我配置法律周报」。AI 按适配向导引导你完成四问配置。

<details>
<summary>终端手动运行（备选）</summary>

```bash
cd ~/.workbuddy/skills/legal-weekly-briefing
python3 scripts/demo.py
```
</details>

---

## 标准执行流程（前置检查 → 三层通道 → 八判据评分 → 三层交付）

> 2026-07-29 MP 跨号接口关闭后确立的标准执行链路。每次真实周报按此流程：前置检查 → 通道拉取 → 构建 → 评分 → 交付。

### Step 0: 执行前置检查（强制，不可跳过）

Agent 必须先完成「执行前置检查」段落的三层通道检测 + 路径声明。
基于结果走后续分支：

```
L1 微信读书 ✓ → Step 1 (主通道，最佳质量)
L1 ✗ 且 L2 元宝 ✓ → Step 1 (元宝补充通道)
L1/L2 ✗ 且 L3 TokenHub ✓ → Step 1 (API 兜底通道，⚠️ 已验证无公众号内容，仅保留兼容)
三层全 ✗ → Agent 声明降级 → 跳过 Step 1-2，走 WebSearch 构建候选
```

### Step 1: 通道登录态就绪

```bash
# L1 微信读书（主通道）
python3 scripts/weread_login.py          # 扫码登录，保存 ~/.config/weread_state.json

# L2 元宝（补充通道）
python3 scripts/yuanbao_login.py         # 扫码登录，保存 ~/.config/yuanbao_state.json

# L3 TokenHub（⚠️ 已验证无公众号内容，仅保留代码兼容，不建议使用）
# 密钥文件：~/.config/tencentcloud/tokenhub_api_key
```

### Step 2: 拉取四号文章

```bash
# L1 微信读书搜一搜（主）：山东高法 / 上海一中法院 / 上海二中院 / 中国应用法学
python3 scripts/fetch_weread_week.py --days 7        # → mp_articles_weread.json

# L2 元宝反查（补）：缺失本号原文的条目反查 mp 直链
python3 scripts/fetch_yuanbao_supplement.py          # → yuanbao_links.json
python3 scripts/merge_candidates.py                  # → candidates_merged.jsonl（L1+L2 合并）

# L3 TokenHub（⚠️ 已验证无公众号内容，仅保留代码兼容，不建议使用）
python3 scripts/fetch_hunyuan_week.py --days 7       # → mp_articles.json
```

### Step 2.5: AI+法律动态补充（Agent WebSearch，防板块空置）

> ⚠️ L1/L2 只抓法院公众号（纯法律内容），**AI+法律板块没有自动内容源**——不补这一步，周报「AI + 法律」板块必空（2026-08-01 实测踩坑）。

- Agent 用 WebSearch 搜本周（近 7 天）AI+法律动态（法律大模型/智能体/法律科技/司法智能化）
- 选 **3 条**（与上一期周报已收录条目去重），按 AI+法律 4 维评分特征构建候选：
  - `category: "ai-legal"` + features：`signal_strength`（1 格局级/2 应用落地/3 融资动态）+ `depth` + `relevance` + `domestic_relevance`
  - digest 取搜索摘要（新闻稿），recommend 写律师视角实务价值（≥30 字）
- 追加到 `candidates_merged.jsonl` 后统一跑 pipeline

### Step 3: Agent 精修候选（内容过滤 → 跨期去重 → 摘要 → 推荐 → 特征，五步全做）

> **本步是内容质量的核心环节，不可跳过**。2026-08-01 实测：跳过本步（全自动直出）会同时出现 5 类问题（摘要文末片段/法条段、推荐理由全空、评分失真、非实务混入、跨期重复）。机器负责产候选，**Agent 负责精修**——只精修最终进周报的 ≤10 条，成本可控。对比分析见 `新渠道内容质量解决方案.md`。

**Agent 精修五步（顺序执行）**：

1. **内容过滤**：非实务类文章剔除——法院文体活动（"之旅""交流赛""运动会"）、互动庆祝（"百期""感谢有你""周年"）、征稿启事、法院建设/会议新闻、文化建设类。拿不准就剔除（Tier 3 噪音原则）。
2. **跨期去重**：读 `scripts/` 下最新一份 `周报_*.md`（+html）的 mp URL，按 `__biz/mid/idx/sn` 指纹剔除已收录文章（转载版 URL 不同，辅以标题级去重）。滚动 7 天窗口与上期天然重叠，不去重雷达区必重复。
3. **摘要（abstract）质量修复**：L1 digest（微信读书 desc）质量预筛——以"来稿/投稿/关注/点击/长按/扫描/更多信息"等文末特征词开头，或以《法条名》第X条句式开头（法条引用段）→ 低质，WebFetch 取正文开头 150-200 字（案情/内容提要）替换。⚠️ 中国应用法学【法官办案心得】文末固定带投稿须知、山东高法案例类易抽中法条段，重点检查。
4. **推荐理由（recommend）**：每条 ≥30 字律师视角实务价值（裁判规则/举证要点/抗辩思路/调解策略）。**写不出推荐理由 = 这条不该进精选**。
5. **特征标注（features）**：按 `feature-guide.md` 八判据逐条赋值（判据1案例密度→case_density，判据4作者实证→author_empirical_depth，判据7地域贴近→jurisdictional_proximity 等）。**features 为空 → k-NN 评分与内容无关**（2026-08-01 实测文体新闻得 7.3 分），必须标注。

### Step 4: 运行流水线 + 验证

```bash
# Level 1（WebSearch/手动构建）：输入 candidates.jsonl
PYTHONPATH=scripts python3 scripts/run_pipeline.py candidates.jsonl
# Level 3（L1+L2 自动发现）：输入 Step 2 合并产出的 candidates_merged.jsonl
PYTHONPATH=scripts python3 scripts/run_pipeline.py scripts/candidates_merged.jsonl
python3 scripts/verify.py  # 期望: 23 通过 / 0 失败
```

流水线 Stage 5 自动完成三层分流：
- **路径1**：taxonomy 关键词命中 → 直接写入 `ima_import_queue.jsonl`
- **路径2**：启发式规则命中 → 直接写入 `ima_import_queue.jsonl`
- **路径3**：均不命中 → 写入 `needs_llm_classify.jsonl`（由 Step 5 的 LLM 兜底分类后回填队列）

### Step 5: LLM 批量兜底分类（Agent 层，仅当 needs_llm_classify.jsonl 非空时触发）

若 `needs_llm_classify.jsonl` 非空，Agent 读取该文件 → 一次性将全部待分类标题传给 LLM →
LLM 返回分类结果 → Agent 按 taxonomy.yaml 映射 folder_id → 回填 `ima_import_queue.jsonl`。
**分类完成后清空 `needs_llm_classify.jsonl`。**

```bash
# Agent 检查是否有待分类队列
wc -l needs_llm_classify.jsonl
# 若 > 0，Agent 执行 LLM 批量分类，prompt 模板：
#   "对以下法律文章标题按 taxonomy.yaml 的 11 个分类归类，
#    输出 JSON: [{idx: 0, category: '公司'}, ...]"
# 结果回填后 Agent 追加到 ima_import_queue.jsonl
# 分类完成后：
> needs_llm_classify.jsonl  # 清空已处理队列
```

### Step 6: IMA 入库（消费队列，强制执行）

流水线和 LLM 分类完成后，`ima_import_queue.jsonl` 中所有条目必须实际导入 IMA 知识库。

Agent 执行：
1. 检查 `taxonomy.yaml` 的 `knowledge_base_id` ≠ `YOUR_KNOWLEDGE_BASE_ID`（占位符时阻断，提示用户先配置）
2. 读取 `ima_import_queue.jsonl`，按 `folder_id` 分组
3. 逐组调用 **ima-skill（OpenAPI）** 的 `import_urls`（knowledge_base_id + folder_id + urls[]，单次 ≤10 条）——⚠️ `taxonomy.yaml` 的 KB_ID/folder_id 是 **OpenAPI 体系**（`~/.config/ima/client_id` + `api_key` 凭证），ima-mcp 连接器是另一套 ID，不通用。执行方式：`cd ~/.workbuddy/skills/ima-skills && node ima_api.cjs "openapi/wiki/v1/import_urls" '{...}'`
4. 导入成功 → 调用 `reset_queued_cache()` 清空去重缓存
5. 导入成功 → 截断 `ima_import_queue.jsonl`（消费完成，清空队列）
6. 输出汇总：「已入库 X 条 / 跳过重复 Y 条 / 失败 Z 条」

```bash
# Agent 读取队列 → 调用 IMA MCP
# import_urls 单次最多 10 条 URL，超过分批
# 导入完成后：
python3 -c "import sys; sys.path.insert(0,'scripts'); from ima_importer import reset_queued_cache; reset_queued_cache()"
> /dev/null 2>&1 ima_import_queue.jsonl  # 截断已消费队列
```

---

## 适配向导（4 问流程）

> 用户表达「想配置法律周报」意图时，Agent 必须主动引导。完整话术和分支逻辑见 `references/adaptation-wizard.md`。

| 问次 | 主题 | 决定 | Agent 关键动作 |
|------|------|------|--------------|
| 1 | 执业方向 | `interest_keywords` + taxonomy priority | 写入 settings.yaml；告知「兴趣赛道加成 +0.3 分」 |
| 2 | 关注公众号 | `sources.yaml` | 保留四个示范公众号默认；追加用户指定的公众号 |
| 3 | 微信读书账号 | 是否启用 Level 3 主通道 | 有 → 引导微信读书扫码配置（见 `references/weread-setup-guide.md`）；无 → 保持 WebSearch 模式 |
| 4 | IMA 知识库 | 是否启用 Level 2 | 有 → 先确认「自建个人 KB」（铁律检查）→ 引导获取 KB_ID/folder_id/API 凭证；无 → 保持 Level 1 |

**只想要 Level 1**：在 Agent 问完前两问后告知，Agent 跳过第三、四问。

---

## Level 1 · 纯评分引擎

### 核心工作流

```
用户说「帮我生成本周法律周报」
  → Agent 搜索近一周法律动态 + 法院公众号文章
  → 构建 candidates.jsonl（含 abstract + recommend）
  → run_pipeline.py（去重 → k-NN 评分排序 → MD + HTML）
  → present_files 交付周报
```

### k-NN 评分引擎 v3.0

**法律条目（7 维评分 + 1 维雷达）**

| 维度 | 权重 | 取值 | 说明 |
|------|------|------|------|
| case_density | 0.18 | 1-3 | 1=有具体案例+裁判要旨, 2=提案例无细节, 3=无案例 |
| norm_anchoring | 0.18 | 1-3 | 1=入库案例/司法解释/法条原文, 2=有法条引用, 3=无规范锚定 |
| actionability | 0.18 | 1-3 | 1=可直用裁判规则, 2=有分析需提炼, 3=只描述问题不給解法 |
| author_empirical_depth | 0.16 | 1-3 | 1=审级高+论证深(至正系列), 2=有实证论证(中院法官), 3=泛泛而谈 |
| framework_quality | 0.12 | 1-3 | 1=先定法域框架再填内容, 2=有结构不清, 3=直接堆材料 |
| relevance_halflife | 0.10 | 1-3 | 1=基础方法永不过时, 2=中期价值, 3=前沿快过时 |
| jurisdictional_proximity | 0.15 | 0/1 | 1=浙江/金华/永康法官, 0=其他（2026-08-01 上调，本地规则预判价值） |

> ⚠️ **金华锚点积累（2026-08-01）**：prox 维度生效依赖训练集里的金华样本（当前 0 条，演示验证有锚点时 prox=1 高 0.5 分）。每周周报遇到浙江/金华/永康法院的文章 → 标注 `jurisdictional_proximity: 1` 注入训练集；用户本地办案案例也可手动注入。无锚点时 prox 维度不参与 k-NN 区分（权重已生效，等锚点）。
| ~~执业视野提醒~~ | — | — | 不进评分，雷达区实现 |

> 老四维（author_tier/platform_tier/depth/relevance）已废弃，权重置 0.00，保留仅为兼容旧训练集。

**AI+法律条目（4 维有效）**

| 维度 | 权重 | 1 | 2 | 3 |
|------|------|---|---|---|
| signal_strength | 0.50 | 格局级（大厂入局/旗舰模型/监管） | 应用落地级 | 融资动态级 |
| depth | 0.25 | 有具体功能细节+分析 | 有具体分析 | 新闻/综述 |
| relevance | 0.15 | 直接对标国内律师实务 | 有一定参考 | 泛行业资讯 |
| domestic_relevance | 0.10 | 国内可借鉴=1 | 不适用=0 | — |

### 评分锚定（v3）

| 分数 | 法律条目锚点 | AI+法律条目锚点 |
|------|-------------|----------------|
| 9-10 | 入库案例+裁判要旨(case=1,norm=1,action=1) 或司法解释直接发布 | signal_strength=1 格局级 + depth=1 |
| 8-8.9 | 至正系列(author=1,frame=1) / 入库案例(非主攻) / 中院法官+良好框架 | signal_strength=2 应用落地级 |
| 7-7.9 | 法官办案心得(中院/基层) / 分析深度一般 / 非核心执业方向 | 行业动态有参考 |
| 5-6 | 纯新闻/会议综述 / 无案例+无规范锚定+无框架 | signal_strength=3 融资动态级 |

### 法律条目补充规则

1. **入库案例**：case_density=1 + norm_anchoring=1 + actionability=1 → 基准 9.0
2. **至正系列**：author_empirical_depth=1 + framework_quality=1 → 基准 8.2+
3. **法官办案心得**：按审级分 — 中院 7.7-8.0，基层 7.4-7.7
4. **非主攻方向**：刑事/知产/行政/环境 → 常规扣 0.5-1

### 降级行为

| 场景 | 行为 |
|------|------|
| 无训练集 | 七维线性降级 + confidence=0，不崩 |
| 候选不足 10 | run_pipeline 非零退出 |
| 训练集为老四维映射 | `_map_old_features_to_v3()` 自动转换，精度待人工校准 |

### 已知限制

- 训练集 91 条：70 条老四维映射近似 + 21 条真实 v3 样本（2026-08-01 注入，经用户逐条验收）——v3 空间已有点，k-NN 置信度随真实样本累积持续提升（每周跑完沉淀新样本）
- 摘要生成依赖 WebFetch + 人工，不适合全量自动化
- 兴趣赛道加成（+0.3）在 `settings.yaml` 的 `interest_keywords` 中配置

> 特征标注速查、训练数据替换指引 → `references/feature-guide.md`

---

## Level 2 · IMA 知识库入库

> 完整指南、接入链路、踩坑速查 → `references/ima-level2-guide.md`

**前置条件**：Level 1 验证通过 + IMA 账号 + API 凭证已配。

**工作原理**：`run_pipeline.py` 产出 `ima_import_queue.jsonl` → 按 `taxonomy.yaml` 关键词分配 folder_id → 调用 IMA OpenAPI `import_urls` 入库。

**周报 vs IMA vs 雷达区**（三层分流）：
- **精读区（Tier 1）**：diversity-aware 选 10 条，同源≤2，进 MD 周报 + HTML 卡片区
- **IMA 入库（Tier 2 之一）**：score ≥ 6.5 法院源条目全部入库，不限条数
- **雷达区（Tier 2 之二）**：legal 未进精读前 7 的条目进 HTML「其他领域速览」（最多 8 条，低分条做低调视觉标记）
- **噪音（Tier 3）**：非 legal 源 + 非 court 源 + 未进 AI 精读的条目，不显示不进库

**分类规则**：10 个分类，按优先级排序——专业领域（建筑工程/劳动法/交通事故 priority=9）高于通用兜底（合同借贷 priority=8），避免"劳动合同"被"合同"误捕获。

**IMA 铁律**：仅使用用户自建个人知识库；`knowledge_base_id` 占位符未替换时导入自动阻断。

---

## Level 3 · 微信读书搜一搜 + 元宝 + TokenHub 三层通道

> 完整配置指南 → `references/weread-setup-guide.md`（微信读书，主）· `references/yuanbao-setup-guide.md`（元宝，补）· `references/mp-setup-guide.md`（旧 MP 通道，已 DEPRECATED）

**前提条件**：微信读书账号（主通道，扫码即可）+ 腾讯元宝账号（补充通道）。

**原理**：2026-07-29 微信关闭 MP 跨号文章接口后，公开 API（腾讯云 WSA、TokenHub 等）因版权不含公众号内容。微信读书网页版「搜一搜」是唯一能返回 mp.weixin.qq.com 原文直链的免费通道；元宝产品端有微信内容生态授权，可反查缺失的本号原文。TokenHub 已验证无公众号内容，仅保留代码兼容（见 references/mp-setup-guide.md 历史记录）。

**三层通道分工**：
- **L1 微信读书（主）**：`fetch_weread_week.py` 搜 4 号近 7 天文章 → `mp_articles_weread.json`
- **L2 元宝（补）**：`fetch_yuanbao_supplement.py` 对 `__biz` 指纹不匹配（缺失本号原文）的条目反查 → `merge_candidates.py` 合并 → `candidates_merged.jsonl`
- **L3 TokenHub（⚠️ 已排除）**：`fetch_hunyuan_week.py` 已验证无公众号内容（P3 验收结论），仅保留代码兼容，不建议使用

**替代方案**（无微信读书账号）：WebSearch 手动发现 → 整理 `candidates.jsonl` → 评分；或纯依赖 `legal-hot` skill。

---

## 周报交付格式

标题: `# 法律周报 2026年X月X日-X月X日 · 第N期`

三板块（按评分降序）：
```
## AI + 法律
【9.5】标题 | URL | 描述（含信号级别）

## 纯法律
【9.0】标题 | URL | 描述（含领域标签）

## 其他领域速览（雷达区）
【6.5】标题 | URL | 描述（执业圈外动态，低分≠消失）
```

页脚：引擎版本 + 通道状态（weread/yuanbao/tokenhub）+ IMA 导入统计 + 排除清单。

---

## 交付门禁

> 完整门禁清单、四条铁律、违规案例 → `references/delivery-gate.md`

| 编号 | 检查项 | 级别 | 说明 |
|------|--------|------|------|
| G1 | `render_html.py` 存在且可导入 | P0 | 文件缺失即阻塞 |
| G2 | 模板风格 = `#f8f7f5` + `#1a1a2e`，无翻页 JS | P0 | 样式不符即阻塞 |
| G3 | 模板含 `abstract`/`recommend`/`fav-btn` | P0 | 缺字段即阻塞 |
| G4 | `demo.py` 候选含 `abstract`/`recommend` | P0 | 示范数据不完整即阻塞 |
| G5 | `run_pipeline.py` 含 HTML 渲染步骤 | P0 | 流水线缺步骤即阻塞 |
| G6 | `taxonomy.yaml` 的 `knowledge_base_id` 非作者/他人 KB | P0 | 作者 KB → 阻断；占位符 → 警告 |
| G7 | `render_html.py` 的 `radar_score_ceiling` 从 `settings.yaml` 读取 | P0 | 硬编码 → 阻塞 |

```bash
python3 scripts/verify.py
# 期望: "23 通过 / 0 失败" → exit code 0
```

---

## 外部依赖

| 依赖 | 说明 |
|------|------|
| 微信读书账号 | L1 主通道，`weread_login.py` 扫码（无需会员） |
| 腾讯元宝账号 | L2 补充通道，`yuanbao_login.py` 扫码 |
| TokenHub API 密钥 | L3 兜底，`~/.config/tencentcloud/tokenhub_api_key`（实测无公众号内容） |
| IMA OpenAPI 凭证 | `~/.config/ima/client_id` + `api_key` |
| pyyaml | Python 包，`pip3 install pyyaml` |
| Python 3.9+ | 脚本运行环境 |

---

## 安全与隐私

- **IMA 知识库**：文章导入的是**你自己的知识库**，不在第三方服务器上
- **通道登录态**：`~/.config/weread_state.json`（微信读书）与 `~/.config/yuanbao_state.json`（元宝）仅存储本地，**绝对不要分享或提交到 Git**（`.gitignore` 已排除）
- **API 凭证**：`client_id` / `api_key` 仅请求 IMA 官方 API（`ima.qq.com`），不发送到其他服务器

### 绝对不要分享

| 文件 | 风险 | 防护 |
|------|------|------|
| `~/.config/weread_state.json` | 含微信读书完整登录态（微信授权） | `.gitignore` 已排除（`we*.json`） |
| `~/.config/yuanbao_state.json` | 含元宝登录态（微信授权） | `.gitignore` 已排除（`*.state.json`） |
| `~/.config/tencentcloud/tokenhub_api_key` | API 密钥，可消耗配额 | 位于 home 目录，不进代码 |
| `~/.config/ima/client_id` + `api_key` | 他人可向你的 IMA 知识库写入 | 仅本地存储 |
| `config/.env` | 可能含 API 密钥 | `.gitignore` 已排除 |

---

## References 索引

| 文件 | 内容 |
|------|------|
| [`references/feature-guide.md`](references/feature-guide.md) | 特征标注速查 + 训练数据替换指引 + 石头评分八判据（v2.0） |
| [`references/评分体系维护指南.md`](references/评分体系维护指南.md) | 评分标准怎么来（人机协作标注法）+ 加新号/校准操作清单 |
| [`references/adaptation-wizard.md`](references/adaptation-wizard.md) | 适配向导 4 问流程（Agent 话术 + 分支逻辑） |
| [`references/ima-level2-guide.md`](references/ima-level2-guide.md) | IMA Level 2 完整指南（接入链路 + 分类规则 + 踩坑表） |
| [`references/ima-pitfalls.md`](references/ima-pitfalls.md) | IMA 接入踩坑卡（7 坑速查 + 接入链路图） |
| [`references/mp-setup-guide.md`](references/mp-setup-guide.md) | ~~MP 自动发现完整配置~~ **⚠️ DEPRECATED 2026-07-29**（微信关闭跨号接口，仅供历史参考） |
| [`references/weread-setup-guide.md`](references/weread-setup-guide.md) | 微信读书搜一搜配置（主通道：登录/抓取/登录态管理/常见失败） |
| [`references/yuanbao-setup-guide.md`](references/yuanbao-setup-guide.md) | 元宝反查配置（补充通道：登录/反查/合并/常见失败） |
| [`references/delivery-gate.md`](references/delivery-gate.md) | 交付门禁卡（23 项核查 + 铁律 + 违规案例） |
| [`references/automation-setup.md`](references/automation-setup.md) | 自动化调度配置（WorkBuddy / GitHub / cron） |

---

## 打包结构

```
legal-weekly-briefing/
├── SKILL.md                         ← 本文件
├── scripts/                         ← 评分引擎 + 流水线 + 渲染 + 验证
├── assets/config/                   ← settings.yaml / sources.yaml / taxonomy.yaml
├── assets/data/                     ← 训练样本 + 回归用例
└── references/                      ← 详细指南（10 个文件）
```

## Rationalizations

1. **分级架构**：四级独立运行，上层依赖下层，降低开源用户门槛
2. **k-NN 选型**：7+1 维特征向量可解释（法律七维评分 + 雷达区视野提醒），训练数据可替换，降级不崩
3. **IMA 独立管道**：周报精选 ≠ IMA 全量，各自优化目标不同
4. **三层通道**：微信读书搜一搜（mp 直链，主）+ 元宝反查（本号原文，补）+ TokenHub（API 兜底）；2026-07-29 微信关闭 MP 跨号接口后确立
5. **门禁驱动**：verify.py 23 项检查保证交付一致性，评分回归测试 ≠ 交付质量保证

## 配置指南（零基础版）

> 用户说「配置法律周报」时触发此段。按 Level 逐级引导，每级完成后再问是否升级。

### Level 1 · 纯评分（零配置，2 分钟可用）
用户只需说「帮我生成本周法律周报」→ Agent 自动 WebSearch → 评分排序 → 交付。
**无需任何配置**。唯一可选：告诉 Agent 你的执业方向（如「建筑工程」），评分会自动加成 +0.3 分。

### Level 2 · + IMA 知识库（需 5 分钟配置）
**需要什么**：IMA 账号（ima.qq.com 注册，免费）+ 自建个人知识库。
**怎么做**：① 登录 IMA → 左侧「知识库」→「新建」→ 记住名称 ② 打开 IMA 开发者设置 → 复制 `client_id` 和 `api_key` ③ 在知识库设置 → 复制 `knowledge_base_id`（一串数字）④ 把这些值告诉 Agent → Agent 写入配置 → 完成。
**效果**：每周评分 ≥ 6.5 的文章自动入库，以后可检索。

### Level 3 · + 自动发现（需微信读书账号，10 分钟配置）
**需要什么**：微信读书账号（App 或网页版均可，免费，不需要会员）。
**怎么做**：① 微信读书 App 或 weread.qq.com 用微信登录即可 ② 跑 `python3 scripts/weread_login.py` → 浏览器弹出 → 扫码 → 登录态自动保存（约 10 天~数周有效）③ 跑 `python3 scripts/fetch_weread_week.py --days 7` 自动拉取 4 个号的文章。
**效果**：不再需要手动搜文章，Agent 自动从 4 个法院公众号拉取（每周可定时自动跑）。
**可选补充**：再配置元宝（`yuanbao_login.py`）开启 L2 反查，覆盖微信读书漏掉的「本号原文」。

### 常见问题
- **没有微信读书账号**：直接用 Level 1，Agent 用 WebSearch 搜索文章，效果类似
- **微信读书搜不到某号**：该号可能未被微信读书收录（少见），由元宝反查或 WebSearch 兜底
- **IMA 注册不了**：跳过 Level 2，周报功能完全不受影响
- **不想装 Python 包**：Agent 会帮你装 `pip3 install pyyaml`，一行命令
