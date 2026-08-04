# 输出选择指南

当用户询问最佳格式或明确请求 CSV、Excel、PDF 或 PowerPoint 就绪输出时，使用本指南。

## 最佳格式规则
- 对争议日志、问题日志以及上传到内部追踪器或电子计费系统，使用 `csv`。
- 对财务友好审查工作簿、可排序问题日志或用户将编辑的表格，使用 `xlsx`。
- 对叙述性报告、审计备忘录和执行摘要，使用 markdown `.md`。
- 当用户想要将渲染为 PDF `.pdf` 的固定叙述性文档时，使用 PDF 友好 HTML 或谨慎约束的 PDF 就绪 markdown。
- 当用户想要幻灯片但环境不支持原生 `.pptx` 生成时，使用 PowerPoint 就绪大纲内容。

## 按交付物的实务选择
- 详细问题日志：CSV 或 XLSX
- 详细审计报告：markdown 加 PDF 友好 HTML
- 执行摘要：markdown 加 PDF 友好 HTML
- QBR 或 MBR 包：markdown 加 PDF 和 PowerPoint 就绪大纲
- 跨所比较表格：XLSX
- 谈判要点：markdown 或 CSV，取决于他们想要叙述还是追踪器

## 脚本
- `scripts/export_issue_log.py`：CSV、markdown 或 XLSX 问题日志输出
- `scripts/build_exec_pack.py`：markdown 报告、PDF 友好 HTML 报告或 PowerPoint 就绪大纲

## 注意事项
- 除非环境支持该转换，否则不要承诺真正的 PDF 或 `.pptx` 文件。
- 如用户只需要可在 Excel 中使用的内容，CSV 即可。
- 对 PDF、Word 和 PowerPoint，必须应用 [visual-output-rules.md](visual-output-rules.md) 以避免文本重叠、未换行标签和不可用的宽表格。
