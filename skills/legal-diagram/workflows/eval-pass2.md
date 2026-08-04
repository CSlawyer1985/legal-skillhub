# 第 2 遍评估工作流

评估第 2 遍丰富化质量的操作者流程。将 LLM 补丁与用户所有的期望补丁标签进行比对；原始计数，无阈值。每个冻结夹具运行一次；评分在全部九个夹具上汇总。

## 目的

通过在冻结清单上执行丰富化流程，并将输出补丁与标签期望（必需、加分、禁止）评分，来评估第 2 遍补丁质量。返回每个夹具的分数和汇总表；驱动指令和证据打包的迭代。这不是测试框架（测试位于 `scripts/tests/`），而是供操作者审查的结构化评估运行。

## 评估运行流程

对 `scripts/tests/eval/manifests/` 中的每个夹具：

1. **读取清单。** 加载 `scripts/tests/eval/manifests/<fixture>.frozen.json`。注意 `llm_enrichment.directives[]` 数组和 `llm_enrichment.evidence_packets[]` 列表（清单是冻结的规范版本；绝不重新运行第 1 遍）。

2. **完全按照 workflows/extract.md 第 3 步执行第 2 遍。** 遵循读取顺序、指令处理器和补丁纪律，就像清单来自脚本运行一样：
   - 先读取清单，再 `llm_enrichment.evidence_packets[]`，然后 `llm_enrichment.directives[]`。
   - 仅在需要时使用指令 `hint_ids` 引用的片段（来自 `extraction_hints[].snippet` + `context_heading`）。
   - 应用补丁纪律：仅返回 RFC 6902 JSON Patch 操作。每个新增或变更的实体都携带 `evidence_id` 和 `source_ref`。
   - 不将丰富化应用于任何真实输出；补丁就是被测试的工件。将补丁写入临时文件以供评分。

3. **运行评分器。** 执行 `python scripts/eval_pass2.py --manifest scripts/tests/eval/manifests/<fixture>.frozen.json --patch <patch.json> --labels scripts/tests/eval/labels/<fixture>.pass2-labels.json`。捕获 JSON 输出。退出码 0 = 已评分；退出码 1 = 补丁门控阻止了补丁（`ok: false`，参见 `gate_findings[]`）；退出码 2 = 输入格式错误。

4. **收集每个夹具的结果。** 记录：`ok` 状态（true/false）、`gate_findings[]`（补丁门控的发现）、`labelled`（标签是否完整）、`vacuous`（若标签携带 `labelled: false` 则为 true）、`score` 对象（required_pass/required_total/bonus_pass/bonus_total/forbidden_violations）。

5. **在全部九个夹具之后构建汇总表。** 列：夹具 | 门控状态 | required_pass/required_total | bonus_pass/bonus_total | 禁止违规 | vacuous。

## 标签文件格式

第 2 遍期望的用户所有事实真相。模式版本：`legal-diagram-pass2-labels-v1`。

顶层结构：

```json
{
  "schema_version": "legal-diagram-pass2-labels-v1",
  "fixture": "<fixture-name>",
  "frozen_manifest_sha256": "<hex-digest>",
  "labelled": false,
  "expectations": [],
  "forbidden": [],
  "todo": []
}
```

字段含义：
- `schema_version`：固定为 `legal-diagram-pass2-labels-v1`。
- `fixture`：夹具标识符（例如 `en_spa_contract`）。必须与冻结清单文件名匹配。
- `frozen_manifest_sha256`：冻结清单字节的 SHA-256 十六进制摘要。评分器在不匹配时发出 `labels_stale` 警告；触发重新冻结（参见“重新冻结流程”）。
- `labelled`：布尔值。true = 操作者已审查该夹具的所有期望和禁止规则。false = 不完整；评分器在输出中发出 `vacuous: true`，表示分数为占位值。
- `expectations`：期望补丁条目数组（参见下方“期望条目模式”）。
- `forbidden`：禁止实体规则数组（参见下方“禁止条目模式”）。
- `todo`：可选数组，供下一次标签会话的操作者提示使用（若 `labelled: false`）。评分器不使用；仅供操作者参考。
- `_sha_audit`：携带在 sha 行上的安全审计抑制说明（十六进制摘要会使 base64 扫描器产生假正例）。评分器忽略它；重新冻结时将其与 `frozen_manifest_sha256` 保持在同一物理行上。

