---
name: prc-legal-research-law-search
description: Use when 用户需要检索、定位或核验中国大陆法律、行政法规、司法解释、部门规章及规范性文件，尤其是法规名称、具体条款、效力状态或自然语言法律问题。
metadata:
  version: 1.2.0
  compatibility: 元力平台 SkillHub；需要可访问 yuandian-law MCP 和有效的元典开放平台凭据
  author: 华宇元典
  argument-hint: '[法规名 + 条款号 | 主题关键词 | 自然语言问题]'
  variant: Yuanli platform MCP, no-Web
---

# 中国法律条文检索

## 适用范围（先读）

本 skill 通过 `legal_research.search_laws` / `legal_research.fetch_law` capability 接入元典法律法规库（`yuandian-law` MCP），**仅中国大陆法适用**。

## 元力平台 MCP 连接门禁（前置）

触发本 Skill 后必须先检查 `yuandian-law` 是否实际连通，不能只根据配置记录判断。

1. 按 [references/mcp-onboarding.md](references/mcp-onboarding.md) 执行能力发现和只读最小探测。
2. 按 [references/tool-contract.md](references/tool-contract.md) 选择工具，但参数和必填项始终以运行时工具模式为准。
3. 缺少平台绑定时返回 `NOT_CONFIGURED`，不得由普通会话改写全局配置或重启服务。
4. 连接状态只能是 `READY`、`NOT_CONFIGURED`、`AUTH_FAILED`、`NETWORK_FAILED`、`CAPABILITY_MISSING`、`RATE_LIMITED` 或 `UNKNOWN_FAILURE`。
5. 只有 `READY` 才能继续检索；其余状态停止并给出可执行的修复提示。

## 数据源硬边界

本 Skill 唯一允许的数据源是 `yuandian-law` MCP。MCP 配置、连通性、鉴权或调用失败后必须停止。

严禁使用 Web Search、网页搜索、搜索引擎、浏览器检索、第三方网站或模型记忆替代元典检索。即使用户要求“先上网搜”“凭记忆回答”“先给大概条文”或任务紧急，也不能绕过此边界。

**不要在以下场景使用本 skill：**

- **美国法等非中国大陆法事项**：本 skillpack 不覆盖；请走当地商业法律研究服务（Westlaw / LexisNexis / CoCounsel 等）或当地律所。
- **其他法域**（EU / UK / HK / Singapore 等）：当前本 cluster 不覆盖；建议使用对应区域法律研究工具。
- **港澳台地区**：本 skill 默认基于中国大陆法律体系，港澳台不在元典覆盖范围。
- **起草法律文件、表格或模板** — 超出本 skill 范围。
- **执行具体任务的指令** — 超出本 skill 范围。
- **穷举式检索**（如"找出所有讨论 XX 的法条"） — 元典 MCP 有返回数量限制，无法保证穷举。
- **需要综合分析法律问题、输出研究报告** — 建议使用 `prc-legal-research-deep-research`。
- **需要查找案例判决** — 建议使用 `prc-legal-research-case-search`。
- **需要查询企业信息** — 建议使用 `prc-legal-research-company-search`。

## 前置条件 / 连接器探测

`legal_research.search_laws` capability（实际由 `yuandian-law` MCP 提供）必须实际连通才能运行。未连通时按上方状态门禁停止并报告。

**严禁仅凭配置文件声明就认为连接器可用**——必须实际探测一次轻量级 capability（如 list / health-check）成功后才往下走。失败标 `[连接器未核验]` 并停止：

```text
元典法律检索工具连接或探测失败，本次检索已停止。请根据状态检查平台绑定、API 凭据、订阅和网络后重试；
不会改用 Web Search 或模型记忆。订阅与凭据问题联系数据源方（元典开放平台
https://open.chineselaw.com/，支持邮箱 yuandianzonghe@thunisoft.com）。
```

## 第一步：分析查询意图

从对话上下文中获取用户的查询需求，无需用户重复输入。分析用户的需求，确定检索策略：

