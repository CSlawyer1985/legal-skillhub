---
name: hegui-consult
description: 上市公司合规、任职资格、公司治理及信息披露咨询。用户询问某事项是否合法合规、是否需要公告、是否影响董事、独立董事或高级管理人员任职资格，或涉及减持、回购、关联交易、担保、重组、分红、股权激励、停复牌、内幕信息、业绩预告、退市风险、权益变动、再融资、募集资金、问询回复及三会治理时使用。先调用 hegui MCP 查询并核验法规数据库中的现行正文；法规结构化结论仅用于内部路由，只有法规支持披露义务时才检索公告数据库中的同类案例。查完法规后根据返回 JSON 内容判断是否需要公告格式（条款指向格式或事项需出具公告时），补取对应板块的现行公告格式文件及可下载模板附件。最终答复必须提供正式法规名称、文号、状态、条款原文和适用分析，附适用的公告格式模板，并附通过验证的公告案例及数据库记录对应的公告原文件。禁止独立联网搜索或使用模型记忆补充法规和公告。
---

# 上市公司合规咨询

调用 `hegui_consult` 完成“法规证据判断 → 内部路由 → 公告案例检索 → 正式答复”。法规负责法律判断；内部结构化结论只控制流程；公告仅反映披露实践。

## 一、不可突破的规则

> **P0 · 最高优先级(先于下列所有条)**：`hegui_consult` 返回的 `draft_answer`、`answer_contract`、整包 JSON 及 `regulation_search` 材料清单，都是"供你消费的内部检索材料"，**不是**面向用户的答复。**严禁原样复制、摘抄或转述任何工具返回文本作为最终回复**——尤其严禁直接输出以"法规候选(内部材料…""法规材料(仅 coverage 命中…""以下为按现有信息先行检索…"开头的材料清单，或"答复应按…组织""请据此作答"这类本是写给你看的元指令。你必须读完材料后，用**自己的话**组织出独立的「结论 → 法规依据(逐字完整条文＋文号＋生效状态) → 适用分析」；一旦察觉自己在粘贴工具返回的大段文本，立即停止并改写。

1. 只使用 `hegui_consult` 返回的法规数据库记录、公告数据库记录及其对应原文附件。不得调用网页搜索、搜索引擎、浏览器或其他公开网站补充材料。
2. MCP 根据数据库记录访问法规或公告 PDF、DOCX、HTML 附件，属于数据库证据链，不属于独立互联网检索。
3. 只依据 `applicability.passed=true`、正文完整、且当前子问题已被 `coverage`/`excerpt` 命中**或**经法规原件全文核验定位的条款作确定结论（自动摘录未命中不等于无规定，见 [retrieval-strategy.md](references/retrieval-strategy.md) 第五节『法规原件全文兜底核验』）。
4. 不把法规标题、内部路由结论、`draft_answer`、公告案例或模型记忆当作法规条文依据。
5. 法规结构化结论只用于决定是否检索公告，不向用户展示为正式法规内容。
6. 只有法规直接支持披露义务，或条件性披露的触发条件已由用户事实满足时，才检索公告案例。
7. 公告案例不得反推法律结论；公告必须匹配板块、主体和事件，必要限定事实须经正文验证。
8. 数据库未命中、正文不完整或公告文件无法验证时，明确说明材料不足，不得联网或凭记忆补位。
9. 缺少会改变结论的事实时，只给附前提判断并补问，不得虚构处罚机关、违法领域、金额、比例或监管认定。
10. 默认按匿名场景处理，不机械索取公司名称、姓名、证券代码等识别性信息。补问前先判断该事实是否改变法规适用或结论、能否用主体类别/板块/时间范围/金额比例区间/条件真假替代；广泛问题先给通用规则与分情形结论，再列最少待核实事实。详见 [clarification-policy.md](references/clarification-policy.md)。
11. 工具超时、检索轨道失败、服务异常或意图漂移属**技术性检索失败**，不得表述为“没有相关规定”，也不得归因于用户未提供敏感信息。应先校验检索意图、分级精准重试，区分“技术故障 / 库未收录 / 正文不完整 / 命中未覆盖 / 用户事实不足”。详见 [retrieval-strategy.md](references/retrieval-strategy.md)。
12. `excerpt` 是**检索线索**，不是可直接引用的法规原文。凡展示“法规原文/条款原文”，必须是从正式原件确认边界的**完整条文**（从条号起、到下一条条号前止，含全部款项目、但书、例外），逐字引用、不得摘录/缩写/改写/加省略号；原文、规则概括与适用分析必须分开。强制规范见 [citation-standard.md](references/citation-standard.md)。