### 期望条目模式

操作者指定补丁应交付的结果：

```json
{
  "id": "E1",
  "credit": "required",
  "kind": "field_filled",
  "path": "/parties/0/name",
  "predicate": {},
  "note": "party name must be present"
}
```

字段含义：
- `id`：唯一标识符（例如 `E1`、`E2`、……）。操作者分配；格式无约束，但在夹具内唯一。
- `credit`：`required` 或 `bonus`。required = 整体接受必须通过；bonus = 向更高质量加分。评分器分开求和。
- `kind`：`field_filled`、`value_matches`、`entity_added`、`unchanged` 之一。决定谓词形态：
  - `field_filled`：检查路径是否已填充（非 null、非空字符串/列表/字典）。谓词 `{}`（忽略）。
  - `value_matches`：检查路径处的值是否匹配约束。谓词恰好携带一个：`equals`（深度相等）、`one_of`（值在列表中）、`regex`（对字符串值进行全匹配）。示例：`{"equals": "Active"}` 或 `{"one_of": ["Active", "Inactive"]}` 或 `{"regex": "[0-9]{4}"}`。
  - `entity_added`：检查补丁后数组中是否出现新实体。谓词形态：`{"array": "obligations", "match": {"field": "value", ...}}`。`array` 是 `extraction_result` 内的实体数组名称（例如 `obligations`、`parties`），而非指针。match 字典指定新实体必须携带的字段；所有匹配字段须精确匹配。实体必须是相对冻结版本的全新实体；若其携带 `evidence_id`，该 id 必须解析为已知证据包或提示（补丁门控已要求整个实体添加时携带 `evidence_id`，因此通过门控的补丁总是携带一个）。此 kind 不使用 `path`；将其设为 `""`。
  - `unchanged`：检查路径处的值是否与冻结清单中同一路径的值深度相等。谓词 `{}`（忽略）。
- `path`：指向丰富化 `extraction_result` 的 JSON Pointer，而非清单根（RFC 6901，`/` 转义为 `~1`，`~` 转义为 `~0`）。示例：`/parties/0/name` 或 `/hierarchy/0`。
- `predicate`：约束对象形态取决于 `kind`：
  - `field_filled`：`{}`。
  - `value_matches`：恰好一个键（`equals`、`one_of`、`regex`）。无嵌套。
  - `entity_added`：`{"array": "<entity array name>", "match": {<field-match>}}`。
  - `unchanged`：`{}`。
- `note`：操作者评论；评分器忽略（供操作者参考）。

### 禁止条目模式

操作者指定不得变更的实体或路径：

```json
{
  "id": "F1",
  "kind": "no_entity_added",
  "array": "parties",
  "match": {"name": "Acme Corp"},
  "note": "hallucination trap: Acme not mentioned"
}
```

字段含义：
- `id`：唯一标识符（例如 `F1`、`F2`、……）。
- `kind`：`no_entity_added` 或 `path_untouched` 之一。
  - `no_entity_added`：检查数组中是否出现与画像匹配的新实体。使用顶层 `array` 和 `match` 字段。实体若在补丁后为全新（超出冻结清单中的实体）且所有匹配字段精确匹配，则构成违规。
  - `path_untouched`：检查路径值是否未变更（与冻结版本深度相等）。值变更或路径被删除时触发违规。添加先前不存在的路径不触发此规则；请防护冻结清单中已存在的路径。使用顶层 `path` 字段。
