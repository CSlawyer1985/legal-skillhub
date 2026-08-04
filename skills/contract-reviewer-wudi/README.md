# 合同审核 WUDI | Contract Reviewer WUDI

> 中文合同审核 Skill，专为 OpenClaw / Claude AI 设计的智能合同审查工具。
> 以 **修订痕迹（Track Changes）** 为核心输出，直接写入 Word 文档，所见即所得。

<p align="center">
  <img src="images/04_track_changes.png" width="600" alt="修订痕迹效果">
</p>

## ✨ 核心特性

| 能力 | 说明 |
|------|------|
| 📝 **修订痕迹** | 审核意见直接写入 Word Track Changes，红绿对比一目了然 |
| 💬 **批注气泡** | 法律背景说明、结构性提示以 Word Comment 形式呈现 |
| 📋 **清洁版生成** | 一键生成接受全部修改后的清洁版文档 |
| 🔄 **多轮迭代** | 支持版本跟踪、差异对比、回滚管理 |
| 🔍 **交叉引用检查** | 自动检测孤立引用、缺失条款、自引用问题 |
| 🏷️ **合同类型检测** | 自动识别 41 种合同类型（关键词匹配 + 置信度排序） |
| 📚 **条款智能推荐** | 内置 22 个专业条款模板，审核时自动匹配替代条款 |
| 📄 **PDF/扫描件 OCR** | 自动识别 PDF 类型，支持 Vision/Tesseract 转换 |

## 📊 覆盖范围

- **41 种合同类型**：买卖、租赁、建设工程、技术服务、劳动合同、股权转让、PPP、金融衍生品等
- **350+ 关键条款**审核规则
- **229+ 常见风险**识别点
- **82 个法律依据**（《民法典》合同编为主）

## 🖼️ 效果展示

### 1. 合同输入
上传 Word 或 PDF 格式的合同文件即可开始审核。

<p align="center"><img src="images/01_input.png" width="500"></p>

### 2. 合同类型识别
自动检测合同类型，匹配对应审核规则库。

<p align="center"><img src="images/02_type_detection.png" width="500"></p>

### 3. 风险扫描
逐条扫描合同条款，识别法律风险并分级标注。

<p align="center"><img src="images/03_risk_scan.png" width="500"></p>

### 4. 修订痕迹（核心输出）★
审核修改直接写入 Word 修订痕迹，红色删除、绿色新增，对比清晰。

<p align="center"><img src="images/04_track_changes.png" width="600"></p>

### 5. 批注气泡
无法用修订表达的内容（法律背景、结构性提示）以批注形式呈现。

<p align="center"><img src="images/05_comments.png" width="500"></p>

### 6. 清洁版输出
一键生成接受全部修改后的干净文档。

<p align="center"><img src="images/06_clean_version.png" width="500"></p>

## 📁 目录结构

```
contract-reviewer-wudi/
├── SKILL.md                          # Skill 主文件（AI 审核规则引擎）
├── LICENSE.md                        # GPL-3.0 许可证
├── scripts/
│   ├── contract_parser.py            # 合同结构解析引擎
│   ├── apply_changes.py              # 修订痕迹与批注写入引擎
│   ├── generate_clean.py             # 清洁版生成引擎
│   ├── iteration_manager.py          # 多轮迭代管理引擎
│   ├── clause_recommender.py         # 条款智能推荐引擎
│   ├── check_cross_refs.py           # 交叉引用检查
│   ├── full_pipeline.py              # 完整审核流水线
│   ├── pdf_ocr.py / vision_ocr.py    # PDF OCR 模块
│   ├── preflight_check.py            # 预检工具
│   ├── round_analyzer.py             # 轮次分析
│   ├── generate_comparison.py        # 对比视图生成
│   └── config.py                     # 共享配置
├── references/
│   ├── clause-library/               # 22 个专业条款模板 (JSON)
│   ├── contract-types/               # 41 种合同类型定义 (JSON)
│   ├── review-playbook.md            # 审核操作手册
│   ├── engine-guide.md               # 引擎使用指南
│   └── output-spec.md                # 输出规范
├── agents/
│   └── openai.yaml                   # Agent 配置示例
├── tests/
│   └── test_contract_reviewer.py     # 单元测试
└── images/                           # 效果截图
```

## 🚀 安装

### OpenClaw 用户

1. 将本仓库 clone 到 Skill 目录：

```bash
git clone https://github.com/wux818738-alt/contract-reviewer-wudi.git ~/.qclaw/skills/contract-reviewer-wudi
```

2. 重启 OpenClaw Gateway，Skill 会自动加载。

### 依赖

- Python 3.8+
- `python-docx`（修订痕迹 / 批注写入）
- `PyMuPDF` 或 `pdfplumber`（PDF 解析，可选）
- `Tesseract`（扫描件 OCR，可选）
- `LibreOffice`（清洁版生成，可选）

## 📜 许可证

[GPL-3.0](LICENSE.md) © 2026 WUDI

## 🙏 致谢

本 Skill 的审核方法论基于法律审核通用实践，属于行业公共知识。感谢所有法律从业者对本领域的贡献。
