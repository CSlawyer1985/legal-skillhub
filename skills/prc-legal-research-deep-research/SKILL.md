---
name: prc-legal-research-deep-research
description: 中国法律综合研究助手。用户描述涉及中国法律的事实情景、提出法律争议问题、询问某行为 是否合法合规、要求分析法律条文适用性、或需要输出法律备忘录时触发。研究框架参考英美 法下的 IRAC / CREAC 与德国法下的 Gutachtenstil；产出客观法律备忘录。本 skill **仅覆盖中国大陆法**——非中国大陆法事项请走当地商业法律研究服务或当地律所。
metadata:
  displayName: 法律综合研究
  argument-hint: '[事实情景 + 法律争议问题 | 合规性论证问题 | 法律观点验证问题]'
---

# 中国法律综合研究

## 适用范围（先读）

本 skill 通过 `legal_research.search_laws` / `legal_research.search_cases` + `web_research.search_secondary_sources` capability 接入元典法规库（`yuandian-law` MCP）、元典案例库（`yuandian-case` MCP）和二手文献检索（`tavily` MCP），**仅中国大陆法适用**。

**不要在以下场景使用本 skill：**

- **美国法等非中国大陆法事项**：本 skillpack 不覆盖；请走当地商业法律研究服务（Westlaw / LexisNexis / CoCounsel 等）或当地律所。
- **其他法域**（EU / UK / HK / Singapore 等）：不覆盖。
- **港澳台地区**：不在元典覆盖范围。
- **起草法律文件、表格或模板** — 超出本 skill 范围。
- **执行具体任务的指令** — 超出本 skill 范围。
- **穷举式检索**（如"找出所有讨论 XX 的法条 / 案件"） — 元典 MCP 有返回数量限制，无法保证穷举。
- **仅需查找单条法律条文原文** — 建议使用 `prc-legal-research-law-search`。
- **仅需查找特定案例全文** — 建议使用 `prc-legal-research-case-search`。
- **仅需查询企业工商 / 风险信息** — 建议使用 `prc-legal-research-company-search`。

## 前置条件 / 连接器探测

`legal_research.search_laws` + `legal_research.search_cases` + `web_research.search_secondary_sources` capability 必须**全部**实际连通才能跑：

- `yuandian-law` + `yuandian-case`：未连通则停止，告知用户确认对应 MCP 服务器 API 凭据已配置 + 网络可达 + 重启 agent。
- `tavily`：未连通则停止，告知用户确认 Tavily MCP API 凭据已配置。

**严禁仅凭配置文件声明就认为连接器可用**——必须实际探测一次轻量级 capability 成功后才往下走。任一失败标 `[连接器未核验]` 并停止。

## MCP 工具清单

### 一手权威资料 — 元典工具

**法规法条（`yuandian-law` server，对应 `legal_research.search_laws` / `legal_research.fetch_law` capability）**：

| 工具 | 用途 | 关键参数 |
|------|------|---------|
| `yuandian_rh_fg_search` | 法规关键词检索 | `keyword`、`sxx`、`xljb_1`、`top_k` |
| `yuandian_rh_fg_detail` | 法规全文 | `fgmc` 或 `id`，可选 `refer_date` |
| `yuandian_rh_ft_search` | 法条关键词检索 | `keyword`（必填）、`fgmc`、`sxx`、`xljb_1`、`top_k` |
| `yuandian_rh_ft_detail` | 法条详情原文 | `fgmc`+`ftnum`，或 `id` |
| `yuandian_law_vector_search` | 法条语义检索 | `query`、`sxx`（列表）、`return_num` |

**案例文书（`yuandian-case` server，对应 `legal_research.search_cases` / `legal_research.fetch_case` capability）**：

| 工具 | 用途 | 关键参数 |
|------|------|---------|
| `yuandian_rh_qwal_search` | 权威案例检索（指导性 / 典型） | `qw`、`ay`、`ajlb`、`top_k` |
| `yuandian_rh_ptal_search` | 普通案例检索（裁判文书） | `qw`、`fxgc`、`ajlb`、`yyft`、`top_k` |
| `yuandian_rh_case_details` | 案例详情全文 | `type`（"ptal" 或 "qwal"，必填）、`ah` 或 `id` |
| `yuandian_case_vector_search` | 案例语义检索 | `query`、`wenshu_type`、`dianxing`、`return_num` |

