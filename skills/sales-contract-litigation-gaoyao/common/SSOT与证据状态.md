# SSOT 与证据状态

## 六张底稿

1. 主体与角色表。
2. 合同、补充协议与条款链。
3. 标的、交付、验收、质量与数量链。
4. 价款、发票、付款、冲抵、退货与余额链。
5. 催告、异议、解除、诉讼时效与程序时间线。
6. 诉请—要件—事实—证据—法源矩阵。

## 字段规则

每个事实字段至少包含：

- `value`
- `status`
- `evidence_ids`
- `source_locator`
- `page_or_clause`
- `updated_at`
- `used_by_claims`
- `used_by_documents`

状态只能是 `verified`、`single-source`、`ocr-only`、`conflict`、`missing` 或 `not-applicable`。

## 金额规则

价款余额必须记录合同总价、调整项、退货/减价、已付款、付款主体、冲抵、发票口径、计算基准日和完整算式。内部台账、对账草稿或破损公式不得单独证明债务确认。

## 证据规则

每项证据包含 `evidence_id`、匿名逻辑 locator、完整 sha256、页码/条款、证据状态、证明对象、反证风险和下一步。证据目录编号必须与起诉状、代理词、法律意见和办案方案一致。

## 风险规则

每项风险必须包含：

- `severity`: `fatal`、`major`、`general`
- `likelihood`: `high`、`medium`、`low`、`unknown`
- `impact_on_claim`: `delete`、`amend`、`downgrade`、`filing-ok-but-win-or-recovery-risk`
- `evidence_basis`: 证据编号或明确的 `missing`

禁止虚构百分比。风险未闭合时保留 HOLD，不因文本认可而自动解除实体门。
