---
name: element-complaint-filler
slug: element-complaint-filler
displayName: 要素式法律文书一键生成
version: 1.0.0
description: >-
  要素式法律文书一键生成（起诉状/答辩状/强制执行申请书）。根据用户提供的原始材料，
  自动提取信息并填入要素式模板。已内置两个模板：民间借贷-要素式起诉状、强制执行申请书-要素式起诉状。
  如案由不同，需用户自行上传要素式模板（.docx）。
  触发场景：(1) 用户要求填写要素式起诉状/答辩状/强制执行申请；(2) 用户提供了传统格式的法律文书；
  (3) 用户说"填入要素式表格""生成要素式文书"等。
  推荐模型：DeepSeek V4 Pro。
---

# Element Complaint Filler — 要素式法律文书一键生成

根据用户提供的原始材料（起诉状/答辩状 .doc/.docx 或文字描述）和要素式模板（.docx），
自动提取关键信息并填入模板，生成可直接提交法院的要素式文书。

## 内置模板（assets/）

以下两个模板已经过实战验证。如果用户案由匹配，直接用；不匹配则请用户上传自有模板。

| 模板 | 文件 | 字段映射 |
|------|------|----------|
| 民间借贷-要素式起诉状 | `assets/民间借贷-要素式起诉状.docx` | `references/民间借贷-要素式起诉状_fields.md` |
| 强制执行申请书-要素 | `assets/强制执行申请书-要素式起诉状.docx` | `references/强制执行申请书-要素式起诉状_fields.md` |

**匹配方式**：如果用户说"民间借贷起诉状"或"强制执行申请书"且没有上传模板文件，直接用内置模板。
如果用户上传了自己的模板文件，以用户上传的为准。如果案由不是以上两种，告知用户需要自行提供要素式模板。

## 核心工作流程

### 第 0 步（新增）：安全拷贝 + 样式发现

**永远不要直接修改原件。** 先安全拷贝，再自动发现模板的字体和样式。

```python
from fill_helpers import copy_template, discover_template_style

# 1. 安全拷贝
work_path = copy_template("/path/to/模板.docx")
# 返回: /path/to/模板_filled.docx

# 2. 自动发现样式
style = discover_template_style(work_path)
# 返回: {'font_name': '仿宋', 'style_id': '6', 'style_name': 'Table Text'}

# 3. 用发现的样式填充全局变量
import fill_helpers
fill_helpers.FONT_NAME = style['font_name']
fill_helpers.TABLE_TEXT_STYLE = style['style_id']
```

**为什么这一步不能跳过**：不同法院的模板使用不同的样式 ID（可能是 "5"、"7"、"8"），不同字体（方正书宋_GBK / 仿宋 / 宋体）。硬编码会导致字体错误。

### 第 1 步：读取原始材料

```python
from fill_helpers import read_source
text = read_source("/path/to/起诉状.doc")
```

### 第 2 步：分析模板结构

```python
from fill_helpers import inspect_template
print(inspect_template(work_path))  # 现在还会输出发现的样式信息
```

关注：模板是起诉状还是答辩状、每个表格的行列数、哪些 cell 是 ghost。

### 第 3 步：自动提取结构化信息（新增）

不再需要手工从原始文本中抠信息，使用内置解析器：

```python
from fill_helpers import (
    parse_parties, parse_claims, parse_facts, detect_case_type
)

# 自动提取当事人信息
parties = parse_parties(text)
# parties['plaintiff'] = {'name': '赵建华', 'gender': '女', ...}
# parties['defendant'] = {'name': '张茂凤', 'gender': '女', ...}

# 自动提取诉讼请求（按条拆分）
claims = parse_claims(text)
# ['判令被告向原告归还款项100,000元', '...']

# 自动提取事实与理由全文
facts = parse_facts(text)

# 自动检测案由
case_type = detect_case_type(text)
# '民间借贷'
```

### 第 4 步：编写填写脚本

使用 `scripts/fill_helpers.py` 的工具函数。核心规则（七个血的教训）：

1. **只写唯一 cell**：
   ```python
   if not is_unique_cell(table, ri, ci):
       continue
   ```

2. **不涉及的部分加 "/"**（`cell_skip` 已内置防误伤保护——如果 cell 已被填入实际数据，不会追加 "/"）：
   ```python
   cell_skip(table.cell(ri, ci))
   ```

3. **概要框直接粘贴原文**：
   ```python
   cell_set(t2.cell(4, 0), claims_text.split('\n'))
   cell_set(t2.cell(17, 0), facts_text.split('\n'))
   ```

4. **出生日期用段落级替换**：
   ```python
   cell_replace_para(cell, '出生日期：', '出生日期：1955 年 6 月 25 日')
   ```

