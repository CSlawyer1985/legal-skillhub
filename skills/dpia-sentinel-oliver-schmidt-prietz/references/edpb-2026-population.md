# EDPB 2026 年 DPIA 模板——填充指南

> 与官方 EDPB 模板 `references/edpb-2026-template-v1.docx` 配合使用。

本指南将官方 EDPB DPIA 模板中的每个表格和占位符映射到填充它的评估数据。使用 docx 编辑技能中的 OOXML 编辑工作流（解包 → 操作 → 重新打包）。

---

## 工作流

```
1. 将 references/edpb-2026-template-v1.docx 复制到工作目录
2. 解包：python ooxml/scripts/unpack.py template.docx unpacked/
3. 阅读 ooxml.md 参考文档以了解 Document library API
4. 对 unpacked/word/document.xml 运行填充脚本
5. 重新打包：python ooxml/scripts/pack.py unpacked/ output-dpia.docx
```

---

## 表格索引

模板包含 35 个表格。每个表格通过其位置和首行内容识别。

| 表格 | EDPB 章节 | 操作 | 识别模式（首行文本） |
|-------|-------------|-----------|----------------------------------------|
| 0 | 版本历史 | 跳过 | `Version`、`Date`、`Adoption information` |
| 1 | 0.1 控制者 | 填充单元格 | `Controller` |
| 2 | 0.2 处理者 | 添加行 | `Processor`、`Definition of their obligations` |
| 3 | 0.3 名称 | 填充单元格 | `Internal name given to the processing` |
| 4 | 0.4 规划 | 填充单元格 | `Estimated launch date` |
| 5 | 0.5 DPIA 技术表 | 填充单元格 | `Current version and version log` |
| 6 | 1.1.a 个人数据 | 添加行 | `Processed personal data (item or element)` |
| 7 | 1.1.b 目的 | 添加行 | `Purpose: specific and explicit reasons` |
| 8 | 1.1.c 二次使用 | 添加行 | `Secondary or compatible uses` |
| 9 | 1.1.d 性质/范围/背景 | 填充叙述 | `Nature of the processing` |
| 10 | 1.2 功能描述 | 添加行 | `Processing phase or stage`、`Type of operations` |
| 11 | 1.3 资产 | 添加行 | `Means of processing and supporting assets` |
| 12 | 1.4 行为准则 | 添加行 | `Code of conduct` |
| 13 | 2.1.a 法律依据 | 添加行 | `Purpose/use`、`Legal basis (Article 6(1) GDPR)` |
| 14 | 2.1.b 第 9(2) 条解除 | 添加行 | `Special category of personal data`、`Reasons to lift` |
| 15 | 2.2.a 最小化/保留 | 添加行 | `Justification of the need`、`Recipients`、`Retention period` |
| 16 | 2.2.b 数据质量 | 添加行 | `Quality metrics, requirements or thresholds` |
| 17 | 2.3.a 第 5 条措施 | 填充单元格 | `Compliance with Article 5(1)(a-f)` |
| 18 | 2.3.b 数据主体权利 | 填充单元格 | `Data subject rights` |
| 19 | 2.3.c 其他 GDPR | 填充单元格 | `Compliance with other GDPR requirements` |
| 20 | 2.3.d 设计保护 | 填充 + 添加行 | `Data protection by design and by default` |
| 21 | 2.3.e 安全 | 填充 + 添加行 | `Security of processing (Article 32 GDPR)` |
| 22 | 3.1 固有影响 | 添加行 | `Threats posed by the processing, as it has been designed` |
| 23 | 3.2 必要性 | 填充叙述 | `Evaluate if the envisaged processing is effective` |
| 24 | 3.3 相称性 | 填充叙述 | `Discuss the importance of the processing` |
| 25 | 4.1.a 运营影响 | 添加行 | `Threats posed by malfunctions and deviations` |
| 26 | 4.1.b 方法 | 填充叙述 | `Likelihood and severity levels and their meanings` |
| 27 | 4.1.c 固有风险 | 添加行 | `Risks to the data subject's rights and freedoms` |
| 28 | 4.2.a 附加措施 | 添加行 | `Technical, legal/contractual and organisational measures` |
| 29 | 4.2.b 剩余风险 | 添加行 | `Reassessed risks to the data subject's rights` |
| 30 | 4.2.c 计划 | 填充叙述 | `Specific activities, responsible team, timelines` |
| 31 | 5.1 DPO 意见 | 填充叙述 | `If there is a DPO` |
| 32 | 5.2 数据主体意见 | 填充叙述 | `Where appropriate, provide the data subjects'` |
| 33 | 6 结论 | 标记决定 | `REJECTED`、`CONSULTATION`、`APPROVED` |
| 34 | 6 理由 | 填充叙述 | （结论后的空单元格） |

