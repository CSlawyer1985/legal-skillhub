# 质量与误用边界

## 3S 质量门

### Simple

- 图只保留对当前受众任务有效的信息，详细事实移到来源表或附表。
- 使用稳定简称和 ID，但首次出现时给出对应关系。
- 不用装饰元素、重复文字和无意义图标消耗注意力。

### Straight

- 节点和连线使用直接的事实动词，不让读者自己猜箭头含义。
- 观点必须与支撑事实相连；逻辑有断点时标为缺口，不用布局跨过去。
- 标题说明图回答的问题，不写“案件关系图”这类空标题。

### Strategy

- 内容服从明确的沟通目的，但关键限定、反证、冲突和未知项不能因不利而删除。
- 关键条款、时间、金额、原话或动作在确有必要时保留精确文本和来源。
- 同一事实对不同受众可有不同详略，事实状态不能随受众改变。

## 三个记录主维度、独立裁判处理维度与规格级工作流门

统一术语为“3 个记录主维度 + 独立裁判处理维度 + 1 个规格级工作流门”。各层必须分栏记录，不得互相代用或合并命名：

- `fact_status=confirmed/disputed/unknown`：当前允许材料对命题的支持状态；
- `record_type=fact/source_statement/inference/legal_rule`：记录性质；
- `lifecycle=current/superseded/not_applicable`：记录是否在当前版本与范围继续适用；
- 独立 `adjudication_status`：当事人或裁判机关的处理状态；
- 规格顶层唯一 `workflow_status=ready/research_draft/hold`：产物能否进入下一步，不得下沉到节点或边。

`HOLD` 不是事实状态；`inference` 不是事实状态；`superseded` 与 `not_applicable` 也不是事实状态。不得通过改写事实状态解除流程门，也不得通过生命周期标签删除反证。

`fact_status=confirmed` 仅表示“当前允许使用的材料支持，且当前输入未见实质冲突”。对外优先写“当前材料支持”；它不等于无争议、独立查证、裁判确认或终局认定。来源陈述必须使用 `record_type=source_statement`，并记录 `asserted_by` 与 `verification_basis`；裁判确认必须另有裁判文书、效力和具体定位说明，不能从 `confirmed` 推导。

`fact_status=disputed` 必须并列 `support_refs` 与 `conflict_refs`。`fact_status=unknown` 的 `support_refs=[]`，但可保留 `context_refs`、`conflict_refs` 和 `gap_reason`；这些信息说明语境、冲突或缺口，不能当作命题的支持。

## 客观真实与合法立场

允许：选择相关事实、调整视觉层级、把己方推论标为推论、并列双方口径。

禁止：

- 把争议事实画成既定事实；
- 用颜色、面积、距离或线粗暗示没有依据的责任、因果或重要性；
- 隐去会改变命题的例外、反证或不确定性；
- 把时间先后画成因果，把关联画成控制，把支付画成合同主体；
- 仅因行为与政策、市场或行业背景在时间上重合，就宣称已经识别“真实意图”；
- 把图表当作证据、法律意见、裁判结论或胜诉承诺；
- 复刻原书图表、配色、版式或连续案例内容。

行为—背景对照只能用于生成假说：列出替代解释，把命题记为 `record_type=inference`，并依据材料使用 `fact_status=disputed` 或 `fact_status=unknown`，说明需要什么独立支持才能改变事实状态。

## 来源与法源门

- 每个作为支持性内容呈现的节点、连线和主张必须有来源定位；`unknown` 不得有 `support_refs`，但可用 `context_refs`、`conflict_refs` 与 `gap_reason` 解释为何仍未知。
- 作者观点、一般方法、案件材料、律师推论和现行法分别标注。
- 本 Skill 不内置 2017 年书中的具体法条、期限或裁判规则。
- `legal_review` sentinel 始终存在。无触发内容时写 `required=false`、`law_check_status=not_required`、`legal_rule_refs=[]`；出现法条、法律、管辖、流程图、程序、期限、时效、法定条件、裁判规则、救济、上诉或 `record_type=legal_rule` 时，必须写 `required=true` 并由人工实质核验权威来源、法域、适用时点和日期。法律定位只回链到 `source_kind=legal_authority` 或 `decision`，且 `legal_review.legal_rule_refs` 必须逐条覆盖所有 `legal_rule support_refs`。未核验时设 `workflow_status=research_draft`；若会影响对外提交、行动路径或重大结论，设 `workflow_status=hold`。
- OCR 文字只能作为检索层；关键数字、日期、主体、条款和短引必须回看原页。

