# 法律 Skill IR

Skill IR 是平台中立的语义契约；它描述 Skill 拥有什么能力、如何受控运行以及如何验证，不描述某个平台的固定文件名。生产、团队复用、跨平台或高风险法律 Skill 在扩展目录前先写 IR。生成包以 `manifest.json` 的 `skill_contract`、法律能力配置、权限、降级、评测和复核字段作为导出来源；导出器不得把元技能自己的任务套给下游 Skill。

本文件定义 `legal-skill-ir/v0.3`。其中 `legal_profile` 采用独立的 `universal-legal-core/v0.1`：前者是整个 Skill 的语义契约版本，后者是通用法律能力模型版本，两者不得混写或互相替代。

创建阶段使用 `legal-skill-intake/v0.2` 收集业务真值和评测材料；生成器兼容读取 `v0.1`，但新生成结果统一写入 `v0.2`。intake 是创建输入，不是运行时依赖；生成后的目标 Skill 必须自包含。

## 最小字段

```json
{
  "schema_version": "legal-skill-ir/v0.3",
  "name": "skill-name",
  "version": "0.1.0",
  "owner": "owner",
  "provenance": {
    "identity": "CSlawyer",
    "homepage": "https://chenshi.ai",
    "created_with": "legal-meta-skill",
    "created_with_version": "1.0.0"
  },
  "maturity": "scaffold|production|library|governed",
  "maturity_label_zh": "草案级|专业复用级|基础设施级|高风险治理级",
  "job": "recurring legal job",
  "decision": {"goal": "", "owner": "", "supported_action": ""},
  "target_users": [],
  "inputs": [],
  "outputs": [],
  "exclusions": [],
  "triggers": {"should": [], "should_not": [], "near_neighbor": []},
  "workflow": [],
  "decision_points": [],
  "failure_modes": [],
  "legal_profile": {
    "schema_version": "universal-legal-core/v0.1",
    "activation_policy": "mandatory-review-conditional-expansion",
    "modules": {
      "task_context": {},
      "jurisdiction": {},
      "temporal": {},
      "actors": {},
      "matter": {},
      "claims_and_elements": {},
      "authority_and_interpretation": {},
      "proof": {},
      "procedure": {},
      "outcomes_and_enforcement": {},
      "strategy_and_uncertainty": {},
      "governance": {}
    }
  },
  "capability_summary": {
    "total": 12,
    "active": 12,
    "not_applicable": 0,
    "blocked": 0
  },
  "migration_warnings": [],
  "evidence_boundary": {},
  "resources": {"references": [], "scripts": [], "evals": [], "assets": []},
  "permissions": {},
  "degradation": {},
  "eval_plan": {},
  "review": {"owner": "", "cadence": "", "reverification_triggers": []}
}
```

上例中的空模块对象仅用于展示固定键位，不是可交付配置。创建实际 IR 时，应从 `assets/templates/legal-capability-profile.json` 复制完整结构并按目标 Skill 填充；不得保留空模块、删除模块或把示意对象当作已完成配置。

`provenance` 记录作者与生成来源，键形与导出器实际输出一致（`identity`、`homepage`、`created_with`、`created_with_version`）；`branding_mode` 位于 IR 顶层而非 `provenance` 内。新建 Skill 默认使用 `CSlawyer` 和 `https://chenshi.ai`；改造已有 Skill 时在 `provenance` 或交接中保留原作者与许可证信息，再增加 `created_with` 或 `maintained_with`，不得覆盖原始署名。

## 导出器字段与确定性

`scripts/export_legal_skill_ir.py` 的 `build_ir(skill_dir, generated_at=None)` 只读取目标 Skill 并构造字典，不写入目标目录。CLI 在构造后才按 `--output` 写 JSON，因此保持原有相对输出路径以目标 Skill 根目录为基准的行为。

