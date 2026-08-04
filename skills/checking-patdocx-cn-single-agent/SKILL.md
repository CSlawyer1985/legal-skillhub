---
name: checking-patdocx-cn-single-agent
description: |
  检查中国专利申请文件(.docx/.doc)中的撰写问题，按照专利法、专利法实施细则和专利审查指南的规则审查摘要、权利要求书、说明书等章节，在修订模式下执行替换、删除和添加批注说明。Use when user asks to check, review, audit, or proofread a Chinese patent application document (.docx or .doc), or when user provides a .docx or .doc file of a Chinese patent application for quality inspection. Do NOT use when user explicitly requests multi-agent mode or parallel review — use checking-patdocx-cn-multi-agents instead.
---

# 中国专利申请文件质检员

AI 辅助审查中国专利申请文件（.docx / .doc），按照专利法、专利法实施细则和专利审查指南的规则，对摘要、权利要求书、说明书等章节进行多维度审查，生成在修订模式下执行替换、删除、批注的 docx 副本，同时生成审查意见汇总报告。

> ⚠️ **.doc 格式支持**：本 skill 支持输入 `.doc` 格式文件。处理时会自动使用 pywin32（COM 自动化）调用 Microsoft Word 将 `.doc` 转换为 `.docx`，然后按标准流程处理。**要求**：Windows 系统 + 已安装 Microsoft Word + 已安装 pywin32 库。

## 功能特性

| 功能 | 说明 |
|:---|:---|
| 专利文本提取与章节分割 | 自动提取 docx/doc 文本并分割为摘要、摘要附图、权利要求书、说明书、说明书附图 5 个章节 |
| 多维度审查规则（13条） | 涵盖摘要检查（2条）、权利要求书审查（6条）、说明书审查（2条）、全文审查（2条）、整理汇总（1条） |
| 修订模式操作 | 对于明确了具体操作的修改建议，在修订模式下执行字词替换或删除，同时添加批注说明 |
| 批注标记问题位置 | 对于无法明确具体操作的修改建议，在 docx 文档中添加批注标记问题位置 |
| 审查意见汇总报告 | 按章节整理所有审查意见，生成结构化 markdown 报告 |

## ⛔ 关键禁止事项

> **以下行为会导致输出文档内容丢失或审查结果不可靠，严格禁止：**

1. **禁止自行编写修正脚本**：必须使用 `review_adder.py` 添加批注和修订。自行编写脚本调用 `Document` 类的 `get_node` + `replace_node` 会导致**严重内容丢失**
2. **禁止跳过验证步骤**：第七步的内容完整性验证是**强制性的**，未通过验证的文档**禁止**输出给用户
3. **禁止在终端中直接执行多行 Python 代码**：必须直接调用 `patent_extractor.py`、`review_adder.py` 和 `verify.py`
4. **禁止在 skill 目录内创建工作文件夹**：工作文件夹必须创建在输入 docx 文件所在目录下，所有路径必须使用绝对路径
5. **禁止自行编造时间戳**：时间戳必须通过执行命令获取真实值

## 路径变量说明

| 变量 | 含义 | 示例 |
|:---|:---|:---|
| `<skill_name>` | 本 skill 的名称，同时也是输出 docx 文件中批注的作者名 | `checking-patdocx-cn-single-agent` |
| `<skill_root>` | 本 skill 的根目录 | `D:\path\to\.trae\skills\checking-patdocx-cn-single-agent` |
| `<input_docx>` | 输入 docx/doc 文件的**绝对路径** | `D:\docs\专利申请文件.docx` |
| `<input_dir>` | 输入 docx 文件所在目录的**绝对路径** | `D:\docs` |
| `<input_stem>` | 输入 docx 文件名（不含扩展名） | `专利申请文件` |
| `<timestamp>` | 第二步获取的本地时间戳 | `20260424_153025` |
| `<work_dir>` | 工作文件夹的**绝对路径** | `D:\docs\checking-patdocx-cn-single-agent_20260424_153025` |

