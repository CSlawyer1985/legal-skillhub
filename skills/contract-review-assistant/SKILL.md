# 合同审查辅助系统 v2.1

## 功能概述

智能合同审查助手 v2.1，在v2.0基础上集成**法律知识库**，支持条款提取、风险识别、差异比对、意见生成，多格式输出（Word/PDF/HTML/Markdown），支持邮件发送和历史记录管理。

## 核心能力

### 1. 条款提取
- 自动识别合同中的核心条款（当事人信息、标的物、价款、履行期限、违约责任等）
- 提取关键条款内容并结构化展示
- 支持多种合同类型（买卖合同、租赁合同、服务合同等）

### 2. 风险识别
- 检测异常条款和高风险表述
- 识别可能的不利条款（如过重违约责任、模糊条款等）
- 标注风险等级（高、中、低）
- 支持LLM增强分析（可选）

### 3. 差异比对
- 对比合同不同版本的差异
- 高亮显示修改内容
- 生成差异报告

### 4. 意见生成
- 基于风险识别结果生成审查意见
- 提供修改建议和谈判要点
- 生成专业的审查意见书
- 支持AI专业意见生成（可选）

### 5. 法律知识库 ⭐ 新增
- 内置6部核心法律知识库（宪法、民法典、劳动合同法、劳动法、刑法、合同法）
- 自动识别合同条款涉及的法律问题
- 提供相关法律条文作为审查依据
- 支持关键词检索法律条文

## 多格式支持

### 输入格式
- **文本**：直接输入合同文本
- **TXT**：文本文件
- **DOCX**：Word文档
- **PDF**：PDF文档
- **图片**：JPG/PNG/BMP（需OCR支持）

### 输出格式
- **Word（.docx）**：专业的格式化文档
- **PDF（.pdf）**：便携式文档
- **HTML（.html）**：网页格式，可在线预览
- **Markdown（.md）**：轻量级标记格式

## 邮件发送

- 支持SMTP协议发送邮件
- 支持附件上传（Word/PDF文档）
- 提供邮件模板配置
- 支持批量发送

## 使用方法

### 命令行使用
```bash
# 审查文件
python main_v2.py -f contract.txt

# 指定输出格式
python main_v2.py -f contract.txt -fmt html

# 使用LLM增强
python main_v2.py -f contract.txt --llm --api-key YOUR_API_KEY

# 发送邮件
python main_v2.py -f contract.txt --email legal@company.com
```

### Python API使用
```python
from main_v2 import ContractReviewSystem

# 创建系统实例
system = ContractReviewSystem()

# 审查合同
result = system.review_file('合同.docx')
# 或
result = system.review_text('合同文本内容...')

# 导出报告
system.export_report('报告.docx', 'docx')
system.export_report('报告.html', 'html')
system.export_report('报告.md', 'md')

# 发送邮件
system.setup_email('smtp.qq.com', 587, 'your@qq.com', 'password')
system.send_report_email('recipient@example.com', attachment_path='报告.docx')
```

## 技术实现

- **Python 3.8+**
- **python-docx**：Word文档生成
- **pdfplumber/PyPDF2**：PDF解析
- **pytesseract**：图片OCR识别
- **reportlab**：PDF生成（可选）
- **SQLite**：审查历史记录管理
- **SMTP**：邮件发送

## 依赖安装

```bash
pip install python-docx pdfplumber PyPDF2 pytesseract Pillow reportlab
```

## 文件结构

```
合同审查助手/
├── SKILL.md              # 本文档
├── skill.json            # Skill配置
├── main.py               # 基础版本入口
├── main_v2.py            # 完整版入口（v2.1）
├── requirements.txt      # 依赖列表
├── knowledge_base_compressed/  # 压缩版法律知识库（用于上传）
│   ├── law_index.json     # 知识库索引
│   ├── 中华人民共和国宪法.txt
│   ├── 中华人民共和国民法典.txt
│   ├── 中华人民共和国劳动合同法.txt
│   ├── 中华人民共和国劳动法.txt
│   ├── 中华人民共和国刑法.txt
│   └── 中华人民共和国合同法.txt
└── scripts/
    ├── __init__.py        # 模块初始化
    ├── contract_review.py # 基础审查模块
    ├── enhanced_review.py # 增强审查模块（LLM）
    ├── word_generator.py  # Word生成
    ├── output_generator.py # 多格式输出
    ├── email_sender.py    # 邮件发送
    ├── file_parser.py     # 文件解析
    ├── law_search.py      # 法律知识库检索（本地+在线）
    └── official_law_search.py # 全国人大法规库实时查询
```

## 法律知识库说明

### 本地知识库
- 位置：`knowledge_base_compressed/`
- 格式：纯文本（.txt），便于上传和分享
- 包含6部核心法律：宪法、民法典、劳动合同法、劳动法、刑法、合同法

### 在线实时查询
- 数据源：全国人大法律法规库（https://flk.npc.gov.cn）
- 自动识别重要条款时实时查询最新法规
- 支持关键词：违约金、保密、知识产权、不可抗力、争议解决等

## 适用场景

- 法务人员合同审查
- 企业合同管理
- 律师事务所合同分析
- 商务谈判准备
- 合同版本对比
- 批量合同审查

## 版本历史

### v2.1 (2026-05-08)
- ✨ **新增法律知识库**：内置6部核心法律（宪法、民法典、劳动合同法、劳动法、刑法、合同法）
- ✨ **自动法律检索**：识别合同条款涉及的法律问题
- ✨ **法律依据输出**：在审查报告中自动附加相关法律条文

### v2.0 (2026-05-08)
- ✨ 集成LLM增强审查能力
- ✨ 支持多格式输入（PDF、图片OCR）
- ✨ 支持多格式输出（Word/PDF/HTML/Markdown）
- ✨ 添加审查历史数据库
- ✨ 命令行参数优化

### v1.0 (2026-05-08)
- 基础条款提取
- 风险识别
- Word文档生成
- 邮件发送
