# Word 文档格式规范

用于生成专业 .docx 版《人工智能法》合规报告的样式和结构规范。使用 `docx-js` 库（JavaScript/TypeScript）。

**风格：** 简洁专业——中性、权威，适合法律文件、审计追踪和监管申报。

---

## 前置条件

生成 .docx 文件之前，请阅读 docx-processing skill 中的完整 docx-js 参考：
`~/.claude/skills/docx-processing-anthropic/references/docx-js.md`

该文件提供 docx-js API、关键格式规则和常见陷阱。以下规范建立在该基础之上。

---

## 1. 文档级设置

### 页面设置

| 属性 | 值 | docx-js（DXA） |
|----------|-------|---------------|
| 纸张尺寸 | A4（210 x 297 毫米） | 默认 |
| 上边距 | 2.54 厘米（1 英寸） | 1440 |
| 下边距 | 2.54 厘米（1 英寸） | 1440 |
| 左边距 | 2.54 厘米（1 英寸） | 1440 |
| 右边距 | 2.54 厘米（1 英寸） | 1440 |
| 方向 | 纵向 | 默认 |

A4 可用宽度：9360 DXA（1 英寸边距下）。

### 默认字体

```javascript
styles: {
  default: {
    document: {
      run: { font: "Calibri", size: 22, color: "333333" } // 11pt, dark gray
    }
  }
}
```

---

## 2. 字体层次

### 标题样式

覆盖 Word 内置标题样式以确保目录兼容性：

```javascript
paragraphStyles: [
  {
    id: "Title", name: "Title", basedOn: "Normal",
    run: { size: 36, bold: true, color: "000000", font: "Calibri" }, // 18pt
    paragraph: { spacing: { before: 0, after: 300 }, alignment: AlignmentType.LEFT }
  },
  {
    id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
    run: { size: 36, bold: true, color: "000000", font: "Calibri" }, // 18pt
    paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 }
  },
  {
    id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
    run: { size: 28, bold: true, color: "222222", font: "Calibri" }, // 14pt
    paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 }
  },
  {
    id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
    run: { size: 24, bold: true, color: "333333", font: "Calibri" }, // 12pt
    paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 2 }
  }
]
```

### 正文文本

| 元素 | 字体 | 字号 | 颜色 | 间距 |
|---------|------|------|-------|---------|
| 正文 | Calibri | 11pt（22） | #333333 | after: 120 |
| 强调 | Calibri 粗体 | 11pt（22） | #333333 | — |
| 法律引用 | Calibri 斜体 | 11pt（22） | #555555 | — |
| 免责声明文本 | Calibri 斜体 | 10pt（20） | #666666 | — |
| 表格单元格文本 | Calibri | 10pt（20） | #333333 | — |
| 表格表头文本 | Calibri 粗体 | 10pt（20） | #333333 | — |

行距：1.15（docx-js `line` 属性为 276，以行的 1/240 为单位）。

```javascript
paragraph: { spacing: { line: 276 } } // 1.15 line spacing
```

---

## 3. 表格样式

### 标准评估表

用于所有评估矩阵、义务跟踪表、筛查表。

```javascript
const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };
const headerShading = { fill: "F2F2F2", type: ShadingType.CLEAR };
```

| 属性 | 值 |
|----------|-------|
| 边框 | 1pt 实线 #CCCCCC（浅灰） |
| 表头行填充 | #F2F2F2（极浅灰） |
| 表头文本 | 粗体，10pt |
| 数据行填充 | 无（白色） |
| 单元格边距 | top: 60，bottom: 60，left: 120，right: 120 |
| 垂直对齐 | 表头用 VerticalAlign.CENTER，数据用 VerticalAlign.TOP |

### 元数据表（键值对）

用于文档控制块、系统识别、分类摘要。

| 属性 | 值 |
|----------|-------|
| 左列（标签） | 粗体，宽度约 35% |
| 右列（值） | 常规字重，宽度约 65% |
| 边框 | 与标准表相同 |
| 无表头行填充 | 两行均使用白色背景 |

### 仪表板/摘要表

用于最终分类结果和标记部分。

| 属性 | 值 |
|----------|-------|
| 边框 | 2pt 实线 #999999（较深灰，稍重） |
| 表头填充 | #E8E8E8 |
| 章节标题的全宽单列行 | 跨所有列，粗体，#F5F5F5 填充 |

---

## 4. 页眉和页脚

### 页眉（除封面外的所有页面）

```javascript
headers: {
  default: new Header({
    children: [new Paragraph({
      tabStops: [{ type: TabStopType.RIGHT, position: 9360 }],
      spacing: { after: 0 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" } },
      children: [
        new TextRun({ text: "[Report Title]", font: "Calibri", size: 16, color: "999999" }), // 8pt
        new TextRun({ text: "\t" }),
        new TextRun({ text: "[Date]", font: "Calibri", size: 16, color: "999999" })
      ]
    })]
  })
}
```

### 页脚（所有页面）

```javascript
footers: {
  default: new Footer({
    children: [new Paragraph({
      tabStops: [{ type: TabStopType.RIGHT, position: 9360 }],
      border: { top: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" } },
      children: [
        new TextRun({ text: "Confidential", font: "Calibri", size: 16, color: "999999", italics: true }),
        new TextRun({ text: "\t" }),
        new TextRun({ text: "Page ", font: "Calibri", size: 16, color: "999999" }),
        new TextRun({ children: [PageNumber.CURRENT], font: "Calibri", size: 16, color: "999999" }),
        new TextRun({ text: " of ", font: "Calibri", size: 16, color: "999999" }),
        new TextRun({ children: [PageNumber.TOTAL_PAGES], font: "Calibri", size: 16, color: "999999" })
      ]
    })]
  })
}
```

