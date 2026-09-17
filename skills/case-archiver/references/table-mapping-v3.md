# V3 表格映射与迁移

V3 的目标是：模板稍有合并、拆分或插入列时，不再静默把内容写进错误单元格。字段定位按以下优先级使用。

## 1. 显式标记符（推荐）

在 Word 模板中放置唯一标记，例如 `{{案号}}`。标记被 Word 拆成多个 run 也能识别。

```json
{
  "name": "案号",
  "marker": "{{案号}}",
  "source": "auto",
  "from": "判决书|裁决书",
  "key": "案号"
}
```

同一标记确实需要填写多处时才设置 `"replace_all": true`。默认只填第一处，避免误改。

## 2. Word 内容控件

在 Word“开发工具”中给内容控件设置 Tag 或标题。配置使用：

```json
{
  "name": "承办律师",
  "control_tag": "承办律师",
  "source": "auto",
  "key": "受托人"
}
```

内容控件适合长期维护的标准表单；标签应在整个模板内保持唯一。

## 3. 标签相对定位

不能修改模板时，根据标签寻找同格、右格或下格。

```json
{
  "name": "案由",
  "selector": {
    "type": "cell_anchor",
    "table": 0,
    "label": "案由",
    "direction": "right",
    "match": "exact"
  },
  "mode": "replace",
  "source": "auto",
  "key": "案由"
}
```

- `table`：V3 模板检查报告中的表格序号；建议填写，减少歧义。
- `direction`：`same`、`right`、`below`。
- `offset`：相对移动格数，默认 1。
- `match`：`exact`（推荐）、`contains`、`regex`。
- `occurrence`：同一表内标签重复时，从 0 开始指定第几处。

合并单元格按底层 XML 单元格去重，`right` 指“右侧下一个真实单元格”，不是合并区产生的重复别名。

## 4. 旧坐标兼容

V2 的 `loc: [表, 行, 列]` 仍可使用，但应增加保护条件：

```json
{
  "name": "固定选项",
  "loc": [0, 4, 2],
  "expected_text": "□一审",
  "mode": "choice",
  "value": "一审诉讼"
}
```

坐标越界或保护文字不符时，V3 会报错并保留原输出，不再静默标记为完成。

## 写入模式

| mode | 行为 |
|---|---|
| `replace` / `value` | 替换目标格内容，适合纯值格 |
| `after_label` | 保留同格标签，替换标签后的值 |
| `append` | 兼容 V2；目标值已存在时不重复追加 |
| `prepend` | 写到原内容前 |
| `amount` | 处理“元”、免费、免收等金额格 |
| `choice` | 将选中项改为 `☒`，其他项规范为 `☐` |

`choice` 支持把输入值映射到模板选项：

```json
{
  "mode": "choice",
  "options": {
    "一审": "一审诉讼",
    "仲裁": "劳动仲裁"
  }
}
```

## 内容长度与格式

```json
{
  "format": {
    "max_chars": 400,
    "overflow": "warn",
    "font_size_pt": 10.5,
    "auto_shrink": true,
    "min_font_size_pt": 8.5,
    "alignment": "left",
    "vertical_alignment": "center"
  }
}
```

- `overflow`：`warn`（默认，不丢内容）、`error`、`truncate`。法律文书一般不要使用 `truncate`。
- `alignment`：`left`、`center`、`right`、`justify`。
- `vertical_alignment`：`top`、`center`、`bottom`。
- 多行值中的换行会保留。

## 严格模式与写后校验

模板配置默认 `"strict": true`。任何非空字段出现以下情形时，该表格项记为 `error`，不覆盖已有输出：

- 标记、内容控件或标签不存在；
- 标签不唯一且没有 `table`/`occurrence`；
- 旧坐标越界或保护条件失败；
- 保存后无法在 DOCX 中重新找到写入值；
- 内容超过 `max_chars` 且 `overflow=error`。

错误和警告写入 `.归档状态.json` 的 `fill_report`，便于定位具体字段。

## V2 配置迁移

1. 运行 `python scripts/fill_docx.py 模板.docx --out 模板检查.json`。
2. 优先在模板中加入 `{{字段名}}`，或给 Word 内容控件设置 Tag。
3. 不能改模板的字段改为 `cell_anchor`。
4. 暂时保留的 `loc` 增加 `expected_text`。
5. 审阅接入向导生成的 `review_required=true` 字段。
6. 用一份脱敏案卷试归档，确认 `fill_report.errors` 为空并查看 Word 渲染结果。

