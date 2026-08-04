# 合同智能比对 - Contract Smart Compare

**Skill ID:** contract-compare  
**版本:** 1.0.0

---

## 功能概述

合同智能比对是一款基于 AI 的合同文档差异分析工具。自动识别并标注两份或多份合同之间的条款差异，生成结构化差异报告。

### 核心能力

1. **智能条款提取**
   - 自动识别合同中的编号条款（第一条、第二条、Article X 等）
   - 支持 PDF、Word（DOCX）、纯文本（TXT）格式
   - 图片扫描件支持 OCR 识别（STANDARD+）

2. **差异精准比对**
   - 逐条对比：第X条 → 原内容 → 新内容
   - 三类差异分类：新增条款 / 删除条款 / 修改条款
   - 多版本时间轴排列（PRO）

3. **风险智能评估**（PRO）
   - AI 自动判断差异条款的法律风险等级（高/中/低）
   - 重点关注：责任条款、违约条款、费用条款变更

4. **关键条款摘要**（PRO）
   - AI 自动提取合同核心条款
   - 快速理解每版合同的关键变化

5. **多格式输出**
   - Markdown 差异报告（所有套餐）
   - Excel 差异清单（STANDARD+）
   - 风险摘要报告（PRO）

---

## 定价

| 套餐 | 月费 | 功能 |
|------|------|------|
| FREE | 免费 | 每月5次，2份合同比对（TXT/DOCX），Markdown报告 |
| STANDARD | ¥29/月 | 不限次数，支持PDF/图片OCR，差异分类，Excel导出 |
| PRO | ¥99/月 | STANDARD全部 + 多版本比对（3份+），风险评估，关键条款摘要 |

---

## 使用方式

### 命令行比对（两份合同）

```bash
# 基本比对
python -m src.main compare contract_a.pdf contract_b.pdf --label-a "合同V1" --label-b "合同V2"

# 输出到文件
python -m src.main compare contract_a.docx contract_b.docx -o diff_report.md

# STANDARD+：同时导出Excel
python -m src.main compare contract_a.pdf contract_b.pdf --excel -o report/

# PRO：显示未变更条款
python -m src.main compare contract_a.docx contract_b.docx --include-same -o full_report.md
```

### 多版本比对（PRO）

```bash
python -m src.main multi v1.pdf v2.pdf v3.pdf \
  --labels "初稿" "修改版" "终稿" \
  --dates "2024-01-01" "2024-03-15" "2024-06-01" \
  --output multi_version_report.md \
  --excel
```

### 解析合同文本

```bash
python -m src.main parse contract.pdf --max-chars 3000
```

---

## 环境变量

| 变量名 | 说明 | 必填 |
|--------|------|------|
| OPENAI_API_KEY | OpenAI API Key（GPT-4o 等） | 二选一 |
| ANTHROPIC_API_KEY | Anthropic API Key（Claude 3.5 等） | 二选一 |
| CONTRACT_COMPARE_TOKEN | 月付 Token（STANDARD/PRO） | STANDARD/PRO |
| CLAUDE_MODEL | 模型名称（默认：claude-sonnet-4-20250514） | 可选 |

---

## 支持文件格式

| 格式 | FREE | STANDARD | PRO |
|------|------|----------|-----|
| TXT | ✅ | ✅ | ✅ |
| DOCX | ✅ | ✅ | ✅ |
| PDF | ❌ | ✅ | ✅ |
| JPG/PNG（OCR） | ❌ | ✅ | ✅ |

---

## 技术栈

- **PDF 解析：** PyMuPDF + pdfplumber
- **Word 解析：** python-docx
- **文本编码：** chardet（自动检测 UTF-8/GBK 等）
- **图片 OCR：** pytesseract + Pillow
- **AI 比对：** OpenAI GPT-4o / Anthropic Claude（用户自带 Key）
- **Excel 导出：** openpyxl

---

## 安全说明

- 所有上传文件存储在 `/tmp/contract-compare/`（临时目录）
- API Key 完全由用户自行配置，Skill 不存储、不传输
- 文件路径经过严格消毒处理（仅允许字母、数字、下划线、连字符、点）
- 所有网络请求均设置 10 秒超时

---

## 订阅验证

STANDARD/PRO 用户需配置 `CONTRACT_COMPARE_TOKEN`（前缀：`CONTRACT-COMPARE-`），通过 yk-global API 验证月付订阅状态。

Token 示例：`CONTRACT-COMPARE-xxxxxxxxxxxx`

---

## 安装依赖

```bash
pip install -r requirements.txt

# OCR 支持（可选，未安装则跳过图片解析）
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim
# macOS:
brew install tesseract
```

---

*如需购买收费版，请访问 [YK-Global.com](https://yk-global.com)*
