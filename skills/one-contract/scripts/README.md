# One-Contract 执行器

执行器负责实现已经完成专业判断的 review plan，不根据风险描述中的关键词推断法律结论、商业授权或风险级别。

## 模块化企业合同知识

- `knowledge/route_enterprise_contract.py`：输出含主辅大类编码的 v2 稳定合同画像；只有标题、交易结构、旧大类证据和我方角色一致时才解除人工确认门。
- `knowledge/select_active_assets.py`：按全局、大类、具体类型三层返回正式资产；候选大类卡只返回不含正文的影子元数据。中低置信或跨大类时须显式确认主大类。
- `knowledge/validate_assets.py`：检查十大类卡完整性、覆盖划分、状态、溯源和模块索引，以及既有 manifest、隐私和 DOCX 边界。
- `knowledge/detect_equity_transfer_triggers.py`：对结构化股权转让事实检查多文本价格不一致、无独立商业实质的对价改名、出资瑕疵和优先购买权程序异常；触发结果只定向限制明确禁止的动作。

上述脚本不读取本地合同库，也不能把资产从候选状态自动晋级。

大类选择示例：

```bash
python scripts/knowledge/select_active_assets.py \
  --primary-type-id type-equipment-material-procurement \
  --our-role buyer \
  --scene-tag equipment_purchase \
  --classification-status high
```

中低置信经人工确认后可传 `--confirmed-domain-code EC-02`。候选大类卡正文只能由源码树中 `scripts/tests/evaluate_domain_candidates.py --offline-evaluation` 读取；该测试入口不会进入导出包。

股权转让触发器示例：

```bash
python scripts/knowledge/detect_equity_transfer_triggers.py --facts /path/to/equity-facts.json
```

事实文件可包含 `documents`、`declared_consideration`、`actual_total_consideration`、`payments`、`capital_status` 和 `preemption`。脚本不从关键词直接推定违法；材料缺失时要求人工确认但不单独定为 P0；P0 命中时仅阻断规避性或依赖该事实的自动动作，仍允许合规方向修订。

## 依赖与测试

```bash
python3 -m pip install -r scripts/requirements.txt
PYTHONPATH=. python3 -m unittest discover -s scripts/tests -v
```

盲测、CI 或并行评估必须隔离运行态配置，避免测试身份与审查记忆写入 Skill 本体或串入其他 case：

```bash
export CONTRACT_COPILOT_CONFIG_DIR=/path/to/current-case/runtime-config
export CONTRACT_COPILOT_REVIEW_MEMORY=/path/to/current-case/runtime-config/review-memory.json
```

每个 case 使用独立目录，并把该目录随本轮输入、输出和失败记录一并留存。正式使用若需要跨次保留审查偏好，可以继续使用 Skill 默认配置目录。

## 标准执行

每次使用新的输出目录，避免覆盖旧结果：

```bash
python scripts/review/apply_review_plan.py \
  --input /path/original.docx \
  --plan /path/review-plan.json \
  --output /path/round-01/reviewed.docx \
  --quality-dir /path/round-01/quality \
  --author "审查人" \
  --organization "机构"
```

执行器默认：

- 不覆盖既有输出、报告或日志；
- 将所有被编辑的 XML/RELS 统一序列化为 UTF-8；
- 生成含真实 `w:ins` / `w:del` / Word 批注的审阅件；
- 运行严格质量门并生成接受版、拒绝版与 `quality-gate.json`；
- 环境具备 LibreOffice、`pdfinfo` 和 `pdftoppm` 时自动生成审阅件、接受版、拒绝版及意见书的 PDF/PNG 渲染证据；
- 任一 finding 或质量门失败时仍尽量保留产物和日志，但以非零状态退出。

默认 `--visual-policy allow-structural`：渲染命令可用时必须成功渲染；命令不存在时允许继续，但产物明确标为 `structural_validation`/“结构验证版”。需要硬性渲染门时使用 `--visual-policy require`。生成 PNG 仅表示渲染证据已就绪，仍需逐页检查裁切、重叠、缺字和字体替代。