5. **证据清单和调解意愿留空**：不填、不打勾。

6. **一键填写当事人**（支持自然人和法人）：
   ```python
   fill_natural_person(cell, parties['plaintiff'])
   fill_legal_entity(cell, company_data)
   ```

7. **字体统一**：
   ```python
   ensure_font(cell)  # 使用第 0 步发现的字体和样式
   ```

### 第 5 步：生成后核对

生成 .docx 后，直接抽检关键字段，发现问题当场修。

```python
from fill_helpers import validate_output
warnings = validate_output(work_path)  # 自动扫描遗漏

# 人工抽检关键字段
print(doc.tables[0].cell(2, 1).text)  # 原告
print(doc.tables[1].cell(1, 1).text)  # 被告
print(doc.tables[2].cell(5, 1).text)  # 本金
print(doc.tables[2].cell(6, 1).text)  # 利息
```

## 函数速查

### 模板操作
| 函数 | 用途 |
|------|------|
| `copy_template(src)` | 安全拷贝，返回工作路径 |
| `discover_template_style(path)` | 自动发现字体和样式 ID |
| `inspect_template(path)` | 输出模板完整结构（含样式信息） |

### 材料读取与解析
| 函数 | 用途 |
|------|------|
| `read_source(path)` | 读取 .doc/.docx/纯文本 |
| `parse_parties(text)` | 提取原告/被告结构化信息 |
| `parse_claims(text)` | 拆分诉讼请求为列表 |
| `parse_facts(text)` | 提取事实与理由全文 |
| `detect_case_type(text)` | 检测案由（民间借贷/买卖合同/等） |

### Cell 操作
| 函数 | 场景 |
|------|------|
| `cell_replace(cell, old, new)` | 单行字段：姓名、电话、身份证号 |
| `cell_replace_para(cell, keyword, new)` | 跨 run 字段：出生日期、住址 |
| `cell_set(cell, lines)` | 完整覆写：概要框、自由文本 |
| `cell_skip(cell)` | 不涉及项：加 "/"，已防二重调用 |
| `cell_tick(cell, label)` | 勾选复选框 |
| `cell_gender(cell, gender)` | 性别勾选（防双框专用） |
| `ensure_font(cell)` | 字体统一样式 |
| `is_unique_cell(table, ri, ci)` | Ghost cell 判断 |
| `fill_natural_person(cell, data)` | 一键填写自然人 |
| `fill_legal_entity(cell, data)` | 一键填写法人/非法人组织 |

### 验证
| 函数 | 用途 |
|------|------|
| `validate_output(path)` | 检查遗漏字段 |

## 注意事项

- **模板优先**：以用户提供的模板为准，不要假设字段位置
- **不臆造内容**：原始材料没有的信息不要编造
- **保留原文**：事实描述原文粘贴，不做 AI 改写
- **合并单元格陷阱**：先 `inspect_template` 确认 ghost 映射再写
- **还款情况行**：部分模板中该行数据区因垂直合并与"标的总额"共享 cell，可能无法独立填写
- **字体名字面≠渲染字体**：XML 中的字体名（如"仿宋"）可能被 WPS/Word 映射到不同字体（如"方正书宋_GBK"），以 `discover_template_style` 实际返回值为准

## 强制执行申请书实战教训（补充规则）

以下规则来自强制执行申请书填写的翻车经验：

1. **优先 run 级替换，不要 cell_set 覆写已有内容的 cell**。已有内容的 cell（如申请执行事项）有复杂的段落和 run 结构，`cell_set` 会把整个 cell 清空重写，丢失原模板格式。正确做法是遍历原有 run，只替换数值。

2. **性别勾选用 `cell_gender`，不要手动拼**。部分字体（如仿宋）下 □ 和 ☑ 渲染完全一样，"男□ 女☑"会看起来像两个相同的框。`cell_gender` 把整行重写为单一 run"性别：女☑"，去掉未选项的 □。

3. **`ensure_font` 只对新增内容调用**。已有数据的 cell（如模板中已预填的姓名），其字体走的是样式继承，强制写显式字体会改变显示效果。只在 cell_set 覆写过的 cell 上调用 ensure_font。

4. **模板可能已预填数据**。部分模板（如从法院系统导出的）已包含当事人信息、案号、判决主文等。先检查哪些字段已有值，只改需要改的，不要覆写已有正确数据。

5. **模板样式不统一**。同一个模板中，不同 cell 可能使用不同 pStyle（如 Normal vs style 7）。`inspect_template` 输出的 `[pStyle=X]` 标注可以帮助识别。修改 cell 时不要改变其原有 pStyle。
