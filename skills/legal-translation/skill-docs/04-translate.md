> **预检。**进入本步骤前应已完成上一步骤。**SKILL.md 管辖每一步的纪律；如果本会话中尚未完整阅读 SKILL.md，停止并先 `Read('SKILL.md')` 再继续。** SKILL.md 中的硬性规则同样适用于本步骤。**在聊天模式中（无工作区文件夹、无自动管理的待办列表）同样的纪律适用——不要略读本步骤文档，不要捆绑批次，不要跳过底部的逐步骤内部合规检查。** **如果本轮对话始于压缩后的转录，压缩摘要不视为已阅读本步骤文档——在任何工具调用前现在完整 `Read()` 它。**

### 步骤 4：翻译所有段落

*[内部合规检查——不要向用户复述或转述。在执行前重新阅读本步骤中的每一条规则。不要偏离技能的任何一行。不要捆绑工作、跳过检查或"为效率而解释"——每一次此前的偏离都产生了低于技能设计应交付质量水平的输出。无论如何，技能的硬性门禁都会阻止偏离；提前合规总比撞上门禁并重写 paragraphs.json 更快。]*

**技能级硬性规则适用于本步骤。**完整规则块见 SKILL.md。在步骤 4 中最吃紧的规则：每批最多 35 段（由 `validate_translations.py` 强制执行）、翻译期间每个段落的完整 `text` 字段必须在你的上下文窗口中、以及每个定义部分段落的 `en_runs` 是强制性的（在步骤 5 开始时由 `validate_en_runs.py` 强制执行）。

通过填写 JSON 中的 `"en"` 字段翻译**每个非空段落**。

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

1. **翻译完整段落，而非片段。**你拥有完整的句子上下文——使用它。

2. **精确保留段落边界。**一个源段落 = 一个英文段落。切勿合并或拆分段落。每个段落从原始文件继承其格式（样式、编号级别、缩进）。拆分或合并会破坏这种对齐。

