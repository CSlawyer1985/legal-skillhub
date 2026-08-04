# 定制 DPIA 报告——填充指南

如何用评估数据填充 `dpia-custom-template-v1.docx`。使用 docx 技能的 OOXML 编辑工作流：解包 → 使用 Document library 的 Python 脚本 → 重新打包。

## 设置

```bash
# 1. 首先阅读 docx 技能的 OOXML 参考（ooxml.md）
# 2. 解包模板
python ooxml/scripts/unpack.py references/dpia-custom-template-v1.docx /tmp/dpia-custom
# 3. 所有编辑完成后，重新打包
python ooxml/scripts/pack.py /tmp/dpia-custom output-dpia.docx
```

## 模板结构

- **21 个表格**，带标题行（深藏青色 `1B3A5C` 背景）
- **占位文本 `____`** 标记待填字段（213 处）
- **`[方括号文本]`** 标记需要替换为内容的叙述占位符
- **风险表**使用颜色编码单元格底纹：低=`E8F5E9`、中=`FFF8E1`、高=`FFF3E0`、极高=`FFEBEE`
- **页眉：** `____ — DPIA-YYYY-NNN — CONFIDENTIAL`（替换为组织名称 + 编号）
- **页脚：** 页码自动生成

## 表格索引

表格通过其第一行标题单元格文本识别。

| # | 第一标题单元格 | 章节 | 操作 |
|---|-------------------|---------|-----------|
| T1 | "Field" | 封面页 | 填充单元格 |
| T2 | "Version" | 文档控制 | 添加行 |
| T3 | "Verdict" | 1.3 建议 | 填充单元格 |
| T4 | "Trigger" | 2.1 第 35(3) 条 | 填充单元格 |
| T5 | "#" | 2.2 九项标准 | 填充单元格 |
| T6 | "Jurisdiction" | 2.3 管辖范围 | 添加行 |
| T7 | "Field"（控制者） | 3.1 控制者信息 | 填充单元格 |
| T8 | "Purpose" | 3.3 法律依据 | 添加行 |
| T9 | "Category" | 3.4 数据类别 | 添加行 |
| T10 | "Group" | 3.5 数据主体 | 添加行 |
| T11 | "Entity" | 3.9 接收者 | 添加行 |
| T12 | "Data Category" | 3.11 保留期限 | 添加行 |
| T13 | "Risk ID" | 5.2 风险登记册 | 添加行 |
| T14 | "L \ S" | 5.3 固有风险热力图 | 填充单元格 |
| T15 | "Risk ID"（第 2 个） | 6.1 缓解措施 | 添加行 |
| T16 | "Risk Level" | 7.1 剩余风险摘要 | 填充单元格 |
| T17 | "L \ S"（第 2 个） | 7.2 剩余风险热力图 | 填充单元格 |
| T18 | "Verdict"（第 2 个） | 7.3 总体立场 | 填充单元格 |
| T19 | "Field"（DPO） | 9 数据保护官意见 | 填充单元格 |
| T20 | "Field"（审查） | 11 审查 | 填充单元格 |
| T21 | "Role" | 12 签署批准 | 填充单元格 |

## 操作类型

### 填充单元格
将现有单元格中的 `____` 占位文本替换为评估数据。表格结构保持不变。

### 添加行
克隆第一个数据行（标题后的行），然后用数据填充克隆行。之后删除模板占位行。

### 填充叙述
将 `[方括号占位符]` 段落替换为评估叙述文本。

### 热力图填充
在正确的 L×S 坐标处将风险 ID 文本添加到热力图单元格中。热力图是 6 列表格（行标签 + 5 个严重程度列）。行从 L=5 向下递减至 L=1。

## 逐表说明

### T1 — 封面页信息
| 行 | "值"列内容 |
|-----|----------------------|
| Processing Activity（处理活动） | 来自描述阶段的活动名称 |
| Controller（控制者） | 控制者名称 |
| Reference（编号） | DPIA-YYYY-NNN 格式编号 |
| Version（版本） | 文档版本 |
| Date（日期） | 评估日期 |
| Classification（密级） | 保留 CONFIDENTIAL 或调整 |
| Status（状态） | 批准时 DRAFT → FINAL |

### T2 — 文档控制
为每个版本条目克隆数据行。列：版本 | 日期 | 作者 | 变更 | 批准人。

### T3 — 建议裁决（第 1.3 节）
用以下之一填充"Verdict"单元格：`APPROVED`（批准）/ `CONDITIONALLY APPROVED`（有条件批准）/ `CONSULT SA`（咨询监督机关）/ `REJECTED`（拒绝）。应用底纹：
- APPROVED → `E8F5E9`（绿色）
- CONDITIONALLY APPROVED → `FFF8E1`（黄色）
- CONSULT SA → `FFF3E0`（橙色）
- REJECTED → `FFEBEE`（红色）

