> **预检。**你应在完成上一步后进入本步骤。**SKILL.md 管辖每个步骤的纪律；如果本会话尚未完整阅读 SKILL.md，停止并在继续前 `Read('SKILL.md')`。**SKILL.md 中的硬规则同样适用于本步骤。**在聊天模式（无工作区文件夹、无自动管理的待办列表）下，同样的纪律适用——不要略读本步骤文档，不要合并批次，不要跳过底部的分步内部合规检查。**如果本轮始于压缩后的记录，压缩摘要不视为已阅读本步骤文档——在任何工具调用前立即完整 `Read()` 它。**

### 重新打包前词汇表合规 + 丢失内容验证——在步骤 10 中自动运行

两个重新打包前强制门禁作为 `repack_docx.py`（步骤 10）的一部分自动运行。操作者运行步骤 10，两个门禁在向输出 `.docx` 写入任何字节之前自动触发。没有单独的对应命令，也没有可跳过的标志。

* **词汇表合规扫描（重新打包前）**——在已后处理的 `document.xml` 上重新运行 `lexicon_compliance.py --stage pre-repack`。捕获通过段兜底分配、批注翻译或页眉/页脚样板渗入的任何借译。退出码 1 = 阻止；重新打包中止。修复 `paragraphs.json` 中有问题的 `en` / `en_segments` 条目，重新运行步骤 5，然后按顺序重新运行每个强制的后处理步骤。不要直接修补 XML。
* **应用后丢失内容验证**——重新运行 `validate_apply.py --strict`，将 `paragraphs.json` 中声明的翻译（`en`、`en_deleted`、`en_segments`）与落在修改后 `document.xml` 中的内容比较。捕获“条款 5 丢失日期”类缺陷——字符碎片化的括号加日期 `ins` 簇在分配期间丢失日期标记。这是与步骤 5 中应用时 `validate_apply` 调用分离的独立运行：在步骤 5 与步骤 10 之间，文档被 `post_process`、`strip_noop`（在含跟踪更改的文档上从 post_process 自动调用）、`reorder_definitions`、`translate_numbering` 和 `translate_headers_footers` 修改。重新打包前运行确认这些步骤都没有丢弃标记。

如需步骤 10 前手动预检（可选——两个门禁都会自动触发）：

```bash
python <skill-path>/scripts/lexicon_compliance.py \
  <workdir>/final/word/document.xml --stage pre-repack
python <skill-path>/scripts/validate_apply.py \
  <workdir>/paragraphs.json <workdir>/final/word/document.xml --strict
```

> **分词前的段拼接。**当段落携带 `en_segments` 时，`validate_apply.py` 在分词前拼接段的 `en` 文本，因此横跨 `w:ins`/`w:del` 或 `w:commentReference` 边界的词（例如被批注引用拆分为 `dir` + `ection` 的 `direction`）按读者看到的完整词匹配，而非按两个绝不会出现在应用输出中的碎片。

### 强制重新打包前检查清单

重新打包前，验证所有适用步骤都已在该文档上运行。**每个适用步骤都是强制的**——没有可选加入。列表分为无条件步骤（每份文档都运行）和条件步骤（仅当触发条件为真时运行）。直到每个适用项都被勾选，才进行重新打包。

**无条件——每份文档都运行：**

1. `apply_translations_textmatch.py`——翻译已应用到 document.xml。**自动运行 `validate_translations.py`（应用前，关键问题阻止）、`validate_segment_shapes.py` 和 `validate_reject_all.py`（应用前，仅含跟踪更改的文档），以及 `validate_apply.py --strict`（应用后）。**无需单独调用。
2. `post_process.py --fix`——间距、斜体、Schedule 分页符已修复。**在含跟踪更改的文档上自动调用 `strip_noop_tracked_changes.py`**（折叠纯正字法 del/ins 对 + 剥离 ins 包 del 幽灵包装）。
3. `reorder_definitions.py`——定义已按英文术语字母顺序排序（脚本自动检测无定义部分并干净退出）。
4. `quality_check.py --verbose --aux-dir <workdir>/final`——报告零问题。**Rev12：`--aux-dir` 为强制**，使 quality_check 扫描 `numbering.xml`、`headerN.xml`、`footerN.xml` 和 `comments.xml` 中的源语言残留。
5. `repack_docx.py --paragraphs <paragraphs.json>`——打包输出。**打包前自动运行 `lexicon_compliance.py --stage pre-repack` 和 `validate_apply.py --strict`**，外加既有的打包后源语言残留扫描。
6. 任何文档特定补丁已重新应用（例如编号后缀修复）。

