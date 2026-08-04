> **预检。**进入本步骤前应已完成上一步骤。**SKILL.md 管辖每一步的纪律；如果本会话中尚未完整阅读 SKILL.md，停止并先 `Read('SKILL.md')` 再继续。** SKILL.md 中的硬性规则同样适用于本步骤。**在聊天模式中（无工作区文件夹、无自动管理的待办列表）同样的纪律适用——不要略读本步骤文档，不要捆绑批次，不要跳过底部的逐步骤内部合规检查。** **如果本轮对话始于压缩后的转录，压缩摘要不视为已阅读本步骤文档——在任何工具调用前现在完整 `Read()` 它。**

### 步骤 8：翻译辅助 XML 文件——强制性

*[内部合规检查——不要向用户复述或转述。在执行前重新阅读本步骤中的每一条规则。不要偏离技能的任何一行。不要捆绑工作、跳过检查或"为效率而解释"——每一次此前的偏离都产生了低于技能设计应交付质量水平的输出。无论如何，技能的硬性门禁都会阻止偏离；提前合规总比撞上门禁并重写 paragraphs.json 更快。]*

OOXML 将列表编号、页眉、页脚、批注、脚注和尾注存储在 `word/document.xml` 之外的单独 XML 文件中。主翻译流程（步骤 2-7）只处理 `document.xml`——每个辅助文件都必须在本步骤中单独翻译。在步骤 9（质量检查）之前运行所有适用的小步骤，以便 QC 遍历也扫描辅助文件。

> **绝不将辅助 XML 部件（`comments.xml`、`footnotes.xml`、`endnotes.xml`、`headerN.xml`、`footerN.xml`、`numbering.xml`）经由 Python 的 `xml.etree.ElementTree` 往返处理。不要头嫁接，不要命名空间注册，完全不要。**使用随附的命名空间安全脚本之一，或 `lxml`（保留前缀），或仅在 `<w:t>` / `<w:delText>` 标签之间替换文本的纯正则方法。解释见下文"ElementTree 损坏辅助 XML"陷阱。

#### 步骤 8a：翻译编号格式字符串——强制性（如果 numbering.xml 存在）

```bash
python <skill-path>/scripts/translate_numbering.py \
  <original_source_language>.docx \
  <workdir>/final/word/numbering.xml \
  --language <source-language>
```

`word/numbering.xml` 定义列表和标题编号。每个级别有一个 `w:lvlText`，其 `w:val` 属性是渲染后的前缀字符串。如果这些字符串包含源语言词汇（匈牙利语 `%1. sz. Melléklet` = "Schedule %1"），输出会在附表标题、附录标题和章节标题上显示混合语言编号。

脚本从格式字符串自动检测源语言，并应用内置翻译映射（匈牙利语、意大利语、德语、法语、西班牙语、葡萄牙语、荷兰语、波兰语、芬兰语）。如果自动检测失败，传递 `--language`。

**不要跳过。**混合语言编号（"1. sz. Melléklet" 而非 "Schedule 1"）立即可见。如果脚本报告 "No word/numbering.xml found"（未找到 word/numbering.xml）或 "No translatable format strings found"（未找到可翻译的格式字符串），文档不需要此步骤——干净退出。

#### 步骤 8b：翻译页眉和页脚——强制性（如果有任何源语言文本）

OOXML 将页面页眉/页脚存储在单独的 `word/header1.xml`、`word/footer2.xml` 等文件中。它们通常混合标准样板（签名栏、水印、角色标签）和自由文本内容（协议标题如 `Samenwerkingsovereenkomst`、版本标签如 `Versie DRAFT 1 – juli 2021`、首字母签注栏标签如 `Parafen`、月份名称、水印）。使用搭建 + 应用往返。

**8b.1 — 提取。**

```bash
python <skill-path>/scripts/translate_headers_footers.py \
  <original_source_language>.docx \
  --extract <workdir>/headers_footers.json
```

为每个非空页眉/页脚段落写入一个 JSON 条目，含源文本、运行元数据和空 `en` 字段。纯页码和仅制表符的行被跳过。打印英文直通提醒：将英文源文逐字复制到 `en`，不改写。