## 二、按需读取引用文件

- 补问或界定作答范围前读取 [clarification-policy.md](references/clarification-policy.md)（默认匿名、最少补问、通用规则先行、条件式结论）。
- 首次结果意图漂移、覆盖不足或疑似检索失败时读取 [retrieval-strategy.md](references/retrieval-strategy.md)（分级检索、意图校验、失败判别、降级顺序、原件全文兜底核验）。
- 任何要展示法规原文/条款原文前读取 [citation-standard.md](references/citation-standard.md)（excerpt 是线索非原文、完整条文引用、原文与分析分开、输出格式与自检清单）。
- 需从正式原件定位/截取完整条文、判定条款能否引用时读取 [full-text-verification.md](references/full-text-verification.md)（条文边界识别、`quote_ready` 证据闸门、完整性检查、PDF/DOCX/OCR、可选校验脚本）。
- 所有咨询在形成内部路由前读取 [routing-contract.md](references/routing-contract.md)。
- 法规返回后需判断是否补取公告格式时读取 [format-retrieval.md](references/format-retrieval.md)。
- 只有路由允许检索公告时读取 [announcement-retrieval.md](references/announcement-retrieval.md)。
- 所有咨询在组织最终答复前读取 [answer-contract.md](references/answer-contract.md)。
- 仅在修改、验证或回归测试本技能时读取 [evaluation-cases.md](references/evaluation-cases.md)。

## 三、提取问题要素

保留用户原话并提取：

- 板块：沪主板、深主板、创业板、科创板、北交所；
- 主体：公司、控股股东、实际控制人、股东、董事、独立董事、高级管理人员等；
- 核心事件：处罚、留置、冻结、减持、担保、交易、任免、诉讼等；
- 法律子问题：披露、任职资格、程序、时限、合规性等；
- 限定事实：机关、违法性质、发生时间、金额比例、是否涉及本公司、是否伴随市场禁入或不适当人选认定等。

一个问题涉及多个法律子问题时**自动拆开**，不要把所有内容塞进一次检索。常见拆分维度：法规适用范围、实体合规性、决策/审批程序、信息披露义务、披露时点、任职资格、责任与风险、公告实践。每个子问题单独建立法规证据与内部路由，一类条款不得替代另一类。精准重试/降级时**每次 MCP 调用只解决一个子问题**、保留同一事实背景——这能显著减少检索超时、意图漂移、不同法规体系混用、以及“用披露条款答任职资格 / 用公告反推法律结论”。

## 四、首次只查法规

首次调用使用：

```json
{
  "query": "用户原话",
  "bankuai": ["已确认板块"],
  "effective_status": [1, 2],
  "search_announcements": false,
  "clarify_on_missing": false,
  "strict": false,
  "regulation_limit": 10,
  "regulation_detail_count": 5
}
```

仅在用户明确查询历史版本时加入失效状态。板块未知且会改变规则选择时补问；可在已有事实下先返回部分材料，但不得混用不同市场规则。

> **跨板块 /「全板块」问题**：不要把"全板块"当作 `bankuai` 值传入(聚源库无此取值，会错误召回某单一板块规则)；应按涉及的具体板块分别查询，或省略 `bankuai` 让服务端按通用规则匹配。用户问题若带重复板块前缀(如"创业板创业板…")，按一次板块理解、不要叠加。