重要返回说明：

- `yuandian_rh_ft_search` 的 `llm_content` 格式：`"- 《{fgmc}》{ft_num}##{content}"`。
- `yuandian_rh_qwal_search` / `yuandian_rh_ptal_search` 返回 `{"total": int, "lst": [...]}`，取 `lst` 时先判断 `total > 0`。
- `sxx` 字段：现行有效 / 失效 / 已被修改 / 部分失效 / 尚未生效。
- 语义检索返回列表，每条含 `score`（相似度评分）。

**关键词检索 vs 语义检索使用原则**：

- **关键词检索**：已知具体法规名称 / 法条号 / 案号，或已提取出精确术语。
- **语义检索**：问题模糊、口语描述、术语不确定，或需发现跨法规潜在相关法条；寻找事实相似判例时语义检索召回更全。

### 二手文献（Secondary Sources） — Tavily 工具

对应 `web_research.search_secondary_sources` capability。使用 `tavily-search` 工具检索，通过 `include_domains` 参数限定来源范围：

**律所文章**（头部律所）：

```
include_domains: ["kwm.com","junhe.com","fangda-partners.com","zhonglun.com",
                  "tongshang.com","haiwen-law.com","hankunlaw.com","jingtian.com",
                  "meritsandtree.com","globe-law.com","allbrightlaw.com","dehenglaw.com",
                  "grandalllaw.com","yingkelawyer.com"]
```

**政府解读**：

```
include_domains: ["gov.cn","npc.gov.cn","court.gov.cn","spp.gov.cn","moj.gov.cn",
                  "mhrss.gov.cn","samr.gov.cn","csrc.gov.cn","pbc.gov.cn","mofcom.gov.cn"]
```

**学术资源**：

```
include_domains: ["cnki.net","wanfangdata.com.cn","pku.edu.cn","tsinghua.edu.cn",
                  "ruc.edu.cn","cupl.edu.cn","iolaw.org.cn","chinalawreview.org",
                  "legaldaily.com.cn","legal.people.com.cn"]
```

## 工作原则

1. **客观性**：备忘录用于识别风险，不争辩事实。不挑选有利案例，负面判例同样必须引用。
2. **一手资料为王**：最终结论只能依据法律法规和裁判文书。二手文献只用于构建框架和引出线索。
3. **来源透明**：
   - 所有法条必须经元典 MCP 工具验证后引用，按三级标签标注（见下文「来源标签三级分级」）。
   - 二手文献在正文中引用时，须写明：**"据 [机构名][作者（如有）]《文章标题》"**，并列出完整标题 + URL。
   - 自己的推理分析，在段落末尾注明"（分析推断）"。
4. **时效优先**：优先引用 `sxx=现行有效` 的法规；已失效或已修改的必须明确标注，并尝试获取当前有效版本。
5. **冲突处理 hierarchy**：上位法 > 下位法；新法 > 旧法；特别法 > 普通法。
6. **效力层级说明**：引用行业指引、协会规范等非强制性规范时，须明确说明其性质，**不得**与法律、行政法规、司法解释同等对待。
7. **言简意赅，实事求是**。

## 八阶段工作流

### 第一阶段：信息完整性检查

从对话上下文中获取用户的问题，无需用户重复输入。

**事实陈述型**：核验主体信息（谁、性质）、核心事实（时间 / 地点 / 事件）、争议问题（要解决什么）。

**法律问题型**：核验问题的完整性和真实性，确认适用法域。

信息不完整时**向用户补问**，不要在信息不足时开始研究。

### 第二阶段：研究问题的提出和确认 — 硬性暂停

向用户列出以下内容并**明确等待用户回复"确认"或"继续"后**，方可进入下一阶段，**不得自行推进**：