## 来源账本与流程门

- `source_ledger` 每项完整记录 11 个字段：`source_id`、`source_kind`、`source_hash_or_version`、`custody_or_processing_location`、`ingested_at`、`source_cutoff`、`authorized_use`、`locator_prefix`、`page_or_unit_locator_scheme`、`ocr_or_derivation_note`、`description`。
- `workflow_status=ready` 只表示指定版本对指定受众、渠道和字段已通过适用门，不证明命题真实或法律结论正确。
- `workflow_status=research_draft` 只允许在授权范围内继续研究，不能作为可行动、可提交或已核法律结论。
- `workflow_status=hold` 表示授权、隐私、法源、来源完整性或其他强制门失败；`hold_control` 必须记录 `scope`、`reason`、`owner` 和非空 `recovery_conditions`。其他工作流状态时 `hold_control=null`。
- `hold` 解除后只能根据剩余门转为 `research_draft` 或 `ready`；新材料、新法域、新接收人、新渠道或新字段会重新触发相应门。
- 空间、现场、路线、边界、方位、平面、坐标或测绘视觉必须建立 `spatial_review`，记录 `diagram_kind`、测量方法、坐标/比例、方向基准、采集日期、数据版本、遮挡、误差、投影变形、时间变化、视角偏差和建模假设；非空间任务使用 `null`。

## 可访问性与载体

- 颜色不是唯一编码；同时使用线型、文字或图例。
- 检查灰度打印、投影、小屏和低分辨率环境。
- 字号、线宽、对比度和箭头方向保持一致；长图拆页时重复图例和 ID。
- 对不能看图的受众提供同源文字/表格替代，不让替代文本新增结论。

## 隐私、交付与发布

- 只处理当前用户已授权的材料与用途。
- 默认本地处理、不外发。用 `privacy_authorization` 治理 sidecar 记录 `processing_location`、`allowed_processors`、`allowed_recipients`、`allowed_channel`、`field_allowlist`、`redaction_status`、`retention_policy`、`human_release_approved`、`human_release_by`、`human_release_at` 与 `authorization_basis`；人工放行只对当前版本、对象、渠道和字段有效。
- 外部处理器、外部接收人、渠道或字段未明确获批时，设 `workflow_status=hold`；不得先上传、共享或提交后补授权。
- 真实案件的姓名、案号、地址、账号和敏感金额不进入可复用模板。
- 内部来源表、风险标记、构建日志与法院可见件物理分离。
- 本地构建、验证、安装、生产晋升和外部发布是独立权限。
- 来源书当前仅允许本地内部蒸馏；`external_publish_authorized=false`。

## 输出一致性检查的边界

- render manifest 必须声明 `released_fields`，且不得超出 `privacy_authorization.field_allowlist`；实际渲染法律规则时还须包含 `legal_rules`，渲染事实、来源陈述或推论时须包含 `facts`。
- `line:` 只检查 UTF-8 文本的目标行/行段是否存在并含对应元素 ID；`cell:` 只检查 CSV/TSV 目标单元格；`node:`、`shape:`、`table:` 检查 token 与元素 ID 相等且存在于可检查文本；`slide:` 检查真实 PPTX 幻灯片 XML 中是否含元素 ID。
- `page:` 不受 bundled checker 支持，不能把其语法通过当作页面几何已经核验。
- DOCX/PPTX/XLSX 会被当作 Office ZIP 解压，并扫描成员中的 `TODO_DO_NOT_DELIVER`、绝对路径、父目录穿越及可检查文本；这不是 Office 视觉渲染审查。
- 脚本不能判断视觉语义、发现所有未建模断言、确认实质正确性或证明真实授权；现图遗漏与误导、法律适用、隐私放行和最终交付仍须人工检查。

## 必须停止的情况

- 无法确认材料使用授权、处理位置、处理器、接收人、渠道或受众允许字段；
- 关键页面不可读，或 OCR 与原页冲突；
- 想作为支持性内容呈现的命题没有 `support_refs`，或图表必须靠猜测才能闭合；`unknown` 可保留上下文和缺口，但不得被画成支持性结论；
- 当前法律规则、期限、程序或法域未经核验且会影响对外提交、行动路径或重大结论；内部研究若可安全继续，也必须保持 `workflow_status=research_draft`；
- 图示可能造成实质误导且不能用状态、图例或拆图控制；
- 用户要求复制整书、原图或未授权公开真实案情。

来源方法：`lv-jy-2017` PDF 117–155；来源门、状态语义、隐私和权限分离来自皋陶治理强化。