> ⚠️ **所有路径必须使用绝对路径**。Windows 路径中的反斜杠 `\` 在命令行参数中直接使用即可，**不要**手动添加额外转义。

## 工作流检查清单

在开始执行前复制以下清单，并在每一步完成后显式标记状态。

- [ ] Step 1：判断文件类型（非 .docx/.doc 则终止）
- [ ] Step 2：获取时间戳并创建工作文件夹
- [ ] Step 3：提取文档文本并分割章节
  - **反馈闭环**：若提取失败或章节缺失，检查文件是否损坏并告知用户
- [ ] Step 4：按审查规则逐章审查
  - **反馈闭环**：审查完成后自检——每条意见是否有明确 context？action_type 是否正确？old_text 是否为 context 的子串？
- [ ] Step 5：整理汇总审查意见
- [ ] Step 6：添加批注和修订到 docx
  - **反馈闭环**：若跳过数量 > 0，检查原因并修正 reviews JSON 后重新执行本步
- [ ] Step 7：内容完整性验证（强制性）
  - **反馈闭环**：若验证未通过，排查原因并修正后重新执行 Step 6 和 Step 7
- [ ] 输出结果

## 工作流程

### 第一步：判断文件类型

检查用户输入的文件是否为 `.docx` 或 `.doc` 格式：

1. 获取用户输入的文件路径，检查文件扩展名是否为 `.docx` 或 `.doc`（不区分大小写）
2. 如果文件扩展名**不是** `.docx` 或 `.doc`，**直接告知用户**：

```
⚠️ 目前本 skill 只支持解析 .docx 和 .doc 格式的专利申请文件，不支持 .pdf 等其他类型文件。
请将文件转换为 .docx 格式后重试。
```

并**终止工作流程**。如果是 `.docx` 或 `.doc`，继续执行第二步。

> ⚠️ **.doc 格式自动转换**：如果输入文件为 `.doc` 格式，`patent_extractor.py`、`review_adder.py` 和 `verify.py` 会自动调用 `doc_converter.py`（基于 pywin32 COM 自动化）将 `.doc` 转换为临时 `.docx` 文件，处理完成后自动清理临时文件。**要求**：Windows 系统 + 已安装 Microsoft Word + 已安装 pywin32 库。

### 第二步：获取时间戳并创建工作文件夹

**必须先执行以下命令**获取当前本地时间戳：

```bash
python -c "from datetime import datetime; print(datetime.now().astimezone().strftime('%Y%m%d_%H%M%S'))"
```

将输出的时间戳记为 `<timestamp>`。**必须实际执行此命令**，不得自行编造或猜测时间戳。

然后定义工作文件夹路径（**必须**创建在输入 docx 文件所在目录下，使用**绝对路径**）：

- `<work_dir>` = `<input_dir>\<skill_name>_<timestamp>`

创建工作文件夹：

```bash
mkdir "<work_dir>"
```

后续步骤中的中间产物都放在 `<work_dir>` 下。

### 第三步：提取文档文本并分割章节

#### 3.1 提取完整文本

```bash
python "<skill_root>\scripts\patent_extractor.py" "<input_docx>" --extract-only > "<work_dir>\extracted_text_<timestamp>.txt"
```

> ⚠️ 文本提取已覆盖正文段落、表格和文本框（包括传统文本框 `w:txbxContent` 和现代形状文本框 `wps:txbx`）。脚注、尾注中的文字仍无法提取，如果文档包含这些元素，应提醒用户可能存在未检查到的区域。

#### 3.2 分割为章节

```bash
python "<skill_root>\scripts\patent_extractor.py" "<input_docx>" --output-json "<work_dir>\sections_<timestamp>.json"
```

该命令会输出一个 JSON 文件，包含以下 5 个章节的文本：

| 字段 | 章节 |
|:---|:---|
| `abstract_text` | 摘要 |
| `abstract_fig` | 摘要附图 |
| `claims` | 权利要求书 |
| `description` | 说明书 |
| `description_figs` | 说明书附图 |

### 第四步：AI 按审查规则逐章审查

> ⚠️ 这是核心审查步骤。AI 必须逐一读取审查规则文件，将规则内容作为审查提示词，结合对应章节的文本进行审查。

#### 4.1 读取审查规则

审查规则文件位于 `<skill_root>\审查规则\` 目录下，共 13 个 .txt 文件。AI 必须**逐一读取**每个规则文件的完整内容。

#### 4.2 按章节应用审查规则

| 章节 | 审查规则文件 | 说明 |
|:---|:---|:---|
| 摘要 | `11-摘要-简单检查1.txt` | 字数、段落、商业用语、附图标记等 |
| 摘要 | `12-摘要-复杂检查1.txt` | 摘要表述完整性、各要素一致性 |
| 权利要求书 | `31-权利要求书-简单审查1-格式检查1.txt` | 序号格式、编号、句号使用等 |
| 权利要求书 | `31-权利要求书-简单审查2-格式检查2.txt` | 附图标记、模糊词、绝对化词等 |
| 权利要求书 | `31-权利要求书-简单审查3-所述的引用基础.txt` | "所述"引用基础、应加"所述"等 |
| 权利要求书 | `31-权利要求书-简单审查4-引用与主题.txt` | 从属权利要求引用关系、多引多、单一性等 |
| 权利要求书 | `32-权利要求书-复杂审查1.txt` | 保护范围不清楚、权利要求不简要 |
| 权利要求书 | `32-权利要求书-复杂审查2-单一性.txt` | 独立权利要求之间的单一性 |
| 说明书 | `41-说明书-简单审查1.txt` | 发明名称、技术领域、背景技术、发明内容等 |
| 说明书 | `42-说明书-复杂审查1-说明书公开是否充分.txt` | 说明书公开充分性 |
| 全文 | `61-全文-简单审查1.txt` | 错别字、术语一致性、附图标记一致性等 |
| 全文 | `62-全文-复杂审查1.txt` | 权利要求书是否得到说明书支持、摘要与说明书一致性 |

#### 4.3 执行审查

对每个章节，按以下流程执行审查：

1. 读取该章节对应的审查规则 .txt 文件的**完整内容**
2. 将规则内容作为审查提示词，结合第三步提取的章节文本，逐条检查是否存在问题
3. 对于权利要求书的审查规则，需要结合权利要求之间的引用关系进行分析
4. 对于全文审查规则（61、62），需要同时参考摘要、权利要求书和说明书的文本
5. 收集所有发现的问题

#### 4.4 输出审查意见 JSON

将所有审查发现的问题整理为 JSON 格式，保存为 `<work_dir>\reviews_<timestamp>.json`。

详细的 JSON schema、字段说明和示例请参见 `参考/reviews_json_schema.md`。

**关键要求**：
- 审查意见必须基于审查规则，不得随意添加规则外的意见
- 每条审查意见必须有明确的 `context`（文档中实际存在的文本片段）
- `action_type` 为 `"replace"` 或 `"delete"` 时，`old_text` 必须是 `context` 的子串或等于 `context`
- `context`、`old_text` 和 `highlight_text` 必须是文档中实际存在的原文逐字复制，不得改写、意译或增减字符，任何不匹配都会导致批注定位失败；`highlight_text` 必须是 `context` 的子串
- 当同一 `context` 在文档中出现多次但只需标注特定位置时，使用 `occurrence` 字段（从 1 开始的整数）指定第几次出现；不指定时默认标注第一次出现

### 第五步：整理汇总审查意见

使用审查规则 `71-整理汇总输出.txt` 中的模板，将第四步的所有审查意见整理为一份结构化的 markdown 报告。

1. 读取 `<skill_root>\审查规则\71-整理汇总输出.txt` 的内容，按照其中的模板格式组织审查意见
2. 将审查意见按章节分类
3. 权利要求书部分按权利要求序号分组列出问题
4. 保存为 `<input_dir>\<input_stem>_review_report_<timestamp>.md`

详细的报告模板和格式要求请参见 `参考/report_template.md`。

> ⚠️ 报告文件放在**输入文件同目录下**，**不放入**工作文件夹。

### 第六步：添加批注和修订到 docx

使用 `review_adder.py` 脚本将审查意见添加到 docx 文档中。根据审查意见的 `action_type` 字段，脚本会执行不同操作：

| `action_type` | 操作 | 说明 |
|:---|:---|:---|
| `"comment"` | 仅添加批注 | 不修改原文，仅在目标位置添加批注标记 |
| `"replace"` | 修订模式下替换 + 批注 | 在修订模式下将 `old_text` 替换为 `new_text`，并添加批注说明 |
| `"delete"` | 修订模式下删除 + 批注 | 在修订模式下将 `old_text` 标记为删除，并添加批注说明 |

```bash
python "<skill_root>\scripts\review_adder.py" "<input_docx>" "<input_dir>\<input_stem>_ReviewOut_<timestamp>.docx" --reviews-file "<work_dir>\reviews_<timestamp>.json"
```

> ⛔ **必须使用 `review_adder.py`，禁止自行编写批注/修订脚本。** 自行编写脚本会导致严重内容丢失。`review_adder.py` 内部已正确处理文本拆分逻辑和跨 run 文本映射。

> **精准定位能力**：`review_adder.py` 已内建精准匹配能力，可在 docx 文件中精准且最小化地定位待修改或待批注的文本：
> - **跨 run 精准定位**：当目标文本跨越多个 `w:r` 元素时，能精确计算字符偏移量，只标记目标文本范围，不影响 run 中的其他文本
> - **批注精准定位**：纯批注（comment）模式下，优先使用 `highlight_text` 指定批注精确覆盖范围（仅批注该文本而非整个 context）；若未指定 `highlight_text`，则批注范围覆盖整个 context
> - **修订批注精准定位**：replace/delete 模式下，批注仅覆盖实际修订的文本（w:del/w:ins 节点），不包含修订前后的未修改文本
> - **occurrence 字段**：当同一 context 在文档中出现多次时，可通过 `occurrence` 字段（从 1 开始的整数）指定标注第几次出现；不指定时默认标注第一次出现
> - **空白字符容错**：搜索文本时先尝试精确匹配，失败后自动尝试忽略空白字符差异的模糊匹配

> ⚠️ **Windows PowerShell 环境**：禁止使用 `PYTHONPATH=xxx python -m ...` 的 bash 语法，必须使用 `python "<skill_root>\scripts\review_adder.py"` 直接调用。

脚本执行后会输出处理统计信息。**如果跳过数量大于 0**，需要检查原因并修正 reviews JSON 后重新执行本步。

### 第七步：内容完整性验证（强制性）

> ⛔ **本步骤为强制性步骤，不得跳过。** 未通过验证的文档**禁止**输出给用户。

```bash
python "<skill_root>\scripts\verify.py" "<input_docx>" "<input_dir>\<input_stem>_ReviewOut_<timestamp>.docx" "<work_dir>"
```

该脚本会自动执行以下三项验证：

1. **段落数量验证**：对比原始文档与审查文档的段落数量
2. **模拟接受修订验证**：确认只有预期的字词被修改
3. **文件结构验证**：确保审查文档保留了原始文档的所有文件

如果任何验证项未通过（输出 ❌），必须排查原因并修正后重新执行第六步和第七步。

## 最终输出结果

向用户报告审查结果：

```
📋 专利申请文件审查完成

