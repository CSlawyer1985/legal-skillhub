---
name: prc-legal-research-case-search
description: Use when 用户需要按案号、案由、关键词、法院、裁判时间或自然语言事实检索中国大陆公开裁判文书、指导性案例和典型案例。
metadata:
  version: 1.2.0
  compatibility: 元力平台 SkillHub；需要可访问 yuandian-case MCP 和有效的元典开放平台凭据
  author: 华宇元典
  argument-hint: '[案号 | 主题关键词 | 自然语言事实描述]'
  variant: Yuanli platform MCP, no-Web
---

# 中国裁判文书检索

## 适用范围（先读）

本 skill 通过 `legal_research.search_cases` / `legal_research.fetch_case` capability 接入元典案例库（`yuandian-case` MCP），**仅中国大陆法院裁判文书**。

## 元力平台 MCP 连接门禁（前置）

触发本 Skill 后必须先检查 `yuandian-case` 是否实际连通，不能只根据配置记录判断。

1. 按 [references/mcp-onboarding.md](references/mcp-onboarding.md) 执行能力发现和只读最小探测。
2. 按 [references/tool-contract.md](references/tool-contract.md) 选择工具，但参数和必填项始终以运行时工具模式为准。
3. 缺少平台绑定时返回 `NOT_CONFIGURED`，不得由普通会话改写全局配置或重启服务。
4. 连接状态只能是 `READY`、`NOT_CONFIGURED`、`AUTH_FAILED`、`NETWORK_FAILED`、`CAPABILITY_MISSING`、`RATE_LIMITED` 或 `UNKNOWN_FAILURE`。
5. 只有 `READY` 才能继续检索；其余状态停止并给出可执行的修复提示。

## 数据源硬边界

本 Skill 唯一允许的数据源是 `yuandian-case` MCP。MCP 配置、连通性、鉴权或调用失败后必须停止。

严禁使用 Web Search、网页搜索、搜索引擎、浏览器检索、裁判文书网、第三方网站或模型记忆替代元典检索。即使用户要求“先上网找案号”“凭记忆给案例”“只查法院官网”或任务紧急，也不能绕过此边界。

**不要在以下场景使用本 skill：**

- **美国法案例 / 其他非中国大陆法案例**：本 skillpack 不覆盖；请走当地商业法律研究服务（Westlaw / LexisNexis / CoCounsel 等）或当地律所。
- **其他法域**（EU / UK / HK / Singapore 等）：不覆盖。
- **港澳台地区**：不在元典覆盖范围。
- **仲裁机构作出的裁决**（如 CIETAC、ICC、各地仲裁委）：不在覆盖范围。
- **劳动仲裁机构作出的裁决**：不在覆盖范围。
- **起草法律文件、表格或模板** — 超出本 skill 范围。
- **执行具体任务的指令** — 超出本 skill 范围。
- **穷举式检索**（如"找出所有讨论 XX 的案件"） — 元典 MCP 有返回数量限制，无法保证穷举。
- **需要查找法律条文** — 建议使用 `prc-legal-research-law-search`。
- **需要综合分析法律问题、输出研究报告** — 建议使用 `prc-legal-research-deep-research`。
- **需要查询企业信息** — 建议使用 `prc-legal-research-company-search`。

## 前置条件 / 连接器探测

`legal_research.search_cases` capability（实际由 `yuandian-case` MCP 提供）必须实际连通才能运行。未连通时按上方状态门禁停止并报告。

**严禁仅凭配置文件声明就认为连接器可用**——必须实际探测一次轻量级 capability 成功后才往下走。失败标 `[连接器未核验]` 并停止：

```text
元典案例检索工具连接或探测失败，本次检索已停止。请根据状态检查平台绑定、API 凭据、订阅和网络后重试；
不会改用 Web Search、裁判文书网或模型记忆。订阅与凭据问题联系数据源方（元典开放平台
https://open.chineselaw.com/，支持邮箱 yuandianzonghe@thunisoft.com）。
```

## 第一步：分析查询意图

从对话上下文中获取用户的查询需求，无需用户重复输入。

**已知案号**：
- 直接调用 `yuandian_rh_case_details`（`type="ptal"`），若无结果再试 `type="qwal"`。

