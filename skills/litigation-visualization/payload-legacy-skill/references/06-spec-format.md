# 可视化规格、来源回链与交付一致性

先生成来源化 JSON 规格，再据此生成 Mermaid、表格、PPT、DOCX 或其他可编辑图。规格是材料、分析与视觉之间的中间层，不是证据真实性、证明力、裁判结论或现行法正确性的认证。

## 三个记录主维度、独立裁判处理维度与规格级工作流门

统一术语是“3 个记录主维度 + 独立裁判处理维度 + 1 个规格级工作流门”，不得合并命名。每个 `node`、`edge`、`claim` 都必须分别记录：

| 维度 | 允许值 | 回答的问题 |
|---|---|---|
| `fact_status` | `confirmed` / `disputed` / `unknown` | 当前登记材料能否支持这条记录，是否存在冲突 |
| `record_type` | `fact` / `source_statement` / `inference` / `legal_rule` | 这条内容是什么性质 |
| `lifecycle` | `current` / `superseded` / `not_applicable` | 这条记录在当前版本是否仍适用 |

裁判处理另用独立的 `adjudication_status=not_adjudicated/party_admission/procedurally_disputed/judicially_determined`，非 `not_adjudicated` 时还必须提供 `adjudication_refs`。规格或版本顶层另有且只有一个 `workflow_status=ready/research_draft/hold`；不得下沉为节点、边或主张状态。

`confirmed` 是人工或受控流程对“当前获准材料支持该记录，且未见实质冲突”的低承诺标记；对外显示为“当前材料支持”，不能推导为“事实真实”“证据采信”或“法院确认”。验证脚本只检查来源定位格式和来源登记表回链，不验证这个人工判断本身。

`superseded` 和 `not_applicable` 必须另有非空 `lifecycle_reason`。不要把 `not_applicable`、`superseded` 或 `inference` 塞进 `fact_status`。

## 完整最小示例

以下示例是虚构的本地研究规格。它不包含法律规则、管辖、流程图、期限、时效、救济或上诉等触发内容，因此始终存在的 `legal_review` sentinel 使用 `required=false`。

