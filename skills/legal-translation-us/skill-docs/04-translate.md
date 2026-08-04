> **预检。**你应在完成上一步后进入本步骤。**SKILL.md 管辖每个步骤的纪律；如果本会话尚未完整阅读 SKILL.md，停止并在继续前 `Read('SKILL.md')`。**SKILL.md 中的硬规则同样适用于本步骤。**在聊天模式（无工作区文件夹、无自动管理的待办列表）下，同样的纪律适用——不要略读本步骤文档，不要合并批次，不要跳过底部的分步内部合规检查。**如果本轮始于压缩后的记录，压缩摘要不视为已阅读本步骤文档——在任何工具调用前立即完整 `Read()` 它。**

### 步骤 4：翻译所有段落

*[内部合规检查——不要向用户复述或转述。执行前重新阅读本步骤中的每条规则。不要偏离技能的任何一行。不要合并工作、跳过检查或“为效率而变通”——以往的每次偏离都产生了低于技能设计质量要求的输出。技能的硬门禁无论如何都会阻止偏离；事先合规总是比撞上门禁后重写 paragraphs.json 更快。]*

**技能全范围硬规则适用于本步骤。**完整规则块见 SKILL.md。在步骤 4 中最咬人的规则：每批 ≤35 段（由 `validate_translations.py` 强制执行）、翻译时每个段落的完整 `text` 字段必须在你的上下文窗口中、每个定义部分段落必须填写 `en_runs`（在步骤 5 开始时由 `validate_en_runs.py` 强制执行）。

通过填写 JSON 中的 `"en"` 字段，翻译**每个非空段落**。

```json
{
  "idx": 42,
  "text": "\"Evento Rilevante Potenziale\" indica ciascun evento...",
  "runs": [
    {"start": 0, "end": 1, "text": "\"", "bold": false, "italic": false},
    {"start": 1, "end": 31, "text": "Evento Rilevante Potenziale", "bold": true},
    {"start": 31, "end": 95, "text": "\" indica ciascun evento...", "bold": false}
  ],
  "en": "\"Potential Event of Default\" means any event which...",
  "en_runs": [
    {"start": 0, "end": 1, "bold": false},
    {"start": 1, "end": 27, "bold": true},
    {"start": 27, "end": 80, "bold": false}
  ]
}
```

#### 翻译规则

1. **翻译完整段落，而非片段。**你有完整句子上下文——利用它。

2. **精确保留段落边界。**一段源段落 = 一段英文段落。绝不合并或拆分段落。每个段落从其原始位置继承格式（样式、编号级别、缩进）。拆分或合并会破坏这种对齐。

