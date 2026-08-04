> **预检。**进入本步骤前应已完成上一步骤。**SKILL.md 管辖每一步的纪律；如果本会话中尚未完整阅读 SKILL.md，停止并先 `Read('SKILL.md')` 再继续。** SKILL.md 中的硬性规则同样适用于本步骤。**在聊天模式中（无工作区文件夹、无自动管理的待办列表）同样的纪律适用——不要略读本步骤文档，不要捆绑批次，不要跳过底部的逐步骤内部合规检查。** **如果本轮对话始于压缩后的转录，压缩摘要不视为已阅读本步骤文档——在任何工具调用前现在完整 `Read()` 它。**

### 重新打包前词典合规 + 内容丢失验证——在步骤 10 中自动运行

两个重新打包前强制性门禁作为 `repack_docx.py`（步骤 10）的一部分自动运行。操作者运行步骤 10，两个门禁在任何字节写入输出 `.docx` 之前自动触发。它们没有单独的命令，也没有跳过标志。

* **词典合规扫描（重新打包前）**——对后处理后的 `document.xml` 重新运行 `lexicon_compliance.py --stage pre-repack`。捕获通过片段回退分配、批注翻译或页眉/页脚样板溜进来的任何仿译。退出码 1 = 阻塞；重新打包中止。修复 `paragraphs.json` 中有问题的 `en` / `en_segments` 条目，重新运行步骤 5，然后按顺序重新运行每个强制性的后处理步骤。不要直接修补 XML。
* **应用后内容丢失验证**——重新运行 `validate_apply.py --strict`，将 `paragraphs.json` 中声明的翻译（`en`、`en_deleted`、`en_segments`）与修改后的 `document.xml` 中实际落地的内容比较。捕获"第 5 条日期丢失"缺陷类别，即字符碎片化的括号加日期 `ins` 簇在分配期间丢失日期标记。这与步骤 5 中应用时的 `validate_apply` 调用是独立的运行：在步骤 5 和步骤 10 之间，文档被 `post_process`、`strip_noop`（在 TC 文档上从 post_process 自动调用）、`reorder_definitions`、`translate_numbering` 和 `translate_headers_footers` 修改。重新打包前运行确认这些步骤都没有丢弃标记。

如需在步骤 10 之前进行手动预检（可选——两个门禁都会自动触发）：

```bash
python <skill-path>/scripts/lexicon_compliance.py \
  <workdir>/final/word/document.xml --stage pre-repack
python <skill-path>/scripts/validate_apply.py \
  <workdir>/paragraphs.json <workdir>/final/word/document.xml --strict
```

> **分词前的片段拼接。**当段落携带 `en_segments` 时，`validate_apply.py` 在分词前先拼接片段的 `en` 文本，因此跨越 `w:ins`/`w:del` 或 `w:commentReference` 边界的词（如被批注引用拆分为 `dir` + `ection` 的 `direction`）会被匹配为读者看到的完整词，而非两个永远不会出现在应用输出中的碎片。

### 强制性重新打包前检查清单

在重新打包之前，验证所有适用的步骤都已在此文档上运行。**每个适用的步骤都是强制性的**——没有选择加入。列表分为无条件步骤（每份文档都运行）和条件步骤（仅当触发条件为真时运行）。在检查完每个适用的框之前，不要继续重新打包。

**无条件——每份文档都运行：**

1. `apply_translations_textmatch.py` — 翻译已应用到 document.xml。**自动运行 `validate_translations.py`（应用前，关键时 BLOCK），外加 `validate_segment_shapes.py` 和 `validate_reject_all.py`（应用前，仅限 TC 文档），外加 `validate_apply.py --strict`（应用后）。**无需单独调用。
2. `post_process.py --fix` — 修复间距、斜体、附表分页。**在 TC 文档上自动调用 `strip_noop_tracked_changes.py`**（折叠仅正字法的 del/ins 对 + 剥离幻影 ins 包 del 包装器）。
3. `reorder_definitions.py` — 定义按英文术语字母排序（脚本在不存在定义部分时自动检测并干净退出）。
4. `quality_check.py --verbose --aux-dir <workdir>/final` — 报告零问题。**Rev12：`--aux-dir` 是强制性的**，以便 quality_check 扫描 `numbering.xml`、`headerN.xml`、`footerN.xml` 和 `comments.xml` 中的源语言残留。
5. `repack_docx.py --paragraphs <paragraphs.json>` — 打包输出。**打包前自动运行 `lexicon_compliance.py --stage pre-repack` 和 `validate_apply.py --strict`**，外加现有的打包后源语言残留扫描。
6. 任何文档特定补丁重新应用（如编号后缀修复）。

**条件——仅当触发条件适用时运行：**