3. **为任何源 `runs` 数组显示文本加粗的段落提供 `en_runs`，并为定义部分或标题段落（其样式提供加粗）中的每个段落提供 `en_runs`。** `apply_translations_textmatch.py` 内部的自动检测器仅处理经典的带显式引号的 `"X" means …` 定义形状。它会漏掉序言中定义词括号的加粗（`(the "Agreement")`、`(hereinafter the "Substation")`）、当事人栏定义词、附表清单以及任何*包含*加粗引号片段但并非教科书式定义行的正文段落。对所有这些，显式填充 `en_runs`——在你的 `en` 字符串中定位每个加粗引号短语并为其发出 `{"start": …, "end": …, "bold": true}`。

   **样式提供的加粗。**定义部分和条款/章节标题经常从*段落样式*获得加粗（如 `FWBL1`、`ITScheduleL1`、自定义模板样式，其 `styles.xml` 中的 `<w:rPr>` 携带 `<w:b/>`），而运行级 `<w:rPr>` 留空。`extract_paragraphs.py` 仅读取运行级格式，因此即使渲染后的源文是加粗的，`runs[i].bold` 也是 **`false`**。如果你只为这些段落提供 `en` 而将 `en_runs` 留空，`apply_translations_textmatch.py` 的默认关闭覆盖（其存在目的是防止样式加粗从 `basedOn` 父级泄漏进正文段落）将*剥离*样式的加粗，标题或定义将渲染为纯文本。通过运行级加粗之外的结构线索识别这些段落：

   **限定语——击败样式的运行级覆盖。**一些作者会在标题段落的每个运行上应用直接运行级 `<w:b w:val="0"/>` 和/或 `<w:i w:val="0"/>` 覆盖，专门为了抑制该段落的样式继承加粗或斜体（典型模式：Heading3 样式提供加粗斜体，但作者希望这个*特定*标题渲染为纯文本，因此在运行级覆盖）。在这种情况下，渲染后的源文是**纯文本**而非加粗/斜体，发出 `en_runs:bold=true` 会使翻译*过度加粗*——与上述加粗不足缺陷相反。
   
   按段落应用的决策规则：
   
   - 如果段落位于定义部分 / 具有标题样式**且** **至少一个**运行显示 `runs[i].bold = true`：发出带 `bold: true` 的 `en_runs`（加粗不足防御——原始规则）。
   - 如果段落位于定义部分 / 具有标题样式**且** **每个**运行都显示 `runs[i].bold = false`（即每个运行都携带显式运行级覆盖）：发出带 `bold: false` 的 `en_runs`。作者选择击败样式的加粗；尊重这一选择。
   - 同样的规则对斜体对称适用：仅当至少一个运行显示 `runs[i].italic = true` 时发出 `italic: true`；如果每个运行都显示 `runs[i].italic = false` 则发出 `italic: false`。
   - 加粗和斜体相互独立——一个段落可以纯加粗（斜体被覆盖关闭，加粗从样式继承）或仅斜体（加粗被覆盖关闭，斜体保留）。按"任一运行为 true → true；所有运行为 false → false"的逐属性规则分别决定每个属性。
   
   为什么这样有效：当每个运行都有显式 `false` 覆盖时，运行级属性就是 Word 渲染的内容。当*没有*运行有任何覆盖（所有 `runs[i].bold` 为 `false` 是因为运行级 `<w:rPr>` 沉默）时，样式继承的加粗胜出。两种情况在 `extract_paragraphs.py` 的输出中都产生 `runs[i].bold = false`（提取仅读取运行级，无法区分"沉默"与"显式 false"），因此在沉默情况下仍需要结构线索来发现定义部分——但*所有运行加粗为 false* 检查独特地识别显式覆盖情况，并排除错误的加粗发出。

   **段落标记覆盖（`p_rpr_b` / `p_rpr_i`）——最强信号。**一些作者在*段落标记*处应用加粗/斜体覆盖（`<w:pPr><w:rPr><w:b w:val="0"/><w:i w:val="0"/></w:rPr></w:pPr>`）而非逐运行。这种模式在挪威语 / 斯堪的纳维亚草稿中很常见，其中 Heading3 默认渲染为加粗斜体，但选定的段落有意为纯文本。提取仅读取运行级，因此所有这些段落在 `runs` 数组中看起来相同。截至 rev38，`extract_paragraphs.py` 还以 JSON 条目上的三态字段捕获段落标记设置：
   
   - `p_rpr_b == "false"`（或 `p_rpr_i == "false"`）——作者显式关闭了本段落的样式继承加粗（或斜体）。发出 `en_runs:[{...,"bold": false, ...}]`（或 `italic: false`），无论该段落本会被视为标题与否。
   - `p_rpr_b == "true"`——作者显式开启段落标记加粗。发出 `bold: true`。（斜体相同。）
   - 字段不存在——无段落标记设置；由 pStyle 级联决定。应用上述标题规则和全运行加粗 false 限定语。
   
   标题的决策优先级（按顺序应用，第一个匹配即停）：
   1. `p_rpr_b == "false"` ⇒ 发出 `bold: false`（段落标记胜出）
   2. `p_rpr_b == "true"` ⇒ 发出 `bold: true`（段落标记胜出）
   3. 任何运行显示 `runs[i].bold == true` ⇒ 发出 `bold: true`
   4. 每个含文本的运行都显示 `runs[i].bold == false` 且无 `p_rpr_b` 且段落采用标题样式 ⇒ 发出 `bold: true`（样式级联胜出；沉默 rPr 情况）
   5. 否则 ⇒ 发出 `bold: false`
   
   同样的五条规则使用 `p_rpr_i` 和 `runs[i].italic` 对斜体对称且独立适用。加粗和斜体分开决定——一个段落可以纯加粗、仅斜体、两者兼有或两者皆无。

   - **定义部分**通常有标签——一个读作 `Definitions`、`Defined Terms`、`Definitions and Interpretation`、`Interpretation` 的章节标题段落，或以 `Article 1`、`Clause 1`、`Section 1` 为前缀，或编号为 `Definitions` 的附件。此类部分中的正文段落遵循谓词模式 `Term : means / shall mean / has the meaning given to it in / indicates / signifies`，术语周围带或不带引号。
   - **条款/章节标题**可通过其段落样式识别（任何不在标准 `Normal` / `BodyText` / `Default` 集合中的 `pStyle` 值——特别是自定义模板样式如 `FWBL1`、`ITScheduleL1`、`Heading1`、`FWHeader`）或通过其结构形状识别（简短、全大写或首字母大写、无句末句号）。

   当遇到任一模式时，即使源 `runs` 数组未显示加粗，也要为该部分中的每个段落填充 `en_runs`。对于带加粗斜体定义词的词条，发出
   `[{"start": 0, "end": <term_end>, "bold": true, "italic": true},
   {"start": <term_end>, "end": <text_len>, "bold": false, "italic": false}]`。
   对于由样式渲染为加粗的标题段落，发出
   `[{"start": 0, "end": <text_len>, "bold": true}]`。

   仅当源 `runs` 数组未显示加粗**且**段落不在定义部分**且**其 `pStyle` 为正文样式时，`en_runs` 才可为 null。有疑问时，应用上述限定语——检查是否**每个**运行都有 `runs[i].bold = false`（斜体同理）。如果是，发出 `en_runs:[{...,"bold": false, "italic": false}]` 以*击败*作者显式抑制的样式继承加粗/斜体。如果至少一个运行显示加粗或斜体为 true，发出这些属性为 true。"默认提供 en_runs"的建议在精神上是正确的（规范不足会剥离真正加粗标题的加粗），但你必须按限定语以**正确**的加粗/斜体值填充 `en_runs`——对作者有意渲染为纯文本的段落过度加粗，与对真正加粗标题加粗不足一样明显。

4. **使用参考文件中适合领域的英文法律词典。**

5. **保持定义词一致**——每次翻译相同。

6. **自然的英文词序**："all existing and future plants" 而非 "plants existing and future"。

7. **英文法律交叉引用惯例**："this Deed"、"Clause 2"（内部引用而非 "Article 2"）、"above"/"below"（而非 "that precedes"/"that follows"）。

8. **英文变体：默认英式。**仅当用户的原始提示明确要求时才使用美式英语。完整的防漂移规则和决策点列表见下文"目标英文变体"部分——有疑问时用英式。

9. **空段落**（仅空白）：将 `en` 设置为相同的空白。

10. **纯结构性文本**（当事人名称、地址、注册号）：以最小改动复制——翻译描述但保持名称/数字完整。

11. **页眉/节标题**如 "SCHEDULE B" 或 "ALLEGATO 1"：翻译标题文本。

12. **保持标题和页眉在页面宽度内。**封面标题和章节标题从原始文件继承固定字号和缩进。如果英文翻译明显长于源文，可能溢出页面边界而不可见。缩写或重组以保持在可比字符长度内。