- `array`（用于 `no_entity_added`）：`extraction_result` 内的实体数组名称（例如 `parties`、`obligations`），而非指针。
- `match`（用于 `no_entity_added`）：字段约束；所有匹配字段存在且精确匹配时实体构成违规。
- `path`（用于 `path_untouched`）：指向 `extraction_result` 中被防护值的 JSON Pointer。
- `note`：操作者评论。

## 标签会话流程

操作者按夹具填充期望和禁止项：

1. **打开一个夹具的标签文件**（例如 `en_spa_contract.pass2-labels.json`）。以 `labelled: false` 开始。

2. **读取冻结清单。** 理解提取基线（第 1 遍的当事方、事件、义务等）。

3. **读取指令。** 审查 `llm_enrichment.directives[]`，了解第 2 遍丰富化的意图。

4. **执行第 2 遍**（作为操作者，手工，使用“评估运行流程”第 2 步中的流程）。决定您会做哪些补丁。

5. **填充 `expectations[]`。** 对每个您期望的结果：
   - 分配唯一 `id`。
   - 选择 `credit` 层级（必需项用 required，加分项用 bonus）。
   - 指定 `kind` 和 `path`。
   - 编写 `predicate`（`field_filled` 和 `unchanged` 省略；`value_matches` 和 `entity_added` 提供 match）。
   - 添加 `note`（为什么重要）。

6. **填充 `forbidden[]`。** 对每个幻觉陷阱或不变量：
   - 分配唯一 `id`。
   - 选择 `kind`（`no_entity_added` 或 `path_untouched`）。
   - 提供 `array`/`match`（用于 `no_entity_added`）或 `path`（用于 `path_untouched`）。
   - 添加 `note`。

7. **特殊情况：en_spa_contract 的“todo”占位。** 读取 `todo` 数组（提示 H4 和 H14）。若存在，标签会话首先处理它们：审查这些提示的证据，决定期望结果，并将这些条目从 `todo` 移入 `expectations[]`，附上适当的谓词。

8. **标签验证。** 确保：
   - 所有 `expectations[].id` 在夹具内唯一。
   - 所有 `forbidden[].id` 在夹具内唯一。
   - 每个 `path` 是语法有效的 JSON Pointer（以 `/` 开头，转义 `~` 和 `/`）。
   - 谓词与声明的 `kind` 匹配。
   - 在设置 `labelled: true` 之前移除 `todo` 数组。

9. **设置 `labelled: true`。** 在以下条件满足前绝不设置 `labelled: true`：
   - 所有期望和禁止规则都已针对当前清单审查有效性。
   - 操作者已确认标签捕获了预期的丰富化结果。

10. **保存并提交。** 标签值是操作者所有的事实真相。代理只能转写操作者在标签会话中口述的内容；不允许代理编写标签内容。

## 重新冻结流程

当第 1 遍演进且冻结清单重新生成时：

1. **检测过期。** 运行评分器；若任何夹具发出 `labels_stale` 警告，则清单已变更。

2. **将新黄金版本复制到冻结位置。** 用新的黄金清单替换 `scripts/tests/eval/manifests/<fixture>.frozen.json`。

3. **更新冻结 SHA。** 计算新清单字节的 SHA-256。更新该夹具标签文件中的 `frozen_manifest_sha256` 以匹配。

4. **审查期望有效性。** 在新的标签会话中，审查每个期望和禁止条目。检查：
   - 路径在新清单中是否仍然存在（JSON Pointer 匹配）？
   - 实体数组路径和字段名称是否仍然匹配？
   - 谓词是否仍然有意义（例如 `value_matches` 的正则是否仍然适用）？

5. **仅在审查后保持 `labelled: true`。** 若任何条目无效，修复或移除它。仅在验证后将 `labelled` 设为 `true`。

6. **记录重新冻结。** 在夹具的标签文件或操作者日志中添加说明：日期、原因（例如“第 1 遍 enrichment_hints 模式更新”）、所做的变更。