1. 归纳的核心法律争议问题（1-3 条）。
2. 拟研究的范围和方向。
3. 关键前提假设（如有）。

> **硬性暂停**：未收到用户确认，**禁止开始任何检索工作**（包括 Tavily 和元典 MCP 调用）。

### 第三阶段：二手文献（Secondary Sources）检索

使用 `tavily-search` 构建问题框架，引出一手资料线索。

检索策略（依次执行）：

1. 政府解读：`tavily-search`（`include_domains` 限定政府网站）。
2. 律所文章：`tavily-search`（`include_domains` 限定头部律所）。
3. 综合检索：`tavily-search`（不限域名，`search_depth="advanced"`）。

国内问题用中文；涉外问题同时用英文。

### 第四阶段：二手文献分析

从检索结果提取：

1. **引用的法律法规清单** — 法规名称 + 法条号（待元典 MCP 验证）。
2. **引用的案例** — 案号或案件名（待元典 MCP 验证）。
3. **扩展关键词** — 用于第五阶段检索。

### 第五阶段：一手权威资料检索与验证

**5.1 验证二手文献引用**

对每条提取的法规 / 法条调用 `yuandian_rh_ft_detail`（参数：`fgmc`+`ftnum`）核实：

- 法条是否真实存在。
- 内容是否一致。
- 是否现行有效。

**5.2 扩展检索**

```
yuandian_rh_ft_search(keyword, sxx="现行有效", top_k=15)
yuandian_rh_fg_search(keyword, sxx="现行有效", top_k=5)
yuandian_rh_qwal_search(qw, ajlb="民事案件", top_k=10)
yuandian_rh_ptal_search(qw, ajlb="民事案件", top_k=10)
```

注意：调用 `yuandian_rh_ptal_search` / `yuandian_rh_qwal_search` 后**先检查 `total > 0` 再取 `lst`**。

**5.2.1 语义检索补充（按需使用）**

以下两种情况追加语义检索：

1. 关键词检索结果不足（召回 < 3 条相关结果）。
2. 用户问题较为模糊，难以提炼精确关键词。

```
yuandian_law_vector_search(query, sxx=["现行有效"], return_num=15)
yuandian_case_vector_search(query, wenshu_type="民事案件", return_num=10)
```

语义检索返回的每条结果含 `score`，优先使用 score 较高的结果；仍须通过 `yuandian_rh_ft_detail` 或 `yuandian_rh_case_details` 获取完整原文后再引用。

**5.3 按需获取全文**

案例高度相关或需分析裁判说理时再调：

```
yuandian_rh_case_details(type, ah)  # type ∈ {"ptal", "qwal"}
yuandian_rh_fg_detail(fgmc)
```

### 第六阶段：分析与推理

**法律解释方法链**（按序执行）：

1. 文义解释 — 法条文字的可能含义边界。
2. 体系解释 — 法条在整部法律中的上下文逻辑。
3. 历史解释 — 立法者原意（参考答记者问、立法释义）。
4. 客观目的论解释 — 法律漏洞或文义模糊时。

**推导链条**：

事实认定 → 问题识别 → 适用规则 → 规则解释 → 规则涵摄（Subsumption） → 形成结论 → 评估风险与不确定性。

**执行要求**：

- 严格遵循推导链条，不得从二手文献观点直接跳转到结论。
- 缺少关键事实前提时，主动列明缺失事实及其对结论的影响。
- 对有不确定性的问题，明确区分"较强观点""较稳妥观点""待进一步核实事项"。

### 第七阶段：验证和风险识别

输出前自检以下事项：

- [ ] 是否确认了所引用法条的时效性（现行有效 / 已修订 / 已废止）？
- [ ] 是否优先使用了更高级别法律渊源？
- [ ] 是否存在仅引用条文编号、未核实条文内容的情况？
- [ ] 是否存在超出所引用的法律渊源支持范围的推断？
- [ ] 是否存在仅引用二手转述、未见原文的情况？
- [ ] 是否混淆了不同法域、不同层级规范或不同时间版本？
- [ ] 是否把实务观点、学术观点误写为明确法律结论？
- [ ] 裁判分歧明显时，是否如实呈现了不同裁判立场？

