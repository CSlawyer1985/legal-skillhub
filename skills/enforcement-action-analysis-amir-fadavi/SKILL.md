---
name: "enforcement-action-analysis-amir-fadavi"
description: "分析任何 OFAC 或 OFSI 执法行动——经 URL、粘贴文本或上传文档——并将结构化根本原因分析生成为格式化 Excel（.xlsx）电子表格。当用户指名、链接、粘贴或上传 OFAC 或 OFSI 执法行动，并请求以下任何内容时使用本技能：根本原因分析、合规差距、出了什么问题、经验教训、组织自我评估或补救规划。当用户询问“analyze this enforcement action”“what were the root causes”“turn this into a checklist”或“how do I make sure this doesn't happen to us”时也触发。输出单工作表 .xlsx 表格，六列：根本原因 | 出了什么问题 | 问题如何发生 | 什么本可阻止它 | 我的组织对此免疫吗？（是/否/部分）| 备注。"
metadata:
  author: "Amir Fadavi"
  license: "mit"
  version: "2026-06-10"
---

# 执法行动分析技能

将任何 OFAC 或 OFSI 执法行动的结构化根本原因分析生成为格式化 Excel 电子表格。输出为六列表格，设计用作金融机构和非金融公司的合规官、企业内部律师、外部律师和顾问的工作文档。

---

## 输入

用户将以三种方式之一提供执法行动：

1. **URL** ——获取并解析文档（PDF 或 HTML）
2. **粘贴文本** ——直接使用对话中的文本
3. **上传文件** ——从 `/mnt/user-data/uploads/` 读取

若均未提供，请用户提供执法行动后再继续。

---

## 步骤 1——提取案件事实

在识别根本原因之前，从执法行动中提取以下内容：

- **主体**（和解方名称）
- **监管机构**（OFAC 或 OFSI；如有说明，含部门/分部）
- 和解或执法发布的**日期**
- **和解金额**
- **制裁计划**（如伊朗、俄罗斯、古巴）及引用的具体法规
- **违规期间**
- **明显违规次数**
- **严重 / 非严重**
- **是否自愿自我披露？**

用这些内容命名输出文件并填充工作表标题单元格。

---

## 步骤 2——识别根本原因

通读完整执法行动——尤其是**明显违规描述**、**加重因素**和**合规考量**章节。这些是根本原因的主要素材。

识别**所有不同的根本原因**。根本原因是离散的合规失败——政策、流程、培训、技术或判断上的缺口——导致违规发生。不要为保持表格简短而合并无关的失败。典型执法行动产出 2–5 个根本原因；复杂案件（如大宗商品交易、多方规避计划）可能更多。

**对每个根本原因，起草三部分内容：**

### 列：出了什么问题
1–3 句，描述该案例中发生的具体失败。基于事实、以执法行动文本为依据。不使用泛化合规语言。

### 列：问题如何发生
1–3 句，解释潜在的合规失败机制——为何组织的计划未捕捉到这一点。取材自：
- 监管机构陈述的加重因素
- 合规考量章节
- OFAC 合规框架根本原因分类法（见下文）
- 从事实作出的逻辑推断

### 列：什么本可阻止它
2–4 句，描述本可预防或检测违规的具体控制措施。针对案件事实具体化。始终反映 OFAC 的合规考量章节——这些是监管机构自身的明示期望，不可遗漏。

---

## OFAC 根本原因分类法（参考）

源自 OFAC 合规框架附录。识别根本原因时用作检查清单：

- 缺乏正式制裁合规计划
- 政策和程序不充分（包括未针对新业务线更新）
- 误用 OFAC 法规（包括“重形式轻实质”错误）
- 未更新或使用自动化筛查工具
- 筛查工具未配置覆盖相关清单（如 SSI/非 SDN 清单）
- 未识别和升级红旗
- 对客户、中间人或相对方缺乏尽职调查
- 合规职能分散且应用不一致
- 制裁合规培训不足
- 未对既有关系进行持续监控
- 未更新合规计划即进入新业务线

---

## 步骤 3——构建电子表格

使用 **openpyxl**（Python）。不得使用任何其他库创建文件。

### 工作表结构

- **第 1 行：** 标题单元格（合并 A1:F1）——`Root Causes of Apparent Violations — [Subject] ([Regulator], [Date])`
- **第 2 行：** 列标题
- **第 3 行起：** 每个根本原因一行

### 列布局

| 列 | 标题 | 宽度（字符） |
|-----|--------|--------------|
| A | Root Cause（根本原因） | 22 |
| B | What Went Wrong（出了什么问题） | 38 |
| C | How It Went Wrong（问题如何发生） | 42 |
| D | What Could Have Stopped It（什么本可阻止它） | 46 |
| E | Is my organization immune to this?（我的组织对此免疫吗？） | 22 |
| F | Notes（备注） | 28 |

### 样式

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

NAVY   = "1B3A6B"
STEEL  = "A8C4E0"
LIGHT  = "EEF2F9"
WHITE  = "FFFFFF"
INK    = "1A1A2E"
GREY   = "D0D8E4"