3. **为以下段落提供 `en_runs`：源 `runs` 数组显示文本为粗体的任何段落，以及定义部分中的每个段落或样式提供粗体的标题段落。**`apply_translations_textmatch.py` 内部的自动检测器只处理带显式引号的经典 `"X" means …` 定义形状。它会漏掉序言中定义词圆括号（`(the "Agreement")`、`(hereinafter the "Substation")`）、当事方块定义词、附表清单以及任何*包含*粗体引号片段但不是教科书式定义行的正文段落上的粗体。对所有这些，显式填写 `en_runs`——在你的 `en` 字符串中定位每个粗体引号短语，并为其发出 `{"start": …, "end": …, "bold": true}`。

   **样式提供的粗体。**定义部分和条款/条款标题经常从*段落样式*获得粗体（例如 `FWBL1`、`ITScheduleL1`、`styles.xml` 中 `<w:rPr>` 携带 `<w:b/>` 的定制模板样式），而 run 级 `<w:rPr>` 为空。`extract_paragraphs.py` 只读取 run 级格式，因此即使渲染出的源是粗体，`runs[i].bold` 也是 **`false`**。如果只对这些段落提供 `en` 而让 `en_runs` 为 null，`apply_translations_textmatch.py` 的默认关闭覆盖（存在目的是防止样式粗体从 `basedOn` 父级泄漏进正文段落）将*剥离*样式的粗体，标题或定义将渲染为纯文本。通过 run 级粗体之外的结构线索识别这些段落：

   **限定词——击败样式的 run 级覆盖。**有些作者在标题段落的每个 run 上应用直接的 run 级 `<w:b w:val="0"/>` 和/或 `<w:i w:val="0"/>` 覆盖，专门为了抑制该段落的样式继承粗体或斜体（典型模式：Heading3 样式提供粗斜体，但作者想让这个*特定*标题渲染为纯文本，因此在 run 级覆盖）。此时，渲染出的源是**纯文本**，而非粗体/斜体，发出 `en_runs:bold=true` 会*过度加粗*翻译——与上述粗体不足缺陷相反。
   
   决策规则，按段落应用：
   
   - 如果段落位于定义部分 / 具有标题样式**且** **至少一个** run 显示 `runs[i].bold = true`：发出 `en_runs`，`bold: true`（防粗体不足——原规则）。
   - 如果段落位于定义部分 / 具有标题样式**且** **每个** run 都显示 `runs[i].bold = false`（即每个 run 都携带显式 run 级覆盖）：发出 `en_runs`，`bold: false`。作者已选择击败样式的粗体；尊重该选择。
   - 同一规则对斜体对称适用：仅当至少一个 run 显示 `runs[i].italic = true` 时发出 `italic: true`；如果每个 run 都显示 `runs[i].italic = false`，发出 `italic: false`。
   - 粗体和斜体相互独立——一个段落可以纯粗体（斜体被覆盖关闭、粗体从样式继承）或仅斜体（粗体被覆盖关闭、斜体保留）。对每个属性分别按相同的逐属性“任一 run 为 true → true；全部 run 为 false → false”规则决定。
   
   为什么这样有效：当每个 run 都有显式 `false` 覆盖时，Word 渲染的是 run 级属性。当*没有* run 有任何覆盖时（所有 `runs[i].bold` 都为 `false`，因为 run 级 `<w:rPr>` 是静默的），样式继承的粗体胜出。两种情形在 `extract_paragraphs.py` 的输出中都产生 `runs[i].bold = false`（提取只读 run 级，无法区分“静默”与“显式 false”），因此在静默情形下仍需要结构线索来发现定义部分——但*所有 run 都粗体为 false* 的检查能唯一识别显式覆盖情形，并排除错误的粗体发出。

   **段落标记覆盖（`p_rpr_b` / `p_rpr_i`）——最强的信号。**有些作者在*段落标记*（`<w:pPr><w:rPr><w:b w:val="0"/><w:i w:val="0"/></w:rPr></w:pPr>`）而非逐 run 应用粗体/斜体覆盖。此模式在挪威语/斯堪的纳维亚语草稿中常见——Heading3 默认渲染为粗斜体，但选定的段落有意为纯文本。提取只读 run 级，因此所有这些段落在 `runs` 数组中看起来相同。自 rev38 起，`extract_paragraphs.py` 还将段落标记设置捕获为 JSON 条目上的三态字段：
   
   - `p_rpr_b == "false"`（或 `p_rpr_i == "false"`）——作者显式关闭了该段落的样式继承粗体（或斜体）。无论该段落原本是否会被视为标题，都发出 `en_runs:[{...,"bold": false, ...}]`（或 `italic: false`）。
   - `p_rpr_b == "true"`——作者显式打开了段落标记粗体。发出 `bold: true`。（斜体同理。）
   - 字段缺失——无段落标记设置；由 pStyle 级联决定。应用上述标题规则和所有 run 粗体为 false 的限定词。
   
   标题的决策优先级（按顺序应用，首个匹配停止）：
   1. `p_rpr_b == "false"` ⇒ 发出 `bold: false`（段落标记胜出）
   2. `p_rpr_b == "true"` ⇒ 发出 `bold: true`（段落标记胜出）
   3. 任一 run 显示 `runs[i].bold == true` ⇒ 发出 `bold: true`
   4. 每个含文本的 run 都显示 `runs[i].bold == false` 且无 `p_rpr_b` 且段落为标题样式 ⇒ 发出 `bold: true`（样式级联胜出；静默 rPr 情形）
   5. 否则 ⇒ 发出 `bold: false`
   
   同一五条规则对斜体使用 `p_rpr_i` 和 `runs[i].italic` 对称且独立适用。粗体和斜体分开决定——一个段落可以纯粗体、仅斜体、两者兼备或两者皆无。

   - **定义部分**通常有标签——一个读作 `Definitions`、`Defined Terms`、`Definitions and Interpretation`、`Interpretation` 的节标题段落，或前缀为 `Article 1`、`Clause 1`、`Section 1`，或标为 `Definitions` 的编号附件。此类部分的正文段落遵循谓词模式 `Term : means / shall mean / has the meaning given to it in / indicates / signifies`，术语周围可带可不带引号。
   - **条款/条款标题**可通过其段落样式识别（任何不属于标准 `Normal` / `BodyText` / `Default` 集合的 `pStyle` 值——特别是 `FWBL1`、`ITScheduleL1`、`Heading1`、`FWHeader` 等定制模板样式），或通过其结构形状识别（短、全大写或首字母大写、无句号结尾）。

   遇到任一模式时，为该部分中的每个段落填写 `en_runs`，即使源 `runs` 数组未显示粗体。对粗斜体定义词的定义，发出
   `[{"start": 0, "end": <term_end>, "bold": true, "italic": true},
   {"start": <term_end>, "end": <text_len>, "bold": false, "italic": false}]`。
   对由样式渲染为粗体的标题段落，发出
   `[{"start": 0, "end": <text_len>, "bold": true}]`。

   仅当源 `runs` 数组未显示粗体**且**段落不在定义部分**且**其 `pStyle` 是正文样式时，`en_runs` 才可为 null。有疑问时，应用上述限定词——检查是否**每个** run 都有 `runs[i].bold = false`（斜体同理）。如果是，发出 `en_runs:[{...,"bold": false, "italic": false}]` 以*击败*作者显式抑制的样式继承粗体/斜体。如果至少一个 run 显示粗体或斜体为 true，发出这些属性为 true。“默认提供 en_runs”的建议在精神上正确（规范不足会从真正粗体的标题上剥离粗体），但你必须按限定词用**正确的**粗体/斜体值填写 `en_runs`——过度加粗作者有意渲染为纯文本的段落，与对真正粗体标题粗体不足一样是明显缺陷。

4. **使用参考文件中领域合适的英文法律词汇表。**

5. **保持定义词一致**——每次翻译相同。

6. **自然的英文语序**：“all existing and future plants”而非“plants existing and future”。

7. **英文法律交叉引用惯例**：“this Deed”、“Section 2”（美式默认）或“Clause 2”（英式）——内部引用绝不使用“Article 2”；用“above”/“below”（而非“that precedes”/“that follows”）。

7a. **日期格式——美式默认 = `Month Day, Year`。**当源文件有文字形式的日期（`8 giugno 2053`、`15 huhtikuuta 2026`、`21 de mayo de 2004`）时，用美式英语渲染为 `June 8, 2053` / `April 15, 2026` / `May 21, 2004`——而非 `8 June 2053`。这适用于英文输出中的每个日期，无论源文件如何排列日月年。纯数字日期代码（注册号或数字表格单元格内的 `08.06.2053`）保持原样。方括号占位日期（`[15.1.2021]`）**必须**翻译为美式文字形式（`[January 15, 2021]`），不得保留源语言数字形式。对于嵌入碎片化跟踪更改段的日期，如果日/月顺序必须在接受全部与拒绝全部视图之间翻转，见“混乱 / 字符碎片化整词编辑”小节的选项 B——将完整英文日期放在簇的第一个 ins/del 上，簇的每个其他段为 `"en": ""`。在 `--variant uk` 下，使用 `Day Month Year`（`8 June 2053`，`April 15` → `15 April`）。