---

## 操作类型

### 填充单元格

具有预定义标签行的表格。按标签文本定位行，然后填充相邻的空单元格。

```python
# Pattern: find row by label, set adjacent cell
from document import Document
doc = Document("unpacked")
# Use get_node to find the text, navigate to parent cell, then sibling cell
node = doc.get_node("xpath", ".//w:t[contains(text(), 'Controller')]")
# Navigate: w:t → w:r → w:p → w:tc (this cell) → next w:tc (target cell)
# Set text in target cell
```

### 添加行

具有标题行和一个或多个模板数据行的表格。为每条额外条目克隆最后一行数据行，然后填充单元格内容。

```python
# Pattern: find table, clone last row, fill cells
# 1. Find table by header text
# 2. Get the last w:tr (template row)
# 3. For each data item: deep-clone the template row, clear cell text, set new text
# 4. Insert cloned rows before closing </w:tbl>
# 5. Optionally remove the original empty template row
```

### 填充叙述

包含说明性占位文本的单单元格表格。将占位文本整体替换为评估内容。

```python
# Pattern: find cell by placeholder text, replace all w:t content
node = doc.get_node("xpath", ".//w:t[contains(text(), 'Evaluate if the envisaged')]")
# Clear existing text, set assessment narrative
```

### 标记决定

结论表格（表格 33）以文本形式包含全部四种决定选项。将所选决定加粗或高亮，并在其前加 ☑（替换隐含的复选框空格）。

---

## 逐表填充

### 表格 0——版本历史（跳过）

保持原样。这是 EDPB 文件自身的版本历史，而非 DPIA 的。

### 表格 1——0.1 控制者

| 行标签 | 填充内容 |
|-----------|-----------|
| Controller | 控制者名称/法律实体 |
| Management units responsible... | 管理该处理工作的部门 |
| Main establishment/point of contact... | 地址、联系人、欧盟代表 |
| Information about the DPO... | DPO 姓名、电子邮件、电话 |

共同控制者：克隆整个表格，每个控制者一份，并添加义务/任务行。

### 表格 2——0.2 处理者和子处理者

3 列：`#` | `Processor` | `Definition of their obligations and tasks`

每个处理者/子处理者添加一行。顺序编号（1、2、……N）。

**数据来源：** 处理描述 → 处理者链。

### 表格 3——0.3 处理名称

| 行标签 | 填充内容 |
|-----------|-----------|
| Internal name... | 处理活动名称（取自 ROPA） |
| Current version... | 处理本身的版本历史 |

### 表格 4——0.4 规划

| 行标签 | 填充内容 |
|-----------|-----------|
| Estimated launch date | 日期或"TBD" |
| Estimated end date or expiration conditions | 日期、条件或"Ongoing" |

### 表格 5——0.5 DPIA 技术表

需填充 8 行：

| 行 | 填充内容 |
|-----|-----------|
| Current version and version log | "v1.0 — [日期]" 加上任何先前版本 |
| Team involved in conducting this DPIA | 姓名、角色（考虑 RACI 矩阵） |
| Guidelines, standards, codes of conduct... | "EDPB Guidelines WP 248 rev.01、EDPB DPIA Template v1.0（2026 年 3 月）、[国家指南]" |
| Reasons to conduct the DPIA | 见下方复选框处理 |
| Scope of this DPIA | 包含/排除的内容及其原因 |
| Completion date | 日期 |
| Formal validation date | 日期（须负责官员签字） |
| Is the DPIA intended to be published... | 选择选项，如适用填写"How?" |

