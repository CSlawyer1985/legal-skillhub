---
name: element-based
description: Element-based（要素式起诉状）用于将案件材料填写为 67 类要素式诉状 Word 草案；当用户要求起草、填写或整理要素式起诉状时使用。
---

# Element-based｜要素式起诉状

将案情填入内置范本，生成供律师审核的 `.docx` 草案。运行依赖：Python 3.8+、`python-docx`。

## 工作流

1. 据案情选择 `assets/template_index.json` 中的案由；不能判断时先询问用户。
2. 按 `references/intake-extraction.md` 汇总材料，标注已知、冲突、缺失；冲突和关键缺失项必须确认。
3. 读取该案由的 `text_keys`、`checkbox_groups`、`required` 和 `required_party_roles`，仅使用其中的真实键；`required_party_roles` 须按 `party_types` 对应的自然人姓名或法人名称核验。复杂字段判断见 `references/key-distinctions.md`。
4. 填充并交付前自检：必填项、主体类型、诉请与事实一致性、法条/管辖/授权等人工复核项。

```bash
python "<SKILL_DIR>/scripts/fill_complaint.py" \
  --template "<SKILL_DIR>/assets/templates/<file>" \
  --values "<values.json>" --out "<结果.docx>"
```

## 必须遵守的填写与版式规则

- 拆分主体模板须提供 `party_types`，如 `{"原告":"自然人","被告":"法人","第三人":"无"}`：仅保留对应主体行；第三人为“无”时删除其全部信息行。不拆分模板使用裸键。
- 一般同一逻辑行内的换行改为空格；经常居住地、证件号码必须另起一行。
- 自然人的住所地与经常居住地、法人/非法人组织的住所地（主要办事机构所在地）与注册地/登记地：两项都有且不同则分别保留；仅有一项则同步填写。
- 表格全部段落的左缩进、右缩进、首行缩进均为 0；不得缩小字号；表格大标题居中；删除相邻表格间的空段落。
- 调解意愿、具状人、日期均为必填。具状人（签字、签章）与日期必须分两行、右对齐。
- `claims.*`、`facts.*`、完整表述及请求依据须相互一致；无关项填“无”或留空。

## 免责

仅供参考，交付前应人工核对内容与版式。