**精确查询**（已知条款位置）：
- 用户提供了法规名称 + 条款号 → 直接调用 `legal_research.fetch_law`（对应元典 `yuandian_rh_ft_detail`）。
- 用户提供了法规名称但未指定条款 → 调用 `legal_research.search_laws`（对应 `yuandian_rh_ft_search`）或 `yuandian_rh_fg_detail` 获取全文。

**主题检索**（需要按内容查找）：
- 提炼核心关键词（如"纳税义务发生时间""违约金调整""股东知情权"）。
- 确定筛选条件：`sxx="现行有效"`（默认优先），`xljb_1` 效力级别。

**比较检索**（多法规对比）：
- 优先使用语义检索 `yuandian_law_vector_search` 发现跨法规相关条文。

## 第二步：执行检索

### 工具选择矩阵

| 场景 | 首选 MCP 工具 | 补充工具 |
|------|--------------|----------|
| 已知法规名称 + 条款号 | `yuandian_rh_ft_detail` | `yuandian_rh_fg_detail` 查上下文 |
| 已知法规名称，找相关条款 | `yuandian_rh_ft_search`（fgmc=法规名） | `yuandian_rh_fg_detail` |
| 主题关键词检索 | `yuandian_rh_ft_search`（sxx=现行有效） | `yuandian_law_vector_search` |
| 关键词检索结果 < 3 条相关条文 | `yuandian_law_vector_search` | — |
| 跨法规比较 / 模糊描述 | `yuandian_law_vector_search` | `yuandian_rh_ft_search` |
| 需要法规完整上下文 | `yuandian_rh_fg_detail` | — |

### 关键词检索 vs 语义检索使用原则

- **关键词检索**：已知具体法规名称 / 法条号，或已提取出精确术语。
- **语义检索**：问题模糊、口语描述、术语不确定，或需发现跨法规潜在相关条文。
- **关键词召回 < 3 条相关结果时**，降级到语义检索补充。

### MCP 工具说明

**`yuandian_rh_ft_search`** — 法条关键词检索
- 参数：`keyword`（必填）、`sxx`（时效性，默认"现行有效"）、`xljb_1`（效力级别）、`fgmc`（法规名过滤）、`top_k`（默认 10）。
- 返回：法条列表，每条含 `llm_content`（格式：`"- 《法规名》条款号##内容"`）。

**`yuandian_rh_ft_detail`** — 法条详情
- 参数：`fgmc`（法规名）+ `ftnum`（条款号，如"第一百条"），或 `id`。
- 返回：法条原文、时效状态、效力级别、发布日期。

**`yuandian_law_vector_search`** — 法条语义检索
- 参数：`query`（自然语言描述）、`sxx`（列表，如 `["现行有效"]`）、`return_num`（默认 20）。
- 返回：按语义相似度排序的法条列表，每条含 `score`。

**`yuandian_rh_fg_search`** — 法规关键词检索
- 参数：`keyword`、`sxx`、`xljb_1`、`top_k`。

**`yuandian_rh_fg_detail`** — 法规全文
- 参数：`fgmc`（法规名）或 `id`，可选 `refer_date`（参考日期）。

## 第三步：输出结果

以清晰格式在对话中直接呈现，**无需保存文件**。

### 单条 / 少量条文格式

```
《{法规全名}》{条款号}
{条文原文（完整）}

时效状态：现行有效 / 失效 / 已被修改 / 部分失效
效力级别：法律 / 行政法规 / 部门规章 / 司法解释 / ...
发布日期：YYYY-MM-DD  |  施行日期：YYYY-MM-DD
发布机关：{机关名称}
```

### 多条命中格式

按以下优先级排序：
1. 效力级别高的优先（法律 > 行政法规 > 部门规章 > 司法解释 > 部委文件 > 地方法规）。
2. 同效力级别内，现行有效的优先于失效。
3. 相关度高的优先。

每条保持上述单条格式，条与条之间用分隔线隔开。

### 失效 / 已修改的处理

如检索到的法条已失效或已被修改，**必须明确标注**，并尝试检索当前有效版本：

```
⚠️ 注意：《{法规名}》已于 {日期} 失效 / 修改
当前有效规定见：《{新法规名}》{条款号}
{新条文内容}
```

### 语义检索结果

语义检索结果附上相似度分数（score）供参考，score 越高越相关：