**8b.2 — 翻译 JSON。**使用与正文段落相同的词典和判断为每个条目填写 `en`：

- **默认翻译每个源语言标记。**协议标题（`Samenwerkingsovereenkomst → Cooperation Agreement`）、文档属性标签（`Versie → Version`、`Pagina → Page`）、月份名称（`juli → July`、`styczeń → January`）、草稿/保密水印（`CONCEPT/BOZZA/ENTWURF/PROJET/BORRADOR/MINUTA/TERVEZET/PROJEKT/LUONNOS → DRAFT`；`VERTROUWELIJK/RISERVATO/VERTRAULICH/CONFIDENTIEL/CONFIDENCIAL/POUFNE/BIZALMAS/LUOTTAMUKSELLINEN → CONFIDENTIAL`）、首字母签注栏标签（`Parafen/Parafy/Paraphes/Paraphen/Sigle/Rúbricas/Parafę → Initials`）、签名栏中的角色标签。
- **仅保留专有名词和代码。**项目名称、实体字符串（`Acme Energy Europe B.V.`、`Acme s.r.l.`）、参考代码（`RRF-6.5.1-23`）、缩写（`EUR`、`HUF`、`RRF`）、日期、页码。对于保留的条目，设置 `en == text` 或留为 `null`。
- **英文源文原样直通。**与步骤 4 相同的规则。
- `en == null` 或 `en == ""` 的条目在应用时逐字保留。

**8b.2a — 字段占位符（`<<PAGE>>`、`<<NUMPAGES>>`……）——强制性。**

某些页眉/页脚段落包含 Word *域代码*——运行时求值的占位符，如 `PAGE`（当前页码）、`NUMPAGES`（总页数）、`DATE`（今天日期）、`TIME`、`FILENAME`、`AUTHOR` 等。在 OOXML 中，域编码为一系列运行：

```
<w:fldChar fldCharType="begin"/>  ... <w:instrText> PAGE </w:instrText>
... <w:fldChar fldCharType="separate"/>  <w:t>2</w:t>   <-- cached result
... <w:fldChar fldCharType="end"/>
```

缓存结果（上例中的 `2`）是 Word *当前显示*的内容，每次用户打开文件时重新求值。将该缓存数字视为静态文本并用翻译后的英文覆盖会破坏域——新英文落在错误的运行中，渲染时 Word 重新计算域并产生可见的乱码，如 `Page 2 of 27`（其中 `27` 是正确总数，但布局已损坏，因为静态的 "of" 被丢弃了）。

提取步骤（`translate_headers_footers.py --extract`）检测域，并将每个缓存结果作为占位符标记发出到 `text` 字段中——例如，挪威语页脚 `Side 2 av 2`（其中 `2` 和 `2` 都是缓存域结果）被提取为：

```
"text": "Side <<PAGE>> av <<NUMPAGES>>"
```

**占位符必须在 `en` 字段中逐字保留。**翻译静态环境文本，将 `<<...>>` 标记保持不变：

```
"en": "Page <<PAGE>> of <<NUMPAGES>>"
```

应用步骤将每个 `<<TYPE>>` 替换回原始域结构（`begin / instrText / separate / cached_result / end`），因此 Word 在打开时重新求值域并渲染正确的实时页码。如果你意外翻译了占位符（如写 `Side 2 av 2 → Page 2 of 2` 带字面数字），应用步骤会将字面 `2` 和 `2` 写入静态运行，域结构为空，渲染后的页脚将*永远*显示*字面*数字——绝不会随真实页数更新。相应的域缓存运行变成孤儿空文本，产生上文描述的可见乱码。

识别的占位符类型包括 `<<PAGE>>`、`<<NUMPAGES>>`、`<<SECTIONPAGES>>`、`<<DATE>>`、`<<TIME>>`、`<<CREATEDATE>>`、`<<SAVEDATE>>`、`<<PRINTDATE>>`、`<<FILENAME>>`、`<<AUTHOR>>`、`<<TITLE>>`、`<<SUBJECT>>`、`<<HYPERLINK>>`、`<<REF>>`、`<<PAGEREF>>`。如果在 `text` 中看到 `<<...>>` 标记，将其精确复制到 `en` 中——绝不展开、翻译或重排其内部字母。

