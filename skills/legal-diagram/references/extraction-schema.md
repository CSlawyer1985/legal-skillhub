# 提取模式参考

在 `extract.md` 第 2 遍期间加载，以解决提示并了解哪些字段可由脚本填充、哪些需要 LLM 丰富。字段定义位于 `scripts/extraction/schema.py`；本文件记录每个字段的**检测层级**和**信号**。

## 内容

- 检测层级（三个标签的含义）
- 检测层级汇总表
- 字段组
- 特别说明

## 检测层级

- **script-direct（脚本直接）**：确定性层完全填充字段。仅接受和验证。
- **script-hint（脚本提示）**：信号触发但脚本无法解析结构；发出 `ExtractionHint`。第 2 遍从片段中解决提示为实体。
- **llm-only（仅 LLM）**：无确定性信号存在。清单（manifest）始终发出指令；第 2 遍从文档语义填充。

管理规则：脚本仅在模式完全解析时发出已填充实体；否则发出提示。不确定实体不得从脚本进入结果；第 2 遍只能在所引用片段中有文本支持的情况下填充字段。

## 检测层级汇总

|字段|层级|主要信号|可靠格式|
|---|---|---|---|
|events|script-direct|每句日期正则|md, docx, xlsx|
|legal_authorities|script-direct|引用正则（案例 / 法规 / 条例）|所有文本格式|
|ownership_links|script-direct|`X owns N% of Y`|md, docx|
|parties|script-direct|`Parties:` 块或行内 `Parties: A (role), B (role)`|md, docx|
|entities|script-direct|公司后缀名称（Inc/LLC/Corp…）或实体表|docx, xlsx, md|
|tasks, conditions, claim_classes, data_flows, witnesses, ip_assets, negotiation_issues|script-direct **如为表格形式**，否则 script-hint|表头签名或章节标题|docx, xlsx|
|process_steps, investigation_steps|script-direct 如为编号列表，否则 script-hint|编号列表 + 动作动词|md, docx, pptx|
|obligations|script-direct|`shall` / `must` / `agrees to` 情态动词|md, docx|
|communications|script-hint|“Notice of” / “demands” + 当事方|docx, md|
|concepts|script-hint|标题级联或 `(a)(b)(c)` 枚举|docx, md|
|transfers|script-direct|`X pays/wires Y` + 金额|md, docx|
|obligations.risk_level|llm-only|语言评分标准（`shared/figure-description-schema.md`）|不适用|
|decision_points|llm-only|条件语言|不适用|
|relationships.cardinality_*|llm-only|从所有权/角色推断|不适用|

## 字段组

**时间类**（`events`、`deadlines`、`phases`、`tasks`）。服务类别 4、5、13、14、24、26-28。`events` = 格式鲁棒性最强的字段；即使从 PDF 也可恢复。`tasks` 和 `phases` 从 XLSX 截止日期表填充强劲。

**当事方 / 实体**（`parties`、`entities`、`ownership_links`、`relationships`）。服务 6、14、29。`ownership_links` 需要明确的 `owns N%` 模式；仅以散文陈述的结构降级为关系提示。`relationships.cardinality_*` 为仅 LLM。

**义务 / 控制 / 条件**（`obligations`、`controls`、`conditions`）。服务 7、9、21、30。`obligations` 从情态动词填充；`risk_level` 始终仅 LLM。`controls` 和 `conditions` 从表格填充；否则为标题提示。

**流程 / 调查**（`process_steps`、`investigation_steps`、`decision_points`）。服务 1、11、16、17、26、30。编号列表直接填充；散文序列成为提示。`decision_points` = 仅 LLM（多分支逻辑）。

**通信**（`communications`）。服务 13、15、16。脚本提示：文档类型关键词加发送方/接收方；完整消息顺序通常需要第 2 遍。

**概念 / 权威**（`concepts`、`legal_authorities`）。服务 3、20、21、22。`legal_authorities` = 跨所有文本格式最强的 script-direct 字段（引用正则）。`concepts` 层级：script-hint（标题级联）→ LLM（隐含散文分类法）。

**风险 / 谈判**（`risk_items`、`negotiation_issues`）。服务 8、18、22。从双轴表格直接填充；否则为提示。

**财务**（`transfers`、`claim_classes`）。服务 15、28、29。`claim_classes` 从有序瀑布列表或表格填充。

**隐私 / 知识产权**（`data_flows`、`ip_assets`）。服务 10、25、30。两者均可从表格 script-direct、从标题 script-hint。

**证人**（`witnesses`）。服务 23。从证人表 script-direct，从叙述提及 script-hint。

## 特别说明

- `risk_level` 和 `decision_points` 从不脚本填充；清单始终为它们发出指令。
- PDF 提取在结构上不可靠；`events[]` 和 `legal_authorities[]` 最可恢复，表格最不可靠。
- XLSX 对 `tasks[]`、`deadlines[]` 及任何表映射实体最强；对 `relationships[]` 较弱。
- 对话语境输入无脚本层级。助手填充一切，使用清单的 `absent_fields` 列表作为检查清单。