7b. **附件标签——Schedule 是安全的美式默认。**将源附件词（`liite`、`Bijlage`、`Allegato`、`Annexe`、`Anlage`、`anexo`、`załącznik`、`melléklet`、`附件`、`別紙`）渲染为 `Schedule N`（美式和英式均适用）。`Exhibit N` 在美式中也可接受，尤其用于并购文件。避免以 `Appendix N` 作为主要标签，尽管它被列为可接受——Schedule 是两种变体下的标准法律起草形式。

8. **英语变体：默认美式。**仅当用户原始提示明确要求时才用英式英语。完整防漂移规则和决策点列表见下文“目标英语变体”部分——有疑问时用美式。

9. **对空段落**（仅空白），将 `en` 设为相同的空白。

10. **对纯结构性文本**（当事方名称、地址、注册号），以最小改动复制——翻译描述，但名称/数字保持原样。

11. **对“SCHEDULE B”或“ALLEGATO 1”之类的页/节页眉**，翻译页眉文本。

12. **将标题和页眉保持在页面宽度内。**封面页标题和节标题从原始文件继承固定字体大小和缩进。如果英文翻译明显长于源文，可能溢出页面边界而不可见。缩写或重构以保持在可比较的字符长度内。

13. **绝不缩写、摘要或压缩段落。**英文翻译必须包含源段落的所有实质性内容，包括：所有百分比和数值、所有货币金额（数字和文字形式）、所有定义词及其圆括号定义、所有上限金额和阈值、所有时间期限和截止日期、所有交叉引用。如果源段落写明“每周 1%，上限 15%”，翻译**必须**写明“每周 1%，上限 15%”。如果源文件以数字和文字两种形式规定合同价格，翻译**必须**包含两者。从翻译中省略商业条款是使文档无法使用的关键错误。

14. **数字和字母词之间始终留空格。**法律英语在数字和其修饰的词之间放一个空格：写 `Section 5` / `500 euros` / `12 months` / `3 business days`，绝不写 `Section5` / `500euros` / `12months`。三个例外：英语序数词不加空格（`1st`、`2nd`、`3rd`、`4th`、`21st`）；一两个字母的紧凑单位缩写可直接跟在数字后（`5km`、`10kg`、`500ml`、`24h`）；众所周知的缩写加数字标记连写（`A4`、`MP3`、`H2O`、`B2B`、`3G`）。其他一切都要空格。有疑问时，插入空格——应用前检查器（`validate_segment_shapes.py`）会标记最常见的违规，但仅作为警告；对此类缺陷的主要防御是翻译时就做对。

**设计阶段术语（对施工/EPC 合同至关重要）：**

三阶段设计层级必须正确翻译：

| 设计阶段 | 正确英文 | 应避免的常见错误 |
|---|---|---|
| 阶段 1（概念性） | Preliminary Design | — |
| 阶段 2（中间性） | Detailed Design | “Preliminary Design”（错误阶段）、“Definitive Project”（借译） |
| 阶段 3（可施工性） | Construction Design | “Executive Project”（借译） |

弄错这些（尤其将阶段 2 与阶段 1 混淆）是实质性错误。

#### en_runs 的格式规则

- **定义词**（定义段落中引号内的文本）：`bold: true`
- **节标题**：从段落样式继承格式（通常通过 pPr 加粗）
- **其他一切**：`bold: false, italic: false`

如果不提供 `en_runs`，应用脚本自动检测定义词并应用粗体。这对简单定义有效，但可能漏掉复杂情形。

#### 分批工作 — 强制规模限制（最多 35 段）

**硬限制：每批最多 35 段。无例外。**

该限制同等适用于第 1 批、第 5 批和第 15 批。一个已知失败模式是批次规模随翻译推进而攀升——头几批为 30-35 段，然后为“更快完成”，后续批次静默增长到 50、60、80+ 段。**这是不允许的。**大批次的质量代价对你不可见但真实存在：截断条款、定义词细节被跳过、术语不一致、转述而非翻译的文本。这些错误会累积，且事后很难捕获。

**开始每批前，明确说明段落范围**（例如“批次 4：第 106-140 段，35 段”）。如果剩余段落超过 35 段，你必须将其拆分为多个批次——不要因为“只剩 50 段”就一次全译。

每批：翻译、将 JSON 保存为检查点，然后在继续前验证。

**关键：查看时绝不截断段落文本。**显示待翻译段落时，你必须看到每个段落的完整 `text` 字段。不要使用 `text[:200]` 或 `p['text'][:120]` 这类带字符限制的 Python 预览命令。始终显示完整文本。超过 300 字的段落通常包含出现在段落后半部分的关键商业术语——费率、上限、金额、括号内定义词——截断将静默丢失它们。

每批后运行验证脚本，在继续前捕获截断的翻译：

```bash
python <skill-path>/scripts/validate_translations.py <workdir>/paragraphs.json
```

这检查每个段落的源文与目标文的字符比率。如果任何段落被标记为可能截断（超过 150 字的段落比率低于 0.6），在进入下一批前重新阅读完整源文本并重新翻译。

**变体扫描（逐批，rev45b）。**发布一批前，重新阅读你刚写的英文，查找错误变体形式。在 `--variant us`（默认）下，查找英式拼写；在 `--variant uk` 下，查找美式拼写。历史上 `post_process.py` 中的高频替换字典漏掉的常见长尾失误包括：`plough/plow`、`whilst/while`、`amongst/among`、`learnt/learned`、`spelt/spelled`、`dreamt/dreamed`、`burnt/burned`、`spoilt/spoiled`、`aluminium/aluminum`、`manoeuvre/maneuver`、`cheque/check`、`kerb/curb`、`tyre/tire`、`mould/mold`、`storey/story`、`sceptic/skeptic`、`enquire/inquire`、`ageing/aging`。rev45b 对 `US_SPELLING` 的扩展和 `quality_check.py` 的英式拼写列表现在机械地捕获所有这些，但逐批自扫描是主要防御，因为它在翻译时就阻止失误，而非依赖后处理。SKILL.md“不要询问用户”#1 中的常设规则是**政策**；本逐批检查清单行是**执行**。

#### 附录：仅限含跟踪更改的文档——若没有任何段落含跟踪更改则跳过