**"Reasons to conduct the DPIA"的复选框处理：** 该行包含多个带复选框式缩进的文本块。为标记选中的理由，在选中项前插入"☑ "，未选中项前插入"☐ "。文本块为：

第 35(3) 条强制触发：
- 系统性和大规模评估……（自动化画像）
- 大规模处理特殊类别……
- 对公众可进入区域进行系统性监控……

EDPB 标准：
- 评估或评分
- 具有法律或类似重大影响的自动化决策
- 系统性监控
- 敏感数据或高度个人性质的数据
- 大规模处理的数据
- 数据集匹配或合并
- 涉及弱势数据主体的数据
- 创新性使用或应用新技术或组织解决方案
- 处理阻碍数据主体行使权利时

其他触发：
- 国家法律要求（填写说明）
- DPO 意见
- 数据主体意见
- 行为准则要求
- 其他（填写说明）
- 已变更的现有处理（填写说明）

**发布意向：** 将"Yes it is going to be published: How?"或"Yes, it is going to be shared externally: How?"之后的占位文本替换为实际详情。

### 表格 6——1.1.a 处理的个人数据

4 列：`#` | `Processed personal data (item or element)` | `Explanation` | `Special category`

每个个人数据项添加一行。特殊类别列：
- 如非特殊：文本设为 "No"
- 如特殊：文本设为 "Yes:" 加适用类别文本（如 "Data concerning health"）

**数据来源：** 描述阶段 → 数据类别。

### 表格 7——1.1.b 目的

3 列：`#` | `Purpose` | `Personal data involved + justification`

每个处理目的添加一行。交叉引用表格 6 中的数据项。

### 表格 8——1.1.c 二次使用

3 列：`#` | `Secondary or compatible uses` | `Personal data involved + conditions + compatibility assessment`

仅当存在二次使用时添加行。如无，添加单行："No secondary or compatible uses identified."（未识别出二次或兼容使用。）

### 表格 9——1.1.d 性质、范围、背景

3 个叙述行：

| 行 | 填充内容 |
|-----|-----------|
| Nature of the processing | 涉及的操作、使用的技术 |
| Scope of the processing | 从数据主体视角看的数据量、规模、频率、持续时间 |
| Context of the processing | 用例、业务流程、与数据主体的关系、弱势群体 |

表格之后有两个带占位文本的是/否问题：
- "Is this a cross-border processing?"（是否为跨境处理？）→ 将 "☐ No" / "☐ Yes (justification and details): ____________" 替换
- "Is personal data going to be transferred...?"（个人数据是否将被转移……？）→ 相同模式

用 ☑ 标记适用选项，如为是则填写理由。

### 表格 10——1.2 功能描述

4 列：`#` | `Processing phase or stage` | `Type of operations` | `Explanation`

每个生命周期阶段添加一行。"Type of operations"列包含复选框：
- Collection（收集）/ Use（使用）/ Storage（存储）/ Sharing and Transfer（共享和转移）/ Deletion and Destruction（删除和销毁）

适用类型标 ☑，其他标 ☐。

**数据来源：** 描述阶段 → 数据生命周期（收集 → 使用 → 存储 → 共享 → 删除）。

### 表格 11——1.3 处理方式/资产

3 列：`Processing phase or stage` | `Means of processing and supporting assets` | `Explanation`

每个资产组添加一行。分组：硬件/基础设施、软件、API/模型、人员、场地/场所、组织资产。

**数据来源：** 资产清点阶段。

### 表格 12——1.4 行为准则

3 列：`#` | `Code of conduct` | `Explanation`

