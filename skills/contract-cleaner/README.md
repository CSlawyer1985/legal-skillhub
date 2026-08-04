# Contract Cleaner

> 中文合同文本清洗与格式化工具
> 
> A  Chinese legal document cleaning and formatting tool.

---

## 简介 / Introduction

Contract Cleaner 是一款面向中文法律文本的轻量级预处理工具。它能将混乱的 Word/PDF/Markdown 合同文本转换为**干净、规范、符合法律语言体系**的标准化 Markdown。

Contract Cleaner is a lightweight preprocessing tool for Chinese legal documents. It transforms messy Word/PDF/Markdown contracts into **clean, standardized Markdown** that conforms to legal language conventions.

## 核心特性 / Features

- **多格式输入支持** — Word (.docx/.doc)、PDF（OCR）、Markdown、纯文本
- **确定性规则引擎** — 术语替换、金额格式化、编号规范化等由 Python 代码 100% 保证，零 API 调用
- **AI 语义清洗** — 分块处理 + 上下文注入，自动优化义务句式、结构层级、格式一致性
- **双轨质量验证** — 代码自检（100% 可靠）+ AI 验证（语义补充），未通过则带精确反馈自动收敛
- **最终润色** — 修正语法/句法/低级错误，润色后自动重跑规则引擎防止退化
- **Word 交付物导出** — 可选生成清洁版 docx 和带修订痕迹的对比版 docx

## 清洗流水线 / Pipeline

```
原始合同 (Word/PDF/MD)
        ↓
[Step 1] 文档转换 → Markdown
[Step 2] 格式清洗 → 去除多余标记、空行、页码残留
        ↓
[Step 3] 清洗
    ├─ Stage 0: 规则引擎（确定性规则，0 API）
    ├─ Stage 1: 合同分块（按条款边界，≤3000 字符/块）
    ├─ Stage 2: 分块 AI 清洗（3 pass + 上下文前缀注入）
    ├─ Stage 3: 拼接 + 双轨质量验证
    ├─ Stage 4: 收敛检测（最多 3 轮自动迭代）
    └─ Stage 5: 最终润色 + 规则引擎防退化
        ↓
[Step 4] 输出清洗版 Markdown + 可选 Word 交付物
```

## 快速开始 / Quick Start

### 环境要求 / Requirements

- Python 3.10+
- pandoc（文档转换必需）
- 可选：Tesseract（PDF OCR）、pandiff（修订痕迹版 docx）

```bash
# macOS
brew install pandoc
brew install tesseract tesseract-lang  # PDF OCR 可选

# Python 依赖
pip install requests lxml pypandoc python-docx
# PDF 支持（可选）
pip install pdf2image pytesseract Pillow
```

### 自动模式下首次配置 / First configuration in automatic mode

```bash
python scripts/auto_cleaner.py --config
```

按提示选择 API 提供商并输入 API Key。配置安全保存在 `~/.config/contract-cleaner-pro/api_config.json`。

### 使用示例 / Usage

```bash
# 基本用法
python scripts/auto_cleaner.py -i 合同.docx

# 指定输出目录
python scripts/auto_cleaner.py -i 合同.docx -o ./output/

# 限制清洗轮次（默认 3 轮）
python scripts/auto_cleaner.py -i 合同.docx --max-rounds 2

# 详细日志
python scripts/auto_cleaner.py -i 合同.docx -v
```

## 输出文件 / Outputs

| 文件 | 说明 |
|------|------|
| `合同_清洗版.md` | 核心交付物：规范化 Markdown |
| `合同-原合同（预处理后）.md` | 格式清洗后的原始文本（对比基准）|
| `合同-新合同（预处理后）.md` | 最终结果的预处理版本 |
| `合同-清洁版.docx` | 清洗后的美观 Word 版 |
| `合同-对比版.docx` | 带修订痕迹的对比版（需 pandiff）|

## 确定性规则示例 / Deterministic Rules

以下规则由代码强制执行，无需调用 AI：

| 规则 | 示例 |
|------|------|
| 术语替换 | 缴纳 → 支付、罚款 → 违约金、权力 → 权利 |
| 金额格式 | ¥5,000 → 人民币5000.00元（人民币伍仟元整）|
| 编号规范 | 第1条 → **第一条** |
| 日期格式 | 2026-2-23 → 2026年2月23日 |
| 嵌套应当修复 | 应当确保应当符合 → 应当确保符合 |
| 首部/签署区保护 | 防止甲乙方、附件被错误编入条款编号 |
| 全角半角修正 | １．１ → 1.1（仅限数字/英文/编号场景）|

## 项目结构 / Project Structure

```
contract-cleaner/
├── README.md                      # 本文件
├── SKILL.md                       # Skills CLI 入口文档
├── LICENSE.txt                    # Apache 2.0 许可证
├── scripts/
│   ├── auto_cleaner.py            # 主入口
│   ├── rule_engine.py             # 确定性规则引擎
│   ├── industrial_cleaner.py      # AI 清洗引擎
│   ├── format_cleaner.py          # Markdown 格式清洗
│   ├── document_converter.py      # 文档格式转换
│   ├── self_verifier.py           # 自检验证器
│   └── docx_exporter.py           # Word 交付物导出
├── references/
│   ├── global_text_processing.md  # 完整清洗规范
│   └── troubleshooting.md         # 故障排查与系统依赖
└── tests/                         # 自动化测试
```

## 测试 / Tests

```bash
python -m unittest discover tests/
```

## 开源协议 / License

Apache License 2.0