> 服务端已自行拆解问题并返回可直接消费的字段：`regulation_search.query_plan`（子问题 disclosure/qualification/general）、`regulation_search.quality.answerability`（各子问题是否被正文覆盖）、`regulation_search.quality.rejected`（被剔除候选及原因）、`regulation_search.quality.retrieval`（数量统计）、以及每条 `regulations[].{applicability{passed,reason},content_status,coverage,excerpt,excerpt_source,content_probe,pdf}`。内部路由应**基于这些字段**判断，不必另起炉灶重算。`strict` 现为纯确定式（fagui 已于 2026-07-10 移除全部通义千问，无 LLM 调用与成本），保持 `false` 即可。

## 五、法规证据闸门

逐个法律子问题检查：

1. **适用性**：法规适用于用户板块，或正文明确适用于境内上市公司的通用主体；`bankuai="所有板块"` 不能单独证明适用。
2. **来源完整性**：接受数据库正文或数据库记录对应附件解析出的正文；发布通知必须继续解析正式附件。`content_status` 应为 `parsed` 或 `attachment_parsed`。
3. **正文覆盖**：当前法律子问题须被下列任一方式直接覆盖——(a) `coverage` 含该子问题且 `excerpt` 已返回相关条款原文；或 (b) 自动摘录未命中，但已按 [retrieval-strategy.md](references/retrieval-strategy.md) 第五节『法规原件全文兜底核验』从 hegui 返回的正式法规原件中定位到相关条款，并核验条号、完整上下文、适用主体、板块与生效状态。**不得因自动 `excerpt` 未命中就停查或认定“无规定”**。
4. **版本状态**：只采用现行有效或待生效规则，剔除征求意见稿、草案、说明、旧版和错误法规族。
5. **排除范围**：剔除全国股转、非上市公众公司、基金、银行保险、境外上市公司及错误交易所专属规则。

正文为空、只返回通知、仅标题命中、扫描件无文字层，或既无相关摘录又未完成原件全文核验时，均视为没有直接依据。

**“判定覆盖”与“展示原文”是两件事**：即便 `excerpt` 已足以判断覆盖，向用户展示法规原文时仍须给出从原件确认边界的**完整条文**（见 [citation-standard.md](references/citation-standard.md)），不得把截断的 `excerpt` 当原文直接贴出。每条拟引用条款须先过 [full-text-verification.md](references/full-text-verification.md) 的 **`quote_ready` 闸门**（从本条条号起、到下一条同级条号前止，含全部款项目/但书/例外，条号/数字/比例/期限/否定词已核对）；`quote_ready=false` 的条款不得进入答复的「条款完整原文」。

## 六、检索意图校验与精准重试

拿到结果**先校验、再采用**，不要直接把服务端生成的检索计划当成正确。对照 `search_terms`/`query_plan`/`tracks` 检查：主体、核心事件、法律子问题、板块是否与用户一致；检索词/锚点有没有掺入无关的“交易/处罚/减持/董事”等，或跑到错误法规体系（基金/银行保险/全国股转）。发现意图漂移（如问任职年龄却生成“交易”“行政处罚”），**不得拿跑偏结果作答**，立即精准重试。

出现错误市场、错误主体、正文不完整、任一子问题未覆盖，或疑似技术性检索失败时，按 [retrieval-strategy.md](references/retrieval-strategy.md) 的分级检索与降级顺序处理，要点：

1. 保留首次结果用于审计；
2. **每次只重试一个法律子问题**，保留同一事实背景；
3. 精准检索用“法规体系/族锚点＋板块＋主体类别＋核心事件＋单一法律问题＋必要限定事实”；
4. 保持 `search_announcements=false`；必要时调低 `regulation_limit`/`regulation_detail_count`；
5. 同一子问题最多两轮不同焦点；重复返回同一批无效材料时停止，不空转。