如存在上述任一问题，**在结论中降低确定性并写明风险边界**。

### 第八阶段：生成法律研究备忘录

输出 Markdown 备忘录，同时保存文件：

```
$LEGAL_AGENT_LOCAL_DATA_HOME/work-products/legal-research-cn/deep-research/法律备忘录_<主题>_<YYYY-MM-DD>.md
```

（保存路径走中立 env var，不写死本地绝对路径。无法写入时输出完整 markdown 并提示用户手动保存。）

**备忘录格式**（严格遵循）：

```
# 法律备忘录

**日期**：{YYYY-MM-DD}

**研究问题**：{用户原始问题原文}

**收件人**：{需求方，无则填"内部研究使用"}

**发件人**：{使用者姓名，不知道则留空}

**事由**：{一句话概述研究问题}

---

## 一、核心结论

{简要事实（如有）、法律问题及核心结论，可用表格呈现多主体对比}

## 二、研究前提与适用范围

{前提假设、适用法域、时间范围、主体性质等}

## 三、主要规则依据

### 1. 一般规则
{列出与问题相关的一般性法律原则及法条原文，从宽泛到具体}

### 2. 特别规则
{列出适用于具体情形的特别规定}

## 四、分析

{将规则应用到事实，遵循第三部分的顺序和关键短语，标注每条推理的依据来源}

## 五、实务观点

{二手资料中与结论直接相关的观点。每条观点须标明来源：**机构名（作者）《文章标题》**，并附 URL。}

{URL 写法：凡 URL 前后紧跟中文括号、书名号或标点时，必须用尖括号 `<URL>` 包裹。示例：**某所《文章》**（`<https://example.com>`）}

## 六、风险与不确定性

{法律适用中的不确定因素、裁判尺度差异、地方差异、溯及力问题等}

## 七、结论与实务建议

{一两句话陈述最终结论；分主体列出实务建议}

## 八、主要依据清单

引用格式遵循 `references/citation-format.md`（引用格式要求）。

**法律法规**：
{逐条列出引用的法律、行政法规、司法解释、规范性文件}

**裁判文书**：
{逐条列出引用的判决书、裁定书及公报案例}

**二手参考资料**：
{逐条列出引用的律所文章、政府解读、学术文献等。URL 统一用 `<URL>` 包裹。}

## 九、关键资料溯引图

用 mermaid 展示主要一手资料与二手文献之间的相互援引关系：