```
（语义相似度：{score:.3f}）
《{法规名}》{条款号}
{条文内容}
```

## 来源标签三级分级

- `[settled - 元典法规 YYYY-MM-DD 确认]`：稳定主条款（如《民法典》《刑法》总则条款）经 MCP 实际返回且对照当前日期已确认现行有效。YYYY-MM-DD 为本次检索日期。
- `[元典法规]`：本会话内通过 `legal_research.search_laws` / `legal_research.fetch_law` capability 实际返回的条文，但未对照日期戳。这是默认标签。
- `[verify - 需对照元典原文]`：检索命中但仍需用户对照原文核实的内容（如 ad-hoc 主题检索召回的边缘条文）。

## 工作约束

- **不编造条文**：所有条文必须来自 MCP 工具实际返回结果；未检索到或 MCP 失败时如实说明并停止。
- **时效优先**：优先呈现 `sxx=现行有效` 的条文，失效条文需明确标注。
- **效力层级**：呈现多条结果时说明各条文的效力级别关系。
- **歧义处理**：同名法规有多个版本时，优先返回现行有效版本，并注明版本信息。
- **来源标签**：只对 MCP 实际返回的条文使用上述元典来源标签。

## 工作成果头部

按 profile 中角色 + 法域决定：

- 律师 + 美国法上下文：`PRIVILEGED & CONFIDENTIAL — ATTORNEY WORK PRODUCT — PREPARED AT THE DIRECTION OF COUNSEL`（**本 skill 是中国法 cluster，不适用**）
- 律师 + 中国法：`保密 / 内部法律分析 — 仅供法务团队使用 — 不构成外发法律意见`
- 非律师：`研究笔记 / 内部记录 — 不构成法律意见 — 请律师复核后再依赖`

外发给业务方 / 客户的版本去工作成果头。

## 非律师门

法条检索本身是事实查询（"该法规如何规定"），不必每次都触发非律师门。但当用户**基于本 skill 检索的条文做具体决策**（出具法律意见、向监管机构提交、起草诉讼文件、客户回函等）时，先 surface：

```text
本 skill 返回的法律条文是研究材料——汇集了元典法规库的现行规定。
它不是对你具体事实的法律意见。

如果计划基于这些条文做具体决策（给客户回函、监管提交、诉讼起草），
是否已与律师 / 有执业资格的法律人员复核过？
- 是：明确确认后继续
- 否：建议先与律师复核条文在你具体场景下的适用与边界
```

## 交接

- 用户问题超出单条法律条文检索 → `prc-legal-research-deep-research`（8 阶段研究备忘录）。
- 涉及案例 → `华宇元典-案例研究`。
- 涉及企业信息 → `华宇元典-企业信息查询`。
- 用户问题涉及业务场景（合同 / 隐私 / 监管 / 用工） → 对应 cluster 的 review skill，配合本 skill 的法条检索作为支撑：
  - 商事合同：`commercial-contract-review` 等。
  - 数据隐私：`privacy-use-case-triage` / `privacy-reg-gap-analysis` 等。
  - 监管合规：`regulatory-policy-diff` / `regulatory-gap-surfacer` 等。
  - 劳动用工：`employment-termination-review` / `employment-wage-hour-qa` 等。

## 本 skill 不做的事

- 不对美国法或其他非中国大陆法事项使用——非中国大陆法事项请走当地商业法律研究服务或当地律所。
- 不在 `legal_research.search_laws` capability 不可达时尝试用模型知识"模拟"检索。
- 不使用 Web Search、浏览器、第三方网站或模型记忆替代元典 MCP。
- 不编造条文、不伪造时效状态、不虚构发布日期。
- 不替代律师做具体事实下的法律判断。
- 不保留 Claude 专属配置路径。
- 不要求用户调用 Claude slash command。

## 数据来源

- MCP server：`yuandian-law`（http stream，订阅管理）
- MCP URL：`https://open.chineselaw.com/mcp/law/stream`
- 数据来源：元典开放平台（北京华宇元典信息服务有限公司）
- API 文档：https://open.chineselaw.com/
- 支持邮箱：yuandianzonghe@thunisoft.com
