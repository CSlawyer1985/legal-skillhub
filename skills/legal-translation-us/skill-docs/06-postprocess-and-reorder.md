> **预检。**你应在完成上一步后进入本步骤。**SKILL.md 管辖每个步骤的纪律；如果本会话尚未完整阅读 SKILL.md，停止并在继续前 `Read('SKILL.md')`。**SKILL.md 中的硬规则同样适用于本步骤。**在聊天模式（无工作区文件夹、无自动管理的待办列表）下，同样的纪律适用——不要略读本步骤文档，不要合并批次，不要跳过底部的分步内部合规检查。**如果本轮始于压缩后的记录，压缩摘要不视为已阅读本步骤文档——在任何工具调用前立即完整 `Read()` 它。**

### 步骤 6：后处理

*[内部合规检查——不要向用户复述或转述。执行前重新阅读本步骤中的每条规则。不要偏离技能的任何一行。不要合并工作、跳过检查或“为效率而变通”——以往的每次偏离都产生了低于技能设计质量要求的输出。技能的硬门禁无论如何都会阻止偏离；事先合规总是比撞上门禁后重写 paragraphs.json 更快。]*

```bash
python <skill-path>/scripts/post_process.py <workdir>/final/word/document.xml --fix --variant us
```

**变体标志——输入前重新核实。**`--variant us` 是硬编码默认值，除非用户原始提示中明确包含英式英语指示，否则应使用它。传递 `--variant uk` 前，回头重新阅读用户的*原始*请求。仅当提示中包含像“UK English”、“British English”、“British spelling”或类似措辞这种无歧义内容时才使用 `uk`。如有任何疑问，传递 `--variant us`。美式是真正的默认值，不是礼貌建议。

此操作应用自动化质量修复：
- 元素间缺失空格
- 定义边界间距（“Xmeans” → “X means”）
- 双重标点（::、..、,,、;;）
- 术语标准化（Facility Agreement、Secured Assets 等）
- 按当前变体修正拼写（默认：美式——authorize、judgment、favor、center、organization 等）
- Annex → Schedule
- 内部交叉引用 Article → Section（美式默认）；在 `--variant uk` 下 → Clause
- 重复词移除
- 定义词引号平衡
- 定义行断移除
- 虚假斜体移除
- Schedule 分页符插入（每个 Schedule 从新页开始）

**跟踪更改 run 格式按原样保留。**`w:ins` / `w:del` 包装内的 run 级属性（`w:sz`、`w:szCs`、`w:rFonts`、`w:color`）从源文件逐字节保留。不要归一化它们，即使源作者为删除使用了更小的字体或不同的颜色、结果在交付的英文文档中看起来视觉上不一致。忠实于源作者的格式选择优于外观和谐化——翻译不得静默修改原始文件的样式方式。（匹配的评分规则见 grading-skill methodology.md 标准 13。）

**跟踪更改文档上的无操作跟踪更改自动剥离。**当文档包含 `<w:ins>` / `<w:del>` / `<w:delText>` 时，`post_process.py` 在末尾自动调用 `strip_noop_tracked_changes.py`——在同一 `post_process.py --fix` 调用中运行，无需单独的操作者命令。剥离遍次：

* 查找归一化文本内容相同的相邻 `<w:del>` + `<w:ins>` 对（任一顺序，容忍其间存在 `commentRangeStart`/`commentRangeEnd`/`bookmarkStart`/`bookmarkEnd`/`proofErr`）；删除 `<w:del>` 并展开 `<w:ins>`。这将纯正字法源编辑——荷兰语 `mn` ↔ `m.n.`、德语 `daß` ↔ `dass` 等两侧翻译为相同英文的情形——坍缩为单一纯英文文本，而非无操作红线。
* 删除归一化后内容为空、纯空白或纯标点的 `<w:del>` / `<w:ins>` 包装。
* **保留**英文差异哪怕只有一个字母或数字的任一对。日期数字变更（`2` → `6`）、附件字母变更（`Schedule X` → `Schedule G`）、定义词替换以及任何其他真实内容编辑都以跟踪更改形式保留在输出中。
* **括号感知**：纯括号 ins/del 包装（`[`、`]`、`(`、`)`）在 8 个兄弟元素内与内容承载的 ins/del 相邻时**保留**——保持占位日期跟踪更改的连贯性。