**8b.3 — 应用。**

```bash
python <skill-path>/scripts/translate_headers_footers.py \
  <original_source_language>.docx \
  <workdir>/final \
  --apply <workdir>/headers_footers.json
```

将翻译后的 `word/header*.xml` / `word/footer*.xml` 写入 `<workdir>/final/word/`，逐字节保留运行级属性（`w:sz`、`w:rFonts`、`w:color`、`w:b`、`w:i`、域代码、制表位、换行）。步骤 10（重新打包）通过 `--headers-footers-dir` 拾取这些文件。

**旧式仅字典回退。**对于仅水印文档，保留旧模式 `--language <lang>`——快速，但只能翻译其内置字典中的标记。优先使用搭建往返。

#### 步骤 8c：翻译批注——强制性（如果 word/comments.xml 存在）

```bash
# 1. 列出源批注以便起草翻译
python <skill-path>/scripts/translate_comments.py <original>.docx --list

# 2. 将翻译保存到按批注 ID 键控的 JSON 文件中：
#    {
#      "19": "To be named as \"the Plots\"?",
#      "29": "To be discussed with Acme",
#      ...
#    }

# 3. 生成翻译后的 comments.xml
python <skill-path>/scripts/translate_comments.py \
    <original>.docx <workdir>/final \
    --translations <workdir>/comments_translations.json
```

`word/comments.xml` 保存 Word 的页边批注。高度可见，且经常被遗漏翻译。脚本使用纯正则，因此不会触碰任何命名空间前缀。与 8b.1 相同的英文直通提醒：如果批注已是英文，逐字复制源文。步骤 10（重新打包）通过 `--comments` 拾取翻译后的 `comments.xml`。

#### 步骤 8d：翻译脚注 / 尾注——强制性（如果存在）

没有随附脚本（脚注/尾注在法律草稿中罕见），但同样的仅正则规则适用：不要使用 ElementTree。在 `<w:t>` / `<w:delText>` 元素内使用纯正则文本替换，或使用 `lxml`。最小模板：

```python
import re, zipfile

_WT = re.compile(r'(<w:t(?:\s[^>]*)?>)([^<]*)(</w:t>)')
_WDT = re.compile(r'(<w:delText(?:\s[^>]*)?>)([^<]*)(</w:delText>)')

with zipfile.ZipFile('<original>.docx') as z:
    xml = z.read('word/footnotes.xml').decode('utf-8')

# translations: dict mapping exact source w:t text -> English
def rewrite(m):
    op, txt, cl = m.group(1), m.group(2), m.group(3)
    return op + translations.get(txt, txt) + cl

xml = _WT.sub(rewrite, xml)
xml = _WDT.sub(rewrite, xml)

with open('<workdir>/final/word/footnotes.xml', 'w', encoding='utf-8') as f:
    f.write(xml)
```

仅替换文本内容；每个命名空间声明、前缀、rsid 和段落 ID 逐字节通过。

**不要跳过辅助翻译步骤。**编号、页眉、页脚、批注、脚注或尾注中的源语言文本是高严重性缺陷——它要么在每一页上可见（编号、页眉、页脚），要么包含实质性法律内容（批注、脚注）。评分：步骤 8 的输出在标准 5（完整性）下被扣分，如果有任何源语言标记存活则上限为 7。`w:delText` 内的批注在标准 13（修订追踪保真度）下被扣分。

### 步骤 9：运行质量检查——强制性

*[内部合规检查——不要向用户复述或转述。在执行前重新阅读本步骤中的每一条规则。不要偏离技能的任何一行。不要捆绑工作、跳过检查或"为效率而解释"——每一次此前的偏离都产生了低于技能设计应交付质量水平的输出。无论如何，技能的硬性门禁都会阻止偏离；提前合规总比撞上门禁并重写 paragraphs.json 更快。]*

```bash
python <skill-path>/scripts/quality_check.py <workdir>/final/word/document.xml \
  --verbose --with-source <workdir>/paragraphs.json --variant uk \
  --aux-dir <workdir>/final
```

