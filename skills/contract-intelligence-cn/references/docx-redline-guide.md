# Word 原文留痕修改与验证指南

## 一、核心原则

1. 在原 `.docx` 中修改，不根据提取文本重建整份合同；
2. 只处理目标段落、表格单元格或指定插入点；
3. 新增、替换内容统一使用红色 `C00000`；
4. 保留原页面设置、页眉页脚、编号、表格、签署页；
5. 输出后重新打开并转 PDF 检查。

## 二、中文字体

必须同时设置西文字体和东亚字体：

```python
run.font.name = '宋体'
run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), '宋体')
```

否则不同电脑或 LibreOffice 转换时可能出现字体替换或版式漂移。

## 三、替换段落

```python
from docx.shared import RGBColor
from docx.oxml.ns import qn

RED = RGBColor(0xC0, 0, 0)

def replace_paragraph(paragraph, text, red=True):
    for child in list(paragraph._p):
        if child.tag != qn('w:pPr'):
            paragraph._p.remove(child)
    run = paragraph.add_run(text)
    run.font.name = '宋体'
    run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), '宋体')
    if red:
        run.font.color.rgb = RED
```

只替换文本内容，保留原段落格式 `w:pPr`。

## 四、在指定位置插入段落

```python
from copy import deepcopy
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph


def insert_after(paragraph, text):
    new_p = OxmlElement('w:p')
    if paragraph._p.pPr is not None:
        new_p.append(deepcopy(paragraph._p.pPr))
    paragraph._p.addnext(new_p)
    p = Paragraph(new_p, paragraph._parent)
    run = p.add_run(text)
    run.font.color.rgb = RED
    return p
```

用户要求“只增加一段”时，必须只执行一次插入，不触碰其他段落。

## 五、表格不能遗漏

正文检索不能覆盖表格。必须遍历：

```python
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    ...
```

主体名称、金额、账户、签署栏最容易隐藏在表格中。

## 六、红色覆盖验证

```python
red_blocks = 0
paragraphs = list(doc.paragraphs)
paragraphs += [p for t in doc.tables for row in t.rows for c in row.cells for p in c.paragraphs]
for p in paragraphs:
    if any(r.font.color and r.font.color.rgb and str(r.font.color.rgb) == 'C00000' for r in p.runs):
        red_blocks += 1
```

预期有修改但 `red_blocks == 0` 时，禁止交付。

## 七、避免重复编号

段落可能带自动编号，`paragraph.text` 中看不到。若替换文本已包含“1.”“第一条”，应检查并按需移除该段的 `w:numPr`，不得全局删除编号。

## 八、最小修改验证

用户要求只增加一段时，建议：

1. 解压修改前后 `.docx`；
2. 比对 ZIP 内文件；
3. 在 `word/document.xml` 中删除新增节点后，与原文件文本或 XML 比对；
4. 确认原内容、表格、页眉页脚未发生其他变化。

## 九、视觉验证

1. LibreOffice 转 PDF；
2. 渲染每页图片；
3. 检查金额、账号、主体名称是否词内断行；
4. 检查表格是否截断；
5. 检查签署栏和页码；
6. 检查是否出现空白页、孤立标题和大面积异常留白。

## 十、局部修改的非目标内容验证

当用户明确要求“现有内容都不变，只改封面/某一段/某个表格”时：

1. 修改前保存备份；
2. 分离目标区域和非目标区域；
3. 修改后提取非目标区域文本并计算 SHA-256；
4. 前后哈希不一致时，禁止交付并回溯差异；
5. 如需更高强度验证，比对 `word/document.xml`、页眉页脚和媒体关系文件；
6. 只允许因分页渲染自然变化造成视觉位置变化，不允许正文内容变化。

示例：仅重排封面时，应分别提取修改前后第2页起正文文本并执行字节级比对。

## 十一、版本命名真实性

- `修改留痕版`：存在明确红色修改；
- `清洁签署版`：无红色残留，但仍可能有空白字段、附件或签章待补；
- `已签署版`：必须实际存在签字、盖章或可验证电子签名；
- 不得仅因文件名带“最终版”就认定已经签署或生效。