> **如果文档中没有段落含跟踪更改，跳过以下全部内容（直到步骤 4b）。**如果 `extract_paragraphs.py` 报告 `paragraphs.json` 中有任何 `has_track_changes: true` 的段落（或你在 `word/document.xml` 中看到 `<w:ins>` / `<w:del>` 元素），则文档有跟踪更改。如果两者都不成立，跳到步骤 4b——步骤 4 的其余小节不适用。
>
> **如果任何段落含跟踪更改，阅读以下全部内容。**对含跟踪更改的文档，下面每个跟踪更改小节都是强制性的。

#### 跟踪更改段落 — 强制双重翻译

包含跟踪更改（JSON 中 `has_track_changes: true`）的段落需要**两**份翻译：

1. **`en`** — `text` 字段的翻译（“已接受”文本：读者在接受所有更改后看到的内容）。这是你对每个段落所做的正常翻译。

2. **`en_deleted`** — `deleted_text` 字段的翻译（红线视图中显示的带删除线文本）。此文本代表作者编辑时删除的内容。

两份翻译都是必需的，因为应用脚本分别处理这两条文本流：`en` 分配到 `w:t` 元素（当前/可见 run），而 `en_deleted` 分配到 `w:delText` 元素（已删除 run）。如果只提供 `en` 而让 `en_deleted` 为空，删除的文本保持源语言——任何查看跟踪更改的读者都会立即看到，这是高严重度缺陷。

**如何翻译跟踪更改段落：**

遇到 `has_track_changes: true` 的段落时：

1. 阅读 `text` 字段——这是已接受/可见文本。正常翻译为 `en`。
2. 阅读 `deleted_text` 字段——这是带删除线的已删除文本。翻译为 `en_deleted`。删除的文本通常是已被插入文本替换的短语或条款。用与文档其余部分相同的风格和术语翻译。
3. **检查跟踪更改在语义上是否通顺。**翻译完两部分后，验证跟踪更改读起来自然：删除文本（带删除线）应代表旧版本，已接受文本应代表新版本。如果英文作为跟踪更改读不通（例如删除和插入不构成连贯的编辑），调整两份翻译直到更改读起来自然。

**示例：**

```json
{
  "idx": 45,
  "text": "The Developer shall be entitled to assign this Development Agreement",
  "deleted_text": "shall not be entitled to unilaterally",
  "has_track_changes": true,
  "en": "The Developer shall be entitled to assign this Development Agreement",
  "en_deleted": "shall not be entitled to unilaterally"
}
```

在 Word 中，这渲染为：“The Developer ~~shall not be entitled to unilaterally~~ shall be entitled to assign this Development Agreement”——一个连贯的跟踪更改，显示作者从禁止到许可的编辑。

**跟踪更改段落的粗体修复：**应用脚本自动对非标题跟踪更改段落中的所有 run 应用 `w:b val="0"`（关闭粗体）。这防止一种常见缺陷——`w:ins` run（从跟踪插入样式继承粗体）的粗体格式泄漏进翻译后的正文文本。你无需为此做任何特别的事——修复在应用脚本中自动完成。

**跟踪更改粗体关闭旁路（rev38）——当覆盖会过度剥离时。**上述粗体关闭覆盖以 `pStyle` 包含 `heading`/`title`/`cmsor`/`titre` 为键。以普通 Word 默认样式起草的文档——在日本合同和一些斯堪的纳维亚模板中常见，标题的粗体纯粹来自 run 级 `<w:b/>` 而非 Heading-N pStyle——对该检测器呈现的每个标题都是非标题。自 rev38 起，两个额外旁路防止覆盖剥离有意的粗体：

1. **操作者编写的粗体**——如果你发出的 `en_runs` 至少有一个条目的 `bold: true`，该段落跳过覆盖。作者意图胜出。
2. **源段落整体为粗体**——如果每个含文本的源 `runs[i]` 都携带 `bold: true`，则源文件通篇真正为粗体（强烈信号表明它确实是标题），覆盖自动跳过。

对无样式但真正为粗体且携带跟踪更改的标题，你可以依赖旁路 2（什么都不做——覆盖自我跳过），或显式发出 `en_runs: [{"start": 0, "end": <text_len>, "bold": true}]` 触发旁路 1。任一途径都保留标题在应用步骤中的粗体。

#### 分段感知跟踪更改翻译 — 对跟踪更改段落强制

`extract_paragraphs.py` 脚本为每个跟踪更改段落提取 `tc_segments` 数组。该数组按跟踪更改类型将段落分解为有序段：

```json
{
  "idx": 45,
  "has_track_changes": true,
  "tc_segments": [
    {"type": "regular", "text": "A Fejlesztő jogosult"},
    {"type": "del", "text": "egyoldalúan nem jogosult"},
    {"type": "ins", "text": "jogosult engedményezni a jelen Fejlesztési Keretszerződést"}
  ]
}
```

**你必须独立翻译每个段**，并在匹配的 `en_segments` 数组中提供翻译。每个条目必须与对应的 `tc_segments` 条目具有相同的 `type`，外加带英文翻译的 `en` 字段：

```json
{
  "en_segments": [
    {"type": "regular", "en": "The Developer"},
    {"type": "del", "en": "shall not be entitled to unilaterally"},
    {"type": "ins", "en": "shall be entitled to assign this Development Agreement"}
  ]
}
```

**为什么这很重要：**没有分段感知翻译，应用脚本按比例将英文文本分配到所有活动的 `w:t` 元素——忽略跟踪更改边界。这导致英文单词落在相对于 `w:ins`/`w:del` 边界的错误位置，用户接受或拒绝时产生读起来不连贯的跟踪更改。有了 `en_segments`，每个段的翻译只分配到自己的 run，保持跟踪更改语义完整。

**分段翻译规则：**

1. `en_segments` 中段的数量和顺序必须与 `tc_segments` **完全**匹配。
2. 每个 `en_segments[i].type` 必须等于 `tc_segments[i].type`。
3. 翻译每个段，使接受所有更改产生连贯句子，**并且**拒绝所有更改（只保留 `regular` + `del` 段）也读起来连贯。
4. 仍按前文提供 `en`（完整已接受文本）和 `en_deleted`——这些作为应用时段类型不匹配时的兜底。