7. *（如果源文件有修订追踪）* `coalesce_fragmented_tcs.py` — 在 paragraphs.json 中合并字符碎片化 TC 簇（步骤 3b，翻译前）。
8. *（如果 numbering.xml 存在）* `translate_numbering.py` — 翻译编号格式字符串（步骤 8a）。
9. *（如果页眉/页脚包含源语言文本）* `translate_headers_footers.py`（步骤 8b）。
10. *（如果 `word/comments.xml` 存在）* `translate_comments.py` — 翻译批注（步骤 8c）。
11. *（如果源文件有脚注 / 尾注）* 翻译脚注/尾注（仅正则方法；步骤 8d）。

技能强制执行每个适用项目。步骤 1、2、3、4、5、6 每次都运行。步骤 7-11 仅在其触发条件适用时触发。**这不是选择加入。**这些检查是强制性的防漂移门禁，防止在重建之间跳过工作。

**为什么清单是强制性的。**条件块中的步骤在过去的重建中被跳过，导致定义排序、编号、页眉/页脚、批注和仿译漂移缺陷——这些缺陷已在技能中修复但未重新执行。在缺陷修复后重建时，很容易只运行更改过的步骤然后重新打包——但**所有适用的步骤都必须重新运行**，因为每个步骤都会写入 XML 文件，而从源 .docx 重新提取会重置所有之前的修改。

### 步骤 10：重新打包为 .docx

*[内部合规检查——不要向用户复述或转述。在执行前重新阅读本步骤中的每一条规则。不要偏离技能的任何一行。不要捆绑工作、跳过检查或"为效率而解释"——每一次此前的偏离都产生了低于技能设计应交付质量水平的输出。无论如何，技能的硬性门禁都会阻止偏离；提前合规总比撞上门禁并重写 paragraphs.json 更快。]*

使用 Python 重新打包脚本构建输出 .docx。**不要使用 shell `unzip` + `zip` 命令**——它们会创建目录条目和大小写冲突（`customXml/` 与 `customXML/`），导致 Windows 上的 Word 拒绝打开文件。重新打包脚本逐字节复制原始 ZIP 结构，仅替换修改过的 XML 文件：

```bash
python <skill-path>/scripts/repack_docx.py \
  <original_source_language>.docx \
  <workdir>/final/word/document.xml \
  <output>.docx \
  --paragraphs <workdir>/paragraphs.json \
  --numbering <workdir>/final/word/numbering.xml \
  --headers-footers-dir <workdir>/final \
  --comments <workdir>/final/word/comments.xml \
  --footnotes <workdir>/final/word/footnotes.xml \
  --endnotes <workdir>/final/word/endnotes.xml
```

强烈推荐 `--paragraphs`：它启用打包前自动运行的 `validate_apply.py --strict` 检查，捕获 post_process / strip_noop / reorder_definitions 在步骤 5 和步骤 10 内部打包前门禁之间引入的标记漂移。

前三个位置参数之后的每个标志在 CLI 意义上都是可选的——仅当相应步骤产生了翻译后的文件时才包含每个标志：

- `--paragraphs` — 强烈推荐；启用打包前 `validate_apply` 检查
- `--numbering` — 如果步骤 8a 产生了翻译后的 `numbering.xml`
- `--headers-footers-dir` — 如果步骤 8b 产生了翻译后的 `headerN.xml` / `footerN.xml` 文件
- `--comments` — 如果步骤 8c 产生了翻译后的 `comments.xml`
- `--footnotes`、`--endnotes` — 如果步骤 8d 产生了翻译后的脚注/尾注

脚本还自动：
- 从 `word/settings.xml` 移除 `<w:trackRevisions>`（禁用修订追踪模式）
- 跳过 ZIP 目录条目（在 Windows 上导致大小写敏感问题）
- 验证 ZIP 完整性并检查大小写冲突
- **对交付的 `.docx` 运行打包后源语言残留扫描**：从原始 `word/document.xml` 自动检测源语言，然后扫描输出中的每个散文 XML 部件（`word/document.xml`、`word/comments.xml`、`word/footnotes.xml`、`word/endnotes.xml`、每个 `header*.xml` / `footer*.xml`）中的源语言残留，使用与 `apply_translations_textmatch.py` 相同的标记列表。命中按部件分组打印为 WARNING 行；重新打包的退出码不受影响。将警告视为预检：某些命中是合法保留的内容（项目名称、实体名称、参考代码），某些表明辅助部件未被接入本次重新打包。这将静默回归守卫扩展到覆盖交付工件，而非仅工作目录状态。

> **不要在用自制的 `zipfile.writestr` 重新打包后向 .docx 追加辅助文件。**本技能的早期版本推荐那样做。仅当源 XML 由命名空间安全的翻译器产生时才有效。如果它经由 ElementTree 往返过，则前缀已被损坏（`ns1:`、`ns2:` 等），Word 将显示"内容不可读"错误。始终通过上述重新打包标志路由辅助文件，这些标志期望 `translate_comments.py` / `translate_headers_footers.py` / `translate_numbering.py` 的输出。

