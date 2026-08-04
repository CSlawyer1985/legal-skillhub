---
name: tabular-review-lawvable
description: "按用户定义的列分析多个文档（PDF、DOCX）并产出带引用的结构化 Excel 输出的指南。当用户想要：(1) 从多个文档中提取特定信息到表格中，(2) 跨合同比较条款或规定，(3) 创建带来源引用的文档审查矩阵时使用。触发词：'tabular review'、'document matrix'、'extract from documents'、'compare across documents'、'review multiple contracts'。"
metadata:
  author: "Dr. Antoine Louis"
  license: "agpl-3.0"
  version: "2026-04-10"
---

# 表格化审查

从多个文档中提取结构化数据到带引用的 Excel 矩阵中。

## 所需技能

- **pdf**——用于读取 PDF 文档
- **docx**——用于读取 Word 文档
- **xlsx**——用于创建 Excel 输出

## 工作流

### 第 1 步：收集用户需求

使用 `AskUserQuestion` 收集：

1. **文档文件夹路径**——文档在哪里？
2. **输出文件名**——Excel 文件的名称
3. **要提取的列**——要从每个文档中提取什么信息

列定义示例：
```
- 当事人：协议所有当事人的名称
- 生效日期：协议何时生效
- 期限：协议的存续期间
- 准据法：争议的管辖法域
```

### 第 2 步：发现文档

使用 `Glob` 查找所有文档：

```
Glob(pattern: "**/*.pdf", path: "<folder>")
Glob(pattern: "**/*.docx", path: "<folder>")
```

### 第 3 步：并行处理文档

启动后台代理并发处理文档。每个代理：
- 使用 pdf 或 docx 技能读取分配的文档
- 为每个列提取值
- 记录页码/段落引用
- 返回结构化 JSON

**启动代理：**
```
Task(
  prompt: "<agent_prompt>",
  subagent_type: "general-purpose",
  run_in_background: true
)
```

**代理提示模板：**
```
您正在为表格化审查处理文档。

要处理的文档：
<文档路径列表>

要提取的列：
<列定义>

对每个文档：
1. 使用 pdf 技能（.pdf）或 docx 技能（.docx）读取文档
2. 为每个列提取所请求的信息
3. 记录找到信息的页码（PDF）或部分（DOCX）
4. 附上一段简短的引文（30-50 字符）展示来源文本

以 JSON 返回您的结果：
{
  "results": [
    {
      "document": "<文件名>",
      "path": "<绝对路径>",
      "extractions": [
        {
          "column": "<列名>",
          "value": "<提取值>",
          "page": <页码>,
          "quote": "<简短的上下文引文>"
        }
      ]
    }
  ]
}

如您无法为某列找到信息，将值设为 "Not found" 并在引文字段中说明。
```

**分发策略：**
- 对 N 个文档和 M 个代理，每个代理处理 ceil(N/M) 个文档
- 默认：最多 10 个代理
- 根据文档数量调整

### 第 4 步：收集结果

等待所有后台代理完成：

```
TaskOutput(task_id: "<agent_id>", block: true)
```

将所有结果聚合为文档提取的单一数组。

### 第 5 步：生成 Excel 输出

调用 **xlsx skill** 创建输出文件：

```
在 <输出路径> 创建 Excel 工作簿：

工作表 1："Document Review"（文档审查）
- 表头行：Document（文档） | <列1> | <列2> | ...
- 数据行：每个文档一行

对每个提取单元格：
- 单元格值：提取的文本
- 单元格超链接：file://<文档路径>#page=<N>（用于 PDF）
- 单元格批注："Page <N>: '<引文>'"

工作表 2："Summary"（摘要）
- 文档总数：<数量>
- 已处理文档：<数量>
- 提取日期：<今天>
```

## JSON Schema

**提取结果格式：**
```json
{
  "document": "Contract_ABC.pdf",
  "path": "/path/to/Contract_ABC.pdf",
  "extractions": [
    {
      "column": "Parties",
      "value": "Acme Corp and Beta Inc",
      "page": 1,
      "quote": "entered into between Acme Corp and Beta Inc"
    },
    {
      "column": "Effective Date",
      "value": "January 15, 2025",
      "page": 1,
      "quote": "effective as of January 15, 2025"
    }
  ]
}
```

## Excel 输出格式

**带引用的单元格：**
- 值："Acme Corp and Beta Inc"
- 超链接：`file:///path/to/Contract_ABC.pdf#page=1`
- 批注：`Page 1: "entered into between Acme Corp and Beta Inc"`

**颜色编码（可选）：**
- 绿色：已找到值且确信度高
- 黄色：已找到值但不确定
- 红色：未找到值

## 错误处理

| 情形 | 操作 |
|----------|--------|
| 文档不可读 | 记录错误，将该行标记为失败，继续 |
| 未找到列 | 将值设为 "Not found"，在批注中说明 |
| 代理超时 | 收集部分结果，注明不完整 |
| 缺少技能 | 提示用户安装所需技能 |

## 使用示例

```
用户：我想对我的合同做一次表格化审查

Claude：[使用 AskUserQuestion]
  - 哪个文件夹包含您的文档？
  - 输出 Excel 文件应命名为？
  - 您想提取哪些列？

用户：~/Contracts、review.xlsx、Parties/Date/Term/Governing Law

Claude：[通过 Glob 发现 15 个文档]
Claude：[启动 5 个后台代理，每个 3 个文档]
Claude：[通过 TaskOutput 收集结果]
Claude：[通过 xlsx skill 创建 review.xlsx]

输出：review.xlsx，15 行、4 列、带超链接和引用
```