**条件——仅当触发器适用时运行：**

7. *（若源文件有跟踪更改）* `coalesce_fragmented_tcs.py`——字符碎片化跟踪更改簇已在 paragraphs.json 中合并（步骤 3b，翻译前）。
8. *（若 numbering.xml 存在）* `translate_numbering.py`——编号格式字符串已翻译（步骤 8a）。
9. *（若页眉/页脚包含源语言文本）* `translate_headers_footers.py`（步骤 8b）。
10. *（若 `word/comments.xml` 存在）* `translate_comments.py`——批注已翻译（步骤 8c）。
11. *（若源文件有脚注 / 尾注）* 脚注/尾注已翻译（纯正则方法；步骤 8d）。

技能强制执行每个适用项。步骤 1、2、3、4、5、6 每次都运行。步骤 7-11 仅当其触发器适用时触发。**这不是可选加入。**这些检查是强制性的防漂移门禁，防止重建之间跳过工作。

**为什么清单是强制的。**条件块中的步骤在过去的重建中被跳过，导致定义排序、编号、页眉/页脚、批注和借译漂移缺陷——这些已在技能中修复但未重新执行。修复缺陷后重建时，很容易只运行变更的步骤然后重新打包——但**所有适用步骤都必须重新运行**，因为每个步骤都写入 XML 文件，而从源 .docx 重新提取会重置所有先前的修改。

### 步骤 10：重新打包为 .docx

*[内部合规检查——不要向用户复述或转述。执行前重新阅读本步骤中的每条规则。不要偏离技能的任何一行。不要合并工作、跳过检查或“为效率而变通”——以往的每次偏离都产生了低于技能设计质量要求的输出。技能的硬门禁无论如何都会阻止偏离；事先合规总是比撞上门禁后重写 paragraphs.json 更快。]*

使用 Python 重新打包脚本构建输出 .docx。**不要使用 shell `unzip` + `zip` 命令**——它们会创建目录条目和大小写冲突（`customXml/` 与 `customXML/`），导致 Windows 上的 Word 拒绝打开文件。重新打包脚本逐字节复制原始 ZIP 结构，只替换修改后的 XML 文件：

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

强烈推荐 `--paragraphs`：它启用自动运行的打包前 `validate_apply.py --strict` 检查，捕获步骤 5 与步骤 10 内部打包前门禁之间由 post_process / strip_noop / reorder_definitions 引入的标记漂移。

前三个位置参数之后的每个标志在命令行术语上都是可选的——仅当相应步骤产生了翻译文件时才包含：

- `--paragraphs` — 强烈推荐；启用打包前 `validate_apply` 检查
- `--numbering` — 若步骤 8a 产生了翻译后的 `numbering.xml`
- `--headers-footers-dir` — 若步骤 8b 产生了翻译后的 `headerN.xml` / `footerN.xml` 文件
- `--comments` — 若步骤 8c 产生了翻译后的 `comments.xml`
- `--footnotes`、`--endnotes` — 若步骤 8d 产生了翻译后的脚注/尾注

脚本还自动：
- 从 `word/settings.xml` 移除 `<w:trackRevisions>`（禁用跟踪更改模式）
- 跳过 ZIP 目录条目（在 Windows 上导致大小写敏感问题）
- 验证 ZIP 完整性并检查大小写冲突
- **对交付的 `.docx` 运行重新打包后源语言残留扫描**：从原始 `word/document.xml` 自动检测源语言，然后扫描输出中的每个散文 XML 部件（`word/document.xml`、`word/comments.xml`、`word/footnotes.xml`、`word/endnotes.xml`、每个 `header*.xml` / `footer*.xml`）中的源语言残留，使用 `apply_translations_textmatch.py` 使用的相同标记列表。命中按部件分组打印为 WARNING 行；重新打包的退出码不受影响。将警告视为预检：有些命中是合理保留的内容（项目名称、实体名称、参考代码），有些表明某个辅助部件未接入本次重新打包。扩展了 中新增的静默回归守卫，覆盖交付工件而非仅工作目录状态。

> **重新打包后，不要用手写的 `zipfile.writestr` 将辅助文件追加到 .docx。**技能早期版本推荐这样做。它*仅*在源 XML 由命名空间安全的翻译器产生时有效。如果它经过 ElementTree 往返，前缀已损坏（`ns1:`、`ns2:` 等），Word 将显示“unreadable content”错误。始终通过上述重新打包标志路由辅助文件，这些标志预期 `translate_comments.py` / `translate_headers_footers.py` / `translate_numbering.py` 的输出。

### 步骤 11：验证

