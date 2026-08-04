# 要素式文书一键生成器

上传普通诉讼文书（txt/md/docx/pdf/图片），自动识别案由、匹配模板、提取要素、填充内容，输出规范的要素式文书 docx。

## 功能特点

- **58个案由自动识别**：关键词规则匹配，离线可用，无需LLM
- **5种输入格式**：txt / md / docx / pdf / 图片（OCR）
- **双格式输入支持**：自动检测要素式/传统叙述式文书
- **104份模板覆盖**：11大领域分类，本地+GitHub远程下载
- **区域定位填充**：基于段落区域索引的精确XML填充，避免跨区域误填
- **精确勾选框处理**：`before_checkbox + □` 精确匹配，不误勾

## 使用方法

```bash
python scripts/main.py 输入文件.docx
```

或指定案由：
```bash
python scripts/main.py 输入文件.txt --case-type 民间借贷纠纷
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 覆盖领域

刑事自诉 | 婚姻家事 | 合同纠纷 | 劳动争议 | 交通事故 | 保险纠纷 | 知识产权 | 行政纠纷 | 国家赔偿 | 公益诉讼 | 海商海事

## License

MIT
