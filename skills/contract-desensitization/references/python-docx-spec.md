# python-docx 生成技术规范

## 环境准备

```bash
pip install python-docx
```

## 核心代码模板

```python
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# ========================================
# 1. 页面设置（A4，标准边距）
# ========================================
section = doc.sections[0]
section.page_width = Cm(21.0)
section.page_height = Cm(29.7)
section.top_margin = Cm(2.54)
section.bottom_margin = Cm(2.54)
section.left_margin = Cm(2.54)
section.right_margin = Cm(2.54)

# ========================================
# 2. 设置默认样式（宋体正文）
# ========================================
style = doc.styles['Normal']
font = style.font
font.name = 'Calibri'
font.size = Pt(11)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
style.paragraph_format.line_spacing = 1.5

# ========================================
# 3. 封面标题（黑体加粗居中 16pt）
# ========================================
title_para = doc.add_paragraph()
title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
title_para.paragraph_format.space_after = Pt(24)
run = title_para.add_run('【脱敏版本】采购合同（脱敏后）')
run.bold = True
run.font.size = Pt(16)
run.font.name = '黑体'
run.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')

# ========================================
# 4. 合同正文（逐段写入）
# ========================================

def add_contract_paragraph(doc, text, bold=False, font_size=11):
    """添加合同正文段落，保留条款结构与格式"""
    para = doc.add_paragraph()
    para.paragraph_format.line_spacing = 1.5
    run = para.add_run(text)
    run.font.size = Pt(font_size)
    run.font.name = 'Calibri'
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    if bold:
        run.bold = True
    return para

def add_clause_title(doc, title_text):
    """添加条款标题（加粗）"""
    return add_contract_paragraph(doc, title_text, bold=True)

def add_clause_body(doc, body_text):
    """添加条款正文"""
    return add_contract_paragraph(doc, body_text)

# ========================================
# 5. 替代词映射表（附录一）
# ========================================
doc.add_page_break()

mapping_title = doc.add_heading('附录一：替代词映射表（内部还原用）', level=1)
for run in mapping_title.runs:
    run.font.name = '黑体'
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')

warning_para = doc.add_paragraph()
warning_run = warning_para.add_run(
    '⚠️ 本映射表含原始敏感信息，仅供内部还原核对，请勿随脱敏版本对外发布。'
)
warning_run.bold = True
warning_run.font.size = Pt(10)
warning_run.font.color.rgb = RGBColor(204, 0, 0)

# 创建映射表
mapping_data = [
    ['替代词', '原始内容（中文）', '原始内容（外文）', '客体类型'],
    ['某公司A', '深圳市云图科技有限公司', '—', '主体'],
    ['某公司B', '北京智算信息技术有限公司', '—', '主体'],
    ['某人甲', '张伟明', '—', '人员信息'],
    # ... 更多数据行
]

table = doc.add_table(rows=len(mapping_data), cols=4, style='Table Grid')
table.alignment = WD_TABLE_ALIGNMENT.CENTER

# 设置表头格式
for j, header_text in enumerate(mapping_data[0]):
    cell = table.rows[0].cells[j]
    cell.text = ''
    para = cell.paragraphs[0]
    run = para.add_run(header_text)
    run.bold = True
    run.font.size = Pt(10)
    # 灰底
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), 'D9D9D9')
    shading.set(qn('w:val'), 'clear')
    cell._element.get_or_add_tcPr().append(shading)

# 填充数据行
for i in range(1, len(mapping_data)):
    for j, cell_text in enumerate(mapping_data[i]):
        cell = table.rows[i].cells[j]
        cell.text = ''
        para = cell.paragraphs[0]
        run = para.add_run(cell_text)
        run.font.size = Pt(10)

# ========================================
# 6. 脱敏彻底性自检报告（附录二）
# ========================================
doc.add_page_break()

check_title = doc.add_heading('附录二：脱敏彻底性自检报告', level=1)
for run in check_title.runs:
    run.font.name = '黑体'
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')

check_data = [
    ['检查项', '结果', '说明'],
    ['无遗漏的公司全称残留（含外文）', '☑ 通过', '所有主体名称均已替换'],
    ['无统一社会信用代码/证号残留', '☑ 通过', '所有证号已替换'],
    ['无身份证号/护照号残留', '☑ 通过', '未检测到残留'],
    ['无完整金额数字残留', '☑ 通过', '全部金额已替换'],
    ['无 SWIFT/IBAN/账户号残留', '☑ 通过', '全部账户信息已替换'],
    ['无联系方式残留', '☑ 通过', '电话/邮箱已替换'],
    ['双语客体已成对脱敏', '☑ 通过', '中英文已同步脱敏'],
    ['合同条款结构完整性', '☑ 通过', '条款结构与签署栏完整保留'],
]

check_table = doc.add_table(rows=len(check_data), cols=3, style='Table Grid')
check_table.alignment = WD_TABLE_ALIGNMENT.CENTER

for i, row_data in enumerate(check_data):
    for j, cell_text in enumerate(row_data):
        cell = check_table.rows[i].cells[j]
        cell.text = ''
        para = cell.paragraphs[0]
        run = para.add_run(cell_text)
        run.font.size = Pt(10)
        if i == 0:
            run.bold = True
            shading = OxmlElement('w:shd')
            shading.set(qn('w:fill'), 'D9D9D9')
            shading.set(qn('w:val'), 'clear')
            cell._element.get_or_add_tcPr().append(shading)

# ========================================
# 7. 页脚免责声明
# ========================================
footer = section.footer
footer.is_linked_to_previous = False
footer_para = footer.paragraphs[0]
footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer_run = footer_para.add_run(
    '本合同为脱敏版本，敏感信息已按约定替换，仅供对外发布使用。'
)
footer_run.font.size = Pt(9)
footer_run.font.color.rgb = RGBColor(128, 128, 128)
footer_run.font.italic = True

# ========================================
# 8. 保存文件
# ========================================
import datetime
date_str = datetime.datetime.now().strftime('%Y%m%d')
output_path = f'脱敏版本_采购合同_{date_str}.docx'
doc.save(output_path)
print(f'Word文档已生成: {output_path}')
```

## 格式约束清单

| 项目 | 规范 |
|------|------|
| 页面 | A4（21.0cm × 29.7cm），边距 2.54cm |
| 中文字体 | 正文：宋体 11pt；标题：黑体；条款标题加粗 |
| 英文字体 | 正文：Calibri 11pt；标题：Calibri Bold |
| 行距 | 全文 1.5 倍行距 |
| 表格样式 | Table Grid，表头灰底（#D9D9D9）加粗 |
| 分页 | 正文→附录一→附录二 之间均分页 |
| 文件命名 | `脱敏版本_[原合同简称]_[YYYYMMDD].docx` |

## 关键代码模式

### 设置中文字体

```python
run.font.name = '宋体'
run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
```

### 表格单元格灰底

```python
shading = OxmlElement('w:shd')
shading.set(qn('w:fill'), 'D9D9D9')
shading.set(qn('w:val'), 'clear')
cell._element.get_or_add_tcPr().append(shading)
```

### 页脚文字

```python
from docx.oxml.ns import qn
section = doc.sections[0]
footer = section.footer
footer.is_linked_to_previous = False
```
