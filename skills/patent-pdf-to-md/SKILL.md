---
name: patent-pdf-to-md
description: >
  Convert Chinese patent PDFs/DOCX/DOCs to structured Markdown. Supports patent publications (A/B/U) and office action documents (审查意见通知书/驳回决定/复审决定书/无效宣告请求审查决定书). Uses MinerU for high-quality OCR text extraction (falls back to Tesseract), Python scripts for structural parsing and image extraction. Invoke when user needs to process Chinese patent PDFs, convert patent documents to Markdown, or extract patent bibliographic data.
  中国专利PDF/DOCX/DOC转Markdown、专利文档提取、著录项目提取、权利要求书提取、说明书附图提取。支持发明公开(A)、发明公告(B)、实用新型公告(U)三种专利公开类型，以及审查意见通知书、驳回决定、复审决定书、无效宣告请求审查决定书四种审查文件类型。MinerU高质量OCR+Python结构化解析。
allowed-tools: Bash(mineru-open-api:*), Bash(python:*)
---

# 中国专利 PDF / DOCX 转 Markdown

将中国专利 PDF 或 DOCX/DOC 文件转为结构化 Markdown 文件。支持两类文档：

1. **专利公开/公告文件**：包含著录项目、摘要、权利要求书、说明书（含子章节）和说明书附图
2. **审查文件**：审查意见通知书、驳回决定、复审决定书、无效宣告请求审查决定书，包含著录项目、审查意见/决定理由等

程序会自动检测文档类型并选择对应的解析流程，无需手动指定。

---

## 一、支持的输入格式

| 格式 | 说明 |
|------|------|
| `.pdf` | 专利 PDF 文件（文本型/图像型均可） |
| `.docx` | Word DOCX 文件（直接解析 OOXML） |
| `.doc` | 旧版 Word 文件（自动检测 WPS Office / Microsoft Office / LibreOffice 转换为 .docx） |

> **注意**：DOCX/DOC 格式不支持附图提取（无 PDF 页面渲染），其余流程与 PDF 一致。

### .doc 文件转换策略

处理 `.doc` 文件时，程序自动检测系统中已安装的办公软件并执行格式转换，检测优先级：

| 优先级 | 软件 | 平台 | 转换方式 |
|--------|------|------|----------|
| 1 | WPS Office | Windows / macOS / Linux | 命令行 `--headless --convert-to docx` |
| 2 | Microsoft Office | Windows / macOS | Windows: PowerShell COM 自动化；macOS: AppleScript |
| 3 | LibreOffice | Windows / macOS / Linux | 命令行 `--headless --convert-to docx` |

若未检测到任何办公软件，程序会提示安装或建议手动将 `.doc` 另存为 `.docx`。

---

## 二、路径变量

| 变量 | 说明 | 示例 |
|:---|:---|:---|
| `<skill_root>` | Skill 根目录 | `/path/to/.trae/skills/patent-pdf-to-md` |
| `<input_file>` | 输入文件绝对路径 | `/path/to/专利文件.pdf` |
| `<input_dir>` | 输入文件所在目录 | `/path/to` |
| `<input_stem>` | 输入文件名（不含扩展名） | `专利文件` |
| `<timestamp>` | 第3.2步获取的真实时间戳 | `20260604_143025` |
| `<work_dir>` | 临时工作目录 | `<input_dir>/patent-pdf-to-md_<timestamp>` |
| `<base_name>` | 脚本输出的命名基础字符串 | `202210373749.5-CN114909579A-公开文本` |
| `<final_dir>` | 最终输出目录 | `<input_dir>/<base_name>` |

> 所有路径必须使用绝对路径，使用 `/` 作为路径分隔符以确保跨平台兼容性。

---

## 三、Agent 工作流程

### 3.1 文件类型识别

检查输入文件扩展名是否为 `.pdf`、`.docx` 或 `.doc`（不区分大小写）。如果不是，告知用户仅支持这三种格式后**终止**。

### 3.2 创建工作目录

执行命令获取真实本地时间戳：

```bash
python -c "from datetime import datetime; print(datetime.now().astimezone().strftime('%Y%m%d_%H%M%S'))"
```