### 步骤 11：验证

*[内部合规检查——不要向用户复述或转述。在执行前重新阅读本步骤中的每一条规则。不要偏离技能的任何一行。不要捆绑工作、跳过检查或"为效率而解释"——每一次此前的偏离都产生了低于技能设计应交付质量水平的输出。无论如何，技能的硬性门禁都会阻止偏离；提前合规总比撞上门禁并重写 paragraphs.json 更快。]*

#### 步骤 11a — 尽职调查审计——强制性（rev40）

在进行下面的视觉检查之前，运行尽职调查审计。这个单一脚本编排工件级证据，证明所有 11 个步骤确实运行，并产生一次性的 PASS / WARN / FAIL 报告。在这里捕获跳过的步骤只需几秒；在交付后捕获则需要重新运行流程的部分。

```bash
python <skill-path>/scripts/verify_diligence.py <workdir> \
    --orig-docx <original_source>.docx \
    --docx <workdir>/final.docx \
    --variant uk \
    --mode chat   # 或 --mode cowork；如果不确定则省略
```

如果你在聊天模式下操作，传递 **`--mode chat`**（见步骤 1a 的检测信号：`<application_details>` 块、`mcp__cowork__*` MCP 工具的存在、`<env>` 工作区文件夹标志）。如果传递了 `--mode chat` 且总体结论为 FAIL 或 WARN，尽职调查报告将附加一条 Cowork 模式建议，引导用户在其下次翻译时使用漂移较低的环境。如果你在 Cowork 中则传递 `--mode cowork`；只有在你确实无法判断时才省略该标志（默认 `unknown`）。检测是机械的而非启发式的——几乎总有明确的答案。

脚本审计：
- **步骤 4 + 4b** — `paragraphs.json` 存在，`.validate-state.json` 显示每个翻译段落都已验证，无批次超过 35 段上限（或设置了 `accept_large_batch`）。
- **步骤 5** — `final/word/document.xml` 存在且规模非平凡（应用已运行）。
- **步骤 8** — 源文件中存在的每个辅助文件（`numbering.xml`、`header*.xml`、`footer*.xml`、`comments.xml`、`footnotes.xml`、`endnotes.xml`）在 `<workdir>/final/word/` 中都有翻译副本。
- **步骤 9** — `quality_check.py` 对最终文档重新运行并退出码为 0。自动包含 `--aux-dir` 和 `--with-source`。
- **步骤 10 + 11** — 最终 `.docx` 存在，作为有效 ZIP 打开，包含 `word/document.xml`。

退出码：`0` PASS（交付）、`1` WARN（审查并如有意则继续，或传递 `--strict` 将其视为 FAIL）、`2` FAIL（某步骤明显被跳过——交付前修复）、`3` 脚本完整性检查失败（重新安装技能）。

**这不是下面视觉检查的替代品。**它是覆盖审计——它确认每个步骤的*工件*存在；视觉检查确认这些工件的*质量*。两者都运行。如果尽职调查报告 FAIL，不要跳前交付——先修复缺失的步骤。

如果步骤 6 使用了 `--variant us`，这里也传递 `--variant us`——否则在 quality_check 重新运行中会触发英式拼写误报。

#### 步骤 11b — 视觉检查

验证：
- 打开时无"内容不可读"错误
- **无可见修订追踪**——文档应干净打开，无修订标记、无"已改为英语（英国）"注释，且修订追踪关闭
- **标题和标题文本适合页面边距内**——尤其是封面标题不得溢出右边距（目视检查或验证翻译后的标题字符数不比源文显著更长）
- 条款编号与原始文件匹配（1、1.1、1.2、2、2.1 等）
- 子条款标题位于正确的缩进级别
- 正文没有自动编号
- 定义词为**粗体**
- 定义按英文术语字母顺序排列
- 实质性内容中无源语言文本（包括表格单元格、签名栏、表单字段）
- **页眉或页脚中无源语言文本**——检查签名栏、草稿水印和页脚中的角色标签（它们出现在每一页上且高度可见）
- 每个 Schedule/Annex 从新页开始

## 内部合规检查 — 10-repack-and-validate

在进入下一步之前，确认：

- [ ] 你完整完成了强制性重新打包前检查清单
- [ ] 你运行了 `repack_docx.py` 并让其自动调用 validate_apply --strict
- [ ] 你在步骤 11a 运行了 `verify_diligence.py` 且报告 OVERALL: PASS（或 WARN 且所有警告已审查并属有意）
- [ ] 你运行了步骤 11b 视觉验证并审查了任何标记不匹配发现
- [ ] 没有任何残留扫描或 validate_apply 漂移被覆盖标志抑制

如果任何检查不确定，停止。重新阅读本文件。不要继续。