- `generated_at` 未注入时使用导出当天的 ISO 日期；测试或可复现构建可传入固定日期。
- `job`、`decision`、`target_users`、`inputs`、`outputs`、`exclusions`、`workflow`、`decision_points` 和 `failure_modes` 从目标 Skill 自己的 `manifest.skill_contract` 读取。缺失时保持空值并写迁移警告，不根据 Skill 名称猜测，也不使用 `legal-meta-skill` 的工作流作为默认值。
- `permissions`、`degradation`、`eval_plan`、`evidence_boundary` 和 `review` 从目标 manifest 对应字段读取，不以静态计划冒充真实证据。
- 新模型（`schema_version` 为 `universal-legal-core/v0.1` 且包含对象形式的 `modules`）保留其原始 `legal_profile` 字段，并按十二个稳定模块 ID 的顺序重排 `modules`。未知模块若存在，排在稳定模块之后并按字典序排列；导出器不替代校验器判断其合规性。
- `capability_summary` 统计实际导出的模块总数及 `active`、`not_applicable`、`blocked` 三态数量。完整新模型通常为 12 个模块；导出器不得把不完整或旧版 profile 的总数写成 12。
- 旧版 profile 原样保留，不补造 `modules`，摘要均为 0，并在 `migration_warnings` 写明其尚未迁移至 `universal-legal-core/v0.1`。兼容导出不会因旧版配置失败。
- `resources` 仅登记相对于 Skill 根目录的路径，按字典序稳定排序，并忽略隐藏目录及 `__pycache__`、`.pytest_cache`、`.mypy_cache` 等缓存目录；IR 不得包含本机绝对路径。

## `legal_profile` 契约

`legal_profile` 必须包含：

- `schema_version`：固定为 `universal-legal-core/v0.1`。
- `activation_policy`：固定为 `mandatory-review-conditional-expansion`，即十二模块全部检查、条件展开。
- `modules`：恰好包含十二个稳定模块 ID；不得省略、增加近义 ID 或用旧版扁平字段代替模块。

每个模块对象遵循同一状态结构：

| 字段 | 规则 |
|---|---|
| `label_zh` | 使用通用能力模型确定的中文模块名。 |
| `status` | 仅允许 `active`、`not_applicable`、`blocked`。 |
| `reason` | 三种状态均须具体说明与目标 Skill 的重复任务和范围之间的关系，不得为空。 |
| `required_outputs` | `active` 时必须是非空列表，并覆盖通用能力模型规定的最低输出。 |
| `gap` | `blocked` 时必填，列明事实、材料、权威来源、权限、工具或人工判断缺口。 |
| `fallback` | `blocked` 时必填，列明可先行范围、补充或核验动作、人工接管及必要的停止路径。 |

三态只表达能力模块在目标 Skill 中的受控处理方式：

- `active`：该模块适用，目标 Skill 必须完成最低检查并产生最低输出。
- `not_applicable`：该模块已经检查且对该重复任务确实不适用，必须记录与任务相联系的具体理由。
- `blocked`：该模块原则上适用但暂时无法可靠完成，必须同时暴露缺口与降级或停止路径；不得把缺口包装成结论。

十二模块的稳定 ID、中文名称和承接语义如下：

| 模块 ID | 中文名称 | 在 IR 中承接的核心语义 |
|---|---|---|
| `task_context` | 任务目的与受众 | 重复任务、目标用户、实际受众、决定目标、决定责任人、复核者和排除项。 |
| `jurisdiction` | 法域 | 实体法、程序法、地域连接点、准据法、法院或仲裁地、冲突规范和强制性规定。 |
| `temporal` | 时间 | 事实期间、法律核验时点、规范版本、新旧法过渡、时效和程序期限。 |
| `actors` | 主体角色 | 委托、代理、相对方、第三人、资格、授权、行为能力、程序地位和利益冲突。 |
| `matter` | 法律事项 | 专业领域、法律关系、事项对象、生命周期状态、问题范围和排除项。 |
| `claims_and_elements` | 请求与要件 | 请求、主张、抗辩、构成要件、例外、法律效果及要件—事实映射。 |
| `authority_and_interpretation` | 法源与解释 | 权威来源层级、独立核验、来源标签、规范冲突、解释方法和规则—事实涵摄。 |
| `proof` | 证明 | 材料与事实分层、待证事实、证据定位、举证责任、证明标准、证据缺口与不利后果。 |
| `procedure` | 程序 | 机构、管辖、程序阶段、资格、前置条件、受理、送达、保全、举证和期限。 |
| `outcomes_and_enforcement` | 结果与执行 | 法律效果、责任类型、金额敞口、救济组合、可执行性、执行路径和回收约束。 |
| `strategy_and_uncertainty` | 策略与不确定性 | 方案比较、风险模型、假设、未知项、情景分析、建议动作和升级触发条件。 |
| `governance` | 职业治理 | 保密、数据边界、权限、来源留痕、利益冲突、专业责任、人工复核和复核周期。 |