**主题案例检索**：
- 提炼案件关键词（案由、争议焦点、特殊事实情节）。
- 确定筛选条件：
  - `ajlb`：案件类别（民事案件 / 刑事案件 / 行政案件 / 执行案件）。
  - `wszl`：文书种类（判决书 / 裁定书 / 调解书）。
  - `xzqh_p`：省级行政区。
  - `ja_start` / `ja_end`：裁判日期范围。

**权威案例优先**：
- 用户提到"指导性案例" / "典型案例"或需要最权威判例时，优先调用 `yuandian_rh_qwal_search`。

**事实相似判例**：
- 用户描述较复杂的事实情形，难以提炼精确关键词时，使用 `yuandian_case_vector_search`。

## 第二步：分层检索

### 工具选择矩阵

| 场景 | 首选 MCP 工具 | 补充工具 |
|------|--------------|----------|
| 已知案号，需全文 | `yuandian_rh_case_details`（type=ptal） | `yuandian_rh_case_details`（type=qwal） |
| 权威案例（指导性 / 典型） | `yuandian_rh_qwal_search` | `yuandian_case_vector_search`（dianxing=true） |
| 主题关键词检索（无权威要求） | `yuandian_rh_qwal_search`（先）→ `yuandian_rh_ptal_search`（扩展） | `yuandian_case_vector_search` |
| 关键词检索结果 < 3 条相关案例 | `yuandian_case_vector_search` | — |
| 事实相似判例 | `yuandian_case_vector_search` | `yuandian_rh_ptal_search` |
| 按援引法条查案例 | `yuandian_rh_ptal_search`（yyft=["法条全称"]） | `yuandian_rh_qwal_search` |

### 检索顺序（硬性）

1. **权威案例优先**：先调用 `yuandian_rh_qwal_search` 获取指导性 / 典型案例。
2. **普通案例扩展**：调用 `yuandian_rh_ptal_search` 扩大样本量。
3. **语义补充**：若以上两步相关结果 < 3 条，调用 `yuandian_case_vector_search` 补充。

不允许跳过权威案例直接走普通案例 / 语义检索——除非用户明确不需要权威案例。

### MCP 工具说明

**`yuandian_rh_qwal_search`** — 权威案例关键词检索（指导性 / 典型案例）
- 参数：`qw`（全文关键词）、`ay`（案由）、`ajlb`（案件类别）、`ja_start` / `ja_end`（日期范围）、`top_k`。
- 返回：`{"total": int, "lst": [...]}`，取 `lst` 前先检查 `total > 0`。

**`yuandian_rh_ptal_search`** — 普通案例关键词检索
- 参数：`qw`、`fxgc`（分析过程关键词）、`ajlb`、`wszl`、`xzqh_p`、`yyft`（援引法条列表）、`top_k`。
- 返回：`{"total": int, "lst": [...]}`。

**`yuandian_rh_case_details`** — 案例详情全文
- 参数：`type`（"ptal" 或 "qwal"，必填）、`ah`（案号）或 `id`。
- 返回：案例全文，含 `content` / `dsr` / `fxgc` / `pjjg` 等字段。

**`yuandian_case_vector_search`** — 案例语义检索
- 参数：`query`（自然语言）、`wenshu_type`（案件类别）、`dianxing`（true = 仅权威案例）、`cj`（法院层级）、`return_num`。
- 返回：按相似度排序的案例列表，每条含 `score`。

## 第三步：输出结果

以清晰格式在对话中直接呈现，**无需保存文件**。

### 检索结果列表格式

先列权威案例（如有），再列普通案例：

```
【权威案例】（共 X 件）
1. {案件名称}
   案号：{案号}
   法院：{法院名称}  |  裁判日期：{YYYY-MM-DD}  |  文书类型：{判决书 / 裁定书 / ...}
   案由：{案由}
   核心观点：{50-100 字，摘录最关键的裁判意见或法律认定}

2. ...

---

【普通案例】（共 X 件，显示前 X 件）
3. {案件名称}
   案号：{案号}
   法院：{法院名称}  |  裁判日期：{YYYY-MM-DD}  |  文书类型：{...}
   核心观点：{50-100 字}

...

如需某案全文，请告知案号。
```

### 全文输出格式