法规族锚点只用于召回，不是法规依据。可用 `<板块>股票上市规则`、`<板块>上市公司规范运作`、`上市公司信息披露管理办法`、`上市公司独立董事管理办法` 等准确名称。**区分技术失败与真正无结果**：工具超时/`tracks` 有 `ok:false`/服务脱敏提示属技术失败，应重试或稍后再试，不得说成“没有相关规定”。

## 七、形成内部路由

法规证据通过闸门后，按 [routing-contract.md](references/routing-contract.md) 为每个法律子问题形成 `required`、`conditional`、`not_required` 或 `unknown` 状态。

- `required`：披露子问题启动公告检索；
- `conditional`：只有用户事实已经满足法规触发条件时启动，否则补问；
- `not_required`：默认跳过公告检索；
- `unknown`：跳过公告检索，不得用公告补法规。

任职资格、程序或一般合规子问题默认不触发公告检索，除非该子问题本身包含经法规支持的披露义务。

> 路由起点用服务端的 `quality.answerability[子问题]` 与对应 `regulations[].coverage`：answerability=true 且该法规 `applicability.passed=true`、`content_status∈{parsed,attachment_parsed}`、`coverage` 含此子问题，才可能是 `required`/`conditional`；answerability=false 一律先归 `unknown`（**不得据此推 `not_required`**）。

## 八、公告格式补取

形成内部路由后，**根据首次法规返回的 JSON 内容**判断是否需要补取公告格式：优先读结构化信号 `regulation_search.query_plan`(是否含 `format`)、`regulations[].coverage`(是否含 `format`)、`quality.answerability.format`，辅以 `regulations[].excerpt` 语义(**不扫描 draft_answer**)，出现指向规范格式的表述（如“按……本所制定的公告格式予以披露”“公告格式”“参照……格式编制”“编制指引/格式指引”），或某披露子问题为 `required`（含 `conditional` 且触发条件已满足）而用户实际要出具该公告时，读取 [format-retrieval.md](references/format-retrieval.md) 并补取对应板块的公告格式文件。

补取时再次调用 `hegui_consult`，**查询词须含格式类词**以命中服务端 `format` 召回，且 `search_announcements=false`：

```json
{
  "query": "<板块> <公告类型/核心事件> 公告格式",
  "bankuai": ["用户板块"],
  "effective_status": [1, 2],
  "search_announcements": false,
  "strict": false,
  "regulation_limit": 5,
  "regulation_detail_count": 3
}
```

只采用 `applicability.passed=true`、板块一致、`coverage` 含 `"format"`（或标题即“……公告格式……”）且带可下载 `pdf` 的格式文件；库中检索不到时如实说明，不得编造格式条目。首次调用已返回 `query_plan=[format]`（用户本就直接问格式）时无需再调。公告格式是“按什么模板写”，与“要不要披露”的法规依据分开，不得互相反推。

## 九、按路由检索公告

只有路由允许时，读取 [announcement-retrieval.md](references/announcement-retrieval.md)，使用“板块＋主体＋核心事件＋用户限定事实＋单一披露问题”进行精准查询。

现有接口下再次调用 `hegui_consult`：

```json
{
  "query": "精准公告焦点",
  "bankuai": ["用户板块"],
  "effective_status": [1, 2],
  "search_announcements": true,
  "announcement_years": 3,
  "announcement_limit": 8,
  "announcement_content_limit": 2,
  "clarify_on_missing": false,
  "strict": false,
  "regulation_limit": 5,
  "regulation_detail_count": 3
}
```

不得把法规标题、文号或整段条文作为公告查询词；不得单独搜索“董事会”“股东大会”“公司治理”“公司章程”“信息披露”“公告”等宽泛词。

> **时延与两段式的意义**：公告轨（正文 OSS 下载+抽取）是整条链路最慢的部分。先只查法规、仅在披露 `required`（或条件已满足的 `conditional`）时才发第二次带公告的调用——**大多数子问题不该触发公告**，这本身就是省时+省聚源负载的设计。`announcement_content_limit` 保持 2、别调大。重 consult 经公网 CDN 入口可能在 ~30s 被回源超时切断（见部署备注），客户端应给足 ≥90s 或走直连入口；性能不足**不得**降低证据标准。

