# 地区模板包替换指南

## 为什么使用模板包

二进制 Word、Excel 母版属于输出资产，应放在 `assets/template-packs/`；操作说明属于规则，应放在 `references/`。二者分开后，办案逻辑可以复用，地区格式可以独立替换。

默认 `wenzhou` 包只适配温州地区列明的法律援助中心。其他地区使用时，不应只替换抬头或机构名称；会见笔录、阅卷笔录、庭审笔录、归档目录和当地签章要求均可能不同。

## 新建本地模板包

1. 复制 `assets/template-packs/wenzhou/` 到 Skill 目录之外，例如 `/path/to/hangzhou-template-pack/`。
2. 用当地法律援助中心提供或认可的 `.docx` / `.xlsx` 母版逐一替换文件。
3. 编辑 `manifest.json`：设置唯一 `id`、地区、版本、支持的指派机构和每个标准模板键对应的文件名。
4. 在 `manifest.json` 的 `typography` 中设置正文与标题字体、字号和固定行距。温州默认值为正文 `仿宋_GB2312` 14 磅、主标题 `黑体` 16 磅、固定行距 28.5 磅；其他地区应按当地要求替换。
5. 在 Word 母版中使用下列变量，变量可以位于正文、表格、页眉或页脚，但不要拆成多个文本框：

   - `{{aid_center}}`、`{{handling_agency}}`、`{{prosecuting_agency}}`、`{{court}}`
   - `{{law_firm}}`、`{{lawyer}}`、`{{lawyer_phone}}`
   - `{{recipient_label}}`、`{{recipient_name}}`、`{{recipient_id_no}}`
   - `{{charge}}`、`{{charge_legal_basis}}`
   - `{{meeting_place}}`、`{{meeting_date}}`、`{{meeting_start}}`、`{{meeting_end}}`
   - `{{meeting_summary}}`：已核实的实际会见情况；`{{defense_opinions}}`：已核实的主要辩护意见。
   - `{{evidence_statement_content}}`、`{{pretrial_meeting_statement_content}}`：律师核实的情况说明正文；缺失留空，填写提示仅进内部复核清单。
   - `{{assignment_date}}`、`{{closing_date}}`、`{{case_result}}`、`{{summary}}`、`{{sign_date_line}}`

6. 模板中的问答内容只保留通用问题，所有 `答：` 栏必须为空。删除真实姓名、身份号码、联系方式、案号、日期、事实、答复、私章、签名、律师证号、批注、修订记录和作者元数据。
7. 在 manifest.renderers 中为已替换的 Word 模板选择 `placeholders`，例如 `"renderers": {"meeting_trial": "placeholders"}`。此模式只替换变量，不运行温州原句替换、表格定位或段落清理，不要求保留温州原句。没有配置的键使用 `wenzhou-legacy`，仅用于仍与原温州脚本配套的母版，不适合任意当地新模板。
   - 每份变量 Word 模板须含 `{{recipient_name}}`，会见类另须含 `{{charge}}`、`{{charge_legal_basis}}`。
   - 承办通报须含 `{{case_progress_entries}}`，按输入条目逐行填入日期、方式、内容、备注；无条目留空。此模式不按温州表格行定位，需自行设计可扩展的正文或单元格，生成后复核分页。
   - 结案报告须含 `{{case_result}}`、`{{summary}}`；其他需要的字段按第 5 步放置，不支持的变量会报错。
   - Excel 归档目录只复制当地母版，不做变量填充；不要为 `archive_directory` 配置 placeholders。
   - 母版只保留空白问答及经核实的通用内容，不把已会见、已开庭、已结案等事实写死。变量模式不会替律师重写当地格式或判断程序是否发生。
8. 运行：

```bash
python3 scripts/validate_template_pack.py /path/to/hangzhou-template-pack
python3 scripts/audit_distribution_package.py /path/to/hangzhou-template-pack
```

9. 用完全虚构的测试数据分别生成侦查、审查起诉、审判阶段文书并逐页渲染检查。母版改版（包括用 Word 重存）后必须重新执行第 8 步。

## `manifest.json` 最小结构

```json
{
  "id": "local-region",
  "display_name": "某地区刑事法律援助模板包",
  "jurisdiction": "某省某市",
  "version": "1.0.0",
  "typography": {
    "body_font": "当地正文中文字体名称",
    "body_size_pt": 14,
    "title_font": "当地标题中文字体名称",
    "title_size_pt": 16,
    "line_spacing_pt": 28.5
  },
  "assigning_institutions": ["某市法律援助中心"],
  "source_notice": "模板来源和适用范围说明",
  "renderers": {"authorization_investigation": "placeholders"},
  "templates": {
    "authorization_investigation": "authorization_investigation.docx"
  }
}
```

实际清单必须包含验证脚本要求的全部 18 个标准模板键。若当地不使用某项材料，也应提供一份明确写明“当地不适用、须由承办律师核实”的中性母版，不要指向其他地区文件冒充替代。