*[内部合规检查——不要向用户复述或转述。执行前重新阅读本步骤中的每条规则。不要偏离技能的任何一行。不要合并工作、跳过检查或“为效率而变通”——以往的每次偏离都产生了低于技能设计质量要求的输出。技能的硬门禁无论如何都会阻止偏离；事先合规总是比撞上门禁后重写 paragraphs.json 更快。]*

#### 步骤 11a — 勤勉审计 — 强制（rev40）

进行下述视觉检查前，运行勤勉审计。这一个脚本编排了全部 11 个步骤确实运行的工件级证据，并产生一次性 PASS / WARN / FAIL 报告。在这里捕获跳过的步骤花费数秒；交付后再捕获需要重新运行部分流水线。

```bash
python <skill-path>/scripts/verify_diligence.py <workdir> \
    --orig-docx <original_source>.docx \
    --docx <workdir>/final.docx \
    --variant us \
    --mode chat   # 或 --mode cowork；不确定时省略
```

**如果你在聊天模式下操作，传递 `--mode chat`**（见步骤 1a 检测信号：`<application_details>` 块、存在 `mcp__cowork__*` MCP 工具、`<env>` 工作区文件夹标志）。如果传递了 `--mode chat` 且总体判定为 FAIL 或 WARN，勤勉报告将附加 Cowork 模式建议，引导用户下次翻译使用漂移更低的环境。如果你在 Cowork 模式，传递 `--mode cowork`；只有在你确实无法判断时才省略该标志（默认 `unknown`）。检测是机械的，而非启发式——几乎总有明确答案。

脚本审计：
- **步骤 4 + 4b** — `paragraphs.json` 存在，`.validate-state.json` 显示每个翻译段落都已验证，无批次超过 35 段上限（或设置 `accept_large_batch`）。
- **步骤 5** — `final/word/document.xml` 存在且大小非平凡（应用已运行）。
- **步骤 8** — 源中存在的每个辅助文件（`numbering.xml`、`header*.xml`、`footer*.xml`、`comments.xml`、`footnotes.xml`、`endnotes.xml`）在 `<workdir>/final/word/` 中都有翻译副本。
- **步骤 9** — `quality_check.py` 对最终文档重新运行且退出码 0。自动包含 `--aux-dir` 和 `--with-source`。
- **步骤 10 + 11** — 最终 `.docx` 存在、作为有效 ZIP 打开、包含 `word/document.xml`。

退出码：`0` PASS（交付）、`1` WARN（审查并在有意时继续，或传递 `--strict` 视为 FAIL）、`2` FAIL（某步骤被明确跳过——交付前修复）、`3` 脚本完整性检查失败（重新安装技能）。

**这不能替代下述视觉检查。**它是覆盖审计——确认每个步骤的*工件*存在；视觉检查确认这些工件的*质量*。两者都运行。如果勤勉报告 FAIL，不要跳到交付——先修复缺失的步骤。

如果步骤 6 使用了 `--variant uk`，这里也传递 `--variant uk`——否则美式拼写误报会在 quality_check 重跑中触发。

#### 步骤 11b — 视觉检查

验证：
- 打开时无“unreadable content”错误
- **无可见跟踪更改**——文档应干净打开，无修订标记、无“Changed to English (UK)”注释，跟踪更改关闭
- **标题和页眉文本适合页面边距内**——封面页标题尤其不得溢出右边距（目视检查或验证翻译标题的字符数未显著长于源文）
- 条款编号与原始文件匹配（1、1.1、1.2、2、2.1 等）
- 子条款标题缩进级别正确
- 正文无自动编号
- 定义词为**粗体**
- 定义按英文术语字母顺序排列
- 实质性内容（含表格单元格、签名块、表单字段）无源语言文本
- **页眉或页脚无源语言文本**——检查页脚中的签名块、草稿水印和角色标签（它们出现在每一页且高度可见）
- 每个 Schedule/Annex 从新页开始

## 内部合规检查 — 10-repack-and-validate

在进入下一步骤前，确认：

- [ ] 你完整完成了强制重新打包前检查清单
- [ ] 你运行了 `repack_docx.py` 并让它自动调用 validate_apply --strict
- [ ] 你在步骤 11a 运行了 `verify_diligence.py` 且它报告 OVERALL: PASS（或 WARN 且所有警告已审查并有意接受）
- [ ] 你运行了步骤 11b 视觉验证并审查了任何标记不匹配发现
- [ ] 没有残留扫描或 validate_apply 漂移被覆盖标志抑制

如有任何检查不确定，停止。重新阅读本文件。不要继续。