审查文件：xxx.docx
发现问题：N 处

【审查摘要】
- 摘要：X 处问题
- 权利要求书：Y 处问题（涉及 Z 项权利要求）
- 说明书：W 处问题
- 全文一致性：V 处问题

已生成审查版文档：xxx_ReviewOut_<timestamp>.docx
- 明确了具体操作的修改建议已在修订模式下执行替换或删除，可在 Word 中逐一接受/拒绝
- 无法明确具体操作的修改建议以批注标记，可在 Word 中查看
- 批注第一行为问题描述，换行后为修改建议

审查意见汇总报告：<input_dir>\<input_stem>_review_report_<timestamp>.md
中间文件保存在：<work_dir>
```

## 脚本错误处理

当脚本执行出错时，按以下方式处理：

| 脚本 | 常见错误 | 处理方式 |
|:---|:---|:---|
| `patent_extractor.py` | 文件损坏或非 docx 格式 | 告知用户文件可能损坏，建议检查文件 |
| `patent_extractor.py` | 章节识别不完整 | 提醒用户文档结构可能不符合标准专利申请格式 |
| `review_adder.py` | ⚠ 未找到文本 | 检查 context 是否为文档中实际存在的文本，修正后重新执行 |
| `review_adder.py` | ⚠ 未找到待替换/待删除文本 | 检查 old_text 是否为 context 的子串，修正后重新执行 |
| `verify.py` | 段落数量不一致 | 检查是否使用了自行编写的脚本，回退使用 review_adder.py |
| `verify.py` | 模拟接受修订后内容不一致 | 排查修订操作是否影响了非目标文本，修正后重新执行第六步 |

## 文件命名规则

所有输出文件必须包含第二步获取的真实本地时间戳：

| 文件 | 命名格式 | 位置 |
|:---|:---|:---|
| 工作文件夹 | `<skill_name>_<timestamp>` | `<input_dir>` 下 |
| 提取文本 | `extracted_text_<timestamp>.txt` | `<work_dir>` 下 |
| 章节 JSON | `sections_<timestamp>.json` | `<work_dir>` 下 |
| 审查意见 JSON | `reviews_<timestamp>.json` | `<work_dir>` 下 |
| 审查版 docx | `<input_stem>_ReviewOut_<timestamp>.docx` | `<input_dir>` 下 |
| 汇总报告 | `<input_stem>_review_report_<timestamp>.md` | `<input_dir>` 下 |

## 技术架构

```
checking-patdocx-cn-single-agent/
├── SKILL.md                          # 本文件
├── scripts/
│   ├── __init__.py
│   ├── document.py                   # Document 类（OOXML 编辑）
│   ├── utilities.py                  # XMLEditor 基类
│   ├── doc_converter.py              # .doc 转 .docx（pywin32 COM 自动化）
│   ├── patent_extractor.py           # 专利文本提取与章节分割脚本
│   ├── review_adder.py               # 审查意见批注添加脚本（必须使用）
│   ├── verify.py                     # 内容完整性验证脚本
│   └── templates/                    # 批注相关 XML 模板
├── ooxml/
│   └── scripts/
│       ├── unpack.py                 # docx 解压
│       ├── pack.py                   # docx 打包
│       └── validation/              # 验证工具
├── 审查规则/                          # 13 条审查规则文件
├── 参考/                             # 参考文档（渐进式披露）
│   ├── reviews_json_schema.md        # 审查意见 JSON Schema 说明
│   └── report_template.md            # 审查意见汇总报告模板
└── requirements.txt
```

## 依赖

- Python 3.10+
- defusedxml
- lxml
- python-docx
- pywin32（用于 .doc 转 .docx，仅 Windows + Microsoft Word 环境需要）