```json
{
  "case_id": "CASE-LOCAL-001",
  "audience": "内部案件团队",
  "purpose": "核对交易关系与材料缺口",
  "source_cutoff": "2026-07-21",
  "workflow_status": "research_draft",
  "hold_control": null,
  "spatial_review": null,
  "source_ledger": [
    {
      "source_id": "E-001",
      "source_kind": "evidence",
      "source_hash_or_version": "version:synthetic-contract-v1",
      "custody_or_processing_location": "local_only",
      "ingested_at": "2026-07-21",
      "source_cutoff": "2026-07-21",
      "authorized_use": ["internal_case_analysis"],
      "locator_prefix": "E-001#",
      "page_or_unit_locator_scheme": "scanned PDF page number",
      "ocr_or_derivation_note": "OCR is an index only; quoted fields are checked against the page image",
      "description": "合同扫描件"
    },
    {
      "source_id": "P-001",
      "source_kind": "party_statement",
      "source_hash_or_version": "version:synthetic-interview-v1",
      "custody_or_processing_location": "local_only",
      "ingested_at": "2026-07-21",
      "source_cutoff": "2026-07-21",
      "authorized_use": ["internal_case_analysis"],
      "locator_prefix": "P-001#",
      "page_or_unit_locator_scheme": "numbered paragraphs",
      "ocr_or_derivation_note": "born-digital record; no OCR",
      "description": "甲方访谈记录"
    }
  ],
  "privacy_authorization": {
    "processing_location": "local_only",
    "allowed_processors": ["internal:case_team"],
    "allowed_recipients": ["internal:case_team"],
    "allowed_channel": "local_only",
    "field_allowlist": ["case_id", "labels", "source_ids", "facts"],
    "redaction_status": "internal_minimized",
    "retention_policy": "delete_with_matter_schedule",
    "human_release_approved": false,
    "human_release_by": null,
    "human_release_at": null,
    "authorization_basis": "仅供已授权内部案件团队本地研究；未批准外发"
  },
  "legal_review": {
    "required": false,
    "jurisdiction": "not_applicable",
    "legal_rule_refs": [],
    "effective_at": "not_applicable",
    "law_checked_at": null,
    "law_check_status": "not_required",
    "reviewer": "not_applicable"
  },
  "nodes": [
    {
      "id": "N-001",
      "label": "甲方陈述其已签署合同",
      "fact_status": "confirmed",
      "record_type": "source_statement",
      "lifecycle": "current",
      "asserted_by": "甲方（经P-001登记）",
      "verification_basis": "仅核对P-001定位处存在该陈述，未核实陈述真实性",
      "adjudication_status": "not_adjudicated",
      "adjudication_refs": [],
      "support_refs": ["P-001#para-3"],
      "conflict_refs": [],
      "context_refs": [],
      "gap_reason": "none"
    },
    {
      "id": "N-002",
      "label": "签署行为是否真实发生待核",
      "fact_status": "unknown",
      "record_type": "fact",
      "lifecycle": "current",
      "asserted_by": "案件团队待核命题",
      "verification_basis": "现有材料仅提供背景，尚无可作为证明的定位",
      "adjudication_status": "not_adjudicated",
      "adjudication_refs": [],
      "support_refs": [],
      "conflict_refs": [],
      "context_refs": ["E-001#p2", "P-001#para-3"],
      "gap_reason": "缺少签署页原件及签署过程材料"
    }
  ],
  "edges": [],
  "claims": [],
  "legend": {
    "confirmed": "登记来源支持当前记录；不等于法院已确认",
    "disputed": "登记来源或当事人口径冲突",
    "unknown": "材料不足或仅有背景，不得补全"
  }
}
```

## 顶层字段

- `case_id`、`audience`、`purpose`、`source_cutoff` 必须是非空字符串。模板中使用稳定的本地 ID，不放真实姓名或公开案号。
- `workflow_status` 只允许 `ready`、`research_draft`、`hold`。它是规格级唯一工作流门，不表达事实状态，也不得复制到元素。
- `hold_control`：`workflow_status=hold` 时为完整对象，其他状态时必须为 `null`。
- `spatial_review`：空间触发时为完整对象，非空间任务可为 `null`。
- `source_ledger` 是来源登记表；至少登记一项。
- `privacy_authorization` 是处理与外发授权侧车；缺失即验证失败。
- `legal_review` 是始终存在的 sentinel；无触发内容也不得缺失。
- `nodes`、`edges`、`claims` 必须是数组；三类元素的 `id` 在整个规格内唯一。
- `legend` 只能解释 `confirmed`、`disputed`、`unknown` 三种事实状态，三项均须非空。图中还应使用颜色之外的第二编码。

## 来源登记与定位格式

每个 `source_ledger` 项必须包含：

- `source_id`：只用字母、数字、点、下划线、连字符；例如 `E-001`。
- `source_kind`：只允许 `evidence`、`party_statement`、`legal_authority`、`decision`、`context`、`derived`；法律规则定位只能回链到 `legal_authority` 或 `decision`。
- `source_hash_or_version`：使用 `sha256:<64位小写十六进制>`、`version:<portable-id>` 或 `unhashed-with-reason:<具体原因>`。
- `custody_or_processing_location`：来源的保管或处理边界，不写机器绝对路径。
- `ingested_at`：真实 `YYYY-MM-DD` 日期。
- `source_cutoff`：该来源纳入当前规格的截止点。
- `authorized_use`：至少一项的用途数组。
- `locator_prefix`：必须等于 `source_id` 加 `#`；例如 `E-001#`。
- `page_or_unit_locator_scheme`：说明该来源内部采用页、段、单元格或时间戳中的哪一种定位体系。
- `ocr_or_derivation_note`：说明 OCR、转录、计算或其他派生过程及核对边界。
- `description`：可识别该材料的非空说明；不要写机器绝对路径。