**拒绝全部的语法——冠词和介词归属何处（强制阅读）**

规则 3（“拒绝所有更改也读起来连贯”）在实践中很容易违反。缺陷表现为流畅的接受全部阅读加上不合语法的拒绝全部阅读，因为一个语法正确性取决于相邻跟踪更改是否被接受或拒绝的英文单词，最终落在了错误的段中。

工作示例——一个跟踪更改 `<w:del>` 从英语需要两个名词前有“the respective”的条款中删除翻译为“respective”的词。错误拆分将定冠词同时放在常规范围和 del 中：

```
错误
  regular: " to "
  del:     "the respective "
  regular: "the addressees, and"

  accept-all: " to the addressees, and"              ← 读起来好
  reject-all: " to the respective the addressees, and"  ← "the respective the"
```

正确拆分将接受全部下必须消失的冠词移入 del，并让相邻常规范围以裸名词开头，拒绝全部下不需要冠词：

```
正确
  regular: " to "
  del:     "the respective "
  regular: "addressees, and"

  accept-all: " to addressees, and"                  ← 不合语法

正确（调整后）
  regular: " to the "
  del:     "respective "
  regular: "addressees, and"

  accept-all: " to the addressees, and"              ← 读起来好
  reject-all: " to the respective addressees, and"   ← 读起来好
```

**一般规则——冠词、介词以及任何语法正确性取决于相邻跟踪更改是否被接受或拒绝的词，必须位于 del 或 ins 内部，而非与其相邻的常规范围中。**同一规则适用于定义词短语边界：如果两个连续名词短语来自不同段，至少其中一个必须携带自己的前导冠词/逗号/空白，以便恢复被删除的短语不会与相邻常规短语冲突。

**机械执行。**调用 `apply_translations_textmatch.py` 之前，在填好的 `paragraphs.json` 上运行 `validate_reject_all.py`：

```bash
python scripts/validate_reject_all.py workdir/paragraphs.json
```

脚本为每个带 del/ins 的段落从 `en_segments` 重建接受全部和拒绝全部视图，并扫描两者中的双冠词（`the respective the`）、重复词、孤立介词、标点后接字母粘连、双空格、空括号/引号以及禁用搭配列表。通过重写有问题的段修复每个命中，使冠词/介词位于跟踪更改边界的正确一侧，然后重新运行。应用前需要干净运行。

**非拉丁文字源有额外的分段形状规则。**如果源语言使用非拉丁文字——中文、日文、韩文、泰文、老挝文、高棉文、西里尔文（俄语、保加利亚语、塞尔维亚语、乌克兰语等）、希腊文、阿拉伯文、希伯来文、天城文或任何其他——在写 `en_segments` *之前*阅读步骤 4 末尾的**仅限非拉丁文字源**附录。拉丁文字源（意大利语、荷兰语、西班牙语、法语、德语、波兰语、匈牙利语、芬兰语、葡萄牙语、捷克语、罗马尼亚语、越南语、丹麦语、瑞典语、挪威语、英语等）从源文件继承段间空白，可以完全跳过该附录。

在填好的 `paragraphs.json` 上运行 `validate_segment_shapes.py`，在 `apply_translations_textmatch.py` 运行前机械捕获分段形状违规（此步骤适用于每份含跟踪更改的文档，无论源语言为何）：

```bash
python scripts/validate_segment_shapes.py workdir/paragraphs.json
```

它与 `validate_reject_all.py` 互补：形状扫描器警告*预示*缺陷的*拆分*；拒绝全部扫描器捕获重建视图中的*语法*缺陷。两者在应用前都应干净运行。

**ins_then_del 段（幽灵跟踪更改）。**如果源 docx 包含内容仅为 `<w:del>` 的 `<w:ins>`（即作者 A 插入文本，然后作者 B 删除作者 A 的插入），提取步骤发出 `ins_then_del` 类型的段。接受全部和拒绝全部都将幽灵渲染为空，因此该段对可见英文没有任何贡献——但“显示标记”会把你写的任何英文显示为删除线。始终填写这些；将源语言留在那里是跟踪更改文档中最常见的静默残留。

#### 折叠纯正字法和错别字修正跟踪更改编辑 — 强制

源语言概念草稿中的常见模式是只修正**源语言**的跟踪更改——正字法、缩写风格、连字符、变音符号、拼写改革或简单错别字。这些编辑在目标语言中没有语义内容，因此没有有意义的翻译：删除和插入的文本都映射到**相同的英文字符串**。

该规则至少适用于以下类别，不限源语言：

1. **缩写风格**——荷兰语 `mn` → `m.n.`、意大利语 `ecc` → `ecc.`、法语 `cf` → `cf.`
2. **连字符**——荷兰语 `zonneenergie` → `zonne-energie`、荷兰语 `pro-actief` → `proactief`
3. **变音符号恢复**——荷兰语 `coordinaat` → `coördinaat`、法语 `a` → `à`、葡萄牙语 `nao` → `não`、西班牙语 `si` → `sí`
4. **拼写改革**——荷兰语 `pro-actief` → `proactief`（2005 年）、德语 `daß` → `dass`（1996 年）、葡萄牙语 `acção` → `ação`（2009 年）
5. **软连字符 / 行尾痕迹**——行断连字符被烘进文本时的 `voor-geschreven` → `voorgeschreven`
6. **错别字修正**——任何拼写错误修正为正确形式，两种形式翻译为**相同的英文单词**。例如意大利语 `contrato` → `contratto`（*合同*）、波兰语 `umowe` → `umowę`（*协议*）、德语 `Vetrag` → `Vertrag`（*协议*）。与 1-5 相同原则：在英文中消失的源语言编辑。

来自荷兰语概念草稿的真实示例，展示规则的实际运作：