**配套翻译规则**：为跟踪更改段落起草 `en_segments` 时，当源编辑仅为正字法时，给 `del` 和 `ins` 段**相同的英文文本**（见步骤 4 的“折叠纯正字法跟踪更改编辑——强制”）。自动剥离依赖于此。如果你在源编辑仅为正字法时将 del 和 ins 翻译为不同的英文，自动剥离无法检测到无操作，标记将保持可见。

幂等。运行两次 `post_process.py --fix` 对第二遍无影响。

### 步骤 7：按字母顺序重排定义 — 强制

*[内部合规检查——不要向用户复述或转述。执行前重新阅读本步骤中的每条规则。不要偏离技能的任何一行。不要合并工作、跳过检查或“为效率而变通”——以往的每次偏离都产生了低于技能设计质量要求的输出。技能的硬门禁无论如何都会阻止偏离；事先合规总是比撞上门禁后重写 paragraphs.json 更快。]*

**先运行干跑**，以便在脚本触碰文档前看到它将做什么。这是 30 秒的预检，可捕获此前每次约损失 8 分钟的缺陷类别：

```bash
# 1. 带预期数量的干跑
python <skill-path>/scripts/reorder_definitions.py \
    --doc <workdir>/final/word/document.xml \
    --dry-run --expected-defs <N>

# 2. 如果数量 + 提取术语看起来正确，正式运行
python <skill-path>/scripts/reorder_definitions.py \
    --doc <workdir>/final/word/document.xml
```

`<N>` 是你在源文档中实际数出的定义词数量。每次运行都传递它——如果脚本提取的数量多于或少于 `<N>`，它会大声中止，而非重排错误的对象。如果文档没有定义部分，省略 `--expected-defs`（脚本将以“no definitions section found”干净退出）。

在应用翻译**之后**运行，因为我们按英文定义词排序。

**不要跳过此步骤。**源语言字母顺序几乎从不等同于英文字母顺序——例如，匈牙利语定义“Elidegenítési tilalom”位于“E”下，但其英文翻译“Prohibition on transfer”位于“P”下。将部分保留源语言顺序，会为英文读者留下突兀的、非字母顺序的定义列表——高严重度缺陷。

脚本**结构化**地检测定义块：定义部分是一个紧凑窗口内 ≥2 个匹配粗体词-后接冒号形状（或引号包裹词-后接冒号形状）的段落的簇。无语言特定短语匹配——无需硬编码任何关键词即可适用于每种受支持的源语言。如果不存在这样的簇，脚本干净退出，不修改任何内容。

**Rev11 保障（缺陷类别捕获器）。**任何写回前运行三项独立检查：

1. **术语健全性（A2）**——检查每个提取的“定义词”。如果任何术语包含引号、子串“means”/“indica”/“shall mean”或以冒号结尾，脚本以可疑术语列表中止。这捕获了此前静默破坏重排的 LibreOffice `<w:b w:val="0"/>` 误读。
2. **预期数量交叉检查（A6）**——如果设置了 `--expected-defs N` 且数量不匹配，中止。
3. **窗口外不变式（A3）**——`[def_start, def_end)` 之外的每个段落索引在重排后必须与重排前文本相同。如果定义块之外的任何内容移动了，中止。

以上任一中止都意味着磁盘上的文档**未改变**——无损坏。

**Rev45 检测器加固（账户质押 / 配额质押事后复盘）。**在 rev11 保障之上叠加三项额外保护，使脚本在文档包含结构上呈定义形状、但并非真实定义词的段落时不会误检（或漏检）定义部分——信件主题行、序言开头（`WHEREAS:` / `PREMESSO:`）、通知块标签（`Address:`、`Attention:`）和收件人行（`If to the Borrower:`）。