13. **绝不缩写、概括或压缩段落。**英文翻译必须包含源段落的全部实质性内容，包括：所有百分比和数值、所有货币金额（数字和文字形式）、所有定义词及其括号内定义、所有上限金额和阈值、所有时间期限和截止日期以及所有交叉引用。如果源段落规定"每周 1%，上限 15%"，翻译必须写明"每周 1%，上限 15%"。如果源文以数字和文字两种形式规定合同价格，翻译必须包含两者。从翻译中省略商业条款是使文档无法使用的严重错误。

14. **数字和字母词之间始终加空格。**法律英语在数字和其修饰的词之间放一个空格：写 `Section 5` / `500 euros` / `12 months` / `3 business days`，绝不写 `Section5` / `500euros` / `12months`。三个例外：英文序数不加空格（`1st`、`2nd`、`3rd`、`4th`、`21st`）；一或两个字母的紧凑单位缩写可以直接跟在数字后（`5km`、`10kg`、`500ml`、`24h`）；众所周知的缩写加数字组合连写（`A4`、`MP3`、`H2O`、`B2B`、`3G`）。其他一切都需要空格。有疑问时插入空格——应用前检查器（`validate_segment_shapes.py`）会标记最常见的违规但仅作为警告；防御此类缺陷的主要手段是在翻译时做对。

**设计阶段术语（对建工/EPC 合同至关重要）：**

三阶段设计层级必须正确翻译：

| 设计阶段 | 正确英文 | 需避免的常见错误 |
|---|---|---|
| 阶段 1（概念） | Preliminary Design | — |
| 阶段 2（中间） | Detailed Design | "Preliminary Design"（错误的阶段）、"Definitive Project"（仿译） |
| 阶段 3（可施工） | Construction Design | "Executive Project"（仿译） |

弄错这些（尤其是将阶段 2 与阶段 1 混淆）是实质性错误。

#### en_runs 的格式规则

- **定义词**（定义段落中引号之间的文本）：`bold: true`
- **章节标题**：从段落样式继承格式（通常通过 pPr 加粗）
- **其他一切**：`bold: false, italic: false`

如果不提供 `en_runs`，应用脚本会自动检测定义词并应用加粗。这对简单定义有效，但可能遗漏复杂情况。

#### 分批工作——强制大小限制（最多 35 段）

**硬性限制：每批必须最多包含 35 个段落。无例外。**

此限制同样适用于第 1 批、第 5 批和第 15 批。一个已知的故障模式是批次规模随翻译推进而增长——前几批为 30-35，然后后面的批次在你试图"更快完成"时静默增长到 50、60、80+ 段。**这是不允许的。**大批次的质检成本对你不可见但真实存在：条款截断、定义词细节遗漏、术语不一致，以及转述而非翻译的文本。这些错误会累积，事后很难发现。

**在开始每批之前，明确说明段落范围**（如"第 4 批：段落 106–140，35 段"）。如果剩余段落超过 35 段，你必须将其拆分为多个批次——不要因为"只剩 50 段"就一次全部翻译。

每批：翻译、将 JSON 保存为检查点，然后在继续前验证。

**关键：查看时绝不截断段落文本。**显示待翻译段落时，你必须看到每个段落的完整 `text` 字段。不要使用带字符限制的 Python 预览命令，如 `text[:200]` 或 `p['text'][:120]`。始终显示完整文本。超过 300 字符的段落通常包含关键商业术语——费率、上限、金额、括号内定义词——它们出现在段落后半部分，如果被截断将静默丢失。

每批后，运行验证脚本以在继续前捕获截断的翻译：

```bash
python <skill-path>/scripts/validate_translations.py <workdir>/paragraphs.json
```

这会检查每个段落源文与目标文之间的字符比率。如果任何段落被标记为可能截断（超过 150 字符的段落比率低于 0.6），在进入下一批前重新阅读完整源文并重新翻译。

#### 附录：仅限修订追踪文档——如果没有段落包含修订追踪则跳过

> **如果文档中没有段落包含修订追踪，跳过以下所有内容（直到步骤 4b）。**如果 `extract_paragraphs.py` 报告 `paragraphs.json` 中有任何段落的 `has_track_changes: true`（或你在 `word/document.xml` 中看到 `<w:ins>` / `<w:del>` 元素），则文档有修订追踪。如果两者都不是，跳至步骤 4b——步骤 4 的其余小节不适用。
>
> **如果任何段落包含修订追踪，阅读以下所有内容。**以下每个 TC 小节对 TC 文档都是强制性的。

#### 修订追踪段落——强制性双重翻译

包含修订追踪的段落（JSON 中 `has_track_changes: true`）需要**两**个翻译：

1. **`en`** — `text` 字段的翻译（"已接受"文本：读者在接受所有更改后看到的内容）。这是你为每个段落做的正常翻译。

2. **`en_deleted`** — `deleted_text` 字段的翻译（红线视图中显示的删除线文本）。此文本代表作者在编辑期间删除的内容。

两个翻译都是必需的，因为应用脚本分别处理这两条文本流：`en` 分配到 `w:t` 元素（当前/可见运行），而 `en_deleted` 分配到 `w:delText` 元素（已删除运行）。如果你只提供 `en` 而将 `en_deleted` 留空，删除的文本将停留在源语言——任何查看修订追踪的读者都会立即看到这一点，这是高严重性缺陷。

