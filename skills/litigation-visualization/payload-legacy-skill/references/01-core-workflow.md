# 核心工作流

## 0. 触发、授权与默认边界

凡请求把诉讼材料转成图、矩阵或结构化视觉规格，或审查现有诉讼图是否遗漏、失真或误导，先触发本 Skill 并执行安全门。纯法律检索、纯文字校对或纯文字摘要不触发；授权不明或违规公开不是“不触发”，而是触发后停止。

默认策略是：本地处理、不外发、原件只读、最小字段、最短必要保留。先记录受众、用途、材料截止点、处理位置、处理器、接收人、渠道和禁止用途，再判断能否继续：

- 当前用途、材料范围、处理位置、处理器、接收人、渠道或允许字段不明确：`workflow_status=hold`。
- 外部处理器或外部接收人尚未获批准：`workflow_status=hold`，不得先上传后补授权。
- 用户要求违法或未授权公开真实案情：拒绝该动作，并保留最少必要审计记录。
- 权限完整但现行法、程序或期限尚待研究：内部可继续时设 `workflow_status=research_draft`；若未核验会改变对外提交、行动路径或重大结论，设 `workflow_status=hold`。
- 所有适用门均通过且人工复核范围满足当前渠道要求：`workflow_status=ready`。

## 1. 建立治理 sidecar 与条件控制

治理记录与法院、仲裁庭或客户可见件物理分开，不把绝对路径、内部风险标签或构建日志带入交付正文。

### 1.1 `source_ledger`

每项材料至少记录：

```text
source_id:
source_kind:
source_hash_or_version:
custody_or_processing_location:
ingested_at:
source_cutoff:
authorized_use:
locator_prefix:
page_or_unit_locator_scheme:
ocr_or_derivation_note:
description:
```

以上 11 个字段缺一不可；`authorized_use` 是非空用途数组，`source_hash_or_version` 记录哈希、版本或无法哈希的具体理由。OCR 只作检索层。关键主体、日期、金额、条款、方向和短引必须回看原页，并在底稿中使用稳定 `source_id` 与来源内部的页、段、单元格或时间戳定位。

### 1.2 `privacy_authorization` 治理 sidecar

至少记录：

```text
processing_location:
allowed_processors:
allowed_recipients:
allowed_channel:
field_allowlist:
redaction_status:
retention_policy:
human_release_approved:
human_release_by:
human_release_at:
authorization_basis:
```

sidecar 只控制谁可在何处通过何渠道处理或接收哪些字段，不是案件事实的一部分。`human_release_approved=true` 时，`human_release_by`、`human_release_at` 与具体 `authorization_basis` 必须齐全；未放行时前两项为 `null`。接收人、渠道或字段白名单变化时重新过门；不能沿用上一版本的放行。

### 1.3 始终存在的 `legal_review` sentinel

每个规格都建立：

```text
jurisdiction:
required:
legal_rule_refs:
effective_at:
law_checked_at:
law_check_status:
reviewer:
open_questions:
```

无触发内容时写 `required=false`、`law_check_status=not_required`、`legal_rule_refs=[]`，sentinel 仍不得省略。出现 `record_type=legal_rule`，或标题、目的、模式中包含法条、法律、管辖、流程图、程序、期限、时效、法定条件、裁判规则、救济、上诉等内容时，必须写 `required=true` 并进行人工实质核验。`law_check_status=verified` 还须有明确的法域、适用时点、核验日期和人工复核者；`legal_review.legal_rule_refs` 必须逐条覆盖每个 `legal_rule` 记录的全部 `support_refs`，且只回链 `legal_authority` 或 `decision`。书中历史规范、模型记忆和未核网页不能完成该门。未完成时按风险设 `workflow_status=research_draft` 或 `workflow_status=hold`，不得把研究草稿当作可行动结论。

### 1.4 `hold_control` 与 `spatial_review`

`workflow_status=hold` 时，`hold_control` 必须记录非空 `scope`、`reason`、`owner` 和非空数组 `recovery_conditions`；其他工作流状态下必须为 `null`。暂停只限受影响的动作，不改变记录事实状态。

空间、现场、路线、边界、方位、平面、坐标或测绘相关视觉必须建立 `spatial_review`，完整记录 `required`、`diagram_kind`、`measurement_method`、`coordinate_system_or_scale`、`direction_basis`、`collected_at`、`data_version`、`occlusion`、`measurement_error`、`projection_distortion`、`temporal_change`、`viewpoint_bias`、`modeling_assumptions`。非空间任务使用 `spatial_review=null`。

## 2. 建立来源化 SSOT

不要直接从长文生成图。先形成四张中间表：

1. 主体表：稳定 ID、名称/匿名名、角色、别名、来源。
2. 事件表：事件 ID、日期或区间、行为、主体、对象、3 个记录主维度、独立裁判处理维度和来源。
3. 关系/流向表：起点、终点、关系或流向、数量、时间、3 个记录主维度、独立裁判处理维度和来源。
4. 争点证据表：争点、可判断命题、支持材料、冲突材料、反证、上下文、缺口和核验责任。