所有引用字段只接受以下四种完整定位：

```text
SOURCE_ID#pN
SOURCE_ID#para-N
SOURCE_ID#cell-A1
SOURCE_ID#ts-HH:MM:SS
```

其中页号、段号及单元格中的行号从 1 开始，时间为合法的 24 小时制；这里的 `cell-A1` 是表格单元格，不是一般文本“行号”。每个引用中的 `SOURCE_ID` 必须已存在于 `source_ledger`。绝对路径、`file://` URI、空白字符串、简写页码和未登记的伪来源 ID 都会失败。

## 每个元素的字段

每个 `node`、`edge`、`claim` 至少需要：

- 唯一且非空的 `id`；
- `label` 或 `text`；
- `fact_status`、`record_type`、`lifecycle`、`adjudication_status`；
- `asserted_by`：谁提出或记录了该命题；
- `verification_basis`：当前做过什么核对，以及核对边界；
- `adjudication_refs`、`support_refs`、`conflict_refs`、`context_refs` 与 `gap_reason`；没有对应定位时使用空数组，没有缺口时明确写 `none`。

`asserted_by` 必须识别具体说话人、当事人、记录者或来源角色，不能写 `not_applicable`，也不能写空泛的 `unknown`、`未知`、`未注明`。`record_type=source_statement` 时，来源陈述“被材料记录”与陈述内容“事实成立”必须拆成不同记录。

`adjudication_status=not_adjudicated` 时使用 `adjudication_refs=[]`。其他三种状态必须给出非空 `adjudication_refs`：当事人承认使用 `party_admission`，程序上仍有争议使用 `procedurally_disputed`，生效或待说明效力的裁判认定使用 `judicially_determined`。最后一种状态的定位必须回链到 `source_kind=decision`；这仍不等于验证脚本判断了裁判效力或实体正确性。

`edge` 还必须给出 `from`、`to`，且两端必须指向已登记节点。连线标签使用方向明确的事实动词。

## 引用规则

| `fact_status` | `support_refs` | 可选补充字段 |
|---|---|---|
| `confirmed` | 至少一个非空、合规且已登记的定位 | 可用 `context_refs`；不得同时存在非空 `conflict_refs` |
| `disputed` | 至少一个非空、合规且已登记的定位 | 必须有非空 `conflict_refs`；可用 `context_refs` |
| `unknown` | 不得提供证明性定位；省略或使用空数组 | 必须有非空 `gap_reason`；可用 `context_refs`、`conflict_refs` |

`context_refs` 只表示背景或调查线索，不能把未知项升级成已确认。`conflict_refs` 并列保存冲突定位；若确认冲突已解决，应形成新版本及解决记录，不能一边保留冲突一边标 `confirmed`。`gap_reason` 说明未知项为什么尚不能闭合。不要使用旧字段 `status` 或 `source_refs`。

## 暂停控制与空间复核

`hold_control` 与规格级工作流门严格联动：

- `workflow_status=hold` 时必须是对象，完整包含非空 `scope`、`reason`、`owner` 与至少一项 `recovery_conditions`；
- `workflow_status=ready` 或 `research_draft` 时必须为 `null`；
- 它只说明暂停范围与恢复路径，不得改变元素的 `fact_status`、`record_type`、`lifecycle` 或 `adjudication_status`。

`spatial_review` 在标题、目的或模式涉及空间、现场、路线、边界、方位、平面、坐标或测绘时必须是对象，并完整包含：