| 源删除 | 源插入 | 编辑内容 | 英文删除 | 英文插入 |
|---|---|---|---|---|
| `mn` | `m.n.` | *met name* 的缩写——添加句点 | *in particular* | *in particular* |
| `pro-actief` | `proactief` | 2005 年荷兰语拼写改革 | *proactive* | *proactive* |
| `zonneenergie` | `zonne-energie` | 荷兰语三元音冲突——添加连字符 | *solar energy* | *solar energy* |
| `coordinaat` | `coördinaat` | 缺失分音符恢复 | *coordinate* | *coordinate* |
| `2` | `6` | 有意义的日期数字变更（“22”→“26 July”）——保持不同 | *2* | *6* |
| `voor-geschreven` | `voorgeschreven` | 行尾断行的软连字符 | *required* | *required* |

**规则：**当删除和插入的源段翻译为**相同的英文字符串**时——无论是由于正字法、变音符号、缩写、连字符、拼写改革还是简单错别字——给 `del` 和 `ins` 英文段**相同的英文翻译**。不要制造虚假的区分（那位在跟踪更改中写“proactive” ↔ “pro-active”的荷兰语译英译者，把一次无操作的荷兰语修正变成了可见但无意义的英文红线）。

这同时适用于 `en_segments` 和兜底 `en_deleted` / `en` 字段：

```json
{
  "idx": 14,
  "tc_segments": [
    {"type": "regular", "text": "combinatie met "},
    {"type": "del", "text": "zonneenergie"},
    {"type": "ins", "text": "zonne-energie"}
  ],
  "en_segments": [
    {"type": "regular", "en": "combination with "},
    {"type": "del", "en": "solar energy"},
    {"type": "ins", "en": "solar energy"}
  ],
  "en": "… combination with solar energy.",
  "en_deleted": "solar energy"
}
```

`w:ins` / `w:del` 标记仍存在于输出中，因此跟踪更改标记数量被保留，审阅者仍能看到编辑者*在哪里*对荷兰语做了修正。但接受或拒绝该更改产生相同的英文文本——这是正确的，因为在英文中没有任何可接受或拒绝的差异。

**何时不折叠。**如果源编辑改变含义，哪怕微不足道，都用真实英文翻译两侧。日期中 `2` → `6` 这样的错别字修正数字变更**是**有意义的编辑（日期变了），因此逐字翻译 `del: "2"` / `ins: "6"`——审阅者*确实*想在英文中看到数字变更。

**决策测试——分两步：**
1. 只看英文红线的单语英语律师，在“接受”和“拒绝”之间切换会学到什么吗？
2. 会 → 区分翻译 del 和 ins。不会 → 给它们相同的英文。

一个推论：对日期、金额、百分比、相对方名称、定义词或交叉引用编号的纯数字编辑**总是有意义**，绝不折叠。

#### 混乱 / 字符碎片化整词编辑 — 强制

与正字法折叠不同的一种独特病理：源语言编辑者将**单个单词或序数词**改为**另一个单词或序数词**，但逐字母进行——产生许多字符级拆分组成的 `tc_segments` 数组，无法逐段干净翻译，因为英文通常替换整个单词而非字符范围。

典型示例（西班牙语道路使用草稿，条款标题）。此处字符串使用**美式默认**英文（`Section`）；在 `--variant uk` 下通篇替换为 `Clause`。

```
source edit:         "Duodécima" → "Decimotercera"   (12th → 13th)
tc_segments:         [regular "D"], [del "Duod"],
                     [ins "e"],     [del "é"],
                     [regular "cim"],
                     [ins "otercera"], [del "a"],
                     [regular ".- Legislación, Fuero y jurisdicción"]
accepted text:       "Decimotercera.- Legislación, Fuero y jurisdicción"
rejected text:       "Duodécima.- Legislación, Fuero y jurisdicción"
desired English:     accepted  = "Section 13. Governing law, venue and jurisdiction"
                     rejected  = "Section 12. Governing law, venue and jurisdiction"
```

这 7 个字符级段与英文文本之间没有一一对应关系：英文编辑是 `Section 12` → `Section 13`，一次双标记替换。不管翻译者发明什么 `en_segments`，孤儿源字母（`é`、`cim`、`otercera`、`D`、`ecimo`……）都会泄漏进红线视图，结果读起来像 `"Section 13~~Section 12~~eé cim otercera. Governing law…"`——即使接受/拒绝落对了条款编号，外观上也是错的。

**检测——在起草 `en_segments` 之前于步骤 3b 执行。**碎片化整词簇是连续 `tc_segments` 的最大运行段，满足：

1. 包含至少 3 个 ins/del 片段且各至少一个；
2. 任何段的文本内无空白；
3. 在接受侧和拒绝侧各自拼接为连贯的单个单词/序数词（例如 `Decimotercera` 与 `Duodécima`）。

**修正——以英文填写簇的第一个 ins/del、其余簇段填空字符串来搭建 `en_segments`。**两个选项，按偏好顺序：

**选项 A（首选）：运行 `coalesce_fragmented_tcs.py`。**

```bash
python <skill-path>/scripts/coalesce_fragmented_tcs.py <workdir>/paragraphs.json
```

脚本**不触碰** `tc_segments`——XML 结构仍保留每个字符级 run。它做的是**将预填的 `en_segments` 骨架写入**每个被标记的段落，为每个 `tc_segments` 条目生成一个条目，检测到的每个簇的第一个 ins 和第一个 del 上为 `<<TRANSLATE: …>>` 占位符、簇的每个其他段上为空字符串 `""`。翻译者只需填写占位符和非簇槽；簇内的空字符串是给应用步骤的刻意“清除此 run”指令。先用 `--dry-run` 预览。

对上述道路使用示例 idx 117，脚本写入这个骨架（每个 tc_segments 条目一个条目，按原始顺序——8 个源段 8 个条目）：

```json
[
  {"type": "ins",     "en": "<<TRANSLATE: ins='Decimotercera' (accepted)>>"},
  {"type": "del",     "en": "<<TRANSLATE: del='Duodécima' (rejected)>>"},
  {"type": "ins",     "en": ""},
  {"type": "del",     "en": ""},
  {"type": "regular", "en": ""},
  {"type": "ins",     "en": ""},
  {"type": "del",     "en": ""},
  {"type": "regular", "en": ""}
]
```