## 十、公告证据闸门

只采用满足以下条件的公告：

- 板块、主体、核心事件与用户事项一致；
- 标题已经完整确认同类事实，或 `content_probe.snippet` 完成正文验证；
- “非因本公司事项”“在其他单位任职期间”“是否重大”等标题通常不具备的限定事实，已经正文确认；
- 数据库记录对应的公告原文件地址可提供；
- 普通任免、董事会会议、制度说明及仅命中宽泛词的公告已经排除。

无合格案例时直接说明，不凑数。公告检索或正文抽取失败不得影响法规部分答复。

## 十一、按返回状态处理

- `non_regulation`：说明未识别为法规咨询，不强行套规则；
- `clarify`：只就**会改变结论**的非识别性事实补问（见 clarification-policy.md），广泛问题可先给通用规则与分情形结论、再列最少待核实事实；
- `partial_with_clarification`：只给材料支持的附前提判断，并列出缺失事实；
- `consultation`：仍须完成法规和公告证据闸门；
- `service_unavailable`（或返回 `regulation_search.service_degraded=true`）：检索后端技术性故障（多条检索轨道超时/失败）。**据实转达“本次检索因服务波动未完成、请稍后重试”，绝不表述为“没有相关规定”，也不据此作任何合规结论**；可提示用户稍后用更精简的单一子问题＋关键词重试；
- 法规为空或连续重试仍不覆盖：**先判别是技术失败还是真的无结果**（见 retrieval-strategy.md 第三节）。技术失败（超时/`tracks` 有 `ok:false`/服务脱敏/`service_degraded=true`）→ 说明“本次检索因服务波动未完成，可稍后重试”，不得说成无规定；只有服务正常完成、正文完整、精准重试后仍无结果，才说“本次法规数据库未检索到直接匹配的现行规则”，且不进一步推导“法律无规定”。

## 十二、组织正式答复

组织答案前读取 [answer-contract.md](references/answer-contract.md)，依次输出：

1. 结论及适用前提；
2. 正式法规依据：名称、文号、状态、日期、板块、条款号、**条款完整原文**、法规原文件和适用分析。法规原文按 [citation-standard.md](references/citation-standard.md) 逐字引用完整条文，**原文、规则概括、适用分析三者分开**，不得把截断 `excerpt`、概括或 `draft_answer` 当原文；
3. 适用的公告格式（补取到时）：格式文件全名、文号、状态、对应“第几号”模板和可下载附件地址；未补取或未命中时省略或说明；
4. 公告参考案例：公司、代码、板块、标题、日期、同类事实、验证片段和公告原文件；
5. 待核实事项与风险；
6. 必要时给出简短检索不足说明。

明确区分条文直接规定、依据条文推导和无直接依据。不要展示内部路由 JSON、调用日志、鉴权信息或数据库连接信息。发送前对每段法规原文过一遍 [citation-standard.md](references/citation-standard.md) 第十节自检清单，任一项不满足即不得贴出该段原文。

对“某类事项是否合法/是否需要公告/某类人员能否任职”这类广泛问题，**默认给通用规则 + 条件式结论**，不必强行收敛为单一“是/否”：规则有统一口径直接答；按板块区分则分别列口径；按主体或条件区分则输出“情形 A→结论及依据 / 情形 B→…… / 情形 C→暂无直接依据”，最后只列**确定具体情形所需的最少事实**。这比索取识别性信息更适合通用合规咨询。

## 十三、工具边界

- 只查某板块法规且不需要公告案例时，使用 `fagui-bankuai`；
- 查违规处罚或监管措施案例本身时，使用可用的违规案例工具；
- 查指定公告全文时，使用公告工具；
- `hegui_extract_queries` 仅用于调试公告检索词，正常咨询无需单独调用；
- 即使其他工具可联网，也不得用其补充本技能的法规和公告证据。