- `required=true`；
- `diagram_kind`：仅 `not_to_scale_schematic`、`to_scale` 或 `coordinate_map`；
- `measurement_method`、`coordinate_system_or_scale`、`direction_basis`；
- `collected_at`：真实 `YYYY-MM-DD` 日期；
- `data_version`、`occlusion`、`measurement_error`、`projection_distortion`、`temporal_change`、`viewpoint_bias`、`modeling_assumptions`。

非空间任务使用 `spatial_review=null`。字段齐全不等于测绘、勘验或鉴定正确，空间语义仍须人工复核。

## 隐私与外发授权门

`privacy_authorization` 必须完整包含以下字段：

- `processing_location`：默认 `local_only`；
- `allowed_processors`：至少一项，使用 `internal:<role>` 或 `external:<role>`；
- `allowed_recipients`：至少一项，使用相同前缀；默认仅 `internal:case_team`；
- `allowed_channel`：默认 `local_only`；
- `field_allowlist`：至少一项，只列获准进入处理或交付面的语义类别；可用类别为 `case_id`、`labels`、`facts`、`legal_rules`、`source_ids`、`dates`、`amounts`、`relationships`、`procedures`、`spatial_data`、`notes`；
- `redaction_status`、`retention_policy`：非空；
- `human_release_approved`：布尔值，默认 `false`；
- `human_release_by`、`human_release_at`：放行人为明确角色/姓名，日期为真实 `YYYY-MM-DD`；未放行时两者必须为 `null`；
- `authorization_basis`：始终为非空具体依据，放行时不得写 `unknown`、`not_applicable` 等空泛值。

出现以下任一情形即视为离开本地边界：`processing_location` 不是 `local_only`、处理者或接收者含 `external:`、`allowed_channel` 不是 `local_only`。若此时 `human_release_approved=false`，`workflow_status` 必须是 `hold`，不能写成 `ready` 或 `research_draft`。授权侧车只控制允许的处理边界，不自动证明材料可以公开。

## 法律核验门

`legal_review` 是始终存在的 sentinel，必须完整包含：

- `required`：布尔值；
- `jurisdiction`、`effective_at`、`reviewer`：非空；无触发内容时可明确写 `not_applicable`；
- `legal_rule_refs`：引用格式与登记表规则相同；
- `law_checked_at`：`verified` 时必须非空，其他状态可为 `null`；
- `law_check_status`：只允许 `not_required`、`pending`、`verified`。

无触发内容时，必须写 `required=false`、`law_check_status=not_required`、`legal_rule_refs=[]`；sentinel 不得省略。

出现 `record_type=legal_rule`，或 `purpose` / `title` / `visual_mode` / `mode` / `diagram_type` 含法条、法律、管辖、流程图、程序、期限、时效、法定条件、裁判规则、救济、上诉等触发信号时，`required` 必须为 `true`。此时：

1. `law_check_status=verified` 才能进入 `workflow_status=ready`；
2. `verified` 必须有至少一个回链到 `source_kind=legal_authority` 或 `decision` 的 `legal_rule_refs`、采用 `YYYY-MM-DD` 的 `law_checked_at`，以及明确的法域、适用时点和复核者；
3. `legal_review.legal_rule_refs` 必须逐条覆盖每个 `record_type=legal_rule` 的所有 `support_refs`，不能只登记一条概括性法源；
4. 尚未核验时只能使用 `research_draft` 或 `hold`；
5. `required=true` 不得使用 `not_required`，`required=false` 则只能使用 `not_required`。

验证通过只表示法律核验 sentinel 的字段、回链和逐条覆盖关系齐全；脚本不判断法条是否现行、解释是否正确或是否适用于案件。触发后的核验必须是获授权人工法律复核者进行的实质核验，不能由 sentinel 存在或脚本退出码替代。

## 规格验证

在 Skill 根目录运行：

```bash
python3 scripts/validate_spec.py path/to/spec.json
```

成功文案会明确写出：规格结构、定位格式、来源登记表回链及隐私/法律门字段一致性已经检查，但实体真实性、证据权重、授权真实性、裁判效力和法律正确性尚未由脚本验证。不要把退出码 0 改写成实体结论。