为适用的准则添加行。标记复选框："Compliance is likely to be required"（合规可能被要求）或"Compliance is necessary or beneficial"（合规是必要或有益的），用 ☑ 并填写"Why?"。

### 表格 13——2.1.a 法律依据

3 列：`Purpose/use` | `Legal basis (Art. 6(1) GDPR)` | `Justification`

每个目的（来自表格 7）+ 二次使用（来自表格 8）添加一行。法律依据列包含以复选框形式列出的第 6(1)(a-f) 条。适用依据标 ☑。

对第 6(1)(f) 条合法利益：用 LIA 平衡测试结果填写理由列。

### 表格 14——2.1.b 解除处理禁止的理由

3 列：`Special category data item` | `Art. 9(2) reason` | `Justification`

仅当存在特殊类别数据（来自表格 6）时填充。第 9(2) 列包含以复选框形式列出的 (a)-(j)。适用理由标 ☑。

### 表格 15——2.2.a 数据最小化和保留

6 列：`Data item` | `Need justification` | `Recipients` | `Recipient justification` | `Retention period` | `Retention justification`

表格 6 中的每个数据项添加一行。

**数据来源：** 必要性阶段 → 数据最小化审查。

### 表格 16——2.2.b 数据质量

3 列：`Data item` | `Quality metrics/requirements/thresholds` | `Justification`

对质量相关的每个数据项添加一行（尤其适用于 AI/ML 系统、自动化决策）。

### 表格 17-21——2.3.a-e 支持合规的措施

均遵循相同的 4 列模式：`Requirement/Principle` | `List of measures` | `Discussion` | `Implementation status`

**表格 17——第 5 条措施：** 8 个预定义行（公平性、透明度、目的限制、数据最小化、准确性、存储限制、完整性与保密性、问责制）。为每行填充第 2-4 列。

**表格 18——数据主体权利：** 5 个预定义行（信息权第 12-14 条、访问/可携权第 15+20 条、更正/删除权第 16-17+19 条、反对/限制权第 18-19+21 条、无自动化决策权第 22 条）。填充第 2-4 列。

**表格 19——其他 GDPR：** 3 个预定义行（同意第 7 条、处理者第 28 条、国际转移第五章）。填充第 2-4 列。

**表格 20——设计保护：** 2 个模板行。为每项第 25 条措施添加行。

**表格 21——安全：** 2 个模板行。为每项第 32 条措施添加行（假名化、加密、C-I-A-R、恢复等）。

**实施状态处理：** 每行有三个文本形式的状态选项："Planned"（计划中）/ "Partially implemented"（部分实施）/ "Implemented"（已实施）。将适用状态加粗。也可用 ☑/☐ 前缀。

### 表格 22——3.1 设计固有影响（轨道 A）

5 列：`#` | `Threats posed by processing as designed` | `How materialised?` | `Risk sources` | `Impact on rights/freedoms`

评估期间识别的每个轨道 A 风险添加一行。

**数据来源：** 固有风险阶段 → 来自 `risk-catalog.md` 的轨道 A 条目。

### 表格 23——3.2 必要性（叙述）

单单元格。将占位符替换为必要性评估：处理是否有效且侵入性最小？考虑过替代方案的证据。

### 表格 24——3.3 相称性（叙述）

单单元格。将占位符替换为相称性分析：重要性和效益对比对权利/自由的影响。平衡结论。

### 表格 25——4.1.a 运营影响（轨道 B）

4 列：`Threats from malfunctions/deviations` | `How materialised?` | `Risk sources` | `Impacts`

每个轨道 B 风险添加一行。至少必须包含：
1. 非法访问场景
2. 非预期修改场景
3. 数据消失场景

**数据来源：** 固有风险阶段 → 来自 `risk-catalog.md` 的轨道 B 条目。

### 表格 26——4.1.b 方法（叙述）