各模块的触发问题、最低检查、完整最低输出字段和停止或降级条件，以 `references/universal-legal-capability-model.md` 为权威定义。IR 可以增加场景字段，但不得降低该模型的最低契约。

## 旧版字段的语义迁移

旧版扁平 `legal_profile` 中的内容必须按语义迁移，不能只改字段名，也不能因新模型已有近似概念而丢弃原有法律底线：

| 旧版字段 | 迁入模块 | 必须保留的语义 |
|---|---|---|
| `jurisdiction` | `jurisdiction` | 明确法域、地域和适用边界；不得把港澳台或外国法默认为中国大陆法。 |
| `jurisdiction_default` | `jurisdiction` | 保留既有默认法域作为任务启动时的待核前提，不得把默认值当作已确认的准据法、管辖或排除其他法域的结论；运行时仍须核对地域连接点、选择法条款、法院或仲裁地和强制性规定。 |
| `as_of` | `temporal` | 显式处理法律核验时点、规范修订、新旧法衔接、诉讼时效、除斥期间和程序期限。 |
| `issue_scope` | `matter`，并与 `task_context` 的授权范围对齐 | 限定法律问题范围；不得未经授权扩张为全案、全合同或相邻事项审查。 |
| `authority_ladder` | `authority_and_interpretation` | 区分法律、行政法规、司法解释、规范性文件、案例、地方口径和实务材料等效力与证明意义。 |
| `verification_policy` | `authority_and_interpretation`，并由 `governance` 留痕 | 具体法条、司法解释、案例、地方口径、时效和期限须独立检索复核；核心依据缺失时进入停止或人工复核路径。 |
| `verification` | `authority_and_interpretation`，涉及法律时点或程序期限时同时迁入 `temporal` 或 `procedure` | 保留导出器旧缺省配置中对具体法条、司法解释、时效和案例进行独立核验的要求；记录核验日期、来源和状态，核心依据未核验时不得输出确定性结论。 |
| `source_policy` | `authority_and_interpretation`，并由 `governance` 保存来源与审计记录 | 保留现行法、司法解释、权威案例与本地知识库的分层处理和独立核验要求；区分效力层级、来源类型、核验状态与模型推理，不得把本地资料或二手材料直接宣称为现行有效依据。 |
| `source_labels` | `authority_and_interpretation` | 保留来源类型和核验状态标签，例如 `[法条原文]`、`[裁判文书]`、`[本地知识库]`、`[已验证 — YYYY-MM-DD]`、`[模型知识 — 需验证]`。 |
| `fact_evidence_model` | 以 `proof` 为主，并与 `claims_and_elements`、`procedure`、`authority_and_interpretation` 互相引用 | 保留“材料层 → 案件事实层 → 法律评价层 → 程序攻防层”的四层分离和反向追溯；材料内容不得直接等同于已确认事实。 |
| `evidence_policy` | 以 `proof` 为主，并与 `claims_and_elements`、`procedure`、`authority_and_interpretation` 互相引用 | 保留仓库既有“材料、事实、法律评价、程序状态四层分离”要求，并补充结论到材料位置、待证事实、证据状态和程序记录的反向追溯；不得在迁移时压缩成单一证据摘要。 |
| `risk_model` | `outcomes_and_enforcement` 与 `strategy_and_uncertainty` | 区分法律风险与商业或操作摩擦；保留风险类型、触发条件、后果、概率或敞口、可规避性、商业权衡和紧迫性。 |
| `privacy_default` | `governance`，并同步到顶层 `permissions` 与 `evidence_boundary` | 保留 `local-first-data-stays-local` 的本地优先、数据不出机语义；未经用户明确授权不得向外部服务上传真实案卷或私人附件，并继续执行最小权限、必要脱敏、密钥保护和外部传输留痕。 |
| `pdf_policy` | `proof` 与 `governance` | 保留包内法律文件和工作空间规则：原始材料只读、受控转换、材料与中间产物可追溯、质量警告进入人工复核；不得因迁入通用模块而解除 PDF 证据处理边界。 |

