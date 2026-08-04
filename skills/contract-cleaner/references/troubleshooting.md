# 故障排查与系统依赖

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| API调用失败 | 运行 `--config` 重新配置，或检查API Key是否有效 |
| PDF识别失败 | 安装tesseract: `brew install tesseract tesseract-lang` |
| 术语未替换 | 检查是否为政府/能源场景例外（条件术语上下文判断） |
| 清洗轮次达上限 | 增加 `--max-rounds` 或查看质量验证报告中的具体问题 |
| 长合同截断 | 系统会自动分块处理，无需手动干预 |
| 润色后术语回退 | 润色后自动重跑规则引擎修正，如仍有问题请检查日志 |

## 系统依赖

```bash
# macOS
brew install pandoc
brew install tesseract tesseract-lang  # PDF OCR 需要时安装

# Ubuntu
sudo apt install pandoc
sudo apt install tesseract-ocr tesseract-ocr-chi-sim  # PDF OCR 需要时安装

# Python 依赖
pip install requests lxml pypandoc python-docx
# PDF 支持（可选）
pip install pdf2image pytesseract Pillow
```