单单元格。将占位符替换为方法论声明：
- 量表：5 级可能性（可忽略 → 最大）和严重性（可忽略 → 最大）
- 风险公式：L × S → 分数（1-25）→ 等级（低/中/高/非常高）
- 调节因素：加重/减轻性背景调整（±1 档移位）
- 接受阈值：低 = 可接受，中 = 建议采取行动，高 = 必须采取行动，非常高 = 根本性重新设计 / 第 36 条
- 参考："基于 DPIA Sentinel 评分方法论，与 EDPB Guidelines WP 248 rev.01 一致"

### 表格 27——4.1.c 固有风险评估

7 列：`#` | `Risks` | `Likelihood` | `Severity` | `Modulating factors` | `Risk level` | `Acceptable?`

每个风险添加一行（合并表格 22 的轨道 A 和表格 25 的轨道 B）。

**数据来源：** 评估的风险登记册 → 固有风险分数 + 调节因素。

风险等级单元格颜色编码：Low=#E8F5E9、Medium=#FFF8E1、High=#FFF3E0、Very High=#FFEBEE。通过单元格属性上的 `<w:shd>` 应用：
```xml
<w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="E8F5E9"/></w:tcPr>
```

### 表格 28——4.2.a 附加缓解措施

5 列：`#` | `Measures` | `Mitigated risks (from 4.1.c)` | `Appropriateness/effectiveness` | `Implementation status`

每项附加缓解措施添加一行。实施状态：将适用层级加粗。

### 表格 29——4.2.b 剩余风险评估

7 列：`#` | `Risks` | `Additional measures` | `Residual likelihood` | `Residual severity` | `Residual risk level` | `Acceptable?`

每个接受过附加缓解的风险添加一行。剩余风险等级单元格颜色编码。

### 表格 30——4.2.c 计划（叙述）

单单元格。实施路线图：活动、负责团队、时间表、监测/审查安排。

### 表格 31——5.1 DPO 意见（叙述）

单单元格。DPO 意见 + 意见如何得到落实。

### 表格 32——5.2 数据主体意见（叙述）

单单元格。数据主体意见 + 参与说明（或未纳入的原因）。

### 表格 33——6 结论与决定

单单元格，以文本块形式包含全部四种决定选项。为标记所选决定：

1. 找到所选结果的文本块（如 "APPROVED"）
2. 将整个该结果文本块加粗
3. 对 CONDITIONALLY APPROVED（附条件批准）：将 "Condition 1: ___" 和 "Condition 2: ___" 占位符替换为实际条件
4. 对 CONSULTATION（咨询）：标记子理由（剩余风险仍然较高 / 国家法律要求）

按顺序排列的决定选项：
- `REJECTED: The processing must be abandoned.`（拒绝：必须放弃该处理。）
- `CONSULTATION: The processing will be consulted with the SA`（咨询：将就处理咨询监管机构）
- `APPROVED: The processing may proceed [immediately].`（批准：处理可以[立即]进行。）
- `CONDITIONALLY APPROVED: The processing may proceed only after the following conditions are met:`（附条件批准：处理仅在满足以下条件后方可进行：）

### 表格 34——6 理由（叙述）

单单元格。决定的可选理由。控制者希望记录论证理由时填写。

---

## 占位文本替换

模板正文（表格外）中存在 13 个 `_____` 占位符模式。这些是正文中的自由文本字段。

| 位置（周围文本） | 替换为 |
|-----------------------------|-------------|
| "Explanation: ___"（国家法律触发） | 国家法律引用 + 说明 |
| "Other (...): ___"（其他触发理由） | 具体理由文本 |
| "How? ___"（现有处理变更） | 变更描述 |
| "How? ___"（发布详情） | 发布方式/范围 |
| "How? ___"（外部共享详情） | 共享方式/接收方 |
| "Yes (justification and details): ___"（跨境） | 司法辖区 + 理由 |
| "Yes (justification and details): ___"（转移） | 转移目的地 + 机制 |
| "Why?: ___"（行为准则被要求） | 法律义务引用 |
| "Why?: ___"（行为准则有益） | 益处说明 |
| "Condition 1: ___"（附条件批准） | 第一项条件文本 |
| "Condition 2: ___"（附条件批准） | 第二项条件文本 |

