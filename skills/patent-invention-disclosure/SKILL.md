---
name: 专利交底说明书
description: 将任意技术方案按标准 Part A/B/C 骨架自动生成发明专利交底书，输出 .docx。只需提供技术名称、核心原理和应用场景，即可从零生成完整交底书（含通讯信息表、附图占位符、C1~C4技术方案、有益效果、实施方式、边界条件、检索关键词）。
---

# 专利交底说明书 · SKILL.md

## 功能概述

将任意技术方案按中国专利交底书标准 Part A/B/C 格式自动生成 Word 文档。

**两种输入模式均支持：**

- **有源文档**：提供已有技术说明文档 → 自动提取内容并重排为标准格式
- **无源文档**：仅提供技术名称 + 核心原理 + 应用场景 → 从零生成完整交底书

---

## 核心格式模板（必须严格遵循）

### ★ Part A  通讯信息

表格形式，字段：专利名称 / 专利类型 / 发明人 / 撰写人 / 联系方式（邮箱+手机）

### ★ Part B  附图图纸

**附图总体要求**：白底黑线工程图样式，箭头标明数据流向，黑体标注。

**附图清单**：按顺序编号，每张图纸须在正文中以「如图X所示」引用。

**图片占位符**（插入真实图片前使用）：

```
【图片内容描述: 图纸内容说明，标注关键部件和尺寸】
```

不得使用 `TODO` 或 `[图片]` 等非标准占位符。

### ★ Part C  技术方案

**C1. 发明创新点**：2~3句话概括核心技术思想，突出「做了什么 + 带来什么效果」。

**C2. 结构组成与连接原理**：分模块编号（6~8个为宜），每模块包含名称和1~2句话功能描述，说明模块间数据传递方式（消息队列/共享内存/API调用）。

**C3. 各部件硬件互相结合的工作流程**：自然段落，4~6步骤，每步含触发条件、执行动作、产出结果。

**C4. 解决的技术问题**：「问题名称：解决了……的问题」格式，列举3~5项。

### 补充章节（必含）

- **有益效果**：定量数据支撑（如「精度提升70%」「功耗降低40%」）
- **具体实施方式**：「场景一 / 场景二」形式，描述2~3个典型部署场景，含硬件配置、软件环境、操作流程
- **技术边界条件**：明确不适用的情形
- **检索关键词及IPC分类号**：中英文关键词 + IPC分类
- **应用场景图**：图片占位符

---

## 技术流程

### 模式A — 有源文档（已有技术文档需要优化）

**Step 1**：用 Word COM 读取 `.doc` 源文件，提取正文内容。

**Step 2**：将内容按 Part A/B/C 骨架重组，技术内容填入对应章节，图片位置插入占位符。

**Step 3**：用 python-docx 生成 `.docx`。

```powershell
# Word COM 读取（Windows）
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open("C:\path\to\source.doc", $false, $true)
$sb = New-Object System.Text.StringBuilder
foreach ($p in $doc.Paragraphs) { [void]$sb.Append($p.Range.Text) }
$text = $sb.ToString()
$doc.Close($false)
# 注意：不调用 $word.Quit() 避免 RPC 错误
```

### 模式B — 无源文档（从零生成）

**Step 1**：向用户收集以下信息——技术名称、核心技术原理（2~3句）、应用场景（医疗/工业/仓储等）。

**Step 2**：按下方内容生成策略，从零构建 Part A/B/C 各节内容。

**Step 3**：用 python-docx 输出 `.docx`。

---

## 内容生成策略（C语言示例：技术越具体越好）

生成 C2 模块时，避免空泛描述，须包含：

- 具体协议名称（MQTT / BLE 4.2 / HTTP / TCP）
- 具体算法名称（WKNN / 卡尔曼滤波 / EKF / UKF）
- 具体参数指标（帧率/Hz、精度/m、功耗/mA）
- 具体数据结构和存储方式

生成 C3 步骤时，避免笼统表达，须包含：

- 触发条件（空闲 N 秒后 / 检测到信号时 / 用户按下按钮）
- 执行动作（调用什么API / 读写什么数据结构）
- 产出结果（输出什么数据 / 推送到哪个系统）

生成 C4 有益效果时，定量优先于定性：

- ❌「定位精度很高」→ ✅「定位精度达±10cm，相比传统方案精度提升70%」

---

## python-docx 输出代码模板

```python
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document()
section = doc.sections[0]
section.page_width = Cm(21)
section.page_height = Cm(29.7)
section.left_margin = section.right_margin = Cm(3.17)
section.top_margin = section.bottom_margin = Cm(2.54)

def set_font(run, name='宋体', size=10.5, bold=False, color=None):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    if color:
        run.font.color.rgb = RGBColor(*color)

def add_para(doc, text, font='宋体', size=10.5, bold=False, indent=0, before=2, after=4, color=None):
    from docx.shared import Pt
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = Pt(22)
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    run = p.add_run(text)
    set_font(run, font, size, bold, color)
    return p

# Part 标题：黑体 小四/14pt 加粗
add_para(doc, '★ Part A  通讯信息', font='黑体', size=14, bold=True, before=16, after=6)

# 正文：宋体 五号/10.5pt
add_para(doc, '正文内容...')

# 图片占位符：蓝色 加粗
add_para(doc, '【图片内容描述: 系统架构示意图】', font='宋体', size=10.5, bold=True, color=(0,0,200))

doc.save('output.docx')
```

## 字体规范

| 元素 | 字体 | 字号 | 样式 |
|------|------|------|------|
| Part 标题 | 黑体 | 14pt | 加粗 |
| C1~C4 标题 | 黑体 | 12pt | 加粗 |
| 正文 | 宋体 | 10.5pt | 常规 |
| 图片占位符 | 宋体 | 10.5pt | 加粗·蓝色 |

## 输出规范

- 格式：`.docx`（Word 2007+）
- 纸张：A4，边距上下2.54cm / 左右3.17cm
- 行距：固定值 22pt

## 注意事项

1. python-docx 生成新文档时会丢失源文件 Track Changes，如有需要请在 Word 中手动「审阅 → 合并文档」
2. `.doc` 格式（Word 97-2003）须先通过 Word COM 读取内容，再由 python-docx 输出 `.docx`
3. 图片占位符是交给美工/专利局的图纸标注，正文仅需 `【图片内容描述: ...】` 标准格式
4. 从零生成时，技术描述越具体（C2 模块名/C3 步骤细节/C4 定量指标），交底书质量越高