用摘要文本填充"Justification"（理由）单元格。

### T4 — 第 35(3) 条触发条件
三个固定行。对每个触发条件：
- "Applies?"（是否适用）列：`Yes` 或 `No`
- "Analysis"（分析）列：推理文本

### T5 — 九项标准
九个固定行。对每项标准：
- "Met?"（是否满足）列：`Yes` / `No` / `Partially`
- "Reasoning"（理由）列：分析文本

同时替换表下方 `Criteria met: ____ / 9` 段落。

### T6 — 管辖范围
每个相关司法管辖区添加一行。列：管辖地 | 为何相关 | 黑名单已检查 | 是否匹配？ | 条目引用。

### T7 — 控制者信息
三个固定行。填充"Details"（详情）列：控制者名称、DPO 联系方式、欧盟代表。

### T8 — 各目的的法律依据
每个处理目的添加一行。列：目的 | 第 6 条依据 | 理由。
如适用，同时替换 `Art. 9(2) exception` 段落。

### T9 — 数据类别
每个数据类别添加一行。列：类别 | 特殊（第 9 条）？ | 详情。

### T10 — 数据主体
每个数据主体群体添加一行。列：群体 | 弱势？ | 大致数量。

### T11 — 接收者
每个接收者/处理者添加一行。列：实体 | 角色 | 地点 | 转移机制。

### T12 — 保留期限
每个数据类别添加一行。列：数据类别 | 保留期限 | 理由。

### T13 — 固有风险登记册（第 5.2 节）
每个风险添加一行。列：
- Risk ID（风险 ID）：如 `DISC-01`、`SURV-02`
- Track（轨道）：`A` 或 `B`
- Description（描述）：风险描述
- Rights Category（权利类别）：受影响的权利
- L：可能性（1-5）
- S：严重程度（1-5）
- Score（分数）：L × S
- Modulating Factors（调节因素）：加重/缓解因素或"None"
- Adjusted Level（调整后级别）：`Low` / `Medium` / `High` / `Very High`

根据级别对"Adjusted Level"单元格应用底纹。

### T14 — 固有风险热力图（第 5.3 节）
5×5 网格已有 L×S 分数和颜色底纹。填充方法：在匹配坐标的单元格文本中追加风险 ID。

示例：风险 `DISC-01`，L=3，S=4 → 找到 L=3 行、S=4 列的单元格（显示"12"）→ 改为"12\nDISC-01"。

热力图布局（标题后的行索引）：
- 第 1 行：L=5（列：S=1→5，S=2→10，S=3→15，S=4→20，S=5→25）
- 第 2 行：L=4
- 第 3 行：L=3
- 第 4 行：L=2
- 第 5 行：L=1

### T15 — 缓解措施（第 6.1 节）
每个风险添加一行。列：
- Risk ID | Risk | Inherent (score) | Measures | Type (Tech/Org/Legal) | Status (Planned/Partial/Implemented) | Res. L | Res. S | Res. Score | Res. Level

对"Res. Level"单元格应用底纹。

### T16 — 剩余风险摘要（第 7.1 节）
四个固定行（极高、高、中、低——已预置底纹）。填充：
- "Count"（数量）列：每个级别的风险数量
- "Risk IDs"（风险 ID）列：逗号分隔列表

### T17 — 剩余风险热力图（第 7.2 节）
与 T14 相同，但使用剩余风险位置。网格结构相同。

### T18 — 总体立场裁决（第 7.3 节）
与 T3 相同。填充裁决 + 理由，应用裁决颜色底纹。

### T19 — 数据保护官意见（第 9 节）
五个固定行。填充"Details"（详情）列：DPO 姓名、建议、关切、控制者回应、分歧。

### T20 — 审查与监控（第 11 节）
三个固定行。填充"Details"（详情）列：下次审查日期、审查周期、审查负责人。

### T21 — 批准与签署（第 12 节）
五个固定行（DPIA 作者、DPO、处理负责人、IT 安全、高级管理层）。填充"Name"（姓名）和"Date"（日期）列。"Signature"（签名）列留空供手写/数字签名。

## 叙述占位符

这些 `[方括号文本]` 段落应替换为评估内容：

