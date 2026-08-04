# 审查意见 JSON Schema

第四步输出的审查意见 JSON 文件（`reviews_<timestamp>.json`）的格式说明。

## JSON 示例

```json
[
  {
    "section": "摘要",
    "claim_number": null,
    "issue": "摘要字数超过300字",
    "context": "摘要中包含问题原文的上下文片段",
    "suggestion": "建议删减字词，使摘要不超过300字",
    "action_type": "comment",
    "old_text": null,
    "new_text": null,
    "highlight_text": "问题原文的上下文片段"
  },
  {
    "section": "权利要求书",
    "claim_number": 1,
    "issue": "附图标记未加括号",
    "context": "第一箍套1",
    "suggestion": "建议将'第一箍套1'修改为'第一箍套（1）'",
    "action_type": "replace",
    "old_text": "第一箍套1",
    "new_text": "第一箍套（1）"
  },
  {
    "section": "权利要求书",
    "claim_number": 2,
    "issue": "使用了具体数值限定权利要求",
    "context": "所述进气口之间的夹角呈60°或120°",
    "suggestion": "建议使用数值范围限定，如'所述进气口之间的夹角呈60°至120°'",
    "action_type": "replace",
    "old_text": "所述进气口之间的夹角呈60°或120°",
    "new_text": "所述进气口之间的夹角呈60°至120°"
  },
  {
    "section": "说明书",
    "claim_number": null,
    "issue": "包含商业性宣传用语",
    "context": "本卡箍压榨出的山茶油味道香、口感棒。",
    "suggestion": "建议删除商业性宣传用语",
    "action_type": "delete",
    "old_text": "本卡箍压榨出的山茶油味道香、口感棒。",
    "new_text": null
  },
  {
    "section": "说明书",
    "claim_number": null,
    "issue": "发明名称超过25个字",
    "context": "一种用于……的装置",
    "suggestion": "建议精简发明名称至25字以内",
    "action_type": "comment",
    "old_text": null,
    "new_text": null,
    "highlight_text": "一种用于……的装置"
  }
]
```

## 字段说明

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| `section` | string | 问题所属章节：`"摘要"`、`"权利要求书"`、`"说明书"` |
| `claim_number` | number 或 null | 如果问题属于某项权利要求，填写权利要求序号；否则为 null |
| `issue` | string | 问题描述 |
| `context` | string | 问题原文上下文（用于在文档中定位并添加批注） |
| `suggestion` | string | 修改建议 |
| `action_type` | string | 操作类型：`"comment"`（仅添加批注）、`"replace"`（修订模式下替换字词）、`"delete"`（修订模式下删除字词） |
| `old_text` | string 或 null | 需要被替换或删除的原文文本。`action_type` 为 `"replace"` 或 `"delete"` 时必填，为 `"comment"` 时为 null |
| `new_text` | string 或 null | 替换后的新文本。`action_type` 为 `"replace"` 时必填，为 `"delete"` 或 `"comment"` 时为 null |
| `occurrence` | number 或 null | 当同一 `context` 在文档中出现多次时，指定标注第几次出现（从 1 开始计数）。不指定时默认标注第一次出现 |
| `highlight_text` | string 或 null | 批注精准定位文本（comment 类型时强烈建议填写）。指定批注应精确覆盖的文本范围，仅批注该文本而非整个 context。必须是 `context` 的子串且是文档中实际存在的原文。应尽量短小精悍，只包含与问题直接相关的最小文本片段。replace/delete 类型时此字段被忽略（批注范围由修订追踪自动确定） |

## action_type 判定规则

- **`"replace"`**：修改建议中明确指出了需要替换的具体字词（如"建议将'X'修改为'Y'"），填写 `old_text` 和 `new_text`
- **`"delete"`**：修改建议中明确指出了需要删除的具体字词（如"建议删除'X'"），填写 `old_text`，`new_text` 为 null
- **`"comment"`**：修改建议无法明确具体操作（如"建议删减字词"），`old_text` 和 `new_text` 均为 null

## 审查意见要求

- 审查意见必须基于审查规则，不得随意添加规则外的意见
- 每条审查意见必须有明确的 `context`（原文上下文），`context` 必须是文档中实际存在的文本片段
- `context` 应尽量精确定位到包含问题的最小文本片段
- `action_type` 为 `"replace"` 或 `"delete"` 时，`old_text` 必须是文档中实际存在的文本，且必须是 `context` 的子串或等于 `context`
- `highlight_text` 用于 comment 类型时指定批注精准覆盖范围，必须是 `context` 的子串且是文档中实际存在的原文
- `highlight_text` 应尽量短小精悍，只包含与问题直接相关的最小文本片段
- 如果不填写 `highlight_text`，批注将覆盖整个 `context` 范围（可能导致批注范围过大）
- `highlight_text` 对 replace/delete 类型无效（批注范围由修订追踪自动确定，仅覆盖实际修订的文本）
- 当同一 `context` 在文档中出现多次但只需标注特定位置时，使用 `occurrence` 字段（从 1 开始的整数）指定第几次出现；不指定时默认标注第一次出现