### 2.1 三个记录主维度、独立裁判处理维度与规格级工作流门

三个记录主维度互相独立，不得把某一维的值写进另一维：

| 维度 | 允许值 | 回答的问题 |
|---|---|---|
| `fact_status` | `confirmed` / `disputed` / `unknown` | 当前允许材料怎样支持这个命题？ |
| `record_type` | `fact` / `source_statement` / `inference` / `legal_rule` | 这条记录是什么性质？ |
| `lifecycle` | `current` / `superseded` / `not_applicable` | 该记录当前是否继续适用？ |

程序或裁判处理使用独立的 `adjudication_status=not_adjudicated/party_admission/procedurally_disputed/judicially_determined`；它不是第四个记录主维度，后三种必须有 `adjudication_refs`。规格或版本顶层另有且只有一个 `workflow_status=ready/research_draft/hold` 工作流门，不得复制到节点、边或主张。

`HOLD` 不是事实状态；`inference` 不是事实状态；`superseded` 与 `not_applicable` 也不是事实状态。流程暂停不改变命题获得材料支持的程度，命题状态变化也不会自动解除权限或法律核验门。

### 2.2 `fact_status` 的低承诺语义

- `confirmed`：当前允许使用的材料支持该命题，且当前输入未见实质冲突。对外优先标为“当前材料支持”。它不等于无争议、已由独立调查查证、裁判确认或终局认定。
- `disputed`：当前材料中存在实质对立口径、支持与冲突材料或相互竞争的推论。并列 `support_refs` 与 `conflict_refs`，不替裁判者决断。
- `unknown`：当前材料不足以支持命题。`support_refs=[]`；允许填写 `context_refs`、`conflict_refs` 与 `gap_reason`，但上下文、相邻事实或“没有发现相反材料”不能冒充支持。

来源中确实出现一句陈述，只能证明“某人在某材料中作了该陈述”时，写 `record_type=source_statement`，并填写：

```text
asserted_by:
verification_basis:
```

不要因陈述存在而把其内容自动写成 `record_type=fact`。若需表达程序或裁判处理，另设 `adjudication_status=not_adjudicated/party_admission/procedurally_disputed/judicially_determined`；后三种必须有 `adjudication_refs`，其中裁判认定还须回链到 `source_kind=decision`。另行人工核对裁判文书层级与效力，不得由 `fact_status=confirmed` 推导。

### 2.3 其他维度

- `record_type=fact`：中性、可由材料核对的事件、关系或数值命题。
- `record_type=source_statement`：明确归属于某一陈述者的说法，必须带 `asserted_by` 与 `verification_basis`。
- `record_type=inference`：从事实作出的解释、因果、意图或法律策略判断；明确推理链和替代解释。
- `record_type=legal_rule`：法条、程序条件、期限或裁判规则；必须经过 `legal_review` 才能进入可行动输出。
- `lifecycle=current`：在当前版本与任务范围内继续适用。
- `lifecycle=superseded`：已被后续材料、修订或版本替代，保留追溯但不作为当前依据。
- `lifecycle=not_applicable`：经说明后确定不适用于当前对象、法域、期间或问题，保留排除理由。
- `workflow_status=ready`：只对已定义的受众、渠道、字段和版本表示可进入下一步，不是对事实或法律正确性的保证。
- `workflow_status=research_draft`：研究或法律核验未完成，仅限获授权的内部研究用途。
- `workflow_status=hold`：授权、隐私、法源、来源完整性或其他强制门失败；停止受影响的下游动作并记录恢复条件。

图表发现错误时先修正 SSOT，再重新生成图，不直接“修图掩错”。

## 3. 四步法

### A. 明确对象

记录受众的已有知识、当前任务、信息壁垒和可接受详略。决定是否需要图、是否需要多版本，以及哪些内部字段必须排除。

完成标准：能用一句话说明“这张图帮助谁完成什么任务”，且 `privacy_authorization` 覆盖当前处理与接收路径。

### B. 选择类型

按 [00-router.md](00-router.md) 判断核心要素。先选最小够用的图形；有多个核心要素时拆图或建立主从结构。

完成标准：选择理由能关联到争点或理解障碍，而不是“素材里刚好有日期、关系或数字”。空间图还须加载 [02-visual-patterns.md](02-visual-patterns.md) 的空间章节及其指定模板。

若任务是审查现有诉讼图，先把现图中的节点、边、形状、表格或幻灯片元素及其明示/暗示命题编号，再与 SSOT、来源、反证、未知项和权限逐项比对。审查输出必须指出遗漏、错误方向、视觉强弱暗示、未建模断言及需要人工判断的部分；不能把“文件能打开”当成完整性通过。

### C. 确定内容

依次执行：

