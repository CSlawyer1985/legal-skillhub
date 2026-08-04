# fanglawerguidangzhushou（律师案件归档助手）

## 概述

通用律师案件归档自动化工具，支持OCR识别 + 归档卷宗生成 + 办案小结生成 + PDF转换全流程。

**脱敏说明**：本技能已脱敏处理，不含任何个人案件信息、邮箱密码、微信密钥等敏感数据。

## 技能文件清单

| 文件 | 功能 | 说明 |
|------|------|------|
| `archive_case.py` | 主程序：案件归档全流程 | 支持OCR + PDF解析 + 生成归档 |
| `generate_juansong.py` | 生成归档卷宗（民事） | 3页模板格式 |
| `generate_xiaojie.py` | 生成办案小结 | 4段式结构 |
| `ocr_engine.py` | OCR识别模块 | RapidOCR-ONNX |
| `config.py` | 配置文件 | 路径/模板/参数 |
| `backup.py` | 备份脚本 | 自动备份到指定目录 |
| `SKILL.md` | 技能说明文档 | 本文件 |

## 依赖

```bash
# Python环境（3.10+）
# 安装依赖
pip install rapidocr-onnxruntime python-docx pdfplumber openpyxl
```

## 配置（config.py）

```python
# 模板文件路径
TEMPLATE_PATH = "模板目录/归档卷宗模板（民事）.docx"

# 输出目录（默认与案件目录相同）
# 可在 archive_case.py 中通过参数指定

# 线程限制（防止CPU爆表）
OMP_NUM_THREADS = 2
OPENBLAS_NUM_THREADS = 2

# 图片预处理
MAX_SIDE = 1500  # 最大边长
```

## 使用方法

### 方式1：完整流程（推荐）

```bash
python archive_case.py <案件文件夹路径>

# 示例
python archive_case.py "D:\cases\张三案件"
python archive_case.py "G:\案件\李四"
```

### 方式2：分步执行

```bash
# 1. OCR识别
python ocr_engine.py <案件文件夹> -o ocr_result.txt

# 2. 生成归档卷宗
python generate_juansong.py <案件文件夹> --case-info <JSON>

# 3. 生成办案小结
python generate_xiaojie.py <案件文件夹> --case-info <JSON>

# 4. Word转PDF
python docx_to_pdf.py <docx文件>
```

### 方式3：Python调用

```python
from archive_case import main

# 基本调用
main("案件文件夹路径")

# 传入案件信息（避免OCR）
case_info = {
    "contract_no": "（202X）XX民代字第X号",
    "case_no": "（202X）XX民初XXX号",
    "case_type": "民间借贷纠纷",
    "client": "张三",
    "client_role": "原告",
    "opponent": "李四",
    "opp_role": "被告",
    "lawyer": "您的姓名",
    "stage": "1审",
    "court": "XX市XX区人民法院",
    "sign_date": "202X年X月X日",
    "end_date": "202X年X月X日",
    "end_way": "调解",
    "fee": "10000元",
    "pages": "50",
}
main("案件文件夹", case_info)
```

## 输入要求

案件文件夹应包含以下之一：
1. **案件相关图片**（.jpg/.png/.bmp/.tiff）— 将进行OCR识别
2. **现有PDF文件**（如已有归档卷宗）— 将提取案件信息

## 输出文件

程序会在案件文件夹生成：

| 文件 | 说明 |
|------|------|
| `XXX归档卷宗（民事）.docx` | 归档卷宗（3页模板格式） |
| `XXX归档卷宗（民事）.pdf` | PDF版 |
| `XXX办案小结.docx` | 办案小结（4段式结构） |
| `XXX办案小结.pdf` | PDF版 |
| `OCR识别结果.txt` | OCR识别文本（如果运行了OCR） |

## 案件信息识别策略

1. **优先从现有PDF提取** — 查找文件名含"归档卷宗"的PDF
2. **次选OCR识别** — 对图片进行RapidOCR识别
3. **手动传入** — 通过case_info参数直接提供

### 支持提取的字段

- 合同编号、案号、案由
- 委托方（原告/被告）
- 对方当事人
- 受理法院、承办律师、代理阶段
- 接案日期、结案日期、结案方式
- 律师费、页数

## 备份功能

```bash
# 运行备份
python backup.py
```

备份内容包括：
- SKILL.md
- archive_case.py
- generate_juansong.py
- generate_xiaojie.py
- ocr_engine.py
- config.py
- ocr_tool.py（通用OCR工具）

## 性能参数（参考）

| 项目 | 数值 |
|------|------|
| RapidOCR初始化 | ~1秒 |
| 单张图片识别 | ~10秒（3024×4032） |
| CPU占用 | 可控（线程限制） |
| 内存占用 | ~200MB |

## 常见问题

**Q: OCR识别很慢怎么办？**
A: 检查线程限制配置，确保设置了 `OMP_NUM_THREADS=2`

**Q: 识别结果不准确？**
A: 尝试调整图片预处理参数（MAX_SIDE、CLAHE参数）

**Q: 如何修改模板？**
A: 修改 config.py 中的 TEMPLATE_PATH，指向您的归档卷宗模板

---

*版本：v1.0*
*创建：2026-04-06*
*脱敏：已移除所有个人案件信息、邮箱密码、微信密钥*