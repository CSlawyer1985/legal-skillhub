# 快速上手

## 安装

运行测试前请用 `python3 --version` 确认环境为 Python 3.11 或更高版本（推荐 3.12）；macOS 系统自带的 Python 3.9 不受支持。

核心知识组件和办案逻辑可离线使用。生成 `.docx` 文书需要本机安装 Pandoc:

```bash
# 文书生成需要 pandoc
pandoc --version || brew install pandoc   # macOS
# apt install pandoc                      # Linux
```

材料读取、扫描件 OCR、法律法规及案例核验等环节，可按具体任务调用运行环境已有或用户自行配置的外部能力。LaborPilot 不绑定具体的 OCR、法律数据库、MCP 或其他服务。

> **适用范围**:全国规则层适用于各地劳动争议案件;地方口径层包含浙江资料及已废止文件的历史观点，采用前须逐项核验效力、时间与地域适用。浙江以外地区还须核查当地裁判规则。

## 主用法:输入案件 → 生成文书

准备案件数据 JSON(`my_case.json`):

```json
{
  "case": {
    "申请人": "张某",
    "被申请人": "某公司",
    "事实与理由": "..."
  },
  "claims": [
    {"事项": "违法解除劳动合同的赔偿金", "金额": 64000, "计算式": "8000元×4个月×2"}
  ],
  "evidence": [
    {"名称": "银行工资流水", "来源": "申请人", "证明目的": "劳动关系+工资标准"}
  ]
}
```

生成:

```bash
python3 scripts/generate_docs.py \
  --case my_case.json \
  --output ./output \
  --types 仲裁申请书,证据清单 \
  --delivery-status lawyer_review_draft \
  --strict
```

`--types` 必须明确列出本次需要的文书，系统不会顺带生成未请求文件。上述示例将两份 `.docx` 写入 `./output/01_律师复核初稿/`，内部 Markdown 和版式报告写入 `./output/.casework/drafting/`；已有同版本文件不会被覆盖。

输入也支持 PDF 案卷材料、图片、自然语言案件描述。PDF、图片等材料的读取与扫描件 OCR 由运行环境提供；LaborPilot 在取得可读文本后完成要素提取和办案分析。

## 办案中的争点识别

LaborPilot 在处理具体案件时，内部调用编译知识组件匹配相关法律争点，匹配范围按案件需要动态确定。系统将构成要件、举证责任、法律依据、浙江口径、计算规则和风险提示融入案件分析。知识卡不作为独立卡片或完整原始数据对外输出。