**如何翻译 TC 段落：**

遇到 `has_track_changes: true` 的段落时：

1. 读取 `text` 字段——这是已接受/可见文本。正常翻译为 `en`。
2. 读取 `deleted_text` 字段——这是删除线文本。翻译为 `en_deleted`。删除的文本通常是已被插入文本替换的短语或条款。以与文档其余部分相同的风格和术语翻译。
3. **检查 TC 在语义上是否说得通。**翻译两部分后，验证修订追踪读起来自然：删除的文本（删除线）应代表旧版本，已接受文本应代表新版本。如果英文作为修订追踪没有意义（例如删除和插入不构成连贯的编辑），调整两个翻译直到更改读起来自然。

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

在 Word 中，这渲染为："The Developer ~~shall not be entitled to unilaterally~~ shall be entitled to assign this Development Agreement"——一个显示作者从禁止到允许的编辑的连贯修订追踪。

**TC 段落的加粗修复：**应用脚本自动对非标题 TC 段落中的所有运行应用 `w:b val="0"`（关闭加粗）。这防止了一个常见缺陷，即 `w:ins` 运行的加粗格式（从追踪插入样式继承加粗）泄漏进翻译后的正文文本。你不需要为此做任何特别处理——该修复在应用脚本中是自动的。

**TC 加粗关闭旁路（rev38）——当覆盖会过度剥离时。**上述加粗关闭覆盖以 `pStyle` 包含 `heading`/`title`/`cmsor`/`titre` 为键。以普通 Word 默认样式起草的文档——在日本合同和某些斯堪的纳维亚模板中很常见，标题的加粗纯粹来自运行级 `<w:b/>` 而非 Heading-N pStyle——会将每个标题呈现为非标题给该检测器。截至 rev38，两个额外旁路防止覆盖剥离有意的加粗：

1. **操作者撰写的加粗**——如果你发出至少一个条目带 `bold: true` 的 `en_runs`，该段落的覆盖被跳过。作者意图胜出。
2. **源段落整体加粗**——如果每个含文本的源 `runs[i]` 都携带 `bold: true`，源文确实整体加粗（它是标题的强信号），覆盖被自动跳过。

对于携带 TC 的未设样式但真正加粗的标题，你可以依赖旁路 2（什么都不做——覆盖自行跳过）或显式发出 `en_runs: [{"start": 0, "end": <text_len>, "bold": true}]` 以触发旁路 1。任一路径都保留标题的加粗跨越应用步骤。

#### 感知片段的 TC 翻译——对 TC 段落强制性

`extract_paragraphs.py` 脚本为每个 TC 段落提取 `tc_segments` 数组。该数组按修订追踪类型将段落拆分为有序片段：

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

**你必须独立翻译每个片段**，并在匹配的 `en_segments` 数组中提供翻译。每个条目的 `type` 必须与相应 `tc_segments` 条目相同，外加带英文翻译的 `en` 字段：

```json
{
  "en_segments": [
    {"type": "regular", "en": "The Developer"},
    {"type": "del", "en": "shall not be entitled to unilaterally"},
    {"type": "ins", "en": "shall be entitled to assign this Development Agreement"}
  ]
}
```

**为什么这很重要：**没有片段感知翻译，应用脚本会将英文文本按比例分配到所有活动的 `w:t` 元素——忽略 TC 边界。这导致英文单词落在相对于 `w:ins`/`w:del` 边界的错误位置，在用户接受或拒绝时产生读起来不连贯的修订追踪。使用 `en_segments`，每个片段的翻译只分配到其自己的运行，保持 TC 语义完整。

**片段翻译规则：**

1. `en_segments` 中片段的数量和顺序必须与 `tc_segments` 完全匹配。
2. 每个 `en_segments[i].type` 必须等于 `tc_segments[i].type`。
3. 翻译每个片段，使接受所有更改产生连贯句子，**且**拒绝所有更改（仅保留 `regular` + `del` 片段）也读起来连贯。
4. 仍然像以前一样提供 `en`（完整已接受文本）和 `en_deleted`——如果应用时片段类型不匹配，它们作为回退。

**拒绝全部语法——冠词和介词归属（必读）**

规则 3（"拒绝所有更改也读起来连贯"）在实践中很容易违反。缺陷表现为流畅的接受全部阅读加上不合语法的拒绝全部阅读，因为一个语法正确性取决于相邻 TC 被接受还是被拒绝的英文单词落入了错误的片段。

示例——一个修订追踪 `<w:del>` 从一句英文需要在两个名词前加 "the respective" 的条款中删除了翻译为 "respective" 的词。错误的拆分将定冠词同时放入 regular 区间和 del：

```
错误
  regular: " to "
  del:     "the respective "
  regular: "the addressees, and"

  accept-all: " to the addressees, and"              ← 读起来好
  reject-all: " to the respective the addressees, and"  ← "the respective the"
```

正确的拆分将在 accept-all 下必须消失的冠词移入 del，并保持相邻 regular 区间以裸名词开头，reject-all 需要时无需冠词：

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

**一般规则——冠词、介词以及任何语法正确性取决于相邻修订追踪被接受还是被拒绝的词，必须位于 del 或 ins 内部，而非与其相邻的 regular 区间中。**同样的规则适用于定义词短语边界：如果两个连续名词短语来自不同片段，至少其中一个必须携带自己的前导冠词/逗号/空白，以便恢复被删除的短语不会与相邻 regular 短语碰撞。

