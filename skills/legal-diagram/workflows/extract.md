# 提取工作流（两遍）

由 `direct.md` 和 `guided.md` 调用的子工作流（由 `tutorial.md` 模拟）。`SKILL.md` 中的路由门控在本工作流恢复第 2 遍之前运行第 1 遍。返回丰富化的 `ExtractionResult` 及已确认的图表类型。

**调用方契约。** 输入：`input_source`、`intent_hint`、`mode`（`direct` | `guided` | `tutorial`）、`skip_confirmation`（布尔值）、可选 `manifest_cache`。当 `manifest_cache` 存在时（路由门控已运行第 1 遍），跳过第 1-2 步并从第 3 步使用该清单继续。绝不对已提供的 `manifest_cache` 重新运行第 1 遍。

## 第 0 步——输入类型检测

文件路径 → 解析扩展名。粘贴文本 → stdin。两者皆非 → 对话上下文。多个文件 → 逐文件运行第 1-2 步，清单以增量方式合并（拼接实体列表、拼接提示、指令取并集），按自然键对实体去重（事件按名称+日期、当事方按名称、义务按 id）。

## 第 1 步——设置检查（会话缓存）

加载 `shared/setup-check.md`。本次会话缓存结果。依赖缺失：教程模式 → pip 命令；直接模式 → 一行消息。再次失败 → 提供粘贴文本回退（md/text 无需第三方库）。

## 第 2 步——第 1 遍（确定性）

**调用方传入了 `manifest_cache`** → 此步已由路由门控完成；采用该清单并转到第 3 步。否则在此运行第 1 遍。

运行编排器 → 返回**清单**：`extraction_result`、`extraction_hints[]`、`coverage{}`、`matter_type_evidence{}`、`profile_signals{}`（基于原始文本关键词的软画像：privacy/litigation/governance/risk_assessment，活跃阈值 `>= 0.34`；绝不门控第 1 遍，仅引导第 2 遍指令和选择器）。

- 文件：`python scripts/extract_entities.py --input <path> [--pages R] [--sheets A,B]`
- 粘贴文本：`python scripts/extract_entities.py --stdin`（管道传入文本）
- 对话上下文：无脚本。助手通过检查人工构建 `ExtractionResult` 和覆盖范围映射（已填充字段 vs 缺失字段）。
- 超过 50 页的 PDF：先探测（`--probe <pdf>`）；若较大，发出警告并请求页码范围（属于真实不可读情形，而非自由裁量的中断）。扫描版 PDF（清单实体全空、无提示）：警告“检测到扫描版 PDF”，请求粘贴文本。
- 隐私/资源默认值：文件输入仅发出基本名称的 `input_source`；仅对可信内部溯源使用 `--include-source-path`。默认上限：文件 25 MB、PDF 50 页、DOCX 5000 段落、DOCX 200 表格、DOCX 表格 5000 行、PPTX 200 张幻灯片、PPTX 5000 个文本形状、XLSX 20 个工作表、每表 XLSX 1000 行、每表 XLSX 50000 个单元格。仅对可信的本地输入使用对应的 `--max-*` 标志覆盖。

## 第 3 步——第 2 遍（指令驱动的丰富化）

清单包含确定性提取结果，以及未解决候选实体的紧凑 `llm_enrichment` 证据。`llm_enrichment.directives[]` 是唯一的规范指令通道；所有指令类型都出现在那里。

规则：

