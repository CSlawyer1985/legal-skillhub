# TIA → RoPA 交换增量格式

本文件说明 TIA 技能如何生成更新 RoPA 登记册的增量文件。它符合 RoPA 的 `interchange-inbound-schema.json` v1.0（定义于 `skills/ropa/references/interchange-inbound-schema.md`）。

TIA 技能为每项与 RoPA 活动关联的已评估传输生成**一个**增量文件。

---

## 文件位置与命名

增量文件写入：

```
skills/ropa-workspace/<org-slug>/inbound/tia-<target-activity-id>-<timestamp>.delta.json
```

其中：
- `<org-slug>`——组织的短横线标识（例如 `acme-gmbh`）
- `<target-activity-id>`——被更新的 RoPA ActivityEntry / ProcessorEntry 的 UUID
- `<timestamp>`——ISO 8601，精确到小时分钟（例如 `2026-05-28T1430+0200`）

示例：`tia-9a7fa4c8-3b0a-4f9d-a5d6-8e2b7a0f9c12-2026-05-28T1430+0200.delta.json`

---

## 增量文件结构

```json
{
  "schema_version": "1.0",
  "source_skill": "tia v<X.Y>",
  "produced_at": "2026-05-28T14:30:00+02:00",
  "target_activity_id": "9a7fa4c8-3b0a-4f9d-a5d6-8e2b7a0f9c12",
  "target_entry_type": "controller_activity",
  "patches": [
    {
      "op": "replace",
      "path": "/transfers/0/tia_ref",
      "value": "TIA-US-2026-001",
      "field_label": "TIA reference"
    },
    {
      "op": "replace",
      "path": "/transfers/0/tia_status",
      "value": "proceed_with_measures",
      "field_label": "TIA status"
    },
    {
      "op": "replace",
      "path": "/transfers/0/tia_completed_date",
      "value": "2026-05-28",
      "field_label": "TIA completion date"
    },
    {
      "op": "replace",
      "path": "/transfers/0/tia_review_date",
      "value": "2027-05-28",
      "field_label": "TIA next review date"
    },
    {
      "op": "replace",
      "path": "/transfers/0/supplementary_measures",
      "value": ["TM-1 encryption-exporter-keys", "CM-1 transparency-obligation", "CM-2 challenge-clause"],
      "field_label": "Supplementary measures"
    }
  ],
  "context": {
    "summary": "TIA completed for US transfer via SCCs Module 2. Step 3 conclusion: transfer tool not effective, supplementary measures required. Proceed with TM-1 + CM-1 + CM-2.",
    "rationale_doc": "skills/tia-workspace/acme-gmbh/TIA-US-2026-001.docx",
    "rationale_doc_sha256": "<sha256 hex of the docx>",
    "output_links": [
      "skills/tia-workspace/acme-gmbh/TIA-US-2026-001.md"
    ]
  }
}
```

---

## 字段参考

| 字段 | 必填 | 备注 |
|---|---|---|
| `schema_version` | 是 | 对当前 RoPA 入站模式始终为 `"1.0"` |
| `source_skill` | 是 | `"tia v<X.Y>"` |
| `produced_at` | 是 | ISO 8601 带时区 |
| `target_activity_id` | 是 | UUID——必须存在于目标 RoPA sidecar 中 |
| `target_entry_type` | 否 | `controller_activity`（默认）或 `processor_activity` |
| `patches` | 是 | RFC 6902 子集（replace/add 操作） |
| `context.summary` | 是 | 一句话——显示在 RoPA docx 和会话日志中 |
| `context.rationale_doc` | 是 | 正式 TIA .docx 的路径 |
| `context.rationale_doc_sha256` | 建议 | 防篡改证据 |
| `context.output_links` | 可选 | 附加产物（例如 markdown 报告） |

---

## TIA 状态枚举

`tia_status` 补丁值使用以下枚举值：

- `proceed`——第 3 步结论 (1)：传输工具有效
- `proceed_with_measures`——第 3 步结论 (2)：已采取措施，有效性足够
- `proceed_no_realistic_risk`——第 3 步结论 (3)：问题法律无现实适用基础
- `suspend`——第 3 步结论 (2) 但措施不足，或第五章机制未到位
- `adequacy`——受第 45 条充分性决定涵盖（仅轻量评估）
- `art49_consent`——第 49 条第 1 款第(a)项依据
- `art49_contract`——第 49 条第 1 款第(b)项依据
- `art49_other`——其他第 49 条克减（子条款在摘要中注明）

---

## 生产者侧责任

TIA 技能：
1. 读取 RoPA sidecar 以确认 `target_activity_id` 存在。
2. 仅在 TIA 签批后（.docx 第 6 节完成）发出增量。
3. 原子写入文件（临时文件 + 重命名）。
4. 计算理由文档的 SHA-256 并纳入增量。
5. **不**删除或修改任何先前增量。

写入后，增量归 RoPA 所有。RoPA 的合并模式将读取、验证、应用，并相应将文件移至 `inbound/applied/` 或 `inbound/rejected/`。
