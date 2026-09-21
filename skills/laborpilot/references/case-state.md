# 案件图状态数据契约

> 废止复核（2026-09-07）：浙江本次七件地方文件的 `validity_status` 必须为 `repealed`，采用状态仅 `reference_only`／`excluded`。历史事实日期或空 `effective_to` 均不能使其成为现行依据；不能据目录日补造终止日期。

## 用途

`.casework/case_state.json` 是同一案件跨任务、跨阶段的唯一结构化状态入口。它不替代原始案卷，只记录来源、分析状态、工作图运行和经用户确认的决定。完整结构见 [case-state.schema.json](case-state.schema.json)，目录规范见 [output-layout.md](output-layout.md)。

## 基础字段

- `case_id`：案件本地唯一标识，不放身份证号或手机号。
- `task_context`：用户确认的本轮具体任务、期望产物、限制及确认记录。该字段未完整时不得处理案件材料。
- `representation`：`employee`、`employer` 或 `undetermined`。未确认委托立场时必须使用 `undetermined`，不得为了通过 Schema 猜测一方。
- `stage`：未确认时为 `undetermined`；确认后为 `intake`、`pre_arbitration`、`arbitration`、`first_instance`、`second_instance` 或 `closure`。
- `jurisdiction`：默认“浙江省”，具体管辖地另行记录。
- `analysis_date`：ISO 日期，作为时效和新旧法分析基准。
- `risk_level`：`standard`、`complex` 或 `high`，控制验证深度和律师升级要求。

## 业务状态

1. `facts[].status` 只能为 `supported`、`client_statement`、`opponent_allegation`、`disputed` 或 `to_verify`。
2. `supported` 事实至少关联一份材料来源。
3. `decisions[]` 只记录用户明确确认的事实、策略、金额或文书口径，并记录确认人与日期。
4. 不在状态文件中嵌入身份证、病历、聊天记录等原始材料全文，只记录本地路径和摘要。

## 工作图状态

- 新案件必须从 `task_intake` 启动。只有 `task_context`、`representation` 和 `stage` 获得用户确认后，才能进入 `material_ingestion`。
- `current_node`、`pending_nodes` 与 `node_runs`：当前节点、分支待执行节点及每次执行的输入、产物、执行者和结果。
- `validations`：验证者、结论、问题、验证报告路径／哈希，以及本次实际检查的产物 ID／哈希快照。
- `approvals`：策略审批和律师交付审批。律师批准必须绑定具体正式产物、产物哈希、验证记录和验证报告哈希，不能只保存抽象的“已同意”。
- `checkpoints` 与 `paused`：暂停原因、恢复条件和恢复位置。
- `artifacts`：产物交付层级、路径、版本、SHA-256、生成器、LaborPilot 版本、生成者、生成时间、业务来源摘要和上游产物。
- `node_requirement_waivers`：用户明确确认的节点完成条件豁免，至少记录节点、条件编号、具体理由、确认人与时间；空备注不构成豁免。
- `events`：只追加不静默改写的审计日志。

节点通过时，工作图会检查 `materials`、`facts`、`issues`、`evidence`、`rules`、`claims`、`artifacts` 和 `validations` 中对应的结构化记录。即使手工把 `current_node` 改到下游，独立验证仍会重新检查全部上游完成条件。

验证记录同时保存 `report_path`、`report_sha256` 和被验证产物的哈希快照。对抗验证报告还必须包含当前业务状态摘要、六项检查、事实冲突矩阵、程序完整性矩阵和逐争点挑战矩阵；验证节点每次转换都会重新读取报告、核对文件哈希，并按当前案件状态重算报告内容，避免过期报告或事后修改继续生效。

正式产物的完整字段和复算规则见 [正式产物端到端追溯契约](artifact-traceability.md)。`trace-artifact` 会沿 `source_refs[]` 和 `derived_from[]` 反查业务来源、上游文件、验证报告和律师审批；来源记录、上游文件、正式文件或报告被事后修改，原批准不能继续作为阶段结案依据。

经用户或律师确认的数值、事实或策略口径使用 `case_state.py record-decision` 写入 `decisions[]`，生成稳定 `decision_id` 并追加审计事件。后续金额输入通过 `source_ids` 引用该 ID，不应为通过计算门禁而手工编辑状态文件。重复 ID、空泛确认或无效确认日期会被拒绝。

