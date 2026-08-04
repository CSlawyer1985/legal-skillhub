---
name: contract-diff
version: 1.0.0
description: Compare contract templates with scanned stamped contracts, list all differences (additions, deletions, modifications). Output as Word document for easy download. Use when user wants to verify what changes were made between a template and the final signed contract.
---

# contract-diff

Compare contract templates (Word/PDF) with scanned stamped contracts (PDF/images), list ALL differences, and generate a highlighted visualization showing where changes are.

## When to Use

- User uploads a contract template AND a scanned signed contract
- User wants to know EVERY difference between template and signed version
- User needs detailed report showing additions, deletions, and modifications
- User needs visual highlighting of modified areas in the scanned contract

## Workflow

### Step 1: Extract Text from Both Files

**For contract template (.docx):**
Use `python-docx` to extract all text.

**For contract template (.pdf):**
Use `PyMuPDF` (fitz) to extract text.

**For scanned contract (PDF or image):**
Use OCR with pytesseract to extract text with bounding boxes.

### Step 2: Detailed Comparison

Split text into sentences/paragraphs and categorize:

1. **Only in template** - Content that was deleted
2. **Only in scanned** - Content that was added  
3. **Similar but different** - Modified content (with similarity ratio)

Using difflib.SequenceMatcher with threshold:
- > 85% similarity: treated as same
- 50-85% similarity: marked as modified
- < 50% similarity: marked as added/deleted

### Step 3: Generate Highlighted Image

For modified content:
- Find text position in OCR results
- Draw colored highlight box:
  - 🟡 Yellow = Modified content

### Step 4: Generate Detailed Report

Output format:

```markdown
# 合同比对详细报告

## 📋 文件信息
- **模板文件**: [filename]
- **盖章合同**: [filename]

## 📊 比对结果总览
- **风险等级**: 🟢低/🟡中/🔴高
- 🔴 删除内容: X 处
- 🟢 新增内容: X 处
- 🟡 修改内容: X 处

## 🔴 删除内容（模板 → 盖章合同）
1. [content...]
2. [content...]

## 🟢 新增内容（模板 → 盖章合同）
1. [content...]
2. [content...]

## 🟡 修改内容对比
| 模板内容 | 扫描件内容 | 相似度 |
|----------|------------|--------|
| ... | ... | 0.xx |

---
*⚠️ 注：比对结果基于 OCR 文字识别，可能存在误差。*
```

## Usage

```bash
# 安装依赖
pip install python-docx PyMuPDF pillow pytesseract

# 运行比对（输出 Word 文档）
python scripts/compare.py contract_template.docx signed_contract.pdf

# 指定输出文件
python scripts/compare.py template.pdf scan.pdf -o report.docx
```

## Dependencies

Required Python packages:
- `python-docx` - for .docx files
- `PyMuPDF` (fitz) - for PDF text extraction
- `Pillow` - image processing
- `pytesseract` - OCR
- Tesseract-OCR binary (system-level installation required)

## Important Notes

1. **OCR 准确性**: 扫描件 OCR 可能存在误差，特别是手写或模糊文字
2. **高亮精度**: 高亮依赖于 OCR 识别的坐标，可能有轻微偏移
3. **详细比对**: 新版算法会列出所有差异，包括新增、删除、修改
4. **脱敏处理**: 敏感信息用 *** 代替

## Output Files

| 文件 | 说明 |
|------|------|
| `report.docx` | Word 文档格式的详细比对报告（含所有差异，可直接下载） |
| `highlighted.png` | 带高亮标注的图片（可选） |

## Windows Setup

1. Install Python 3.12+
2. Install Tesseract OCR: `winget install tesseract-ocr.tesseract`
3. Install Python packages:
   ```bash
   pip install python-docx PyMuPDF pillow pytesseract
   ```

## Example

```bash
# Compare two contract files, output as Word document
python compare.py "合同模板.docx" "盖章合同.pdf" -o "详细比对报告.docx"
```

Output includes:
- All content only in template (deletions)
- All content only in scanned (additions)  
- All similar but modified content with similarity scores