翻译者用最终表达替换两个占位符，并填写尾部非簇 `regular` 条目为标题其余部分：

```json
[
  {"type": "ins",     "en": "Section 13"},
  {"type": "del",     "en": "Section 12"},
  {"type": "ins",     "en": ""},
  {"type": "del",     "en": ""},
  {"type": "regular", "en": ""},
  {"type": "ins",     "en": ""},
  {"type": "del",     "en": ""},
  {"type": "regular", "en": ". Governing law, venue and jurisdiction"}
]
```

接受时：第一个 ins 携带“Section 13”，其他 ins run 为空，常规 run 贡献 "" 和 ". Governing law…"——段落读为“Section 13. Governing law, venue and jurisdiction”。拒绝时：第一个 del 携带“Section 12”，其他 del run 为空，常规 run 贡献 "" 和 ". Governing law…"——段落读为“Section 12. Governing law, venue and jurisdiction”。无孤儿源字母泄漏。

**选项 B（手动兜底）。**如果跳过选项 A，手工写同样的形状：簇的第一个 `del` 上为完整英文 `del` 短语、第一个 `ins` 上为完整英文 `ins` 短语、簇的每个其他段为 `"en": ""`、非簇段为正常翻译。这依赖 `apply_translations_textmatch.py` 的空字符串行为：`"en": ""`（键存在、值为空）**清除**匹配 run；完全没有 `"en"` 键**保留**源。只要可能，用选项 A——运行脚本。

**为什么不接受乱码。**散布在英文条款标题中的孤儿源语言字母使审阅者的红线不可读。

**相邻缺陷类别——应用时的短连续 ins/del 簇。**两个连续携带短字母数字片段的 `<w:ins>`（或 `<w:del>`）XML 元素（例如 `"P"` 后接 `"S"`）否则会被 `post_process.fix_spacing` 的字母+字母规则重新拼接为 `"P S"`。这自动处理：`extract_paragraphs.py` 在提取时于 `tc_cluster_hits` 中标记此类簇，`apply_translations_textmatch.py` 在应用时于每个包装边界注入零宽空格（U+200B，读者不可见，对 `strip_noop_tracked_changes` 是噪音），从结构上击败字母+字母规则。无需操作者动作。如果残余缺陷漏网，`validate_apply.py --report-clusters --apply-zwsp` 将零宽空格重新注入簇标记的 en 字符串作为双保险兜底——很少需要。

#### 子附录：仅限非拉丁文字源——适用于源文字为非拉丁的跟踪更改文档

> **如果源为拉丁文字则跳过**（意大利语、荷兰语、西班牙语、法语、德语、波兰语、匈牙利语、芬兰语、葡萄牙语、捷克语、罗马尼亚语、越南语、丹麦语、瑞典语、挪威语、英语等）。拉丁文字源携带在提取和应用中存活的词间空白，因此段无需下列规则即可干净分离。
>
> **如果源为非拉丁文字则阅读**——中文、日文、韩文、泰文、老挝文、高棉文、西里尔文（俄语、保加利亚语、塞尔维亚语、乌克兰语等）、希腊文、阿拉伯文、希伯来文、天城文等。

**故障排除——如果 `validate_segment_shapes.py` 通过但应用在跟踪更改接缝处产生粘连文本，先读此段。**这是非拉丁源跟踪更改段落最常见的单一失败模式，答案就是下面的规则 1——直接去那里。不要迭代以下任何一项：边界处的字面 ASCII 空格、仅前导 ASCII 空格、边界处的 NBSP（U+00A0）、每个前导边缘的 NBSP、表意空格（U+3000）、窄空格（U+2009）、en 空格（U+2002）、em 空格（U+2003）。它们都对 `str.isspace()` 返回 `True`，因此 `validate_segment_shapes.py` 在第 224 行（`_rule_alpha_collision_no_space` 空白存在检查）接受它们；它们都会被 `apply_translations_textmatch.py` 在 `en_segments` 分配路径内的 `.strip()` 调用移除（Python 的 `str.strip()` 移除每个 `.isspace()` 返回 `True` 的字符）。对欧洲来源的段落这从不浮现，因为 `distribute_text_across_elements` 从源 `<w:t>` 元素恢复边界空白，而欧洲语言的源元素天然有空格。非拉丁源元素没有字符间空白，因此无任何恢复——渲染输出读为 `"theInvestment"`、`"of500MW"`、`"Section3Insurance"`。有案可查的修正是规则 1 中的可见空格 + 零宽空格混合：常规段之后为 `" ​"`，跟在 ins/del 之后的常规段之前为 `"​ "`。零宽空格（U+200B）是 Unicode 类别 `Cf`（格式），按 `.isspace()` 不是空白，因此 `.strip()` 在零宽空格处停止，相邻字面空格存活。**在编写第一个非拉丁跟踪更改段落之前完整阅读规则 1；不要迭代空白候选。**试错路径每次失败约耗 6-8 次工具调用；阅读一次规则 1 分文不花。

非拉丁文字要么完全不用词间空格书写（中日韩、泰文、老挝文、高棉文），要么携带 `fix_spacing` 处理较不可靠的字符类别（西里尔文、希腊文、阿拉伯文、希伯来文、天城文）。无论哪种方式，英文翻译者必须在段边界**制造**英文需要的空白。如果 `en_segments` 是 `{"regular": "the contract"}, {"ins": "provisions"}, {"regular": " apply to"}`，输出读为 `"the contractprovisions apply to"`——一个视图没问题，另一个把两个词撞在一起。

四条规则，应用于每个 `en_segments` 数组：

