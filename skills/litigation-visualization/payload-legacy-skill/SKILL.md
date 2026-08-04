---
name: litigation-visualization-cn
description: 凡用户请求把诉讼材料转成图、矩阵或结构化视觉规格，或审查现有诉讼图是否遗漏、失真或误导，即触发本 Skill，包括案情时间线、关系或流向图、程序图、证据矩阵、空间示意和庭审图示；触发后先检查材料、用途、处理位置和接收人的授权，授权不明则设 workflow_status=hold，违法或未授权公开则拒绝。纯法律检索、纯文字校对或纯文字摘要不触发；但授权不明、违规公开不是“不触发”，而是触发安全门后停止。
---

# 中国诉讼可视化

把复杂诉讼材料转成服务特定受众、能回到来源核对的可编辑图表。图表用于分析和沟通，不是证据、法律意见、裁判结论或胜诉承诺。

## 不可妥协的规则

1. 凡请求把诉讼材料转成图、矩阵或结构化视觉规格，先进入本 Skill 的授权安全门；只处理对当前用途、处理位置、处理器、接收人和渠道均已授权的材料，原件只读。授权不明时设 `workflow_status=hold`，违法或未授权公开时拒绝。
2. 不凭常识、版面需要或模型记忆补全主体、日期、金额、关系、因果或法律结论。
3. 作为支持性内容呈现的节点、连线和主张都绑定具体来源定位；`unknown` 的 `support_refs` 必须为空，但可记录 `context_refs`、`conflict_refs` 与 `gap_reason`，不得把上下文当支持。
4. 状态概念固定为“3 个记录主维度 + 独立裁判处理维度 + 1 个规格级工作流门”：每条记录使用 `fact_status=confirmed/disputed/unknown`、`record_type=fact/source_statement/inference/legal_rule`、`lifecycle=current/superseded/not_applicable`，裁判处理另用 `adjudication_status`；规格顶层只设一个 `workflow_status=ready/research_draft/hold`。不得把这些层级合并命名。
5. 作者方法、案件事实、律师推论和现行法律规则分层。`legal_review` sentinel 始终存在；无触发内容时写 `required=false` 与 `law_check_status=not_required`。出现法条、管辖、流程图、期限、时效、法定条件、裁判规则、救济或上诉等内容时，必须由人工实质核验权威来源、适用范围与日期，并使 `legal_review.legal_rule_refs` 逐条覆盖所有 `record_type=legal_rule` 的 `support_refs`。
6. 不复制来源书的原图、连续案例、版式或长段文字。
7. 本地制作、交付当前受众、正式安装、生产晋升和外部发布是不同权限；没有明确授权时不执行后一步。

## 工作流

### 1. 定义任务门

先写清：

```text
audience:
purpose:
decision_or_understanding_barrier:
source_scope_and_cutoff:
allowed_output_and_channel:
human_reviewer:
```

同时建立 `source_ledger`、`privacy_authorization` 和始终存在的 `legal_review` sentinel；`workflow_status=hold` 时还必须建立 `hold_control`，空间、现场、路线、边界或坐标图必须建立 `spatial_review`。读取 [references/00-router.md](references/00-router.md) 与 [references/04-quality-boundaries.md](references/04-quality-boundaries.md)。默认只在本地处理且不外发；外部处理器或接收人未获批准时设 `workflow_status=hold`。若短文字或表格已足够，可以在通过安全门后选择不绘图；触发人工法律核验而尚未完成时，设 `workflow_status=research_draft`，会影响对外提交、行动路径或重大结论时设 `workflow_status=hold`。

### 2. 建立来源化事实底稿

在私域工作区先建主体表、事件表、关系/流向表和争点证据表。使用稳定 ID；真实姓名、案号、地址、账号和敏感金额不得进入可复用模板。

`source_ledger` 每项完整记录 11 个字段：`source_id`、`source_kind`、`source_hash_or_version`、`custody_or_processing_location`、`ingested_at`、`source_cutoff`、`authorized_use`、`locator_prefix`、`page_or_unit_locator_scheme`、`ocr_or_derivation_note`、`description`。来源定位描述的是来源内部的页、段、单元格或时间戳定位，不把一般文本行号误称为来源定位。

每条内容记录：

- 中性事实命题；
- `fact_status`：`confirmed`、`disputed` 或 `unknown`；
- `record_type`：`fact`、`source_statement`、`inference` 或 `legal_rule`；
- `lifecycle`：`current`、`superseded` 或 `not_applicable`；
- `adjudication_status`：`not_adjudicated`、`party_admission`、`procedurally_disputed` 或 `judicially_determined`；后三种必须有 `adjudication_refs`，裁判认定还必须回链到裁判来源；
- 支持、冲突、上下文来源与缺口，以及材料 ID 的页、段、单元格或时间戳；

规格或版本顶层另记 `workflow_status`：`ready`、`research_draft` 或 `hold`；不要把它复制进记录后冒充事实属性。

`confirmed` 只表示“当前允许使用的材料支持，且当前输入未见实质冲突”，对外优先写“当前材料支持”；它不等于无争议、已经查证或裁判确认。来源陈述必须写成 `record_type=source_statement`，并记录 `asserted_by` 与 `verification_basis`；如需表达裁判确认，另记裁判文书、效力和定位，不得从 `confirmed` 推导。

`disputed` 同时记录 `support_refs` 与 `conflict_refs`。`unknown` 的 `support_refs=[]`，但允许记录 `context_refs`、`conflict_refs` 和 `gap_reason`；这些来源只说明语境、冲突或缺口，不能冒充对命题的支持。

详细步骤见 [references/01-core-workflow.md](references/01-core-workflow.md)。图中发现错误时先修正底稿，再重新生成图。