- **读取顺序。** 先清单，再 `llm_enrichment.evidence_packets[]`，然后 `llm_enrichment.directives[]`。仅在需要时使用指令 `hint_ids` 引用的片段（`extraction_hints[].snippet` + `context_heading`）。除非指令明确要求源上下文，否则不全文重读。文件输入 → 仅对特定的低置信度候选实体在 `source_ref`/`anchor` 附近阅读。
- **读取策略。** 高置信度 → 不重读。中置信度 → 仅片段。低置信度 → 片段 + 相邻块。存在矛盾、缺失当事方/日期或候选实体字段不兼容时，可使用标题—章节窗口。
- **指令处理器。** `resolve_candidate` → 仅从证据包解析；`null_field_classification` → 按目标 id 应用风险评分标准（`shared/figure-description-schema.md`）；`hint_resolution` → 实例化 `suggested_field`（对于 `freeform_mention` 当事方提示，将提及与已提升的当事方做别名解析，而非新建实体；仅当提及指向有源支持的全新当事方时才新建）；`cross_linking` → 匹配义务↔控制措施、证人↔文件、条件↔当事方；`implicit_inference` → 对 `decision_points`、层级关系、隐含数据流进行语义读取；`directed_inference` → 画像标记的缺失字段；仅从有界的支持跨度读取中填充，每个实体携带 `evidence_id`+`source_ref`，否则添加 `extraction_warning`；`matter_type_resolution` → 选择证据最强的（教程：仅在并列时询问；直接：绝不询问）。
- **补丁纪律。** 仅返回 JSON Patch 操作；每个新增或变更的实体都携带 `evidence_id` 和 `source_ref`；不重述未变更的实体。对于脚本构建的清单（文件或 stdin 输入）：将清单和补丁写入两个临时文件（操作者暂存位置），运行 `python scripts/patch_gate.py --manifest <m.json> --patch <p.json> --apply`，并在 `ok` 为 true 时采用其 JSON 输出中的 `enriched_extraction_result`。出现错误发现时：使用发现的 `rule`/`path`/`message` 修复补丁一次并重新运行。第二次失败时：丢弃失败的操作，附加一个指明被丢弃字段的 `extraction_warning`，通过门控应用幸存的操作，继续。对话上下文输入（无脚本清单）：门控不运行；上述文字规则起约束作用。
- **层级（分组/嵌套）。** `extraction_result.hierarchy` 携带来自文档标题的确定性种子（`source: "deterministic"`）。审计它：删除或重新标记不符合法律逻辑的节点；保持深度 ≤ 2。然后组合标题遗漏的层级（主张 → 要件 → 证据、组 → 子组），在树中添加带 `source: "llm"` 和 `parent` 的节点。每个节点：`{id, label, parent, depth, source}`。像任何字段一样修补 `hierarchy`；每个组合节点都要有证据支撑，绝不虚构事项中不存在的结构。
- **反幻觉（精确性）。** 仅在所提供的证据/片段/锚点中有文本支持时填充。无支持 → 留空并警告。绝不虚构。
- **预算。** 单遍，无递归。指令处理完毕即停止。

## 第 4 步——验证

检查 `is_empty()`。为空、无输入文本、无提示 → 停止，请求更好的输入。稀疏（第 2 遍后少于 3 个实体数组被填充）：`skip_confirmation=true`（直接）→ 附内联说明继续；教程 → 请求一句话的意图描述。

## 第 5 步——意图与选择

构建 `intent_string`（优先级：调用方 `intent_hint` → matter_type + 主导填充字段 → “general”）。运行 `python scripts/diagram_selector.py --extraction-json <enriched JSON>`。置信度路由：≥ 0.75 → 接受；0.50-0.74 → 内联说明推荐并继续（不提问）；< 0.50 → 呈现前 2 个并询问（这是直接模式中唯一允许的中断）。

## 第 6 步——预先确认（条件性）

`skip_confirmation=true` → 一行状态，继续。`skip_confirmation=false`（教程）→ 显示丰富化结果的格式化摘要，询问“看起来对吗？”（Does this look right?）

## 第 7 步——返回调用方

返回丰富化的 `ExtractionResult`、已确认的 `diagram_type`、`rationale`、`extraction_warnings[]` 和 `coverage` 块（以便 `direct.md` 在交付时标注缺失的高价值字段）。