**机械执行。**调用 `apply_translations_textmatch.py` 之前，在填写好的 `paragraphs.json` 上运行 `validate_reject_all.py`：

```bash
python scripts/validate_reject_all.py workdir/paragraphs.json
```

脚本从每个含 del/ins 段落的 `en_segments` 重建 accept-all 和 reject-all 视图，并扫描两者的双冠词（`the respective the`）、重复词、孤立介词、标点后接字母连写、双空格、空括号/引号以及禁用搭配列表。通过重写有问题的片段使冠词/介词位于 TC 边界的正确一侧来修复每次命中，然后重新运行。应用前需要干净运行。

**非拉丁文字源有额外的片段形状规则。**如果源语言使用非拉丁文字——中文、日文、韩文、泰文、老挝文、高棉文、西里尔文（俄语、保加利亚语、塞尔维亚语、乌克兰语等）、希腊文、阿拉伯文、希伯来文、天城文或任何其他文字——在写 `en_segments` *之前*阅读步骤 4 末尾的**仅限非拉丁文字源**附录。拉丁文字源（意大利语、荷兰语、西班牙语、法语、德语、波兰语、匈牙利语、芬兰语、葡萄牙语、捷克语、罗马尼亚语、越南语、丹麦语、瑞典语、挪威语、英语等）从源文继承片段间空白，可以完全跳过该附录。

在 `apply_translations_textmatch.py` 运行之前，在填写好的 `paragraphs.json` 上运行 `validate_segment_shapes.py` 以机械捕获片段形状违规（无论源语言如何，此步骤适用于每个 TC 文档）：

```bash
python scripts/validate_segment_shapes.py workdir/paragraphs.json
```

它与 `validate_reject_all.py` 互补：形状扫描器警告*预示*缺陷的*拆分*；reject-all 扫描器捕获重建视图中的*语法*缺陷。两者都应在应用前干净运行。

**ins_then_del 片段（幻影修订追踪）。**如果源 docx 包含内容仅为 `<w:del>` 的 `<w:ins>`（即作者 A 插入文本，然后作者 B 删除了作者 A 的插入），提取步骤会发出类型为 `ins_then_del` 的片段。accept-all 和 reject-all 都将幻影渲染为空，因此该片段对可见英文没有贡献——但"显示标记"将把你写的任何英文显示为删除线。始终填写这些；让源语言留在那里是修订追踪文档中最常见的静默残留。

#### 折叠仅正字法和错字修复的 TC 编辑——强制性

源语言概念草稿中一个常见模式是仅修复**源语言**的修订追踪——正字法、缩写风格、连字符、变音符号、拼写改革或简单错字。这些编辑在目标语言中没有语义内容，因此没有有意义的翻译：删除和插入的文本都映射到**相同的英文字符串**。

该规则至少适用于以下类别，任何源语言均可：

1. **缩写风格**——荷兰语 `mn` → `m.n.`、意大利语 `ecc` → `ecc.`、法语 `cf` → `cf.`
2. **连字符**——荷兰语 `zonneenergie` → `zonne-energie`、荷兰语 `pro-actief` → `proactief`
3. **变音符号恢复**——荷兰语 `coordinaat` → `coördinaat`、法语 `a` → `à`、葡萄牙语 `nao` → `não`、西班牙语 `si` → `sí`
4. **拼写改革**——荷兰语 `pro-actief` → `proactief`（2005）、德语 `daß` → `dass`（1996）、葡萄牙语 `acção` → `ação`（2009）
5. **软连字符 / 行尾伪影**——`voor-geschreven` → `voorgeschreven`，其中换行连字符被烘进文本
6. **错字修正**——任何拼写错误修正为正确形式，两种形式都翻译为**相同的英文单词**。如意大利语 `contrato` → `contratto`（*contract*）、波兰语 `umowe` → `umowę`（*agreement*）、德语 `Vetrag` → `Vertrag`（*agreement*）。与 1-5 相同的原则：在英文中消失的源语言编辑。

来自荷兰语概念草稿的真实示例，展示该规则的实际应用：

| 源删除 | 源插入 | 编辑内容 | 英文删除 | 英文插入 |
|---|---|---|---|---|
| `mn` | `m.n.` | *met name* 的缩写——添加句点 | *in particular* | *in particular* |
| `pro-actief` | `proactief` | 2005 年荷兰语拼写改革 | *proactive* | *proactive* |
| `zonneenergie` | `zonne-energie` | 荷兰语三元音碰撞——添加连字符 | *solar energy* | *solar energy* |
| `coordinaat` | `coördinaat` | 缺失的分音符恢复 | *coordinate* | *coordinate* |
| `2` | `6` | 有意义的日期数字变更（"22" → "26 July"）——保持区分 | *2* | *6* |
| `voor-geschreven` | `voorgeschreven` | 行尾断行产生的软连字符 | *required* | *required* |

**规则：**当被删除和被插入的源片段翻译为**相同的英文字符串**时——无论是由于正字法、变音符号、缩写、连字符、拼写改革还是简单错字——给 `del` 和 `ins` 英文片段**完全相同的英文翻译**。不要制造虚假的区分（将无操作的荷兰语修复变成可见但无意义的英文红线——比如荷兰语到英语的译者把 "proactive" ↔ "pro-active" 写进 TC）。