1. 全面罗列：在私域底稿中记录所有可能相关的命题、证据、冲突、上下文与缺口。
2. 逻辑整合：按时间、关系、数据、程序或争点建立结构。
3. 3S 精简：Simple、Straight、Strategy。删冗余，不删决定结论的限定、关键条款、反证和未知项。

每个排除项记录理由，至少区分“与目的无关”“另图承载”“权限禁止”“来源不足”“`lifecycle=superseded`”和“`lifecycle=not_applicable`”。后两项是生命周期，不是事实状态。

完成标准：图中每个元素都有任务价值；支持性内容有来源，`unknown` 明示缺口且不把上下文当支持；被删内容不会改变命题或制造单边叙事。

### D. 更好表达

建立稳定图例后再使用颜色、线条、箭头、框架和空间层级。视觉强弱必须有语义或数量依据；不得靠夸张比例、面积或色彩暗示尚未证明的结论。

完成标准：灰度打印、投影和小屏阅读时仍能区分；不依赖颜色作为唯一编码；读者能区分 3 个记录主维度、独立裁判处理维度和规格级流程限制。对外将 `confirmed` 显示为“当前材料支持”，不要显示为“已查明”。

## 4. 验证与状态转换

至少执行：

- 来源回链：随机抽取节点、连线和主张，能回到具体材料定位；`unknown` 的上下文只用于说明缺口。
- 完整性：争点相关的反方事实、反证、冲突和缺口没有被静默删除。
- 一致性：主体名、日期、金额、方向、3 个记录主维度、独立裁判处理维度和规格级工作流门在图、SSOT 与治理 sidecar 中保持层级一致。
- 视觉误导：比例、粗细、颜色、空间距离和箭头没有制造额外事实。
- 法律状态：适用的法条、程序期限和裁判规则已由权威来源按日期核验；否则保持 `research_draft` 或 `hold`。
- 隐私与权限：`privacy_authorization` 中的处理位置、处理器、接收人、渠道、字段白名单、脱敏、保留和人工放行与实际输出一致。
- 人工复核：记录复核人、日期、范围、发现和放行对象；人工通过只对该版本、该受众和该渠道有效。

若先生成 JSON 规格，可运行：

```bash
python3 scripts/validate_spec.py path/to/spec.json
```

该脚本检查结构、来源定位格式、来源登记表回链及隐私/法律/暂停/空间门字段一致性，不判断实体真实性、证据权重、授权真实性、裁判效力或法律正确性。

生成图后还要运行输出一致性门：

```bash
python3 scripts/validate_output.py path/to/spec.json path/to/render-manifest.json
```

render manifest 必须声明 `released_fields`，且只能是 `privacy_authorization.field_allowlist` 的子集。输出脚本检查规格与 artifact 哈希、规格元素一一覆盖、常见路径/占位符泄漏，并验证：`line:` 指向 UTF-8 文本且目标行含元素 ID；`cell:` 指向 CSV/TSV 单元格且含元素 ID；`node:`、`shape:`、`table:` 的 token 等于元素 ID且出现在可检查文本中；`slide:` 指向真实 PPTX 幻灯片且该页 XML 含元素 ID。`page:` 不受支持。DOCX/PPTX/XLSX 会作为 Office ZIP 解压，逐成员扫描占位符、绝对路径与父目录穿越。

上述机械检查不能判断视觉语义是否忠实、是否存在未建模断言、内容是否实质正确或放行授权是否真实；这些仍须人工视觉、法律、隐私与交付复核。

状态恢复遵循：

1. `hold` 只有在对应授权、隐私、法源、来源或视觉风险问题已解决，并记录人工放行后，才能转为 `research_draft` 或 `ready`。
2. `research_draft` 只有在条件触发的研究和法律核验完成、未决问题得到处置并完成相应人工复核后，才能转为 `ready`。
3. 新接收人、新渠道、新字段、新材料或新法域会重新触发相应门；旧版本的 `ready` 不自动继承。
4. 不得为了推进流程，把 `unknown` 改成 `confirmed`，也不得用 `lifecycle=not_applicable` 隐藏不利或冲突材料。

## 5. 默认交付

```text
1. 可编辑图表或矩阵
2. 图例与口径
3. 来源表（内部/客户版按权限提供）
4. 未知项、冲突、反证与待核清单
5. 版本、材料截止点和法律核验日期
6. workflow_status 与人工复核状态
```

法院可见件与 `source_ledger`、`privacy_authorization`、`legal_review`、`hold_control`、`spatial_review` 等治理 sidecar 必须分开；法院可见文本不得出现内部风险标签、绝对路径、构建日志或未获准字段。实际交付字段必须由 render manifest 的 `released_fields` 明示，并且不超出当前 `field_allowlist`。

来源方法：`lv-jy-2017` PDF 23–24、26–38、105–155；SSOT、三主维度/独立裁判处理/规格级工作流门、低承诺状态语义、反证、隐私授权与输出分层为皋陶强化。