**`--aux-dir` 是且强烈推荐。**它指向包含翻译后 `word/numbering.xml`、`word/headerN.xml`、`word/footerN.xml` 和 `word/comments.xml` 的目录（通常为 `<workdir>/final`）。使用此标志，quality_check 还会扫描步骤 8 产生的每个辅助文件中的源语言残留。没有它，页眉 / 页脚 / 编号 / 批注中的仿译和未翻译文本会完全溜过 quality_check（只有 `repack_docx.py` 内部的重新打包后扫描会捕获它们，而该扫描覆盖的规则类别更少）。

**变体标志——使用与步骤 6 相同的变体。** `--variant uk` 是硬编码默认值。仅当步骤 6 以 `--variant us` 运行时才传递 `--variant us`，而后者本身要求用户的原始提示明确要求美式英语。步骤 6 和步骤 9 之间变体不匹配会产生误报"拼写违规"。

审查输出。关键检查：
- `<source_language>_remnants` — document.xml 中有源语言文本？
- `aux_<filename>` — 辅助文件中有源语言文本？
- `numbering`、`truncation`、`formatting`、`definition_order` — document.xml 中的结构缺陷。

**在步骤 10（重新打包）之前，检查应报告 0 个问题。**如果报告了问题，回到相关的前一步骤（正文问题回 paragraphs.json；辅助文件问题回辅助 JSON / 源文件），修复，然后按顺序重新运行步骤 5-9。

**不要为了满足 QC 启发式而静默剥离语义内容。**当 QC 模式标记一个实际是源文忠实翻译的段落时——最常见的是列表连接词如 `; and` / `, and`（意大利语 `; e` 的忠实翻译）——正确的回应是对照源文检查该标记，**而非**修改翻译以让脚本安静。截至 rev34，截断检查有内置白名单，自动抑制 `; and` / `, and` / `; or` / `, or` 误报。如果未来的 QC 标记被证明是类似的误报（源文支持所写的翻译），保留忠实翻译，在交付说明中记录误报，然后继续。达到 0 个问题值得追求，但绝不以保真为代价。见 SKILL.md 常见陷阱——"译者修改忠实于源文的翻译以满足 QC 检查器"。

### 步骤 9 是强制性的——绝不跳过它

`quality_check.py` **不是可选的**。它在每份文档的步骤 9 运行，包括多文档会话中的每份文档。如果脚本因任何原因无法运行——包括疑似安装流程截断——**不要跳过步骤 9 并照常交付**。相反：

1. 运行 `python <skill-path>/scripts/quality_check.py --help` 查看完整性检查是否触发（rev35 添加了带哨兵 `# === SKILL FILE COMPLETE ===` 的 `_check_self_integrity()` 守卫）。如果报告 `FILE INTEGRITY CHECK FAILED — script truncated`（文件完整性检查失败——脚本被截断），本地安装已损坏——从 .skill / .zip 归档重新安装技能并重试。
2. 如果脚本运行但中途出错，修复错误（paragraphs.json 格式错误、document.xml 未找到等）并重新运行。
3. **当步骤 9 因脚本损坏而被跳过时，不要交付翻译。**阻止交付直到 QC 干净运行。apply.py 和 repack.py 内部自动调用的门禁不能替代 QC——它们捕获的是不同类别的缺陷。

## 内部合规检查 — 08-aux-and-quality

在进入下一步之前，确认：

- [ ] 你翻译了步骤 8 中标记的每个辅助 XML 文件（页眉、页脚、批注、脚注、尾注）
- [ ] 你运行了 `quality_check.py` 且运行干净（无完整性检查失败、无 Python 错误）。如果运行不干净，你未继续交付——你重新安装或修复了输入。
- [ ] 你处理了 `quality_check.py` 标记的任何源语言残留
- [ ] 你未断定某个辅助文件"微不足道"而跳过翻译它
- [ ] 如果 QC 标记了一个段落而你"修复"了它，该修复保持了源文保真（你未静默剥离连接词、介词、定义词或其他语义内容以满足检查器）

如果任何检查不确定，停止。重新阅读本文件。不要继续。

**下一步：** `skill-docs/10-repack-and-validate.md`