这同时适用于 `en_segments` 和回退的 `en_deleted` / `en` 字段：

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

`w:ins` / `w:del` 标记仍存在于输出中，因此 TC 标记计数被保留，审阅者仍可以看到编辑者在荷兰语中的修改位置。但接受或拒绝该更改产生相同的英文文本——这是正确的，因为在英文中没有任何区别可以接受或拒绝。

**何时不折叠。**如果源编辑改变含义，即使微不足道，也用真实的英文翻译两侧。日期中像 `2` → `6` 这样的数字更正**是**有意义的编辑（日期变了），因此逐字翻译 `del: "2"` / `ins: "6"`——审阅者*确实*想在英文中看到数字变化。

**判定测试——分两步：**
1. 只看英文红线的单一语言英文律师，在"接受"和"拒绝"之间切换时会学到任何东西吗？
2. 会 → 区分翻译 del 和 ins。不会 → 给它们相同的英文。

推论：对日期、金额、百分比、相对方名称、定义词或交叉引用编号的纯数字编辑**总是有意义的**，绝不能折叠。

#### 错乱 / 字符碎片化的整词编辑——强制性

一种与正字法折叠不同的独特病态：源语言编辑者将**单个词或序数**更改为**不同的单个词或序数**，但逐字母进行——产生包含许多字符级拆分的 `tc_segments` 数组，由于英文通常替换整个词而非字符范围，无法逐片段干净翻译。

典型示例（西班牙语道路使用草稿、条款标题）：

```
source edit:         "Duodécima" → "Decimotercera"   (12th → 13th)
tc_segments:         [regular "D"], [del "Duod"],
                     [ins "e"],     [del "é"],
                     [regular "cim"],
                     [ins "otercera"], [del "a"],
                     [regular ".- Legislación, Fuero y jurisdicción"]
accepted text:       "Decimotercera.- Legislación, Fuero y jurisdicción"
rejected text:       "Duodécima.- Legislación, Fuero y jurisdicción"
desired English:     accepted  = "Clause 13. Governing law, venue and jurisdiction"
                     rejected  = "Clause 12. Governing law, venue and jurisdiction"
```

从这 7 个字符级片段到英文文本不存在一对一映射：英文编辑是 `Clause 12` → `Clause 13`，一个双标记替换。不加干预，无论译者发明什么 `en_segments`，孤立的源字母（`é`、`cim`、`otercera`、`D`、`ecimo`……）都会泄漏进红线视图，结果读起来像 `"Clause 13~~Clause 12~~eé cim otercera. Governing law…"`——即使接受/拒绝落在正确的条款编号上，外观也是错误的。

**检测——在步骤 3b 起草 `en_segments` 之前执行。**碎片化整词簇是连续的 `tc_segments` 的最大运行，它：

1. 包含至少 3 个 ins/del 片段且两种类型至少各有一个；
2. 任何片段文本内没有空白；
3. 在 Accept 和 Reject 两侧各自拼接为连贯的单个词 / 序数（如 `Decimotercera` 与 `Duodécima`）。

**修复——用英文在簇的首个 ins/del 上、其余簇片段上空字符串搭建 `en_segments`。**两种选项，按优先顺序：

**选项 A（首选）：运行 `coalesce_fragmented_tcs.py`。**

```bash
python <skill-path>/scripts/coalesce_fragmented_tcs.py <workdir>/paragraphs.json
```

脚本不触碰 `tc_segments`——XML 结构仍有每个字符级运行。它做的是**向每个标记的段落写入预填充的 `en_segments` 骨架**，为每个 `tc_segments` 条目一个条目，每个检测到的簇的首个 ins 和首个 del 上带 `<<TRANSLATE: …>>` 占位符，其余每个簇片段上带空字符串 `""`。译者只填写占位符和非簇槽；簇内的空字符串是对应用步骤的有意"清除此运行"指令。先使用 `--dry-run` 预览。

对于上文道路使用 idx 117 的示例，脚本写入此骨架（每个 tc_segments 条目一个条目，按原始顺序——8 个源片段对应 8 个条目）：

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

译者将两个占位符替换为最终表达，并填写尾部的非簇 `regular` 条目的标题其余部分：

```json
[
  {"type": "ins",     "en": "Clause 13"},
  {"type": "del",     "en": "Clause 12"},
  {"type": "ins",     "en": ""},
  {"type": "del",     "en": ""},
  {"type": "regular", "en": ""},
  {"type": "ins",     "en": ""},
  {"type": "del",     "en": ""},
  {"type": "regular", "en": ". Governing law, venue and jurisdiction"}
]
```

接受时：首个 ins 携带 "Clause 13"，其他 ins 运行为空，regular 运行贡献 "" 和 ". Governing law…"——段落读作 "Clause 13. Governing law, venue and jurisdiction"。拒绝时：首个 del 携带 "Clause 12"，其他 del 运行为空，regular 运行贡献 "" 和 ". Governing law…"——段落读作 "Clause 12. Governing law, venue and jurisdiction"。没有孤立的源字母泄漏出来。

**选项 B（手动回退）。**如果你跳过选项 A，手动写相同的形状：簇的首个 `del` 上放完整英文 `del` 短语，首个 `ins` 上放完整英文 `ins` 短语，其余每个簇片段上放 `"en": ""`，非簇片段上放正常翻译。这依赖于 `apply_translations_textmatch.py` 的空字符串行为：`"en": ""`（键存在、值为空）**清除**匹配的运行；完全没有 `"en"` 键**保留**源文。尽可能使用选项 A——运行脚本。