## 版本与迁移

1. 当前 Schema 版本为 `2.0`。
2. 日常阶段变更和工作图转换就地更新单一 `case_state.json`；写入前自动将旧状态保存到 `.casework/history/`，`previous_state` 指向该内部快照。
3. 1.0 状态使用 `python3 scripts/case_state.py migrate` 生成 2.0 文件，不覆盖旧文件；迁移完成后以 `.casework/case_state.json` 作为唯一当前状态。
4. 新材料与旧状态冲突时，保留两种记录并标记待确认，不静默覆盖。

## 材料可追溯字段

原始文件至少登记 `source_path`、`source_sha256`、大小、文件类型、页码范围、文字层状态、逐材料接入记录和 `original_or_copy`。存在 OCR 或其他派生文件时，同时登记 `derivative_path`、`ocr_engine`、`ocr_language`、`ocr_status` 与 `visual_review_status`。OCR 结果只是定位线索，不因字段齐全而自动变成证据原文。工作图在进入下游时重新核对源文件当前哈希，不能以格式正确但未经复算的字符串代替材料保全。

事实时间轴由 `build_timeline.py` 写入 `.casework/intake/`。自动从材料中提取的日期句仅为 `to_verify`；只有显式标注且关联已登记材料的事实才可使用 `supported`。案件状态不保存身份证号和手机号，执行器会在事实陈述中将其替换为脱敏占位符。

相互矛盾的事实通过 `conflicts_with_fact_ids` 建立双向关系，并使用 `conflict_status` 区分 `unresolved` 和 `resolved`。存在冲突时必须写明 `conflict_explanation`；未解决时还必须写明具体 `conflict_next_action`。事实不得引用自身或不存在的事实，冲突双方的引用和状态必须一致；未解决冲突的任一事实不得标记为 `supported`。独立对抗验证会将仍未解决的冲突退回核实。

## 争点矩阵字段

`build_issue_matrix.py --discover` 只生成 `analysis_status=to_review` 的候选文件，不写入 `issues[]`。正式争点必须使用稳定 `issue_id`，记录 `issue_type`、代理立场、我方路径、构成要件、对方最强观点与回应、备选路径和失败后果。每个构成要件使用稳定 `element_id`，通过 `fact_ids`、`evidence_ids` 和 `rule_ids` 建立可追溯关系，并以 `supported`、`partially_supported`、`unsupported`、`disputed` 或 `to_verify` 记录支持状态。非 `supported` 要件必须明示证据或事实缺口。

旧案件中若存在只含 `issue_id` 的占位争点，须在提供完整矩阵时显式使用 `--replace-existing-issues`。执行器会以本次矩阵替换旧 `issues[]`，替换前状态仍保留在 `.casework/history/`；未显式使用该参数时，执行器拒绝在旧占位结构旁追加新争点。

## 证据链与举证责任字段

`build_evidence_chain.py --scaffold` 按已复核争点的每个 `element_id` 生成 `analysis_status=to_review` 的骨架，不写入 `evidence[]`。正式证据链使用稳定 `evidence_id`，记录 `issue_id`、`element_ids`、待证命题、证据方向、`fact_ids`、举证责任、证据项和评估结果。执行器会反向重建构成要件和对方路径的 `evidence_ids`，并拒绝无效事实／材料／争点／要件引用或单向链接。

每个争点构成要件都必须有证据链或缺口链，该条件不允许豁免。对方或第三方掌握证据时，仍须记录初始举证主体、证据控制方、责任转移条件、举证不能后果和补证行动。非 `sufficient` 评估必须同时列明 `gaps` 和 `actions`；`gap_only` 不得包含已有证据；`sufficient` 至少要有一项已关联材料且真实性状态已明确的 `available` 证据。

旧案件中若存在只含 `evidence_id` 的占位证据，须在提供完整证据链时显式使用 `--replace-existing-evidence`。替换前状态保留在 `.casework/history/`。

## 法源核验与适用性字段

`build_authorities.py --scaffold` 按每个争点构成要件生成待核验任务，不写入 `rules[]`。正式法源记录使用稳定 `rule_id`，并以 `issue_id`、`element_ids` 和 `orientation` 建立争点追溯。每条记录须保存法律全称、制定机关、效力层级、文号、条号、完整条文及 `article_text_sha256`，以及官方来源或法律数据库名称、URL 和检索时间。