---

## 5. 封面页

极简、干净。文档的第一个分节，后接分节符。

结构（自上而下，垂直分布）：

1. **报告类型**——例如"AI Act Compliance Assessment Report"（《人工智能法》合规评估报告）（18pt，粗体，黑色）
2. **水平线**——细灰线
3. **系统名称**——大号（24pt，粗体）
4. **元数据块**（无边框表格）：
   - 组织：[名称]
   - 日期：[日期]
   - 编制人：[姓名、职务]
   - 编号：[参考编号]
   - 状态：[草稿/定稿]
5. **免责声明**——斜体，10pt，灰色，页面底部

使用垂直间距（段落 `spacing.before`）将内容从上方向下推。封面应感觉开阔，而非局促。

```javascript
// Cover page is its own section with no header/footer
{
  properties: {
    page: { margin: { top: 2880, right: 1440, bottom: 1440, left: 1440 } } // Extra top margin
  },
  headers: { default: new Header({ children: [new Paragraph({ children: [] })] }) }, // Empty header
  footers: { default: new Footer({ children: [new Paragraph({ children: [] })] }) }, // Empty footer
  children: [ /* cover page content */ ]
}
```

---

## 6. 各模板的结构说明

### 模板 A：完整评估报告

9 个章节。主章节（1-9）使用 `HeadingLevel.HEADING_1`，子章节（6.1、6.2 等）使用 `HEADING_2`，次级子章节（6.2.1、6.2.2）使用 `HEADING_3`。

关键结构要素：
- 封面页（独立分节）
- 目录（封面之后、第 1 节之前）
- 第 3 节（范围排除）：6 行评估表
- 第 4.1 节（AI 系统测试）：7 行标准表
- 第 6.1 节（第 5 条筛查）：8 行筛查表
- 第 6.2.2 节（附件三）：8 行类别表
- 第 7 节（义务）：多表矩阵（技术、组织、管理、评估、GDPR）
- 第 8 节（建议）：编号优先级表
- 文末免责声明段落

分页符位置：第 1、3、6、7、8、9 节之前。

### 模板 B：分类记录（Pruefprotokoll）

8 个章节。顶部为文档控制元数据表。通篇大量使用评估表。末尾为评估人/复核人签名块。

关键结构要素：
- 文档控制表（无边框，键值）
- 第 4.1-4.6 节：级联式风险分类表
- 第 6 节：分类结果摘要表（仪表板风格）
- 签名块：评估人和复核人的签署行

分页符位置：第 1、4、6、8 节之前。

### 模板 C：合规登记册条目

跟踪器式文档。顶部为系统元数据表。4 个义务跟踪表（技术、组织、评估、管理体系）。进度摘要表。变更日志。

关键结构要素：
- 系统元数据（键值表）
- 4 个含状态列的义务跟踪表
- GDPR 协调表
- 实施进度摘要（含完成百分比）
- 剩余风险表
- 变更日志表

分页符位置：义务跟踪表、GDPR 协调、实施进度之前。

### 模板 D：管理层简报（Entscheidungsvorlage）

渲染后最多 2 页。紧凑布局。"概览"摘要表。财务敞口表。战略方案比较表。决策/签批块。

关键结构要素：
- 无目录（太短）
- 分类"概览"表（带视觉标记的仪表板风格）
- 前 5 项义务表（RAG 状态）
- 财务敞口表（3 行）
- 战略方案表（4 个方案，含利弊/成本/风险）
- 带复选框行的决策块
- 时间线以格式化文本呈现（非 ASCII 图）

无分页符——必须控制在 2 页内。使用更紧凑的间距（段落 after: 80，而非 120）。

---

## 7. 文件命名规范

```
AI-Act-[Template]-[SystemName]-[YYYY-MM-DD].docx
```

示例：
- `AI-Act-Assessment-Report-TalentScreenAI-2026-03-15.docx`
- `AI-Act-Pruefprotokoll-TalentScreenAI-2026-03-15.docx`
- `AI-Act-Compliance-Register-TalentScreenAI-2026-03-15.docx`
- `AI-Act-Management-Briefing-TalentScreenAI-2026-03-15.docx`

净化系统名称：空格替换为连字符，移除特殊字符。

---

## 8. 生成检查清单

生成 .docx 之前：

- [ ] 所有报告内容已在 markdown 中定稿（第 3 阶段质量检查通过）
- [ ] 已阅读 docx-processing skill 中的 docx-js.md 以获取 API 参考
- [ ] 封面页和文件名可获取系统名称
- [ ] 可获取日期和编制人信息
- [ ] 已确认模板类型（A、B、C 或 D）

生成过程中：

- [ ] 封面页以正确的元数据渲染
- [ ] 目录已包含（管理层简报除外）
- [ ] 所有表格使用一致的边框和填充样式
- [ ] 所有标题使用 HeadingLevel（而非自定义样式）以确保目录兼容
- [ ] 页眉/页脚在所有页面显示（封面除外）
- [ ] 分页符置于主要章节之前
- [ ] 文末包含免责声明文本
- [ ] 文件按正确的命名规范保存
- [ ] 任何 TextRun 中无 `\n` 字符（使用独立段落）
- [ ] 所有表格单元格使用 ShadingType.CLEAR（绝不使用 SOLID）
- [ ] 项目符号列表使用 LevelFormat.BULLET（绝不使用 unicode 符号）