如果旧版还包含未列出的专用字段，应先判断其法律语义、使用位置和验证责任，再放入最接近的模块或 IR 顶层契约；迁移记录应能说明原字段去向，不得静默删除。

## 兼容与升级策略

按 Skill 来源和用户意图区分处理：

1. **新建 Skill，或由 `legal-meta-skill >= 1.0.0` 生成的 Skill**：必须使用 `legal-skill-ir/v0.3`，并采用完整的 `universal-legal-core/v0.1` 配置。十二模块和三态契约属于严格要求；缺少模型版本、激活策略、模块、状态必填项或最低输出时，应在生成或交付门禁中报告错误。
2. **既有 Skill 只有旧版 `legal_profile`**：允许读取、展示和审计。审计结果须输出升级警告，列明缺少的新模型字段和无法确认的模块状态，但不得仅因仍是旧版结构而直接阻断审计，也不得把旧版结构宣称为已符合 `universal-legal-core/v0.1`。
3. **用户明确要求升级既有 Skill**：建立旧字段到新模块的迁移清单，补齐全部十二模块及各自状态，把原有内容放入对应模块并保留来源或迁移说明。无法可靠判断的模块应按实际情况记录具体不适用理由或缺口与降级路径，不能以空对象占位，不能简单丢弃旧字段。

兼容读取只服务于审计和迁移，不降低新建、重新生成或明确升级后的严格门禁。若既有 Skill 在本次任务中还发生了足以构成 `legal-meta-skill >= 0.5.0` 重新生成的实质改造，应在交接中说明并按新模型完成配置，而不是继续依赖旧版豁免。

`legal-meta-skill` 1.0.0 引入的安全、证据、领域补充、DOCX 审阅和署名传播增强是最低契约之上的条件展开层；保持 `universal-legal-core/v0.1`，IR 升级至 `legal-skill-ir/v0.3`。既有包仍可读取和审计，重新生成或明确升级时按新规则获得增强。

## 证据边界与人工控制

分开写：

1. 已运行的结构、触发、输出、安装或人工证据；
2. 设计要求、静态夹具、计划执行项；
3. `missing evidence`：提供方实跑、真实项目回归、人工盲评、外部安装或权限原生执行等尚未取得的证据。

`proof` 模块描述目标法律任务如何处理待证事实和证据；顶层 `evidence_boundary` 描述对 Skill 本身已有验证证据、未验证声明及敏感信息的边界。两者必须互相一致，但不得混为一个字段。

`task_context.reviewer`、`governance.human_review` 与顶层 `review` 必须对齐：分别说明单次任务中的复核者、不得自动定稿的事项，以及 Skill 契约的维护人、复核周期和重新核验触发条件。涉及效力、金额、期限、责任、程序资格、正式提交或对外签发的结论，应明确人工责任人和停止点。

IR 不应包含 API key、Cookie、Token、真实案卷正文、私人附件、用户绝对路径或未经测试的跨平台能力声明。

`maturity` 保留英文机器码用于跨平台兼容；面向用户的报告、门禁和交接统一使用对应中文名称。`assets` 只登记可复制或填充的静态模板与资源，不放第二个精确命名的 `SKILL.md`。