```
【{案件名称}】
案号：{案号}
法院：{法院}  |  裁判日期：{日期}  |  文书类型：{类型}
案由：{案由}

当事人：{原告 / 申请人} vs {被告 / 被申请人}

{全文内容（分段呈现）}
```

### 语义检索结果标注

```
（语义相似度：{score:.3f}）
```

## 来源标签

- `[元典案例]`：本会话内通过 `legal_research.search_cases` / `legal_research.fetch_case` capability 实际返回的案例。默认标签。
- `[verify - 需用户自行对照元典原文]`：检索命中但仍需用户自行核实的内容（如新兴领域薄弱覆盖、跨年份口径差异）；Agent 不访问外部网站。

## 工作约束

- **不编造判决**：所有案例信息必须来自 MCP 工具实际返回；未检索到或 MCP 失败时如实说明并停止。
- **权威优先**：结果中权威案例（指导性 / 典型案例）置于普通案例之前。
- **摘要客观**：核心观点摘要应如实反映裁判立场，不加评论。
- **数量提示**：命中总数 > 显示数量时，告知用户实际总数并提示可进一步筛选。
- **时效说明**：若检索到的案例裁判日期较早（如 5 年以上），建议用户注意司法实践可能的变化。
- **新兴领域覆盖局限**：数据爬虫 / AI 生成内容侵权 / 算法歧视 / 数据合规等新兴领域 qwal 库收录量有限。命中数低时降级到 ptal + vector 检索，并在输出中明示覆盖局限（"qwal 库目前对该主题收录较少，主要从普通案例 / 语义检索补充——以下案例不代表权威立场"）。
- **来源标签**：所有案例引用按上述来源标签标注。

## 工作成果头部

按 profile 中角色 + 法域决定：

- 律师 + 中国法：`保密 / 内部法律分析 — 仅供法务团队使用 — 不构成外发法律意见`
- 非律师：`研究笔记 / 内部记录 — 不构成法律意见 — 请律师复核后再依赖`

外发给业务方 / 客户的版本去工作成果头。

## 非律师门

案例检索本身是事实查询。但当用户**基于本 skill 检索的案例做具体决策**（出具法律意见、向监管机构提交、起草诉讼文件、向客户提出实务建议等）时，先 surface：

```text
本 skill 返回的裁判文书是研究材料——汇集了元典案例库的命中。
它不是对你具体事实的法律意见。

如果计划基于这些案例做具体决策（给客户回函、监管提交、诉讼起草、对外发表观点），
是否已与律师 / 有执业资格的法律人员复核过？
- 是：明确确认后继续
- 否：建议先与律师复核案例在你具体场景下的可援引性、地方实务差异和最新裁判趋势
```

## 交接

- 用户基于案例做综合研究 → `prc-legal-research-deep-research`（8 阶段研究备忘录）。
- 涉及案例援引的法律条文 → `华宇元典-法律法规`。
- 涉及案件主体的企业信息 → `华宇元典-企业信息查询`（含涉诉文书列表等）。
- 用户问题涉及业务场景 → 对应 cluster 的 review skill：
  - 商事合同：`commercial-contract-review` 等。
  - 数据隐私：`privacy-use-case-triage` / `privacy-reg-gap-analysis` 等。
  - 监管合规：`regulatory-policy-diff` / `regulatory-gap-surfacer` 等。
  - 劳动用工：`employment-termination-review` / `employment-wage-hour-qa` 等。

## 本 skill 不做的事

- 不对美国法或非中国法事项使用。
- 不对仲裁 / 劳动仲裁裁决检索（不在覆盖范围）。
- 不在 capability 不可达时尝试用模型知识"模拟"检索。
- 不使用 Web Search、浏览器、裁判文书网、第三方网站或模型记忆替代元典 MCP。
- 不编造案号、不伪造裁判日期、不虚构核心观点。
- 不替代律师做具体事实下的法律判断。
- 不保留 Claude 专属配置路径。
- 不要求用户调用 Claude slash command。

## 数据来源

- MCP server：`yuandian-case`（http stream，订阅管理）
- MCP URL：`https://open.chineselaw.com/mcp/case/stream`
- 数据来源：元典开放平台（北京华宇元典信息服务有限公司）
- API 文档：https://open.chineselaw.com/
- 支持邮箱：yuandianzonghe@thunisoft.com