时间适用性以 `effective_from`、`effective_to`、`relevant_date`、`temporal_basis` 和 `applicability_reasoning` 记录；地域适用性以 `territory_scope`、`applicable_jurisdictions` 和当前 `case_jurisdiction` 记录。正式采用项必须已核验且明确适用，未生效、效力未明或地域错配规则不得采用。已修改、废止或失效规则须写明警示；如作为历史规则适用，`relevant_date` 仍必须位于其效力期间。

每个构成要件都必须关联至少一条已验证且适用的法源，与对方路径的 `rule_ids` 也必须双向一致，该完成条件不得豁免。旧案件的占位 `rules[]` 使用 `--replace-existing-rules` 显式升级，替换前状态保留在 `.casework/history/`。

## 金额计算与请求字段

`calculate_claims.py --scaffold` 根据已复核争点生成 `review_required` 骨架，不写入 `claims[]` 或 `calculations[]`。正式计算记录使用稳定 `calculation_id` 与 `claim_id`，保存公式类型和版本、争点与法源、相关日期、逐项输入及来源、参数引用与解析结果、计算假设、待确认项、风险、算式、中间步骤、金额、舍入口径和内容摘要。每个数值输入的 `source_ids` 必须引用案件状态中已登记的事实、材料、证据、决定或其他合法来源。

`calculations[]` 与 `claims[]` 必须通过 `calculation_id`／`claim_id` 双向对应，金额、状态、争点、法源和待确认项保持一致。计算状态为 `calculated` 时，验证器会使用当前公式版本和已解析参数重新计算金额、算式与中间步骤，并核对 `calculation_digest`；状态为 `needs_confirmation` 时必须列明 `pending_inputs`，且 `amount`、`expression` 和 `steps` 分别为 `null`、`null` 和空数组。存在待确认输入的金额请求不能通过 `claims_procedure`，该条件不允许豁免。

参数包按 `references/parameter-package.schema.json` 管理版本、发布日期、效力期间、地域范围、官方来源和具体参数。解析后的参数必须保存参数包路径与 SHA-256，且覆盖计算的 `relevant_date` 和案件地域。N、N＋1、2N 的 `cap_applies` 必须明确为 0 或 1；值为 1 时须解析 `monthly_wage_cap`，值为 0 时不得混入该封顶参数。公式只执行已经选定的法律路径，不自动判断请求权成立与否，也不自动择高。

旧案件中若存在占位 `claims[]` 或 `calculations[]`，须在提供完整计算输入时显式使用 `--replace-existing-calculations`。替换前状态保留在 `.casework/history/`。金额台账作为 `calculation_ledger` 产物登记到 `artifacts[]`。

## 时效、管辖与程序路径字段

`analyze_procedure.py --scaffold` 按每个已复核争点生成待复核骨架，不写入 `procedural_assessments[]`。律师／Agent 结合已核验法源作出程序判断后，使用 `analyze_procedure.py --input` 写入正式台账；执行器不自动选择时效结论、受理机构或救济路径。

每条 `procedural_assessments[]` 使用稳定 `assessment_id` 关联唯一 `issue_id` 及该争点下的 `claim_ids`，并保存当前 `case_jurisdiction`、`analysis_date`、分析状态、待确认项、风险和 `procedure_digest`。`limitation` 记录时效结论、起算日、截止日、法源及分析；`jurisdiction` 记录管辖结论、受理机构、案件地域、法源及分析；`final_award` 与 `interim_relief` 分别记录一裁终局和先予执行／其他临时救济的适用状态、法源及分析；`remedy_paths` 记录后续起诉、申请撤销、执行或其他救济路径。

所有法源引用都必须已核验、已采用且适用于对应争点。明确标记 `in_time` 或 `out_of_time` 时，起算日和截止日必须完整，且结论与案件分析日一致；程序地域必须与当前案件一致。有 `pending_items` 时，`analysis_status` 只能是 `needs_confirmation`。

`claims_procedure` 只有在金额结果和程序结果均完成时才能通过。每个已复核争点都必须有完整程序分析，全部分析状态必须为 `reviewed` 且待确认项为空。`reviewed_procedure_path` 完成条件不允许豁免。

## 回写闭环

每轮结束至少回写：新增材料、已确认事实、待查事项、证据缺口、法源核验、程序期限、节点结果、验证与审批、成果文件和优先级最高的下一步。