### 3. 选择最小够用的图

按真正构成争点或理解障碍的核心要素路由：

- 时间点、先后、期间或阶段：时间线；
- 主体、合同、控制、担保或事实关系：关系图；
- 资金、货物、票据、股权或文件移动：流向图；
- 数值、差额、比例或变化：数据表/对比图；
- 条件、分支或程序路径：流程图/决策树；
- 争点、事实命题、证据、反证和缺口：争点—事实—证据矩阵；
- 空间位置直接影响理解：空间示意图。

多个核心要素并存时优先拆图，使用稳定 ID 互相引用，不做一张“万能图”。模式细则见 [references/02-visual-patterns.md](references/02-visual-patterns.md)。

若输入是现有诉讼图，先把现图中的节点、边、形状、表格/幻灯片元素及其明示或暗示的命题列成清单，再与 SSOT、来源、反证、未知项和授权范围逐项比对；审查遗漏、方向错误、比例/颜色/空间暗示和未建模断言，而不是只做版面美化。

### 4. 形成内容

依次执行：

1. **全面罗列**：私域底稿先记录所有可能相关的事实、证据、冲突和未知项。
2. **逻辑整合**：按时间、关系、数据、程序或争点建立结构。
3. **3S 精简**：Simple、Straight、Strategy；删冗余，不删决定命题的限定、反证和不确定性。

选择性突出合法立场时，仍须维持来源真实和状态不变。时间先后不自动等于因果，关联不自动等于控制，支付路径不自动证明合同关系。

若行为与政策、市场或行业背景在时间上重合，只能生成待验证假说。至少列一个替代解释，把意图或因果判断记为 `record_type=inference`，并依据材料使用 `fact_status=disputed` 或 `fact_status=unknown`；没有独立支持时不得写成“真实意图”或裁判确认结论。

### 5. 建立规格并验证

优先生成 [references/06-spec-format.md](references/06-spec-format.md) 定义的 JSON 规格，再生成图。可从 `assets/` 复制对应 Mermaid 或 CSV 模板。

在 Skill 根目录运行：

```bash
python3 scripts/validate_spec.py path/to/spec.json
python3 scripts/validate_output.py path/to/spec.json path/to/render-manifest.json
```

第一个脚本检查规格结构、来源定位格式、来源登记表回链及隐私/法律/暂停/空间门字段一致性；第二个检查规格与图文件哈希、`released_fields` 是否为 `field_allowlist` 的子集、元素一一覆盖，以及 `line`、`cell`、`node`、`shape`、`table`、`slide` 定位目标是否含对应元素 ID。`page:` 定位不受支持；DOCX/PPTX/XLSX 会解压扫描可检查成员。两者都不判断视觉语义、未建模断言、实体与法律实质正确性或真实授权，仍须人工复核。

### 6. 质量复核

至少检查：

- 随机抽取节点、连线、金额、日期和主张，能回到具体材料；
- 反方事实、反证、冲突和未知项没有被静默删除；
- 图与底稿中的主体、方向、数值、日期和状态一致；
- 颜色、面积、距离、线粗和箭头没有制造额外事实；
- 颜色不是唯一编码，灰度、投影、小屏和文字替代仍可理解；
- 当前法、程序期限和法域已核验，或明确标为未核验；
- 11 字段 `source_ledger`、`privacy_authorization` 和始终存在的 `legal_review` sentinel 完整；触发法律内容时人工实质核验并逐条覆盖 `legal_rule support_refs`；`hold_control`、条件触发的 `spatial_review` 及 `human_release_by`、`human_release_at`、`authorization_basis` 均与当前版本一致；
- render manifest 的 `released_fields` 与实际输出一致且不超出 `privacy_authorization.field_allowlist`；
- 交付内容符合当前受众权限，且内部治理记录不混入法院可见件。

### 7. 交付

默认输出：

```text
1. 可编辑图表或矩阵
2. 图例、口径和图表回答的问题
3. 来源表（按权限提供）
4. 冲突、未知项与待核清单
5. 材料截止点、版本和法律核验日期
6. `workflow_status` 与人工复核状态
```

需要按案型提问时再读 [references/03-case-type-prompts.md](references/03-case-type-prompts.md)。该文件只是提问提示，不是现行实体法或程序法。

## 渐进加载

| 任务 | 读取内容 |
|---|---|
| 判断是否作图、选择图形 | `references/00-router.md` |
| 全流程、SSOT、验证与交付 | `references/01-core-workflow.md` |
| 具体图形字段与画法 | `references/02-visual-patterns.md` |
| 借款、票据、工程、房地产、国际买卖、公司纠纷提示 | `references/03-case-type-prompts.md` |
| 来源、现行法、隐私、误导与停止条件 | `references/04-quality-boundaries.md` |
| 方法出处、继承与排除边界 | `references/05-source-map.md` |
| JSON 规格与验证脚本 | `references/06-spec-format.md` |
| 术语出现歧义 | `references/07-glossary.md` |

不要一次加载全部参考文件；只加载当前步骤需要的内容。

## 必须停止或降级

- 材料使用授权、处理位置、处理器、外发对象、渠道或允许字段不明确；
- OCR 与原页冲突，关键页面不可读，或来源定位断裂；
- 图必须靠猜测才能闭合；
- 未核验的现行法或期限会改变路径或结论；
- 视觉误导无法通过状态、图例、附表或拆图控制；
- 用户要求复制来源书、隐去关键反证、公开未授权真实案情或把图表冒充证据/裁判结论。

遇到上述情况时，保留已验证部分，明确 `HOLD` 范围、缺失项和恢复条件，不扩大暂停范围。