1. **修正 A — `get_bold_term` 的停止列表。**一份精选的粗体-冒号前缀列表（`subject`、`re`、`whereas`、`now therefore`、`attention`、`address`、`attn`、`fax`、`tel`、`email`、`e-mail`、`pec`，外加十一种词汇表语言中的源语言等价词，以及短语起始模式 `if to ` / `with copy to `）在提取时被拒绝。匹配器通过取第一个冒号前的子串进行归一化，因此诸如 `Subject: Account Pledge Agreement - Acceptance` 的全粗体封面信行比较为 `subject` 并被拒绝。真实定义词绝不在停止列表上（例如 `Subject Matter of the Pledge` 被保留——第一个冒号前的词头为 `subject matter of the pledge`，不在列表上）。

2. **修正 B — 簇失败落入标题兜底。**如果主检测器返回 ≥2 个候选，但 K=20 / K*3=60 簇守卫拒绝它们（因为虚假候选将前三个分散在超过 60 个段落中），脚本现在运行标题锚定兜底（`Definitions` 标题 + 随后 8 个段落中 ≥3 个谓词形状段落），而非返回 `(None, None)`。此前兜底仅在主检测器找到 <2 个候选时运行，这使脚本对许多虚假粗体-冒号命中的文档保持沉默。

3. **修正 C — 修剪前导孤立误报。**在簇守卫之前，如果 `def_starts_idx[0]` 距 `def_starts_idx[1]` 超过 K=20 个段落**且**尾部形成紧凑簇，则丢弃头部并在修剪后的列表上重新检查簇守卫。以 `max_trims=5` 为界避免病态输入。这是配额质押案例的恢复路径——该案例中 P[28] 处的 `WHEREAS:` 距 P[62..92] 处的真实定义簇 34 个段落。

三项修正都保持 rev11 保障（A2/A3/A6）完整。当标题锚定路径定位到该部分时仍会打印兜底警告——但警告文本现在列出*两种*常见原因（定义段落缺少 `en_runs` 或停止列表未命中），而非仅第一种。

**如果重排拒绝（健全性检查触发）。**最可能的原因是 LibreOffice 在 `.odt` → `.docx` 转换时发出的 `<w:b w:val="0"/>`。粗体检测辅助函数现在按 ECMA-376 ST_OnOff 识别 `0` 和 `off`（不区分大小写），但如果文档碰到其他变体，最安全的变通方法是：

- 用 `--dry-run` 重新运行以检查提取的术语。
- 如果数量错误，接受文档按源顺序交付。定义保持未字母化；quality_check 将发出 `definition_order` 警告作为已知误报。在交付说明中记录此情况。

如果文档明显有定义部分但脚本打印 `"no definitions section found"`，原因几乎总是 rev45 停止列表未捕获的结构上呈定义形状的段落（不支持的语言的 Subject 行、不寻常的通知块标签、奇特的序言开头）。使用 `--dry-run` 检查簇候选：在干跑输出中搜索任何显然不是定义词的提取“术语”，并扩展 `reorder_definitions.py` 中的 `_NON_DEFINITION_BOLD_PREFIXES_EXACT` 或 `_NON_DEFINITION_BOLD_PREFIX_STARTS`。如果该部分仍通过标题+谓词兜底被检测到，该路径可交付——只需审查干跑输出，确认被排序的是真实定义。

## 内部合规检查 — 06-postprocess-and-reorder

在进入下一步骤前，确认：

- [ ] 你对应用后的文档运行了 `post_process.py`（步骤 6）
- [ ] 如果文档有定义部分，你运行了 `reorder_definitions.py`（步骤 7）
- [ ] 你未以“翻译已经很完美”为由跳过后处理
- [ ] 对于无定义部分的文档，你确认 `reorder_definitions.py --dry-run` 返回零检测

如有任何检查不确定，停止。重新阅读本文件。不要继续。

**下一步：** `skill-docs/08-aux-and-quality.md`