**为什么不能接受乱码。**孤立的源语言字母散落在英文条款标题中，使红线对审阅者不可读。

**相邻缺陷类别——应用时短连续 ins/del 簇。**两个连续的 `<w:ins>`（或 `<w:del>`）XML 元素携带短字母数字碎片（如先 `"P"` 再 `"S"`），否则会被 `post_process.fix_spacing` 的 alpha+alpha 规则重新连接为 `"P S"`。这会自动处理：`extract_paragraphs.py` 在提取时在 `tc_cluster_hits` 中标记此类簇，`apply_translations_textmatch.py` 在应用时在每个包装器边界注入零宽空格（U+200B，对读者不可见，对 `strip_noop_tracked_changes` 是噪音），从结构上击败 alpha+alpha 规则。无需操作者动作。如果有残留缺陷漏过，`validate_apply.py --report-clusters --apply-zwsp` 会将 ZWSP 重新注入标记簇的 en 字符串作为纵深防御回退——很少需要。

#### 子附录：仅限非拉丁文字源——适用于源文字为非拉丁文字的 TC 文档

> **如果源文为拉丁文字则跳过**（意大利语、荷兰语、西班牙语、法语、德语、波兰语、匈牙利语、芬兰语、葡萄牙语、捷克语、罗马尼亚语、越南语、丹麦语、瑞典语、挪威语、英语等）。拉丁文字源携带在提取和应用中存活的词间空白，因此片段无需以下规则即可干净分离。
>
> **如果源文为非拉丁文字则阅读**——中文、日文、韩文、泰文、老挝文、高棉文、西里尔文（俄语、保加利亚语、塞尔维亚语、乌克兰语等）、希腊文、阿拉伯文、希伯来文、天城文等。

**故障排除——如果 `validate_segment_shapes.py` 通过但应用在 TC 接缝处产生粘连文本，先读此条。**这是非拉丁文字源 TC 段落最常见的单一故障模式，答案是下文规则 1——直接去那里。不要遍历以下任何内容：边界处的字面 ASCII 空格、仅前导 ASCII 空格、边界处的 NBSP（U+00A0）、每个前导边的 NBSP、表意空格（U+3000）、窄空格（U+2009）、en 空格（U+2002）、em 空格（U+2003）。它们都从 `str.isspace()` 返回 `True`，因此 `validate_segment_shapes.py` 在第 224 行（`_rule_alpha_collision_no_space` 空白存在检查）接受它们；它们都会被 `apply_translations_textmatch.py` 在 `en_segments` 分配路径内的 `.strip()` 调用移除（Python 的 `str.strip()` 移除每个其 `.isspace()` 返回 `True` 的字符）。对于欧洲来源段落这从不显现，因为 `distribute_text_across_elements` 从源 `<w:t>` 元素恢复边界空白，而欧洲语言的源元素自然有空格。非拉丁文字源元素没有字符间空白，因此什么都不会恢复——渲染输出读作 `"theInvestment"`、`"of500MW"`、`"Clause3Insurance"`。已记录的修复是规则 1 中的可见空格 + ZWSP 混合体：regular 片段后加 `" ​"`，跟随 ins/del 的 regular 片段前加 `"​ "`。ZWSP（U+200B）是 Unicode 类别 `Cf`（格式），按 `.isspace()` 不是空白，因此 `.strip()` 在 ZWSP 处停止，相邻的字面空格存活。**在撰写第一个非拉丁文字 TC 段落之前完整阅读规则 1；不要遍历空白候选。**试错路径每次失败约耗费 6-8 次工具调用；阅读一次规则 1 零成本。

非拉丁文字要么完全没有词间空格书写（CJK、泰文、老挝文、高棉文），要么携带 `fix_spacing` 处理可靠性较低的字符类别（西里尔文、希腊文、阿拉伯文、希伯来文、天城文）。无论哪种方式，英文译者必须**制造**英文在片段边界需要的空白。如果 `en_segments` 是 `{"regular": "the contract"}, {"ins": "provisions"}, {"regular": " apply to"}`，输出读作 `"the contractprovisions apply to"`——一种视图没问题，另一种将两个词碰撞在一起。

四条规则，应用于每个 `en_segments` 数组：