1. **用可见空格 + 零宽空格混合为每个常规↔ins/del 接缝加书挡（这是默认——仔细阅读，下面两种失败模式都已在生产中观察到）。**在与 ins/del 相邻的常规段的*尾部*边缘，追加 `" ​"`（一个字面空格，然后 U+200B 零宽空格）。在跟在 ins/del 之后的常规段的*前导*边缘，前置 `"​ "`（零宽空格，然后一个字面空格）。可见空格给读者在渲染 docx 中的真实分隔符；零宽空格通过 `apply_translations_textmatch.py` 的 `.strip()` 锚定空格（其按 `str.isspace()` 剥离尾部/前导空白，但由于零宽空格是 Unicode 类别 `Cf` 而非空白，在零宽空格处停止），且零宽空格也被 `validate_apply` 视为标记边界、被 `strip_noop_tracked_changes` 过滤。混合避免的失败模式恰好有两种：

   - **仅字面空格**——应用 `.strip()` 掉尾部/前导空白，接缝在渲染视图和验证器标记视图中都粘连（`"theInvestment"`、`"of500262.5MW on"`）。
   - **仅纯零宽空格**——通过 `.strip()` 存活（验证器标记视图没问题，因为分词器按零宽空格分割），但零宽空格是零宽度的，因此*渲染的* docx 仍读为 `"theInvestment"` / `"of500MW"`。Markdown / `pandoc` 预览看起来正确，因为它们将零宽空格折叠为空白，但 Word 不会。这是在日本出资方担保谅解备忘录运行中报告的失败模式。

   对仅包含数字或其他非字母内容的 ins/del 段（例如 `"500"`、`"262.5"`），ins/del 内部无需更多书挡——常规侧处理分隔符。对直接与另一个 ins/del 相邻（之间无常规，例如 `ins("Loan")` 紧接 `del("Investment")`）的含字母文本的 ins/del 段，用 `"​"`（仅零宽空格）为内部边缘加书挡——两个连续 ins/del 段之间没有渲染读者，因此可见空格一半不必要，加上它会在两侧接受-或拒绝-渲染时产生双空格。一行配方：**常规侧携带可见空格 + 零宽空格；ins↔ins 或 ins↔del 接缝仅携带零宽空格。**

   工作示例（在日本出资方担保谅解备忘录重跑中验证，即混合应用前产生“of500262.5MW on”的案例）：
   ```json
   {"type": "regular", "en": "with installed capacity of ​"},
   {"type": "ins",     "en": "500"},
   {"type": "del",     "en": "262.5"},
   {"type": "regular", "en": "​ MW on the Commercial Operation Date"}
   ```

   字母 ins/del 与字母常规相邻的工作示例：
   ```json
   {"type": "regular", "en": "the ​"},
   {"type": "ins",     "en": "​Investment​"},
   {"type": "regular", "en": "​ Insurance"}
   ```

   纯零宽空格书挡（仅 `"​"`，无可见空格）仅在至少一侧已有自然标点——句号、逗号、分号、开或闭括号、破折号——时才可接受，因此渲染文本从标点本身获得真实视觉分隔符。对字母-字母或字母-数字边界（法律英语散文中的常见情形），使用上述混合。

2. **绝不让段以数字结尾。**跟踪更改边界上的数字加上另一侧的字母会产生 `"2025the"` / `"Section5"`。让数字留在其段中间。
3. **冠词存在于包含名词的 ins/del 内部。**与前文“拒绝全部的语法”小节相同规则；无空白缓冲时此处咬得更狠。
4. **绝不让常规段以介词结尾。**拒绝全部视图中的孤立介词。将介词 + 宾语保持在同一个段中。

`validate_segment_shapes.py`（通用，已在每份含跟踪更改的文档上运行）机械捕获违规。这些规则是保持检查器静默的提示侧配套。

**兜底：`fix_spacing` 覆盖 ins↔del 接缝。**`post_process.py` 的 `fix_spacing` 现在按文档顺序一起遍历 `<w:t>` 和 `<w:delText>`，因此插入 run 与相邻删除的带删除线文本之间的字母+字母冲突会自动插入空格。拒绝全部视图中的可见粘连（来自 `regular("the")` 与 `regular(" Insurance")` 之间 `del("Investment")` 的 `"theInvestment Insurance"`）无需操作者干预即可修复。零宽空格仍是验证器标记视图的推荐书挡——两层互补，而非冗余。

**Rev20：混合现在在上面规则 1 中为默认（曾是 附加说明）。**措辞曾将可见空格 + 零宽空格混合呈现为纯零宽空格默认下的“当可读性重要时”例外，自上而下阅读的操作者先捡起纯零宽空格。纯零宽空格在字母-字母边界（常见情形）的 Word 中渲染粘连，因此呈现顺序被翻转：混合是默认，纯零宽空格是较窄的情形。完整配方和工作示例见上面规则 1。

**Rev18：不要使用 Symbol-other 字符（○ □ △ ◯ ■ ●）作为占位符。**日文、中文和韩文文档常用 ``○``（U+25CB）表示空白日期/数字单元格（``○年○月○日`` = 年/月/日空白）。这些字符是 Unicode 类别 ``So``，`strip_noop_tracked_changes._is_noise_only` 将它们视为噪音——任何唯一内容为这些符号之一的 `<w:ins>` 或 `<w:del>` 包装会在步骤 6 期间被移除，在红线中留下空洞并在步骤 6 结束时触发 validate_apply 漂移错误。**对占位单元格使用数字 ``0``**（或 ``X``、``_``）；它们是字母数字，能通过 `strip_noop` 存活。技能不自动替换，因为有些占位符承载内容（复选框上的真实 ``○`` 标记），因此操作者必须在翻译时选择。

## 内部合规检查 — 04-translate

在进入下一步骤前，确认：

- [ ] 你翻译了源的每个段落（无跳过、无摘要）
- [ ] 你保持在每批 ≤35 段的上限内
- [ ] 你在每批后运行了 `validate_translations.py`（步骤 4b）
- [ ] 你为每个定义部分段落填写了 `en_runs`
- [ ] 你为每个跟踪更改段落生成了 `en_segments`（无捷径）

如有任何检查不确定，停止。重新阅读本文件。不要继续。

**下一步：** `skill-docs/04b-translate-gates.md`
