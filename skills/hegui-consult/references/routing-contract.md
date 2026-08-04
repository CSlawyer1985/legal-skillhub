# 内部路由契约

法规结构化结论只用于控制公告检索，不作为面向用户的法规答复，也不得替代法规原文。

## 一、生成单位

为每个法律子问题分别生成一条路由。披露、任职资格、程序、时限不得合并判断。

```json
{
  "legal_issue": "disclosure",
  "conclusion": "required",
  "basis_strength": "direct_rule",
  "subject": "独立董事",
  "event": "受到行政处罚",
  "qualifiers": ["非因本公司事项"],
  "trigger_conditions": ["中国证监会行政处罚", "其他有权机关重大行政处罚"],
  "satisfied_conditions": ["中国证监会行政处罚"],
  "missing_facts": [],
  "basis_ids": ["法规数据库ID"],
  "announcement_search": true
}
```

## 二、字段约束

- `legal_issue`：`disclosure`、`qualification`、`procedure`、`timing` 或其他明确子问题。
- `conclusion`：只允许 `required`、`conditional`、`not_required`、`unknown`。
- `basis_strength`：只允许 `direct_rule`、`derived_from_rule`、`insufficient`。
- `subject`、`event`、`qualifiers`：只使用用户事实和法规中性规范用语，不增加未提供事实。
- `trigger_conditions`：法规条款明确写出的条件。
- `satisfied_conditions`：用户事实已经满足的条件。
- `missing_facts`：会改变路由结论的事实。
- `basis_ids`：通过适用性和覆盖度校验的法规数据库记录 ID。
- `announcement_search`：只按下述决策表设置。

## 三、结论状态

| 状态 | 使用条件 | 公告检索 |
|---|---|---|
| `required` | 直接条款规定应当披露，且用户事实满足触发条件 | 披露子问题设为 `true` |
| `conditional` | 条款存在处罚机关、重大程度、金额比例等条件，但事实不足 | 默认 `false`；条件补齐且满足后改为 `true` |
| `not_required` | 直接条款明确不要求，或已知事实明确未达到条款条件 | `false` |
| `unknown` | 无直接条款、正文不完整、适用性不明或 coverage 不足 | `false` |

不得因为“没有检索到要求披露的条款”直接推导 `not_required`；这种情况应为 `unknown`。

## 四、决策步骤

1. 检查是否存在适用且覆盖该子问题的法规正文。
2. 没有直接材料时设为 `unknown`。
3. 条款明确列出触发条件时，对照用户已知事实逐项判断。
4. 条件全部满足时设为 `required`。
5. 条件可能满足但事实不足时设为 `conditional` 并列出 `missing_facts`。
6. 只有法规明确排除或已知事实明确低于法定条件时，才能设为 `not_required`。
7. 只有披露子问题的 `required`，或条件已经满足的 `conditional`，才能触发公告检索。

## 五、多问题示例

```json
[
  {
    "legal_issue": "disclosure",
    "conclusion": "required",
    "announcement_search": true,
    "basis_ids": ["A"]
  },
  {
    "legal_issue": "qualification",
    "conclusion": "conditional",
    "announcement_search": false,
    "basis_ids": ["B"],
    "missing_facts": ["处罚机关", "违法领域", "是否存在市场禁入"]
  }
]
```

## 六、展示边界

路由可以保留在工具结果或内部审计记录中，但最终答复不得把该 JSON 当作法规依据。面向用户时必须回到 `basis_ids` 对应的正式法规名称、文号、条款原文和适用分析。