1. **用可见空格 + ZWSP 混合体为每个 regular↔ins/del 接缝加书挡（这是默认值——仔细阅读，以下两种故障模式都已在生产中观察到）。**在与 ins/del 相邻的 regular 片段的*尾*边，追加 `" ​"`（一个字面空格，然后 U+200B ZWSP）。在跟随 ins/del 的 regular 片段的*首*边，前置 `"​ "`（ZWSP，然后一个字面空格）。可见空格给读者在渲染的 docx 中一个真实分隔符；ZWSP 将空格锚定穿过 `apply_translations_textmatch.py` 的 `.strip()`（它按 `str.isspace()` 剥离首尾空白，但在 ZWSP 处停止，因为 ZWSP 是 Unicode 类别 `Cf` 而非空白），ZWSP 也被 `validate_apply` 视为标记边界并被 `strip_noop_tracked_changes` 过滤掉。混合体恰好避免两种故障模式：

   - **仅字面空格**——应用 `.strip()` 剥离首尾空白，接缝在渲染视图和验证器标记视图中都最终粘连（`"theInvestment"`、`"of500262.5MW on"`）。
   - **仅纯 ZWSP**——穿过 `.strip()` 存活（验证器标记视图没问题，因为分词器在 ZWSP 处拆分），但 ZWSP 是零宽的，因此*渲染*的 docx 仍读作 `"theInvestment"` / `"of500MW"`。Markdown / `pandoc` 预览看起来正确，因为它们将 ZWSP 折叠为空白，但 Word 不会。这是在一份日语担保人保函 MOU 运行中报告的故障模式。

   对于仅包含数字或其他非字母内容的 ins/del 片段（如 `"500"`、`"262.5"`），ins/del 内部不需要进一步加书挡——regular 侧处理分隔符。对于包含字母文本且直接与另一个 ins/del 相邻的 ins/del 片段（它们之间没有 regular，如 `ins("Loan")` 紧随 `del("Investment")`），在内边加 `"​"`（仅 ZWSP）书挡——两个连续 ins/del 片段之间没有渲染读者，因此可见空格的一半不必要，添加它会在两侧接受或拒绝渲染时产生双空格。一行配方：**regular 侧携带可见空格 + ZWSP；ins↔ins 或 ins↔del 接缝仅携带 ZWSP。**

   示例（在一份日语担保人保函 MOU 重新运行中验证，即应用混合体之前产生 "of500262.5MW on" 的案例）：
   ```json
   {"type": "regular", "en": "with installed capacity of ​"},
   {"type": "ins",     "en": "500"},
   {"type": "del",     "en": "262.5"},
   {"type": "regular", "en": "​ MW on the Commercial Operation Date"}
   ```

   字母 ins/del 与字母 regular 相邻的示例：
   ```json
   {"type": "regular", "en": "the ​"},
   {"type": "ins",     "en": "​Investment​"},
   {"type": "regular", "en": "​ Insurance"}
   ```

   纯 ZWSP 书挡（`"​"` 仅，无可见空格）仅在至少一侧已有自然标点——句号、逗号、分号、开或闭括号、破折号——时才可接受，这样渲染文本从标点本身获得真实视觉分隔符。对于字母-字母或字母-数字边界（法律英语散文中常见情况），使用上述混合体。
2. **绝不使用数字结束片段。**TC 边界上的数字加上另一侧的字母会产生 `"2025the"` / `"Clause5"`。将数字保持在它们片段的中间。
3. **冠词位于包含名词的 ins/del 内部。**与前文"拒绝全部语法"小节相同的规则；在没有空白缓冲的情况下此处咬得更狠。
4. **绝不使用介词结束 regular 片段。**孤立介词出现在 reject-all 中。将介词 + 宾语保持在同一个片段中。

`validate_segment_shapes.py`（通用，已在每个 TC 文档上运行）机械捕获违规。这些规则是保持检查器沉默的提示侧配套。

**兜底：`fix_spacing` 覆盖 ins↔del 接缝。**`post_process.py` 的 `fix_spacing` 现在按文档顺序同时遍历 `<w:t>` 和 `<w:delText>`，因此在插入运行与相邻删除的删除线文本之间的 alpha+alpha 碰撞会自动插入空格。reject-all 视图中的可见粘连（由 `regular("the")` 和 `regular(" Insurance")` 之间的 `del("Investment")` 产生的 `"theInvestment Insurance"`）无需操作者干预即可修复。ZWSP 仍是验证器标记视图的推荐书挡——两层互补，而非冗余。

**Rev20：混合体现在是上文规则 1 中的默认值（曾是 注意事项）。**措辞将可见空格 + ZWSP 混合体呈现为纯 ZWSP 默认值下的"当可读性重要时"例外，从上往下读的操作者先选中了纯 ZWSP。纯 ZWSP 在 Word 中对字母-字母边界（常见情况）渲染为粘连，因此呈现顺序被翻转：混合体是默认值，纯 ZWSP 是较窄的情况。完整配方和示例见上文规则 1。

**Rev18：不要使用 Symbol 其他字符（○ □ △ ◯ ■ ●）作为占位符。**日文、中文和韩文文档常用 ``○``（U+25CB）表示空白的日期/数字单元格（``○年○月○日`` = 年/月/日空白）。这些字符是 Unicode 类别 ``So``，`strip_noop_tracked_changes._is_noise_only` 将其视为噪音——任何内容仅为一个此类符号的 `<w:ins>` 或 `<w:del>` 包装器会在步骤 6 期间被移除，在红线中留下空洞并触发步骤 6 结束时的 validate_apply 漂移错误。**对占位符单元格使用数字 ``0``**（或 ``X``、``_``）；它们是字母数字，能穿过 `strip_noop` 存活。技能不会自动替换，因为某些占位符是有内容的（复选框上的真实 ``○`` 标记），因此操作者必须在翻译时选择。

## 内部合规检查 — 04-translate

在进入下一步之前，确认：

- [ ] 你翻译了源文的每个段落（无跳过、无摘要）
- [ ] 你保持在每批 ≤35 段的上限内
- [ ] 你在每批后运行了 `validate_translations.py`（步骤 4b）
- [ ] 你为每个定义部分段落填充了 `en_runs`
- [ ] 你为每个 TC 段落生成了 `en_segments`（无捷径）

如果任何检查不确定，停止。重新阅读本文件。不要继续。

**下一步：** `skill-docs/04b-translate-gates.md`
