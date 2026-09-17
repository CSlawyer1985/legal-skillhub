# 配置规范（通用）· case-archiver V3

每家律所的配置位于 `~/.workbuddy/case-archiver/firm_config/<firm>/`。引擎不在技能包内保存律所模板、案卷或客户信息，因此升级技能不会覆盖业务配置。

## 1. paths.json

```json
{
  "firm_name": "示例律师事务所",
  "template_dir": "C:\\...\\归档模板",
  "output_base": "C:\\...\\归档输出",
  "source_base": "C:\\...\\诉讼案件",
  "directory_template": "归档目录（民事代理卷）.doc"
}
```

所有业务路径必须使用绝对路径。

## 2. preferences.json

```json
{
  "merge_pdf": "ask",
  "auto_number_folders": true,
  "leave_blank_not_placeholder": true
}
```

- `merge_pdf` 仅控制是否提示：`ask`、`never`、`always`。V3 不会因为 `always` 自动合并；仍需用户确认并显式传入 `--merge yes`。
- `leave_blank_not_placeholder`：空值保持空白，不写“待填写”等占位词。

## 3. archive_plan.json

`order` 是有序目录项列表：

| 字段 | 含义 |
|---|---|
| `seq` | 目录序号 |
| `name` | 目录项名称 |
| `type` | `table`、`pure`、`copy`、`skip` |
| `template` | `table` 对应 `field_map.templates` 的键 |
| `out` | 输出文件名；复制类不带扩展名时沿用源扩展名 |
| `source` + `pages` | `pure` 的源 PDF 和 1-based 页码 |
| `match` | `copy` 的文件名通配符，按数组顺序优先 |
| `exclude` | `copy` 的排除通配符 |

```json
{
  "order": [
    {"seq": 1, "name": "案件审批表", "type": "table", "template": "审批表", "out": "1.案件审批表.docx"},
    {"seq": 2, "name": "委托须知", "type": "pure", "source": "委托材料全套.pdf", "pages": [13, 14], "out": "2-1 委托须知.pdf"},
    {"seq": 3, "name": "委托代理合同", "type": "copy", "match": ["*聘请律师合同*", "*委托代理合同*"], "out": "3.委托代理合同"}
  ],
  "directory_template_out": "0.归档卷宗目录.doc"
}
```

## 4. field_map.json

V3 顶层带 `schema_version`：

```json
{
  "schema_version": 3,
  "templates": {
    "审批表": {
      "file": "审批表.docx",
      "kind": "docx_form_v3",
      "strict": true,
      "fields": []
    }
  }
}
```

每个字段包含：

- `name`：字段名。
- `source`：`auto`、`agent`、`client`。
- `from` + `key`：自动字段的文件来源和取值语义。
- 定位方式之一：`marker`、`control_tag`、`selector`、`anchor`、`loc`。
- 可选：`mode`、`prefix`、`format`、`verify`。

表格定位、写入模式和 V2 迁移详见 [table-mapping-v3.md](table-mapping-v3.md)。

### 示例

```json
{
  "name": "案号",
  "marker": "{{案号}}",
  "source": "auto",
  "from": "判决书|裁决书",
  "key": "案号"
}
```

```json
{
  "name": "处理方式",
  "selector": {
    "type": "cell_anchor",
    "table": 0,
    "label": "处理方式",
    "direction": "right",
    "match": "exact"
  },
  "mode": "choice",
  "source": "agent"
}
```

## 5. template_mapping.md

人类可读的目录和模板映射说明。它应与 `archive_plan.json` 保持一致，但运行时以 JSON 为准。

## 取值语义 key

内置支持：`受托人`、`委托人`、`对方当事人`、`委托人地址`、`对方当事人地址`、`电话`、`案由`、`标的`、`代理费金额`、`案号`、`处理机关`、`收案时间`、`裁决日期`、`案情简介`、`案件进程`。

未列出的 key 可以扩展；`agent` 字段由 Agent 或人工提供，`client` 字段保持空白。

## 接入新律所

运行 `python scripts/onboard.py`。V3 会：

1. 优先识别 `{{字段}}`/`[[字段]]`；
2. 识别 Word 内容控件 Tag；
3. 去重合并单元格；
4. 为标签右侧空格生成相对定位；
5. 用 `review_required=true` 标出需要人工确认的猜测。

正式使用前必须审阅所有 `review_required=true` 字段。