替换方法：找到包含 `_____` 字符的 `<w:t>` 元素，将下划线替换为实际文本。保留周围文本和 run 格式。

---

## OOXML 模式

### 按标题文本查找表格

```python
from lxml import etree
tree = etree.parse("unpacked/word/document.xml")
ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

# Find all tables
tables = tree.findall(".//w:tbl", ns)

# Match by first-row text content
for tbl in tables:
    first_row = tbl.find(".//w:tr", ns)
    if first_row is not None:
        texts = [t.text for t in first_row.findall(".//w:t", ns) if t.text]
        combined = " ".join(texts)
        if "Processed personal data" in combined:
            target_table = tbl
            break
```

### 克隆数据行

```python
import copy

# Get rows in target table
rows = target_table.findall("w:tr", ns)
template_row = rows[-1]  # Last row is the template

for item in data_items:
    new_row = copy.deepcopy(template_row)
    cells = new_row.findall("w:tc", ns)
    for i, cell in enumerate(cells):
        # Clear existing text
        for t in cell.findall(".//w:t", ns):
            t.text = ""
        # Set new text in first text run
        first_t = cell.find(".//w:t", ns)
        if first_t is not None:
            first_t.text = item[i]
    target_table.append(new_row)

# Remove original empty template row
target_table.remove(template_row)
```

### 设置单元格底纹（风险等级颜色）

```python
color_map = {
    "Low": "E8F5E9",
    "Medium": "FFF8E1",
    "High": "FFF3E0",
    "Very High": "FFEBEE"
}

tc = risk_level_cell
tc_pr = tc.find("w:tcPr", ns)
if tc_pr is None:
    tc_pr = etree.SubElement(tc, f"{{{ns['w']}}}tcPr")
    tc.insert(0, tc_pr)

shd = tc_pr.find("w:shd", ns)
if shd is None:
    shd = etree.SubElement(tc_pr, f"{{{ns['w']}}}shd")

shd.set(f"{{{ns['w']}}}val", "clear")
shd.set(f"{{{ns['w']}}}color", "auto")
shd.set(f"{{{ns['w']}}}fill", color_map[risk_level])
```

### 替换占位文本

```python
for t_elem in tree.findall(".//w:t", ns):
    if t_elem.text and "____" in t_elem.text:
        # Replace underscores with actual content
        t_elem.text = t_elem.text.replace("_" * len_underscores, replacement_text)
```

### 标记复选框

模板在选项前使用纯文本空格。为标记复选框：

```python
# Find the text element for the option
for t_elem in tree.findall(".//w:t", ns):
    if t_elem.text and "Planned" in t_elem.text:
        # Prefix with checkbox character
        t_elem.text = "☑ " + t_elem.text.lstrip()
        break
```

同一组中未选中的选项前加 "☐ "。

---

## 数据来源映射

| 评估阶段 | 填充的表格 |
|-----------------|-----------------|
| 受理 | 1（控制者）、2（处理者）、3（名称）、4（规划）、5（技术表） |
| 描述 | 6（数据项）、7（目的）、8（二次使用）、9（性质/范围/背景）、10（功能）、12（行为准则） |
| 资产清点 | 11（资产） |
| 必要性 | 13（法律依据）、14（第 9 条解除）、15（最小化）、16（质量）、23（必要性叙述） |
| 相称性 | 24（相称性叙述） |
| 缓解（基线） | 17-21（合规措施 2.3.a-e） |
| 固有风险——轨道 A | 22（设计影响）、27（风险表——轨道 A 行） |
| 固有风险——轨道 B | 25（运营影响）、27（风险表——轨道 B 行） |
| 风险方法 | 26（方法叙述） |
| 缓解（附加） | 28（附加措施） |
| 剩余风险 | 29（剩余风险表） |
| 实施计划 | 30（计划叙述） |
| 第 36 条核查 | 31（DPO）、32（数据主体） |
| 文件记录 | 33（结论）、34（理由） |