## 从规格到图

1. 冻结当前规格和来源登记表，并记录规格 SHA-256。
2. 按 `references/00-router.md` 选图。
3. 复制最接近的 `assets/` 模板，用稳定 ID 替换占位内容。
4. 每个图中元素必须继承规格的状态和定位，不能在渲染阶段另造事实或来源。
5. 对未进入主图的规格元素记录非空省略理由；不能静默丢失。
6. 输出可编辑图、同源文字/表格、未知项清单、版本说明和渲染清单。
7. 法院可见件与内部治理记录分开；外发前重新执行权限、隐私和现行法人工检查。

## 渲染清单与输出一致性门

渲染清单使用以下结构，路径相对于清单所在目录：

```json
{
  "spec_sha256": "64位小写SHA-256",
  "released_fields": ["facts", "labels", "source_ids"],
  "artifacts": [
    {"path": "diagram.mmd", "sha256": "64位小写SHA-256"}
  ],
  "elements": [
    {"id": "N-001", "disposition": "included", "artifact": "diagram.mmd", "locator": "line:4"},
    {"id": "C-009", "disposition": "omitted", "reason": "当前图只展示资金流，命题保留在同源表"}
  ]
}
```

规则：

- `spec_sha256` 必须与规格文件字节完全一致；
- `released_fields` 必须是非空、去重的语义类别数组，并且是 `privacy_authorization.field_allowlist` 的子集；渲染 `legal_rule` 时必须含 `legal_rules`，渲染 `fact`、`source_statement` 或 `inference` 时必须含 `facts`；
- 每个 artifact 使用相对路径并登记真实 SHA-256；禁止绝对路径、父目录穿越和符号链接；
- 规格中的每个元素 ID 必须恰好出现一次，不得漏项、重复或增加未知 ID；
- `included` 必须指定已登记 artifact。`line:` 只用于 UTF-8 文本，目标行或行段必须存在且包含对应元素 ID；`cell:` 只用于 CSV/TSV，目标单元格必须包含元素 ID；`node:`、`shape:`、`table:` 的 token 必须等于元素 ID且出现在可检查文本中；`slide:` 只用于 PPTX，目标幻灯片必须存在且其 XML 中含元素 ID；
- `page:` 当前不受 bundled standard-library checker 支持，会明确失败，不能用于声称页面几何已核验；所有 locator 均禁止斜杠、反斜杠和 `..`；
- `omitted` 必须给出非空 reason，且不得伪装 artifact/locator；
- 清单顶层只允许 `spec_sha256`、`released_fields`、`artifacts`、`elements`；artifact 项和 element 项同样采用字段白名单，不能借 `text`、`metadata` 或嵌套对象绕过规格并重写语义；
- 清单元素不得重写 `fact_status`、各类引用、`record_type`、`lifecycle`、`asserted_by`、`verification_basis`、`gap_reason` 或 `adjudication_status`，这些语义一律继承规格；
- artifact 不得含 `TODO_DO_NOT_DELIVER`、绝对路径或 `file://` URI。

DOCX、PPTX、XLSX 会作为 Office ZIP 容器解压；脚本限制展开体积，检查成员路径安全，并扫描 XML/关系/文本成员中的占位符、绝对路径和父目录穿越。该过程只提供可检查文本与 PPTX slide ID 目标核对，不等于实际 Office 版面或视觉语义已经审查。

运行：

```bash
python3 scripts/validate_output.py path/to/spec.json path/to/render-manifest.json
```

该脚本检查规格/artifact 哈希、声明放行字段子集、精确元素覆盖、定位目标 ID 和常见泄漏标记。它不判断视觉语义、未建模断言、事实或法律实质正确性，也不验证真实授权；这些仍须人工视觉、法律、隐私和交付复核。