thin = Side(style='thin', color=GREY)
border = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap = Alignment(wrap_text=True, vertical='top')
center_wrap = Alignment(wrap_text=True, vertical='center', horizontal='center')
```

**标题行（第 1 行，合并 A1:F1）：**
- 合并单元格 A1:F1
- 字体：Arial 14pt 粗体，颜色 `WHITE`
- 填充：`NAVY`
- 对齐：左对齐，垂直居中
- 行高：30

**表头行（第 2 行）：**
- 字体：Arial 11pt 粗体，颜色 `WHITE`
- 填充：`NAVY`
- 对齐：自动换行，垂直顶部
- 边框：四边细线 `GREY`
- 行高：30

**数据行（第 3 行起）：**
- 列 A：字体 Arial 10pt 粗体颜色 `NAVY`，填充 `LIGHT`，边框，左上自动换行
- 列 B–D：字体 Arial 10pt 颜色 `INK`，填充 `WHITE`，边框，左上自动换行
- 列 E：字体 Arial 10pt 颜色 `INK`，填充 `WHITE`，边框，居中对齐——值：`☐ Yes / ☐ No / ☐ Partial`
- 列 F：字体 Arial 10pt 颜色 `INK`，填充 `WHITE`，边框，左上自动换行——空
- 行高：设为 15 *（估算行数）——最低 60，使用 `sheet.row_dimensions[r].height`

**列 A 标签格式：** `RC[N]: [Short Title]`——如 `RC1: SDN-Only Screening`

### 输出路径

```
/mnt/user-data/outputs/[SubjectName]_OFAC_RootCause_Analysis.xlsx
```

使用下划线，不用空格。净化特殊字符。

### 完整代码模板

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import math

wb = Workbook()
ws = wb.active
ws.title = "Root Cause Analysis"

NAVY, LIGHT, WHITE, INK, GREY = "1B3A6B", "EEF2F9", "FFFFFF", "1A1A2E", "D0D8E4"
thin   = Side(style='thin', color=GREY)
border = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap   = Alignment(wrap_text=True, vertical='top')
cwrap  = Alignment(wrap_text=True, vertical='center', horizontal='center')

col_widths = [22, 38, 42, 46, 22, 28]
headers    = ["Root Cause", "What Went Wrong", "How It Went Wrong",
              "What Could Have Stopped It", "Is my organization immune to this?", "Notes"]

# Title row
ws.merge_cells("A1:F1")
t = ws["A1"]
t.value     = "Root Causes of Apparent Violations — [Subject] ([Regulator], [Date])"
t.font      = Font(name="Arial", size=14, bold=True, color=WHITE)
t.fill      = PatternFill("solid", fgColor=NAVY)
t.alignment = Alignment(horizontal='left', vertical='center')
ws.row_dimensions[1].height = 30

# Header row
for i, h in enumerate(headers, 1):
    c = ws.cell(row=2, column=i, value=h)
    c.font      = Font(name="Arial", size=11, bold=True, color=WHITE)
    c.fill      = PatternFill("solid", fgColor=NAVY)
    c.alignment = cwrap
    c.border    = border
ws.row_dimensions[2].height = 30

# Column widths
for i, w in enumerate(col_widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w

# rows = list of (rc_label, what_went_wrong, how_it_went_wrong, what_could_have_stopped)
rows = []  # populated from analysis

for r, (rc, ww, hw, stop) in enumerate(rows, start=3):
    data = [rc, ww, hw, stop, "☐ Yes  /  ☐ No  /  ☐ Partial", ""]
    max_lines = 1
    for i, val in enumerate(data, 1):
        c = ws.cell(row=r, column=i, value=val)
        c.border    = border
        c.font      = Font(name="Arial", size=10, bold=(i == 1),
                           color=NAVY if i == 1 else INK)
        c.fill      = PatternFill("solid", fgColor=LIGHT if i == 1 else WHITE)
        c.alignment = cwrap if i == 5 else wrap
        if val and i < 5:
            lines = math.ceil(len(str(val)) / col_widths[i-1]) + str(val).count('\n')
            max_lines = max(max_lines, lines)
    ws.row_dimensions[r].height = max(60, max_lines * 15)

wb.save("/mnt/user-data/outputs/[Filename].xlsx")
print("Done.")
```

---

## 步骤 4——呈现文件

以输出路径调用 `present_files`。一行背景说明即可（如“FTI 案件有四个根本原因——可下载。”）。

---

## 呈现前的质量检查

- 每个根本原因行的四个文本列均已填充（B–D 无空白）
- “什么本可阻止它”在适用处反映 OFAC 的合规考量
- 根本原因彼此不同——没有两行描述同一潜在失败
- 列 A 标签遵循 `RC[N]: [Short Title]` 格式
- 标题单元格匹配：`Root Causes of Apparent Violations — [Subject] ([Regulator], [Date])`
- 列 E 在每个数据行中包含复选框字符串
- 文件已写入 `/mnt/user-data/outputs/` 并经 `present_files` 呈现
