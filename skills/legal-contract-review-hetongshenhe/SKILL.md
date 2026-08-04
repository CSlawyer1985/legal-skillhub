---
name: legal-contract-review
description: "法务合同审核与风险批注。This skill should be used when the user uploads a contract document (.docx) and wants automated legal review with risk annotations added as Word comments. Triggers: 审核合同, 合同批注, 法务审查, 风险条款, 合同评审, 添加批注, legal review, contract annotation."
---

# Legal Contract Review

## Overview

This skill performs automated legal contract review on .docx files. It extracts contract text, uses an LLM to identify risk clauses and sensitive information, validates the annotations, and adds Word comments (批注) to the original document. The output is an annotated .docx file with risk comments anchored to the relevant contract clauses.

The workflow covers:
- Contract text extraction from .docx
- AI-powered risk clause identification (payment, liability, IP, confidentiality, dispute resolution, etc.)
- Automatic sensitive information detection (prices, bank accounts, tax IDs, phone numbers, emails, etc.)
- Fallback keyword-based annotation when LLM output is insufficient
- Word comment insertion with fuzzy text matching

## Prerequisites

### Python Dependencies

Install the required packages before first use:

```bash
# Use the managed Python environment
# Windows
C:\Users\admin\.workbuddy\binaries\python\envs\default\Scripts\pip install python-docx lxml

# Or if using the managed Python directly
C:\Users\admin\.workbuddy\binaries\python\versions\3.13.12\python.exe -m pip install python-docx lxml
```

### File Requirements

- Input file must be a standard .docx file (not .doc, not scanned/PDF-converted image)
- The contract text must be selectable/editable text (not images, text boxes, or protected content)
- If the file is a scan or image-based Word document, OCR the text first

## Workflow

### Step 1: Extract Contract Text

Extract text from the uploaded .docx file using `scripts/extract_docx_text.py`. This replaces Dify's document-extractor node and extracts text from paragraphs, tables, headers, and footers.

```bash
python scripts/extract_docx_text.py <input.docx> --output <extracted_text.txt>
```

Read the extracted text to understand the contract content.

### Step 2: Generate Risk Annotation JSON

Load the LLM system prompt from `references/llm_prompt.md`. Replace `{{DOC_TEXT}}` with the extracted contract text. Generate a JSON object where:

- **Keys** are exact text snippets from the contract (8-80 Chinese characters, must exist verbatim in the document)
- **Values** are risk comments in the format: `【风险等级】风险点：...；风险后果：...；修改建议：...`

The LLM should focus on: liability, compensation, termination, IP rights, payment, acceptance, dispute resolution, confidentiality, delivery, performance terms, and sensitive information.

### Step 3: Clean and Validate Annotations

Run `scripts/clean_annotations.py` to validate the LLM output. This script:

1. Checks document length (minimum 30 characters)
2. Parses the LLM JSON output and validates each key exists verbatim in the document
3. Runs automatic sensitive information detection using regex patterns (prices, bank accounts, tax IDs, phone numbers, emails, addresses, contract numbers, etc.)
4. Merges LLM-generated and auto-detected sensitive info comments
5. Generates fallback keyword-based comments if LLM output is insufficient
6. Limits total comments to 20

```bash
python scripts/clean_annotations.py \
  --llm-file <llm_output.txt> \
  --doc-file <extracted_text.txt> \
  --output <cleaned_result.json>
```

The output JSON contains:
- `comments_json`: validated JSON string of annotation key-value pairs
- `can_generate`: "true" if annotations are valid, "false" otherwise
- `debug`: processing information
- `doc_preview`: first 500 characters of document text

### Step 4: Add Comments to Word Document

If `can_generate` is "true", run `scripts/add_word_comments.py` to insert Word comments into the original .docx file. This script:

1. Opens the .docx as a zip archive
2. Parses `word/document.xml` with lxml
3. For each annotation key, searches for matching text in paragraphs (exact match first, then fuzzy match with configurable similarity threshold)
4. Splits runs at the match boundaries and inserts `commentRangeStart`, `commentRangeEnd`, and `commentReference` elements
5. Creates `word/comments.xml` with all comment content
6. Updates `[Content_Types].xml` and `word/_rels/document.xml.rels`
7. Saves the annotated .docx file

```bash
python scripts/add_word_comments.py \
  --input <original.docx> \
  --comments '<comments_json_string>' \
  --author "法务审核助手" \
  --output <annotated_output.docx> \
  --threshold 0.55
```

The `--comments` argument accepts the `comments_json` value from Step 3's output. The `--threshold` controls fuzzy matching sensitivity (0.55 is recommended; lower values allow looser matches).

### Step 5: Return Results

Present the annotated .docx file to the user. If `can_generate` was "false", instead return the debug information and suggest:
1. Confirm the file is a standard .docx (not a scan or image)
2. Confirm the contract text is selectable (not in text boxes, headers/footers, or protected areas)
3. Try re-saving the file in Microsoft Word as a new .docx
4. If the contract is image-based, OCR it first

## Annotation Categories

### Risk Clauses (LLM-Generated)
- **Payment terms**: 付款金额、节点、条件、发票要求、逾期责任
- **Acceptance**: 验收标准、流程、异议期限、逾期处理
- **Liability**: 违约情形、违约金计算、损失赔偿范围、责任限制
- **Termination**: 解除条件、通知期限、费用结算、已履行部分处理
- **Dispute resolution**: 管辖法院/仲裁机构明确性、唯一性、可执行性
- **Confidentiality**: 保密范围、期限、例外、返还/销毁、违约责任
- **IP rights**: 成果归属、使用范围、许可方式、侵权担保
- **Delivery**: 交付内容、时间、地点、方式、迟延责任
- **Notice**: 通知方式、送达地址、联系人变更、视为送达
- **Term**: 生效条件、有效期限、续展规则

### Sensitive Information (Auto-Detected)
- Prices/amounts (人民币、美元、元、万元)
- Unit prices (单价、含税单价)
- Bank account numbers
- Bank name/account info
- Tax IDs / unified social credit codes
- ID card numbers
- Phone numbers (mobile and landline)
- Email addresses
- Contact/registered addresses
- Contract/project numbers

## Configuration

### Comment Author
Default: "法务审核助手". Can be customized via the `--author` parameter in Step 4.

### Similarity Threshold
Default: 0.55. Controls fuzzy text matching sensitivity:
- 1.0 = exact match only
- 0.55 = allows minor differences (recommended for contract documents with OCR errors or formatting variations)
- 0.40 = very loose matching (may produce false positives)

### Max Comments
- Total: 20 (enforced in Step 3)
- Sensitive info: 15 (enforced in Step 3)

## Resources

### scripts/
- `extract_docx_text.py` - Extract text from .docx files (paragraphs, tables, headers, footers)
- `clean_annotations.py` - Validate and clean LLM-generated annotation JSON; auto-detect sensitive info
- `add_word_comments.py` - Insert Word comments into .docx using direct OOXML manipulation
- `requirements.txt` - Python dependencies (python-docx, lxml)

### references/
- `llm_prompt.md` - System prompt for generating risk annotation JSON from contract text
