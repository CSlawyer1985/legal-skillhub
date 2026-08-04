# 百炼®标书开放 API 契约参考

> **契约兼容标注（skill biaoshu-bailian 2.1.0）**
> - 适配后端 API：`/api/open/v1`
> - 契约核对日期：2026-07-22（新增 skill/version 端点）（后端字段/枚举变化时更新此处并 bump 版本）
> - 关键枚举快照：`risk_level ∈ {high, review, tip}` · `result_type ∈ {suspected, detected}` · `priority ∈ {high, medium, low}`
> - 自进化枚举：`type ∈ {material, preference, correction}` · `stage ∈ {interpret, write, compliance}` · `category ∈ {misguide, correction, error, suggestion}`
> - 渲染兼容策略：`report.py` 同时兼容文档值（高/中/低）与实测值、证据多形态、缺字段不崩——契约小幅漂移只需 PATCH，不触发 MAJOR。

`scripts/zcm.py` 已封装下列全部端点；本文档供需要直接发请求、排查错误或理解返回结构时查阅。
所有契约均经后端源码 + 本地实跑核实。

## 目录
- [鉴权与环境](#鉴权与环境)
- [核心模型与约定](#核心模型与约定)
- [10 个端点详情](#10-个端点详情)
- [错误码速查](#错误码速查)
- [注意事项](#注意事项)
- [纯 curl 备用调用](#纯-curl-备用调用)

---

## 鉴权与环境

- **Base URL（生产）**：`https://biaoshu.zhiliaobiaoxun.com/api/open/v1`
- 每个请求都带鉴权头：

| Header | 值 | 说明 |
|---|---|---|
| `X-App-Key` | App Key | 必填，形如 `bk_live_xxxxx` |
| `Idempotency-Key` | UUID（可选） | 相同 key 24h 内返回同一 `job_id`，不重复扣费 |

- 服务开关：开放 API 受超级管理员『系统设置』总开关控制，**关闭时整层返回 404**。
- 凭证获取：打开官网 https://biaoshu.zhiliaobiaoxun.com/ 用手机号注册并登录 → 点**左侧菜单『Skill 接入 → 获取 APP Key』** → 弹出面板首次打开自动生成 Key。
  App Key 可随时在该面板查看；重置后旧 Key 立即失效。

## 核心模型与约定

- **project_id**：统一句柄，由「智能解读」产出，是**唯一的招标文件上传入口**。后续抽包 / 生成 / 合规复用同一 project，不重复解读、不重复计费。
- **job_id**：每个异步任务的对外句柄。提交类接口立即返回 `{ "job_id": "..." }`。
- **任务状态**：`queued` → `running` → `succeeded` / `failed` / `canceled`。
- **上传方式**（所有上传类接口二选一）：
  - `multipart/form-data` 直传文件；
  - JSON `{ "file_url": "https://..." }`（远程下载，**仅 https、禁内网/回环、限大小与类型**，违规 422）。
- **限流**：每 App Key 默认 60 req/min、同时进行任务 ≤ 3；超限 429。
- **统一错误体**：`{ "error": { "code": "...", "message": "..." } }`
- **计费**：仅在 ③生成（正文逐条 + 导出）发生一次；①解读、②抽包不扣费，仅受限流约束。
- **结果时效**：任务结果与 .docx 默认保留约 7 天，过期取结果返回 404 `result_expired`。

## 10 个端点详情

### `GET /me` — 连通性与余额
```json
{"wallet_balance":1397084,
 "limits":{"rate_per_min":60,"max_concurrent_jobs":3,"running_jobs":0}}
```

### `POST /interpretations` — 智能解读（唯一上传入口）
- 入参：multipart 字段 `file`（.pdf/.doc/.docx）**或** JSON `{"file_url":"https://..."}`。
- 返回：`{"job_id":"..."}`。
- 结果（`/jobs/{id}/result`）：`{"job_id","service":"interpretation","result":{...}}`。
  `result` 含句柄 `project_id`/`result_id`/`status` + **8 个内容维度 + 控标洞察**，
  完整字段见 [附录 A](#附录-a智能解读结果字段)。**记下 `result.project_id`**。

### `POST /bid-documents/{project_id}/packages` — 抽取分包
- 无 body。返回 `{"job_id":"..."}`。
- 结果：
```json
{"service":"bid_document",
 "result":{"packages":[...],"is_multi_package":true,"package_count":2,
           "suggested_pages":50,"max_total_pages":300}}
```
- 把 `packages` 给用户挑选，收集选中的 `package_ids`。
- `is_multi_package=false` 时可跳过选包，generate 不带 `package_ids`。

### `POST /bid-documents/{project_id}/generate` — 生成成品标书
- 入参 JSON：`{"package_ids":[11,12],"total_pages":80}`（非多包可省略 body 或传 `{}`）。
- 返回 `{"job_id":"..."}`。内部串行「选包 → 抽需求 → 大纲 → 逐条正文 → 导出」，耗时长。
- 进度阶段加权：`select / requirements / outline / content / export`。
- **结果是流式 .docx 二进制**（非 JSON），响应头 `Content-Disposition: attachment; filename="bid_<job_id>.docx"`。

### `POST /projects/{project_id}/compliance-reviews` — 合规审查
- 入参：multipart `bid_files`（一或多份 .doc/.docx）**或** JSON `{"file_urls":[...],"is_blind_bid":false,"is_electronic_bid":false}`。
- project 必须已完成解读，否则 409。返回 `{"job_id":"..."}`。
- 结果（`/jobs/{id}/result`）：`result.compliance` 含 `summary`/`issues`/`similarity_issues`/`manual_items` 等，
  完整字段见 [附录 B](#附录-b合规审查结果字段)。

### `GET /jobs/{job_id}` — 查任务状态（轮询用）
```json
{"job_id":"...","service":"interpretation|bid_document|compliance",
 "phase":null,"status":"running",
 "progress":{"percent":20,"stage":"interpreting","stage_label":"智能解读中","updated_at":"..."},
 "error":null,"created_at":"...","updated_at":"..."}
```

### `GET /jobs/{job_id}/result` — 取结果
- 解读/合规返回 JSON；标书制作返回 .docx 二进制流。

### `POST /jobs/{job_id}/cancel` — 取消
- 尽力而为；已过的扣费点不退款。

### `POST /open/v1/trial-accounts`（无鉴权）

设备指纹开通试用账号；同设备（指纹或 MAC 相同）幂等返回原 Key。

请求：`{"device": {"hostname": "", "platform": "", "arch": "", "username": "", "home_path": "", "mac_hash": ""}}`
（6 项均为字符串，采集失败传空串；全空 → 422 fingerprint_required。）
可选 `channel`（渠道码，如 `s111`，落库 `users.register_channel` 标记账户注册渠道；缺失/非法自动忽略，绝不阻断开通）。

响应：`{"app_key": "bk_live_...", "wallet_balance": 200, "is_new": true}`

错误：422 `fingerprint_required`（全空指纹）；429 `trial_limit_exceeded`（**每个 IP / 每个 MAC 终身仅限自动开通 1 个**，改走手机号注册）。

### `POST /open/v1/auth/register` 变更

入参新增可选 `trial_app_key`：手机号未注册且 Key 对应试用账号（无 phone）时，
绑定到该账号（Key 不变、+200），响应含 `"bound": true`；其余情形自动忽略该参数。
入参新增可选 `channel`（渠道码，如 `s111`）：仅**新建账号**时落库 `users.register_channel`；
已注册/绑定路径忽略（渠道归属以首次建号为准）；缺失/非法自动忽略，绝不阻断注册。

### 402 insufficient_balance 错误体新增字段

`phone_bound`（bool）；未绑手机号时另有 `bind_url`
（`https://biaoshu.zhiliaobiaoxun.com/register?bind_key=<app_key>`）；
`recharge_url` 追加 `?bind_key=<app_key>`。

### 积分前置闸门（提交时 402）

积分余额 < 1 时，`POST /interpretations`、`POST /bid-documents/{pid}/generate`、
`POST /projects/{pid}/compliance-reviews` 三个计费入口在**提交时**直接返回 402
`insufficient_balance`（错误体含上述引导字段），充值或绑定手机号领积分后方可操作；
抽包（packages）与查询类接口不受限。skill 侧提交前也会先调 `GET /me` 预检余额。

### 9. POST /experience/submit —— 经验沉淀（只存不用）

同步接口。把助手总结的经验条目回传平台**原样存储**（`skill_experience` 表），平台侧当前不做任何消费；每用户每日 ≤ 20 条。

| 入参 | 说明 |
|---|---|
| `type` | `material` / `preference` / `correction` |
| `stage` | `interpret` / `write` / `compliance` |
| `title` | 条目标题，≤ 200 字 |
| `content` | 总结文本，≤ 10KB |
| `project_id` | 可选，关联项目溯源 |

返回：`{"id": 123, "total_count": N}`（N=该用户累计沉淀条数）。

### 10. POST /feedback/submit —— 问题上报（只存不用）

同步接口。结构化上报使用问题（`skill_feedback` 表），服务端对手机号/`bk_live_` 等敏感模式二次脱敏；每用户每日 ≤ 20 条。**不接收文件内容。**

| 入参 | 说明 |
|---|---|
| `category` | `misguide` / `correction` / `error` / `suggestion` |
| `scene` | 场景，≤ 200 字 |
| `phenomenon` | 现象描述，≤ 5000 字 |
| `expectation` | 期望行为（可选），≤ 5000 字 |
| `skill_version` / `channel` | zcm.py 自动附带 |

返回：`{"id": 456}`。

### 11. GET /skill/version —— 版本更新检查（需鉴权，只读）

同步接口。返回当前发布的最新 skill 版本，供客户端每日一次比对提示更新。**需 `X-App-Key` 校验**（与其余门面端点一致，无/错 key → 401/403）；受开放 API 总开关保护（关 → 整层 404）。探活性质、不计限流。版本存后端 `skill_setting` 表 `key='skill_version'`（改库即生效、免重新部署）。

| 入参（query） | 说明 |
|---|---|
| `channel` | 可选，渠道码；**两线版本锁步统一，当前不区分渠道、被忽略**（保留仅为向后兼容） |

返回 200：`{"latest": "2.2.0", "notice": null}`
- `latest`：最新版本（semver）。无配置/`null` 或任何非 200（含 401/403/404）→ 客户端静默跳过、不影响命令。
- `notice`：可选自定义提示文案，默认 `null`。

> 客户端行为：每天首次运行（已配置 Key 时）带 `X-App-Key` 查一次，本地 `SKILL_VERSION` 落后才提示；只提示不下载。

## 错误码速查

| HTTP | code | 含义与处理 |
|---|---|---|
| 401 | `missing_credentials` / `invalid_credentials` | 缺 `X-App-Key` Header / App Key 不对 → 检查凭证或重置 Key |
| 403 | `account_disabled` | 凭证或用户被停用 |
| 402 | `insufficient_points` | 余额不足，不扣费不产出 → 充值 |
| 404 | `not_found` | 多为开放 API 总开关未开（整层 404）→ 联系管理员开启 |
| 404 | `job_not_found` / `project_not_found` / `result_expired` | 句柄不存在/非本人/结果过期（7 天 TTL） |
| 409 | `invalid_job_state` | 任务未成功就取结果 / 未解读就生成 / 未抽包就 generate |
| 422 | `validation_error` | 文件缺失/类型不支持 / file_url 非 https 或指向内网 / 缺 package_ids |
| 429 | `rate_limited` / `too_many_concurrent_jobs` | 触发限流 → 退避重试（看 `Retry-After`）或减并发 |
| 429 | `daily_quota_exceeded` | 经验/反馈当日已达 20 条上限，次日再试 |
| 500 | `internal_error` | 服务端异常 → 重试或反馈 |

任务级失败时 `GET /jobs/{id}` 的 `error.code`：`interpretation_failed` / `generation_failed` / `compliance_failed` / `insufficient_points` / `canceled` / `worker_lost`（服务重启导致，需重新提交）。

## 注意事项

- **唯一上传入口**：招标文件只能经 `/interpretations` 上传并产出 `project_id`；制作与合规都复用它，**不要重复上传同一招标文件**。
- **幂等**：网络重试带相同 `Idempotency-Key`（UUID），避免重复建任务/重复扣费。
- **计费**：扣 App Key 所属用户积分，与网页同价；生成前用 `GET /me` 看 `wallet_balance` 预判。
- **内容质量依赖知识库**：正文质量取决于 owner 租户的公司资料库；资料缺失会致内容退化（不硬失败）。
- **来源标记**：经开放 API 产生的数据标记为 **skill** 来源（网页端为「平台」），便于在网页历史/消费流水里区分。

## 纯 curl 备用调用

`zcm.py` 不可用时的等价命令（`$BASE`/`$KEY` 见上）：

```bash
export BASE="https://biaoshu.zhiliaobiaoxun.com/api/open/v1"
H=(-H "X-App-Key: $KEY")

curl -s "${H[@]}" "$BASE/me"                                              # 连通+余额
curl -s "${H[@]}" -F "file=@招标文件.pdf" "$BASE/interpretations"          # 解读
curl -s "${H[@]}" -X POST "$BASE/bid-documents/<pid>/packages"           # 抽包
curl -s "${H[@]}" -H "Content-Type: application/json" \
  -d '{"package_ids":[11,12],"total_pages":80}' \
  -X POST "$BASE/bid-documents/<pid>/generate"                           # 生成
curl -s "${H[@]}" "$BASE/jobs/<jid>"                                     # 查状态
curl -s "${H[@]}" "$BASE/jobs/<jid>/result" -o 投标文件.docx              # 下载成品
curl -s "${H[@]}" -F "bid_files=@投标文件.docx" \
  -X POST "$BASE/projects/<pid>/compliance-reviews"                      # 合规
```

> 字段口径与根目录《百炼®标书Skill服务.md》附录 A/B 一致；`scripts/report.py` 据此渲染报告。

---

## 附录 A：智能解读结果字段

`GET /jobs/{id}/result` 的 `result`（`service=interpretation`）：

```json
{
  "project_id": "123", "result_id": 7, "status": "completed",
  "project_info": [...], "compliance": [...], "disqualification": [...],
  "evaluation": [...], "key_requirements": [...], "business_terms": [...],
  "pricing": [...], "procurement_analysis": {...}, "decision_analysis": {...}
}
```

- **project_info[]** 项目基本信息：`field_name` / `field_value` / `source_page` / `source_text`。
- **compliance[]** 合标项（参与资格）：`category` / `requirement_text` / `source_page` / `source_text` / `is_structured`。
- **disqualification[]** 废标项（红线）：在 compliance 字段基础上多 `type`（资格废标/响应性废标/合规废标）。
- **evaluation[]** 评审项：`component` / `item` / `factor` / `score`(满分) / `weight` / `source_page` / `source_text` / `is_structured`。
- **key_requirements[]** 关键要求：`category` / `requirement_text` / `source_page` / `source_text`。
- **business_terms[]** 商务条款：`term_type` / `term_content` / `source_page` / `source_text`。
- **pricing[]** 报价要求：`component` / `requirement_text` / `source_page` / `source_text`。
- **procurement_analysis{}** 采购背景：`analysis_summary` / `procurement_background` / `procurement_objectives` / `procurement_scope_items[]` / `key_constraints[]` / `key_success_metrics[]`(每条 `{name,detail}`，关键成功指标)（缺失字段可为 null/空）。
- **decision_analysis{}** 控标洞察：
  - 顶层：`participation_recommendation`（建议/谨慎/不建议参与）、`control_risk_level`（高/中/低）、`confidence_level`、`summary[]`、`signals[]`、`evidence_items[]`、`actions[]`、`advantaged_supplier_profile[]`、`our_gap_assessment[]`。
  - `signals[]`：`id` / `dimension`（qualification_barrier/technical_targeting/business_barrier/scoring_bias/acceptance_and_performance_risk/pricing_competitiveness_constraint）/ `title` / `risk_level` / `description` / `reasoning` / `evidence_item_ids[]` / `our_stance`（advantage/risk/neutral/unknown）/ `our_stance_reason`。
  - `evidence_items[]`：`id` / `source_category` / `source_page` / `source_text_excerpt` / `why_it_matters`。
  - `actions[]`：`priority`（high/medium/low）/ `action_type` / `recommendation` / `related_signal_ids[]`。

---

## 附录 B：合规审查结果字段

`GET /jobs/{id}/result` 的 `result.compliance`（`service=compliance`）：

```json
{
  "run_id": 42, "status": "completed", "mode": "standalone",
  "document_id": 123, "interpretation_result_id": 7,
  "summary": {...}, "partial_summary": {...}, "bid_files": [...],
  "issues": [...], "similarity_issues": [...], "manual_items": [...],
  "scope_summary_lines": [...], "error_message": null
}
```

- **summary{}** 汇总：`high_count` / `review_count` / `tip_count` / `similarity_count` / `manual_unchecked_count` / `conclusion`(一句话结论) / `conclusion_phase`(full/rules_only/semantic_partial) / `overview_ready` / `semantic_review.state` / `semantic_review.message_zh`。
- **bid_files[]** 被查文件：`id` / `filename` / `content_hash` / `metadata` / `created_at`。
- **issues[]** 合规问题（核心）：`id` / `bid_file_id` / `bid_filename` / `issue_type`(如 `hard_field_presence` 等) / `risk_level` / `result_type` / `title` / `description` / `tender_evidence` / `bid_evidence` / `suggestion` / `confidence`(0-1) / `status` / `user_note`。
  > ⚠️ **实测枚举值**：`risk_level` = **`high`/`review`/`tip`**；`result_type` = **`suspected`/`detected`**。`summary.high_count/review_count/tip_count` 按 `risk_level` 计数。
  > 证据多形态（因引擎而异）：语义类 `tender_evidence/bid_evidence` 主键 **`excerpt`**（另含 `chunk_id`/`section_path`/`section_title`）；硬字段类 `{field,expected_text}`；规则未命中 `{source}`。`report.py` 的 `_ev` 已按 `excerpt > text > field/expected_text > source` 兼容。
- **similarity_issues[]** 多文件雷同（仅多份投标文件时有）：`file_a_id`/`file_b_id` / `file_a_name`/`file_b_name` / `similarity_type`(text_overlap/structure_overlap) / `risk_level` / `title` / `evidence_a{text,page}`/`evidence_b{...}` / `similarity_score`(0-1) / `suggestion` / `status`。
- **manual_items[]** 人工核查清单：`category` / `title`(简短标题) / `description` / `source` / `is_checked` / `note`(备注) / `checked_by` / `checked_at`。
- **scope_summary_lines[]** 检查范围摘要（适合报告开头展示）。

报告推荐布局：总览 → 风险摘要(summary) → 高风险问题(issues 高) → 待人工复核(result_type=semantic) → 格式提示(低) → 多文件相似度 → 人工核查清单。`scripts/report.py` 已实现此布局。
