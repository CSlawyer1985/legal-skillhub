---
name: labor-material-ingestion
description: 劳动争议原始材料接入与本地处理。当案件以 PDF、图片、扫描件或混合文件提供，需要保全原件、检测文字层、决定是否 OCR、生成分页索引或登记派生文件时使用。
license: AGPL-3.0
metadata:
  homepage: https://jinlishan.com/
  author: 金莉珊律师（微信jinlishan_）
  version: 1.4.4
---

# 劳动争议材料接入

1. 确认当前工作图节点为 `material_ingestion`，对用户明确指定的材料运行：

   ```bash
   python3 scripts/ingest_materials.py \
     --state <case-root>/.casework/case_state.json \
     --source <原始材料路径> \
     --original-or-copy <original|copy|unknown>
   ```

   多份材料重复传入 `--source`。脚本保持原件只读，计算 SHA-256、大小、文件类型和可取得的页数；在 `.casework/materials/` 生成逐材料接入记录、派生文本及 JSON／Markdown 索引，并就地回写 `materials[]`。
2. 先检测文字层的完整性，不因 PDF “能复制几个字”就认定无需 OCR。
3. 执行器只使用本地文本解码、DOCX XML 和可用的本机 `pdfinfo`／`pdftotext`；图片、扫描 PDF 或文本层不足的 PDF 只登记 `ocr_status=pending`。案件、客户或执业材料默认仅本地处理；未获明确授权不调用云端 OCR。
4. OCR、分页图和接触表由运行环境在对应材料目录继续生成；完成后更新 `derivative_path`、OCR 引擎、语言和可视复核状态，不在 OCR 文本中静默修改原文。
5. 在 `materials[]` 登记 `material_id`、`source_path`、`source_sha256`、`page_start/end`、`derivative_path`、`ocr_engine`、`ocr_language`、`ocr_status`、`visual_review_status` 和 `original_or_copy`。
6. 将 OCR 不确定、手写表格、截断聊天、旋转或模糊页列为人工复核任务。
7. 将分页图、OCR、接触表和材料接入索引统一输出到 `<case-root>/.casework/materials/`，不在案件根目录建立用户交付文件；完成后才进入 `intake`。

进入下游前运行 `python3 scripts/workflow_graph.py transition --state <case-root>/.casework/case_state.json --event pass --actor <执行者>`。工作图会重新读取源文件并核对当前 SHA-256、大小、逐材料接入记录和派生文件；只写一个哈希字符串或事后改动原件不能通过门禁。

不识别实体争点，不将 OCR 文本当作经证实事实。
