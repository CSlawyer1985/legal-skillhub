---
name: Judgment Analyzer 判决书分析
slug: judgment-analyzer
version: 1.2.1
description: 分析判决书文档，提取关键信息并生成结构化分析报告。当用户提到「分析判决书」「解读判决书」「判决书总结」「生成判决书报告」「批量分析判决书」时使用。支持 PDF 和 Word (.docx/.doc) 格式，可处理单个文件或整个文件夹。
author: szzzcode
homepage: https://github.com/szzzcode/judgment-analyzer
---

# 判决书分析技能

分析本地判决书文档，提取案件关键信息，生成结构化的摘要报告和综合分析报告。

## 工作流程

### 步骤 1：接收输入

用户指定判决书路径，支持：
- **单文件**：`/path/to/judgment.pdf`
- **文件夹**：`/path/to/cases/`（批量处理所有 PDF/Word 文件）
- 支持格式：PDF、Word (.docx/.doc)

### 步骤 2：文本提取（Python）

运行 `scripts/analyzer.py` 提取原始文本：

```bash
python3 ~/.claude/skills/judgment-analyzer/scripts/analyzer.py <输入路径>
```

脚本会：
1. 读取每个判决书文件（PDF 或 Word）
2. 提取纯文本内容
3. 将文本保存到 `输入路径/摘要/` 文件夹，文件名为 `原文件名.txt`

### 步骤 3：生成摘要（AI）

1. 读取 `摘要/` 文件夹中的所有 txt 文件
2. 按照输出格式模板，对每个案件生成结构化摘要
3. 将摘要保存为 `案件名_摘要.md`
4. 批量处理时，额外生成 `综合分析报告.md`



### 输出格式要求

在提取信息和生成报告时，**必须严格遵守**模板文件中的格式和要求设置。
具体格式以及各项指引，请读取并遵循此文件：
`~/.claude/skills/judgment-analyzer/references/output-template.md`

- **单案件摘要**：遵照模板文件中【摘要报告模式】的 6 个核心模块提取并输出。
- **批量综合报告**：遵照模板文件中【综合分析报告模式】的结构和表格要求输出。

### 触发方式
- 「分析判决书 /path/to/case.pdf」
- 「批量分析 /Users/xxx/Desktop/cases/」
- 「生成判决书综合报告」
- 「对比分析这几份判决书」

## 注意事项

- 脚本路径：`~/.claude/skills/judgment-analyzer/scripts/analyzer.py`
- 首次使用需安装依赖：`pip install -r ~/.claude/skills/judgment-analyzer/scripts/requirements.txt`
- 批量处理时，自动跳过非判决书文件（.pdf, .docx, .doc）
- 摘要文件夹创建在输入文件夹同级目录
- 优先提取文本，如文本质量差可标记"扫描件，需OCR"