`--no-validate` 只关闭编辑过程中的轻量检查，不关闭最终严格质量门，不应用于交付。

## 历史修订

默认 `--existing-revisions reject`：目标段落含历史修订时不直接改写，该 finding 失败并记录原因；可将计划改为批注。

只有明确决定以“接受历史修订后的文本”为本轮基线时，才使用：

```bash
--existing-revisions accept-existing
```

此策略会先在临时副本中接受历史修订，再应用本轮修订；原件不变，执行日志记录历史修订数量和基线策略，拒绝本轮修订后的语义与原件的接受视图比较。

## 源文档批注：回复与悬空批注

> `responses` 与 `linkage_checklist` 已**正式写入** `assets/knowledge_v2/schemas/review_plan.schema.json`
> （可选字段，不新增必填；契约层与运行时同判，见 `tests/test_review_plan_schema.py`）。

### `responses`：逐条回复源批注

与 `findings` 平级：

```json
{
  "responses": [
    {
      "id": "RESP-001",
      "target": {"comment_id": 1},
      "stance": "already_present",
      "evidence": "第1.3条、第4.4条",
      "text": "【审查人核对】现稿已体现：第1.3条已区分两类设备。"
    }
  ]
}
```

- `target` 二选一：`comment_id`，或 `anchor_text`（同时匹配**锚定正文**与**批注内容**，
  后者更常用——锚定正文常常只是一个句号）+ 可选 `occurrence`。
- `stance` 四值：`already_present`（现稿已体现）／`added_this_round`（本轮已补充）／
  `declined`（未按该意见修改）／`pending_fill`（仍需填写或待确认）。
- **`stance=already_present` 必须带 `evidence`**（条文号或落点），否则该条记失败——
  没有依据不得声称现稿已覆盖。
- **审查人不写"采纳/同意/接受/认可"**：那是当事人的表态，见
  `references/redline-comment-policy.md` 十一。
- 源批注无锚点时无法回复，该条记 `skipped`，由报告「源文档批注意见处理」列出。

### `--orphan-comments`：悬空批注策略

`comments.xml` 里存在、正文中无任何锚点的批注（Word 修订窗格不可见）：

| 取值 | 行为 |
|---|---|
| `quarantine`（默认） | 原样导出 `orphan-comments.json` 后从工作底稿移除 |
| `strip` | 直接移除（内容只留执行日志） |
| `reject` | 保留原样，交由质量门报错 |

### `linkage_checklist`：条款联动必检（**缺一组不得出报告**）

```json
{
  "linkage_checklist": {
    "payment_delivery_acceptance": {"status": "checked"},
    "change_termination_breach": {"status": "checked"},
    "confidentiality_data_ip": {"status": "checked"},
    "liability_insurance": {"status": "checked"},
    "expiry_exit_handover": {"status": "not_applicable", "reason": "本协议不含数据迁移安排"}
  }
}
```

六组口径见 `references/review-doctrine.md` 六与 `modular-knowledge-routing.md`「联动组」，
其中「角色边界与第三方专业服务」对应 `common-clause-doctrine` **3.4.1**。

### 填数的三条线（`amount_guard` 软检查）

`replacement_text` / `insert_text` 里需要数字时（口径见 `references/redline-comment-policy.md` 1.6）：

| 类型 | 动作 |
|---|---|
| 天数、期限 | **可直接填**，批注注明「可调整」 |
| 比例（含以金额为基数） | **可直接填**，批注注明「可调整」 |
| 具体金额 | **不填数字**，正文写 `【待填：金额】`，批注给出计算口径 |

执行器对"新增文本里出现具体金额且未标待填"的情况**只提示、不阻断**：
打印一行提示并写入执行日志 `amount_guard`。引用原文既有金额（如附件一报价）不会被误报。

同类的两条软检查（同样只提示）：

| 检查 | 触发 | 口径 |
|---|---|---|
| `subject_check_guard` | 出现主体资格／资信／履约能力等字样，却带了批注或修订动作 | 四之二：主体与资信核查**只进报告** |
| `insurance_burden_guard` | 改文里出现「甲方／我方／双方…投保」 | 3.5.2：保险义务**只加对方** |

