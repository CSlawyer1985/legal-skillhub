# 无流程台账时的材料时间线提取

## 能做什么

当律师没有 Markdown 流程台账时，`scripts/extract_case_timeline.py` 可递归只读扫描本地材料，从 Markdown、TXT、JSON、CSV、DOCX、PDF和常见图片中提取日期线索，并结合上下文初步分类为指派、委托、会见、阅卷、阶段起点、认罪认罚、开庭、裁判或结案等事项。

它生成的是“候选时间线”，不是案件事实认定。输出会保留材料名称、页码/段落/表格位置、提取方式、置信度与“待律师核实”状态。

## 本地提取顺序

1. 可复制文字的文件和PDF先直接读取文字层。
2. 没有可用文字层的PDF，在本机用 `pdftoppm` 渲染，再用 Tesseract OCR。
3. 图片直接在本机用 Tesseract OCR。
4. 文件名中的日期只作为低置信度线索，不能替代正文。

脚本不上传材料、不访问网络、不修改原始文件，也不把案件数据写入 Skill 包。

## 日期与程序含义必须分开

- 起诉意见书标识审查起诉阶段的起点。
- 起诉书或提起公诉信息标识审判阶段的起点。
- “司法机关作出/送达”“律师实际收到”“法援中心行政结案”可能是三个不同日期。
- 同一日期在不同材料中可能代表制作、签发、送达、签收或律师记录时间，必须回看原文和原页。

## 置信度不是事实等级

- 较高：可直接读取的文字层中，日期附近有明确事项关键词。
- 中：可读取文字层中有日期，但事项分类不够明确。
- 低：来自OCR或文件名。

即使标为“较高”，仍然必须由承办律师核对原件。OCR错字、版面错序、页眉页脚日期、附件形成日期都可能造成误判。

## 常用命令

```bash
python3 scripts/extract_case_timeline.py /path/to/materials \
  --output-dir /path/to/workpaper/timeline \
  --ocr auto \
  --max-ocr-pages 200
```

如只想读取文字层而不做OCR：

```bash
python3 scripts/extract_case_timeline.py /path/to/materials \
  --output-dir /path/to/workpaper/timeline \
  --ocr never
```

输出目录必须位于案件材料目录之外，避免后续扫描重复读取自身产物。

## 加密或无法打开的PDF

脚本不会保存卷宗密码。请在案件工作区另存一份本地解密工作副本后再扫描，并继续保留原始加密文件。不得把密码写入 Skill、公共仓库、示例JSON或输出模板。

