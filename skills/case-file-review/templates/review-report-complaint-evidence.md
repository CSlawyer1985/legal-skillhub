# [案件名称] 阅卷报告

> **分析日期**：{{REPORT_DATE}}
> **材料数量**：{{TOTAL_COUNT}} 份（起诉状 1 份 + 证据 {{EVIDENCE_COUNT}} 份）
> **分析模式**：模式 B — 起诉状 + 证据材料
> **OCR 引擎**：{{OCR_ENGINE}}

---

## 一、材料清单与 OCR 处理

### 1.1 程序文书

| 序号 | 编号 | 文件名 | 类型 | OCR 状态 |
|---|---|---|---|---|
| 1 | 起诉状 | {{COMPLAINT_FILENAME}} | 起诉状 | {{COMPLAINT_OCR_STATUS}} |

### 1.2 证据材料

{{EVIDENCE_LIST_TABLE}}

---

## 二、起诉状要点提取

### 2.1 基本信息

| 项目 | 内容 |
|---|---|
| 案由 | {{CAUSE_OF_ACTION}} |
| 原告 | {{PLAINTIFF}} |
| 被告 | {{DEFENDANT}} |
| 受理法院 | {{COURT}}（如有） |
| 案号 | {{CASE_NUMBER}}（如有） |

### 2.2 诉讼请求

{{CLAIMS_LIST}}

### 2.3 事实与理由摘要

{{FACTS_SUMMARY}}

---

## 三、事实与证据梳理

{{EVIDENCE_FACTS_SECTIONS}}

---

## 四、法律关系分析

### 4.1 法律关系定性

起诉状确定的法律关系为：**{{LEGAL_RELATIONSHIP}}**

### 4.2 构成要件逐项对照

{{LEGAL_ELEMENT_TABLE}}

### 4.3 证据不足要件

{{INSUFFICIENT_ELEMENTS}}

---

## 五、证据矛盾点清单

{{CONTRADICTIONS_SECTION}}

---

## 六、时间轴

### 6.1 时间轴总览

![案件时间轴](timeline.png)

### 6.2 Mermaid 时间轴（备选）

```mermaid
{{MERMAID_TIMELINE}}
```

---

## 七、综合分析结论

### 7.1 证据链完整度评估

{{EVIDENCE_CHAIN_ASSESSMENT}}

### 7.2 诉讼请求证据支撑度

| 诉讼请求 | 支撑证据 | 支撑度 | 风险等级 |
|---|---|---|---|
{{CLAIM_EVIDENCE_TABLE}}

### 7.3 关键风险提示

{{KEY_RISKS}}

### 7.4 补证建议

{{SUPPLEMENTARY_EVIDENCE_ADVICE}}

### 7.5 后续行动建议

{{NEXT_STEPS}}

---

*本报告由 case-file-review Skill 自动生成，所有结论均标注证据来源。材料未提及的信息已标注"待补充"，请结合案件实际情况核实。*