​```mermaid
graph TD
    A[二手文献: XX律所文章] -->|引用| B[《民法典》第XXX条]
    C[二手文献: XX判决] -->|引用| D[司法解释第X条]
​```
```

## 备忘录输出后

向用户汇报本次工具使用情况（仅工作内容透明，不暴露 implementation detail）：

- **元典 MCP**：调用了哪些工具（如 `yuandian_rh_ft_detail` / `yuandian_rh_qwal_search`）、各几次、分别检索了什么主题。
- **Tavily**：调用几次、检索了什么关键词、限定了哪些域名（律所 / 政府 / 学术 / 综合）。
- **覆盖局限**：本次研究的命中弱点（如某领域 qwal 收录少、某条文跨年份修订）和建议的人工核验点。

不暴露：元典 MCP 内部 stack trace、API 速率限制 / 计费状态、内部参数动态调整。

## 来源标签三级分级

- `[settled - 元典法规 YYYY-MM-DD 确认]`：稳定主条款（如《民法典》《刑法》总则）经 MCP 实际返回且对照当前日期已确认现行有效。YYYY-MM-DD 为本次检索日期。
- `[元典法规]` / `[元典案例]`：本会话内通过对应 capability 实际返回的内容。默认标签。
- `[verify - 需对照元典原文]` / `[verify - 需对照裁判文书网]`：检索命中但仍需用户对照原文核实的内容（边缘条文 / 跨年份口径 / 地方实务）。
- `[模型知识 — 需核验]`：未经 MCP 核验、来自模型记忆的内容。**仅在 MCP 不可用时使用**，并必须明示模型记忆不可作为法律依据。

## 工作约束

- **不编造法条**：所有法条必须通过 `yuandian_rh_ft_detail` 或 `yuandian_rh_ft_search` 获取原文，返回为空时如实告知，不用 AI 记忆替代。
- **不编造案例**：所有案例必须来自元典 MCP 工具检索结果。
- **每条法条引用必须包含**：法规名称、法条号、原文内容、时效性状态。
- **未经 MCP 核验的内容必须标注 `[模型知识 — 需核验]`**。
- **第二阶段硬性暂停**：未收到用户确认，禁止任何检索（含 Tavily 与元典 MCP）。
- **来源等级三档**：一手权威 → 二手文献 → 自己推理，备忘录中必须分别归位。
- **URL 写法**：URL 前后紧跟中文括号 / 书名号时用尖括号 `<URL>` 包裹。

## 工作成果头部

按 profile 中角色 + 法域决定：

- 律师 + 中国法：`保密 / 内部法律分析 — 仅供法务团队使用 — 不构成外发法律意见`
- 非律师：`研究笔记 / 内部记录 — 不构成法律意见 — 请律师复核后再依赖`

外发给业务方 / 客户的版本去工作成果头。

## 非律师门

本 skill 返回的研究备忘录是**研究材料，不是法律意见**。研究帮助识别权威、构建论证框架，但**不替代律师对具体事实的判断**。

如果使用者非律师并打算将研究结论用于具体决策（出具法律意见、给客户回函、向监管机构提交、起草诉讼文件等），先 surface：

```text
本备忘录是研究材料——汇集了相关法律法规、裁判文书、二手文献观点。
它不是对你具体事实的法律意见。

如果计划基于备忘录做具体决策（给客户回函、监管提交、诉讼起草），
是否已与律师 / 有执业资格的法律人员复核过？
- 是：明确确认后我把备忘录呈现给你
- 否：我可以生成给律师的复核 brief，附本次研究备忘录 + 你的预期用途

等待你的选择。
```

## 交接

- 单条法律条文 → `prc-legal-research-law-search`。
- 案例全文 / 案号检索 → `prc-legal-research-case-search`。
- 企业信息查询 → `prc-legal-research-company-search`。
- 用户问题涉及业务场景 → 对应 cluster 的 review skill：
  - 商事合同：`commercial-contract-review` / `commercial-vendor-agreement-review` 等。
  - 数据隐私：`privacy-use-case-triage` / `privacy-reg-gap-analysis` 等。
  - 监管合规：`regulatory-policy-diff` / `regulatory-gap-surfacer` 等。
  - 劳动用工：`employment-termination-review` / `employment-wage-hour-qa` 等。
- 跨境业务的非中国大陆法部分 → 由用户走当地商业法律研究服务（Westlaw / LexisNexis / CoCounsel 等）或当地律所，本 skillpack 不覆盖。

## 本 skill 不做的事

- 不对美国法或其他非中国大陆法事项使用——非中国大陆法事项请走当地商业法律研究服务或当地律所。
- 不在 MCP capability 不可达时尝试用模型知识"模拟"研究。
- 不编造法条、不编造案例、不伪造时效状态。
- 不暴露 MCP 内部 stack trace / API 速率 / 计费状态等 implementation detail。
- 不替代律师做具体事实下的法律判断。
- 不保留 Claude 专属配置路径。
- 不要求用户调用 Claude slash command。
- 不跳过第二阶段硬性暂停。
- 不省略第七阶段验证自检。
- 不省略第八阶段第九章 mermaid 关键资料溯引图。

## 数据来源

- MCP servers：`yuandian-law` / `yuandian-case`（元典开放平台）+ `tavily`（Tavily）。
- 法规法条 + 案例数据来源：北京华宇元典信息服务有限公司，https://open.chineselaw.com/。
- 二手文献来源：Tavily，限定 include_domains（律所 / 政府 / 学术白名单）。
- 支持邮箱（元典）：yuandianzonghe@thunisoft.com。
- 引用格式参考：`references/citation-format.md`（引用格式要求）。