将输出记录为 `<timestamp>`，定义 `<work_dir>` = `<input_dir>/patent-pdf-to-md_<timestamp>`，创建工作目录：`mkdir "<work_dir>"`。

### 3.3 执行文件类型检测与处理

运行提取命令，程序会自动检测文档类型并选择对应的解析流程：

```bash
cd "<skill_root>/scripts" && python -m patent_extractor.main \
  --input "<input_file>" \
  --output "<work_dir>" \
  [--ocr-engine auto|mineru|tesseract] \
  [--verbose] [--dpi 200]
```

程序内部自动执行以下检测与分流：

1. **文本提取**：根据输入格式选择 `PDFReader` 或 `DocxReader`
2. **文档类型检测**：从提取文本的前 3000 字符自动判断
   - 检测为审查文件 → 加载 [office-action-workflow.md](reference/office-action-workflow.md) 对应流程
   - 检测为专利公开/公告文件 → 加载 [patent-publication-workflow.md](reference/patent-publication-workflow.md) 对应流程

### 3.4 多文件并行处理

当用户需要同时处理多个文件时，自动调用 SubAgent 模块实现并行处理：

- 每个文件分配一个独立的 SubAgent
- 所有 SubAgent 在同一条消息中并行启动
- 每个 SubAgent 使用独立的工作目录：`<work_dir>/<input_stem>/`
- 某个 SubAgent 失败不影响其他 SubAgent 的执行

**SubAgent 提示词模板**：

```
你是一个专业的中国专利文档转换助手。请执行以下转换任务：
1. 读取处理流程：读取 "<skill_root>/reference/patent-publication-workflow.md" 或 "<skill_root>/reference/office-action-workflow.md" 的完整内容
2. 按照处理流程的指令执行文档转换
3. 路径变量：skill_root=<skill_root>, input_file=<input_file>, work_dir=<work_dir>
4. ⛔⛔⛔ 禁止向用户提问、禁止要求用户提供任何信息、禁止因任何原因暂停处理流程
```

### 3.5 故障处理

系统运行过程中若发生故障，立即加载 [fault-handling.md](reference/fault-handling.md)，执行相应的错误恢复流程。

**常见故障快速参考**：

| 故障 | 处理方式 |
|------|----------|
| 文本提取完全失败 | 检查文件完整性，尝试切换 OCR 引擎 |
| MinerU 不可用 | 参考 [ocr-engine.md](reference/ocr-engine.md) 安装或降级到 Tesseract |
| 章节识别错误 | 使用 `--ocr-engine mineru` 提升 OCR 质量 |
| 附图页数不一致 | 检查 PDF 完整性和附图范围 |
| .doc 转换失败 | 安装办公软件或手动转为 .docx |
| SubAgent 执行超时 | 对超时文件单独重试 |

---

## 四、OCR 引擎选择

默认 `--ocr-engine auto`：pdfplumber → fitz → MinerU flash-extract → Tesseract 逐级降级。

```bash
# 强制使用 MinerU（推荐，质量最高）
cd "<skill_root>/scripts" && python -m patent_extractor.main -i "<input_file>" -o "<work_dir>" --ocr-engine mineru

# 强制使用 Tesseract（离线场景）
cd "<skill_root>/scripts" && python -m patent_extractor.main -i "<input_file>" -o "<work_dir>" --ocr-engine tesseract

# 自动降级（默认）
cd "<skill_root>/scripts" && python -m patent_extractor.main -i "<input_file>" -o "<work_dir>" --ocr-engine auto
```

### 其他参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--verbose` / `-v` | 关闭 | 输出详细日志 |
| `--dpi` | 200 | 附图渲染 DPI |
| `--keep-ocr-cache` | 关闭 | 保留 OCR 临时缓存 |

---

## 五、输出文件

| 文件 | 说明 |
|------|------|
| `<work_dir>/output.json` | 结构化 JSON（著录项目、摘要、权利要求书、说明书、附图列表） |
| `<work_dir>/output.md` | 结构化 Markdown（含图片引用） |
| `<work_dir>/output.txt` | 原始提取文本（含页码分隔标记） |
| `<work_dir>/images/` | 说明书附图 PNG 图片（仅 PDF 输入的专利公开/公告文件），按 figPage1.png, figPage2.png 命名 |
| `<work_dir>/logs/` | 运行日志 |