而**措辞越界是硬校验**：`validate_plan` 拒绝在 `responses[].text` 里使用
「采纳／同意该意见／接受该意见／认可该意见」等**当事人表态**（十一：审查人只写核对结论）。

### 其他产出

- `orphan-comments.json`：悬空批注原文（含作者与日期）；
- `legal-citations.json`：本轮引用到的全部法条，供具备数据库的使用方逐条复核现行有效性；
- 报告章节契约：`report/report-sections.json`——生成器逐节自检，缺一节即报错。

## Review plan

```json
{
  "meta": {
    "contract_name": "协商解除劳动合同协议",
    "party_role": "用人单位",
    "review_intensity": "常规",
    "edit_policy": "revise-first"
  },
  "findings": [
    {
      "id": "ET-001",
      "risk_level": "P1",
      "evidence_state": "reasonable_assumption",
      "action": "replace",
      "target_text": "原条款中的唯一连续文本",
      "replacement_text": "可直接进入合同的主方案文本",
      "assumptions": ["当前采用的事实假设"],
      "unknown_facts": ["需要确认的变量"],
      "comment": "请确认变量；若结论相反，按备选方向调整。",
      "linked_clauses": ["结算条款", "权利终结条款"],
      "basis_type": "legal_boundary",
      "legal_basis": "现行有效规则及履行对价平衡",
      "pending_kind": "verify",
      "report_bucket": "general"
    }
  ]
}
```

证据状态与默认动作：

| `evidence_state` | 动作 |
|---|---|
| `confirmed` | 有改文载荷时真实修订 |
| `reasonable_assumption` | 真实修订并附假设/待确认批注 |
| `major_choice` | 仅批注；用户选择后改为 `confirmed` |
| `not_applicable` | 跳过并记录 |

`action` 支持 `auto/comment/report-only/delete/insert/replace/none/skip`。`auto` 只读取显式证据状态和改文载荷。若 `assertions_unverified` 为真，必须同时明确 `uses_placeholders_or_conditions=true`，否则直接改文会降为批注。

### `rule_hit` / `direction_clear`：把「命中明确规则就落笔」接到机制上

```json
{
  "id": "OC-SL-022",
  "rule_hit": "common-clause-doctrine 3.5.2 保险安排",
  "direction_clear": true,
  "evidence_state": "confirmed",
  "action": "replace"
}
```

- 命中**库内明确规则**且**方向明确**的 finding，**不得记 `evidence_state=major_choice`**——
  那会把"有规则可依"误当作"结构性商业选择"，被执行器强制降级为仅批注；
- `validate_plan` 强制校验这一条：填了 `rule_hit` 就必须给 `direction_clear`，
  且 `direction_clear=true` 时 `evidence_state` 只能是 `confirmed` / `reasonable_assumption`；
- 口径见 `references/redline-comment-policy.md` **1.5 与 1.5.1**（规则写在文档里、判定走字段——
  只写文档不接机制，规则不会生效）。

执行前必须通过 `assets/knowledge_v2/schemas/review_plan.schema.json` 对应的运行时校验。旧 `basis`/`principle_basis` 会归一到 `legal_basis`，但无任何依据的 finding 会在编辑 DOCX 之前失败。`pending_kind=fill|verify|authorization` 区分填写、核验与授权；`report_bucket=tax|mixed|general` 决定是整项进入文末、仅迁移 `tax_advice`，还是留在详细意见。

P0 定向阻断只作用于具体 finding。将触发结果写入 `safety.trigger_results`，或提供股权转让 `transaction_facts`；只有 finding 的 `output_kind` 与触发结果 `prohibited_outputs` 精确匹配时才自动标为 `directed_blocked`。也可对单个 finding 显式填写 `directed_block`。执行器会记录并过滤被禁止文本，同时继续其他 finding。

定位支持：

- `target_text` / `search`；
- `occurrence`（从 1 开始）；
- `selector.tag / attrs / line_number / contains / occurrence`。

