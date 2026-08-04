---
name: labor-arbitration-application
description: 根据劳动关系日期、工资、争议类型和现有证据，生成劳动仲裁申请书草稿、备选请求金额、时效提示和证据缺口清单。
compatibility: 需要联网访问 https://api.qixiantech.com；作为腾讯 SkillHub Pay Skill 发布。
metadata:
  version: 1.0.0
  author: 北京市起弦信息技术有限公司
  homepage: https://qixiantech.com
  billing: wechat-agent-pay-x402
---

# 劳动仲裁申请书生成

服务价格 ¥9.99/次。工具不判断案件胜负，不保证立案或支持请求；提交前须核对当地仲裁委管辖、材料和计算口径。

## 付费前置检查

调用前检查当前 Agent 是否已安装 `weixinpay` 插件：

- 已安装：继续收集信息并请求服务。
- 未安装：提示“当前 Agent 暂不支持微信支付付费能力”，终止流程，不发起请求。

## 边界

- `illegal_termination_compensation` 只生成违法解除赔偿金备选测算，不代表工具已经认定解除违法。
- 工资三倍封顶、最长十二年等规则只有在提供当地平均工资且触发条件时才用于初算。
- 仲裁时效存在中止、中断和不同起算点，接口只根据用户填写的日期提示风险。

## 调用流程

1. 说明提交内容会通过 HTTPS 发往第三方服务；删除不必要的身份信息、密钥和商业秘密并取得用户同意。
2. 收集必填字段：`applicant_name`、`employer_name`、`employment_start`、`employment_end`、`filing_date`、`dispute_date`、`monthly_salary`、`claims`、`facts_summary`、`evidence_available`。
3. 按实际情况收集可选字段：`local_average_monthly_salary`、`unpaid_wages_amount`、`weekday_overtime_hours`、`weekend_overtime_hours`、`holiday_overtime_hours`。
4. 主张欠薪时填写 `unpaid_wages_amount`；主张加班费时至少填写一种加班小时数。
5. 删除身份证号、住址、电话等不影响测算的敏感信息；生成后在本地补齐仲裁委要求的身份和送达信息。
6. 在 SkillHub 展示 ¥9.99、服务用途和数据边界，取得用户明确付款确认。
7. 发起请求：

```http
POST https://api.qixiantech.com/api/labor-arbitration-application
Content-Type: application/json
Authorization: Bearer <SkillHub平台调用凭证>
```

```json
{
  "applicant_name": "张某",
  "employer_name": "某科技有限公司",
  "employment_start": "2024-01-10",
  "employment_end": "2026-06-30",
  "filing_date": "2026-07-29",
  "dispute_date": "2026-06-30",
  "monthly_salary": 12000,
  "local_average_monthly_salary": 14000,
  "claims": [
    "unpaid_wages",
    "economic_compensation"
  ],
  "unpaid_wages_amount": 12000,
  "weekday_overtime_hours": 1,
  "facts_summary": "申请人按约提供劳动，用人单位于2026年6月通知解除劳动关系，并拖欠最后一个月工资。双方就工资及解除补偿未能协商一致。",
  "evidence_available": [
    "labor_contract",
    "bank_records",
    "termination_notice"
  ]
}
```

### 平台返回 HTTP 402 时

首次请求不携带 `X-Out-Trade-No`。服务端完成微信支付 Native 下单和
SkillHub AI 预下单后，会返回：

- HTTP 状态码：`402`
- Header `WeixinPay-Required`：支付码
- Header `X-Out-Trade-No`：商户订单号
- Body `WeixinPay`：兼容只读取响应体的 Agent
- Body `amount`：`9.99`，`currency`：`CNY`

收到 402 后：

1. 保存两个响应头，核对金额为 ¥9.99、币种为 CNY。
2. 将 `WeixinPay-Required` 的值作为 `paymentCode` 调用 `weixinpay_pay`，由用户确认并完成真实支付。
3. 支付成功后必须重新请求同一 URL；JSON body 与首次请求逐字段一致。
4. 重试请求必须原样携带 `WeixinPay-Required` 和 `X-Out-Trade-No` 两个 Header。
5. 后端按 `X-Out-Trade-No` 向微信支付查单；只有 `trade_state=SUCCESS`、金额、商户号和 AppID 均匹配时才返回付费结果。
6. 返回 `PAYMENT_REQUIRED` 或 `NOT_PAID` 时等待原订单，不创建新订单；返回 `REFUNDED` 时告知已退款并终止。
7. 禁止伪造支付码、订单号或支付结果，也不要修改原始请求体。

支付后重试示例：

```http
POST <与首次请求相同的 URL>
Content-Type: application/json
Authorization: Bearer <SkillHub平台调用凭证>
WeixinPay-Required: <402 响应中的 payment_code>
X-Out-Trade-No: <402 响应中的 out_trade_no>

<与首次请求完全一致的 JSON>
```

## 展示结果

原样展示 `result_status`、`summary`、`score`、`grade`、`findings`、`recommendations`、`risks`、`missing_info`、`claim_items`、`candidate_total_amount`、`limitation_assessment`、`evidence_checklist`、`application_draft`。

- `draft_ready` 仅表示字段足以生成草稿，不表示案件可以立案或胜诉。

HTTP `402` 按上方流程处理支付；`400` 先修正输入且确认字段类型、长度和枚举值后再重试，不要重复付款；`401/403` 表示平台凭证问题；`409` 订单冲突先查询原订单；`429` 按 `Retry-After` 等待；`5xx` 告知暂不可用。