| 章节 | 占位文本 | 来源 |
|---------|-----------------|--------|
| 1.1 | [2-3 段通俗语言描述...] | 描述阶段 |
| 1.2 | [已识别的首要风险...] | 风险评估 |
| 1.4 | [DPO 建议摘要] | DPO 咨询 |
| 2.4 | [为何开展 DPIA...] | 阈值评估 |
| 3.2 | [处理目的] | 描述阶段 |
| 3.6 | [数据收集自何处] | 描述阶段 |
| 3.7 | [收集 → 存储 → 处理...] | 描述阶段 |
| 3.7 | [数据流图占位符...] | 图表（如有） |
| 3.8 | [系统、平台、算法...] | 描述阶段 |
| 3.10 | [转移机制...] | 描述阶段 |
| 3.12 | [如何落实第 12-22 条权利] | 描述阶段 |
| 4.1 | [每个数据要素是否必要？...] | 必要性评估 |
| 4.2 | [收益与侵扰分析...] | 相称性评估 |
| 4.3 | [LIA 平衡检验...] | 法律依据分析 |
| 4.4 | [数据最小化评估...] | 必要性评估 |
| 4.5 | [必要性与相称性裁决...] | 必要性/相称性关口 |
| 6.2 | [技术措施详细描述] | 缓解阶段 |
| 6.3 | [组织措施详细描述] | 缓解阶段 |
| 6.4 | [法律/合同措施详细描述] | 缓解阶段 |
| 7.4 | [详细理由...] | 剩余风险评估 |
| 8 | [决定：是否需要事先咨询？...] | 第 36 条检查 |
| 10 | [决定：是否已进行咨询？...] | 数据主体咨询 |
| 11 | [处理的重大变更...] | 审查设置 |
| A-D | [附件占位符] | 支持性文件 |

## 页眉/页脚替换

在 `word/header1.xml` 中替换：
- `____` → 组织名称
- `DPIA-YYYY-NNN` → 实际编号
- `CONFIDENTIAL` → 实际密级（如不同）

页脚自动生成（页码）。"Generated with DPIA Sentinel"（由 DPIA Sentinel 生成）文本保留。

## OOXML 代码模式

### 按标题文本查找表格
```python
from document import Document
doc = Document("word/document.xml")
tables = doc.get_nodes("//w:tbl")
for tbl in tables:
    first_cell_text = doc.get_text(doc.get_nodes(".//w:tc[1]", tbl)[0])
    if "Risk ID" in first_cell_text:
        # 找到风险登记册表格
        break
```

### 替换单元格中的占位文本
```python
for node in doc.get_nodes("//w:t"):
    if doc.get_text(node) == "____":
        doc.set_text(node, "replacement value")
        break
```

### 克隆数据行并填充
```python
table = ...  # 通过标题文本找到
rows = doc.get_nodes("w:tr", table)
template_row = rows[1]  # 第一个数据行（标题后）

import copy
new_row = copy.deepcopy(template_row)
cells = doc.get_nodes("w:tc", new_row)
for i, value in enumerate(["R-01", "A", "Description...", ...]):
    text_nodes = doc.get_nodes(".//w:t", cells[i])
    if text_nodes:
        doc.set_text(text_nodes[0], value)

table.addnext(new_row)  # 或在特定位置插入
```

### 应用风险级别单元格底纹
```python
RISK_COLORS = {"Low": "E8F5E9", "Medium": "FFF8E1", "High": "FFF3E0", "Very High": "FFEBEE"}

def shade_cell(doc, cell, level):
    tc_pr = doc.get_nodes("w:tcPr", cell)
    if not tc_pr:
        tc_pr = doc.create_element("w:tcPr")
        cell.insert(0, tc_pr)
    else:
        tc_pr = tc_pr[0]
    shd = doc.create_element("w:shd", {
        "w:val": "clear", "w:color": "auto", "w:fill": RISK_COLORS[level]
    })
    existing = doc.get_nodes("w:shd", tc_pr)
    if existing:
        tc_pr.remove(existing[0])
    tc_pr.append(shd)
```

### 替换叙述占位段落
```python
for para in doc.get_nodes("//w:p"):
    text = doc.get_text(para)
    if text.startswith("[") and text.endswith("]"):
        # 替换为评估叙述
        runs = doc.get_nodes("w:r", para)
        for r in runs[1:]:
            para.remove(r)
        text_node = doc.get_nodes("w:t", runs[0])[0]
        doc.set_text(text_node, "Assessment narrative goes here...")
        break
```

## 数据来源映射

| 评估阶段 | 填充内容 |
|-----------------|-----------|
| 阈值评估 | T4、T5、T6、第 2.4 节叙述 |
| 描述 | T1、T7、T8、T9、T10、T11、T12、第 3 节叙述 |
| 必要性/相称性 | 第 4 节叙述 |
| 固有风险评估 | T13、T14 |
| 缓解措施 | T15、第 6 节叙述 |
| 剩余风险评估 | T16、T17、T18、第 7.4 节叙述 |
| 第 36 条检查 | 第 8 节叙述 |
| DPO 咨询 | T19、第 1.4 节叙述 |
| 数据主体意见 | 第 10 节叙述 |
| 审查设置 | T20 |
| 最终批准 | T3、T18、T21、T1（状态）、T2 |
| 执行摘要 | 第 1 节叙述 |
