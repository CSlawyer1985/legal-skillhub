# 专利公开/公告文件处理流程

> 本文件定义专利公开/公告文件（A/B/U类）的完整处理步骤。当文件类型识别程序判定输入文件为专利公开/公告文件时加载本文件。

---

## 适用范围

- 发明专利公开（A类）
- 发明专利公告（B类）
- 实用新型公告（U类）

输入格式：`.pdf` / `.docx` / `.doc`

---

## 处理步骤

### 步骤 1：文本提取

根据输入文件格式选择对应的提取器：

| 输入格式 | 提取器 | 说明 |
|---------|--------|------|
| `.pdf` | `PDFReader` | 支持 pdfplumber → fitz → MinerU → Tesseract 逐级降级 |
| `.docx` | `DocxReader` | 直接解析 OOXML，支持绝对定位框架坐标排序 |
| `.doc` | `DocxReader` | 自动检测办公软件转换为 `.docx` 后解析 |

**DOCX/DOC 限制**：不支持附图提取（无 PDF 页面渲染），其余流程与 PDF 一致。

**命令**：

```bash
cd "<skill_root>/scripts" && python -m patent_extractor.main \
  --input "<input_file>" \
  --output "<work_dir>" \
  [--ocr-engine auto|mineru|tesseract] \
  [--verbose] [--dpi 200]
```

### 步骤 2：章节识别与拆分

使用 `SectionParser` 将文本按专利文档结构拆分为各章节。

**双重策略**：

1. **策略一（优先）：首页页数信息解析**
   - 从首页提取 `权利要求书X页 说明书Y页 附图Z页`
   - 精确计算各章节页码范围：
     - 著录项目 + 摘要：第 1 页
     - 权利要求书：第 2 ~ 第 (X+1) 页
     - 说明书：第 (X+2) ~ 第 (X+Y+1) 页
     - 说明书附图：第 (X+Y+2) ~ 第 (X+Y+Z+1) 页

2. **策略二（降级）：页眉检测**
   - 若首页无页数信息，通过每页页眉关键词（`权利要求书`、`说明书`、`说明书附图`）检测章节边界

### 步骤 3：保存原始提取文本

将提取的原始文本保存为 `<work_dir>/<base_name>.txt`，保留页码分隔标记，便于人工核对和调试。

`<base_name>` 格式为 `{申请号}-{公开号/公告号}-{文本类型}`，由脚本根据解析出的著录项目自动生成。

### 步骤 4：图号引用提取

从"附图说明"子章节中提取所有图号引用（如"图1"、"图2"），用于后续附图命名。

### 步骤 5：说明书附图提取（仅 PDF）

使用 `ImageExtractor` 从 PDF 中提取附图图片，按 `figPage1.png`、`figPage2.png` 命名保存至 `<work_dir>/images/`。

**附图页数验证**：比对实际提取的图片张数与著录项目记载的附图页数，不一致时抛出错误。

**图片提取边界**：
- 摘要附图（第 1 页摘要文本旁的图片）：**不纳入**说明书附图
- 说明书附图：仅提取页眉"说明书附图"标记章节内的图片

### 步骤 6：JSON 生成

将结构化专利信息输出为 `<work_dir>/<base_name>.json`。

### 步骤 7：Markdown 生成

将结构化专利信息输出为 `<work_dir>/<base_name>.md`，含图片引用。

---

## 输出文件

| 文件 | 说明 |
|------|------|
| `<work_dir>/<base_name>.txt` | 原始提取文本（含页码分隔标记） |
| `<work_dir>/<base_name>.json` | 结构化 JSON |
| `<work_dir>/<base_name>.md` | 结构化 Markdown（含图片引用） |
| `<work_dir>/images/` | 说明书附图 PNG（仅 PDF 输入，按 figPageN.png 命名） |
| `<work_dir>/logs/` | 运行日志 |

> `<base_name>` = `{申请号}-{公开号/公告号}-{文本类型}`，由脚本自动生成并通过 `BASE_NAME:` 标准输出返回。
> Agent 需在脚本执行后将临时工作目录重命名为 `<input_dir>/<base_name>`。

---

## 代码模块

| 模块 | 职责 |
|------|------|
| `main.py` | 主入口，自动检测文档类型并编排对应流程 |
| `pdf_reader.py` | PDF 文本提取（pdfplumber → fitz → MinerU → Tesseract） |
| `docx_reader.py` | DOCX/DOC 文本提取（OOXML 解析） |
| `section_parser.py` | 章节识别、著录项目提取、专利类型识别、首页页数信息解析 |
| `image_extractor.py` | 说明书附图提取（fitz 渲染 PNG） |
| `json_generator.py` | 结构化 JSON 生成 |
| `markdown_generator.py` | Markdown 生成 |