跨 run 定位会对全角/不换行空格、连续空白和不可见字符作规范化，但同一规范化文本多次出现时拒绝猜测，必须提供 occurrence 或更窄 selector。

## 独立质量门

```bash
python scripts/docx_engine/quality_gate.py reviewed.docx \
  --original original.docx \
  --output-dir qa \
  --baseline-view reject \
  --require-revisions \
  --visual-policy allow-structural
```

质量门检查 ZIP、全部 XML/RELS、UTF-8/16 编码声明、内部关系、content types、评论锚点、修订属性，重新打开最终 DOCX，生成接受/拒绝副本，并在环境可用时自动生成 PDF/PNG 渲染证据。它不替代对 PNG 的逐页视觉检查或 Microsoft Word 实机验证。

## 目录

```text
scripts/
  review/apply_review_plan.py   主流程
  review/plan_loader.py         结构化证据状态补全
  review/action_executor.py     动作执行
  docx_engine/reviewer.py       定位、修订、批注
  docx_engine/revision_views.py 接受/拒绝副本
  docx_engine/quality_gate.py   OOXML 与渲染证据门
  report/                       Markdown/DOCX 审查意见书
  tests/                        回归测试
```

## 本地合同规则工作台（3.1 Preview）

```bash
./start.sh --data-dir "/独立的客户规则目录" --idle-timeout-seconds 3600
```

该命令启动本机服务并打开浏览器。日常操作使用“规则总览、试运行、客户规则、公共规则建议”四个中文页面；内部编号收纳在折叠的技术信息中。请勿将客户数据目录放入 Skill 或公开仓库。

开发、无浏览器或自检入口：

```bash
python scripts/open_rule_studio.py --no-browser   # 返回可复制的本机地址
python scripts/open_rule_studio.py --dry-run      # 只检查启动条件，不持续运行
```

Agent 可以使用不暴露会话凭据的快捷入口。`api` 子命令会在内存中取得
token、CSRF 与同源信息；`stop` 通过已认证的本地 API 停止服务，不依赖旧 PID 发送信号：

```bash
python scripts/rule_studio_agent.py start
python scripts/rule_studio_agent.py api /api/v1/rules/tree
python scripts/rule_studio_agent.py api /api/v1/resolutions/preview \
  --method POST --data '{"context":{"primary_type_id":"type-equipment-material-procurement","secondary_type_ids":[],"confirmed_domain_code":"EC-02","our_role":"buyer","scene_tags":["equipment_purchase"],"classification_status":"high","facts":{},"case_authorizations":[],"client_profile_id":null,"client_policy_snapshot_id":null}}'
python scripts/rule_studio_agent.py stop
```

合同类型交叉校验使用 `knowledge/confirm_contract_type.py`。若路由器已给出中高置信且与
手工候选类型冲突，未显式传入 `--human-confirmed` 时返回 `needs_human_review`，
进程退出码为 2，不得加载专项规则。

解析入口（供审查运行时调用）：

```bash
python scripts/knowledge/resolve_effective_rules.py --context <context.json> [--no-studio]
```

最小 `context.json` 示例（仅公共规则）：

```json
{
  "primary_type_id": "type-equipment-material-procurement",
  "secondary_type_ids": [],
  "primary_domain_code": "EC-02",
  "confirmed_domain_code": "EC-02",
  "our_role": "buyer",
  "scene_tags": ["equipment_purchase"],
  "contract_stage": "signing",
  "classification_status": "high",
  "facts": {},
  "case_authorizations": [],
  "client_profile_id": null,
  "client_policy_snapshot_id": null
}
```

采用客户规则时，只能在用户明确选择后填写 `client_profile_id`；`client_policy_snapshot_id` 留空会固定该客户当时的 active 快照。解析结果为 `blocked` 时不得继续声称采用客户口径，须修复快照或由用户明确改选仅公共规则。结果中的 provenance 应随本轮 review plan 一并保存，审查中途不切换快照。

依赖：`pip install -r scripts/requirements-rule-studio-dev.txt`（仅新增 `jsonschema`）。
