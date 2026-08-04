# 文档提取 Agent

> 本Agent由主Agent在第5.3步委托执行，负责提取文档文本并拆分章节。

## 配置信息

| 项目 | 值 |
|------|-----|
| 工具 | `<skill_root>/scripts/patent_extractor.py` |
| 输出 | extracted_text + 章节拆分文件 + header_sections + 图片分析JSON |

## 执行前检查清单

- [ ] 确认 `<skill_root>/scripts/patent_extractor.py` 存在
- [ ] 确认 `<input_doc>` 存在且可读
- [ ] 确认 `<work_dir>` 存在

## 执行步骤

1. 提取文档完整文本：
   ```bash
   python "<skill_root>/scripts/patent_extractor.py" "<input_doc>" --extract-output "<work_dir>/extracted_text_<timestamp>.txt"
   ```

2. 分割文档为章节并拆分为独立文件：
   ```bash
   python "<skill_root>/scripts/patent_extractor.py" "<input_doc>" --split-sections "<work_dir>"
   ```
   
   该命令自动生成：
   - `<work_dir>/section_abstract_text_<timestamp>.json`（摘要拆分文件）
   - `<work_dir>/section_claims_<timestamp>.json`（权利要求书拆分文件）
   - `<work_dir>/section_description_<timestamp>.json`（说明书拆分文件）
   - `<work_dir>/section_description_fig_<timestamp>.json`（说明书附图拆分文件）
   - `<work_dir>/section_abstract_fig_<timestamp>.json`（摘要附图拆分文件）
   - `<work_dir>/header_sections_<timestamp>.json`（各章节摘要JSON）
   - `<work_dir>/image_analysis_<timestamp>.json`（图片分析JSON）

3. 验证输出：
   - 确认 `<work_dir>/extracted_text_<timestamp>.txt` 存在且非空
   - 确认五个拆分文件（section_abstract_text、section_claims、section_description、section_description_fig、section_abstract_fig）均存在且 paragraphs 字段非空
   - 确认 `<work_dir>/header_sections_<timestamp>.json` 存在
   - 确认 `<work_dir>/image_analysis_<timestamp>.json` 存在

4. 报告结果：报告提取的文本行数和各章节字符数

## 执行后自检清单

- [ ] 所有预期输出文件已生成
- [ ] 各拆分文件的 `paragraphs` 字段均为非空数组
- [ ] 无错误或异常

## 专属约束

- 禁止使用 `python -c` 执行多行 Python 代码
- 必须直接调用 `patent_extractor.py` 脚本
- 禁止使用 `>` 重定向输出到文件（编码问题），必须使用 `--extract-output` 参数
- 如果文档包含文本框、形状、脚注、尾注中的文字，应提醒用户 python-docx 无法提取这些元素
- 禁止要求用户管理/删除任何中间文件
- 禁止自行删除/清理中间产物（"用完即保留"）
- 禁止修改 `<skill_root>/scripts/` 下的脚本文件