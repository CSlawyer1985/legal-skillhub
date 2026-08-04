# 争议日志模板

当用户需要可直接粘贴用于 Legal Tracker、CounselLink、Brightflag、电子邮件或内部法务运营跟踪器的审查表时使用本模板。

## CSV 表头模板
```csv
invoice_id,line_id,matter_id,matter_name,timekeeper_name,timekeeper_title,issue_label,issue_summary,rule_or_term_reference,evidence_reference,billed_value,challenged_value,confidence,recommended_action,status,notes
```

## Markdown 表格模板
| Invoice ID | Line ID | Matter | Timekeeper | Issue Label | Issue Summary | Rule or Term Reference | Evidence Reference | Billed Value | Challenged Value | Confidence | Recommended Action | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| INV-001 | 1005 | 雇佣事项A | J. Doe | `vague-narrative` | 叙述未说明任务、问题或工作成果。 | OCG 叙述具体性条款 | 发票第3页，第1005行 | 1240.00 | 620.00 | 中等 | 要求澄清或部分核销。 | 未结 |

## 建议的状态值
- `open`（未结）
- `needs-clarification`（需要澄清）
- `challenged`（已质疑）
- `resolved`（已解决）
- `approved-with-note`（附注批准）

## 使用规则
- 优先使用 [issue-taxonomy.md](issue-taxonomy.md) 中的稳定问题标签。
- 保持 `issue_summary` 足够简短，以便粘贴到计费系统备注中。
- `challenged_value` 用于实际争议金额，而非完整发票，除非有理由。