---

## 六、最终输出

> `<model_name>` 替换为当前会话所使用的大模型名称。

**单文件处理**：

```
专利文档转换完成

输入文件：xxx.pdf
文档类型：实用新型公告（专利公开/公告文件）
输出目录：<final_dir>

【输出文件】
- JSON：<final_dir>/<base_name>.json
- Markdown：<final_dir>/<base_name>.md
- 原始文本：<final_dir>/<base_name>.txt
- 附图：<final_dir>/images/（N 张）
- 日志：<final_dir>/logs/

【提取摘要】
- 专利名称：一种一体式自拍装置
- 申请号：201420522729.0
- 著录项目字段数：N 个
- 权利要求书：N 条
- 说明书子章节：N 个
- 附图验证：记载N页 / 实际N张 → 通过
```

**多文件并行处理**：

```
专利文档批量转换完成（并行处理模式）

处理文件数：N 个
成功：X 个 / 失败：Y 个
使用模型：<model_name>

【处理结果】
- 文件1：实用新型公告 → 成功（附图 N 张）
- 文件2：审查意见通知书 → 成功
- 文件3：失败（原因：...）

失败文件可单独重试。
```

---

## 七、参考文件

| 文件 | 用途 | 加载时机 |
|------|------|----------|
| [reference/patent-publication-workflow.md](reference/patent-publication-workflow.md) | 专利公开/公告文件（A/B/U类）完整处理步骤 | 文档类型识别为专利公开/公告文件时 |
| [reference/office-action-workflow.md](reference/office-action-workflow.md) | 审查文件完整处理步骤 | 文档类型识别为审查文件时 |
| [reference/fault-handling.md](reference/fault-handling.md) | 详细故障处理对策 | 系统运行过程中发生故障时 |
| [reference/patent-type-differences.md](reference/patent-type-differences.md) | 专利类型差异、INID代码、审查文件对比 | 需要了解类型差异或排查著录项目提取问题时 |
| [reference/output-format.md](reference/output-format.md) | JSON Schema 及 Markdown 格式定义 | 需要了解输出格式细节或排查生成问题时 |
| [reference/ocr-engine.md](reference/ocr-engine.md) | MinerU OCR 引擎安装、模式对比、故障排除 | MinerU 不可用或需要排查 OCR 问题时 |
| [reference/workspace-spec.md](reference/workspace-spec.md) | 工作文件夹命名规范、文件组织架构 | 需要了解工作目录结构或多文件并行处理时 |

---

## 八、技术架构

```
patent-pdf-to-md/
├── SKILL.md                                        # 主控制文件（本文档）
├── scripts/
│   └── patent_extractor/
│       ├── main.py                                 # 主入口，自动检测文档类型并编排对应流程
│       ├── pdf_reader.py                           # PDF 文本提取（pdfplumber → fitz → MinerU → Tesseract）
│       ├── docx_reader.py                          # DOCX/DOC 文本提取（OOXML 解析）
│       ├── ocr_engine.py                           # Tesseract OCR 引擎（降级方案）
│       ├── section_parser.py                       # 专利公开/公告文件：章节识别、著录项目提取
│       ├── office_action_parser.py                 # 审查文件：文档类型检测、著录项目提取、正文解析
│       ├── image_extractor.py                      # 说明书附图提取（fitz 渲染 PNG）
│       ├── json_generator.py                       # 结构化 JSON 生成
│       └── markdown_generator.py                   # Markdown 生成
└── reference/
    ├── patent-publication-workflow.md              # 专利公开/公告文件处理流程
    ├── office-action-workflow.md                   # 审查文件处理流程
    ├── fault-handling.md                           # 故障处理对策
    ├── patent-type-differences.md                  # 专利类型差异参考
    ├── output-format.md                            # 输出格式规范
    ├── ocr-engine.md                               # MinerU OCR 引擎详情
    └── workspace-spec.md                           # 工作文件夹规范
```
