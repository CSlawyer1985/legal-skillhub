> **预检。**进入本步骤前应已完成上一步骤。**SKILL.md 管辖每一步的纪律；如果本会话中尚未完整阅读 SKILL.md，停止并先 `Read('SKILL.md')` 再继续。** SKILL.md 中的硬性规则同样适用于本步骤。**在聊天模式中（无工作区文件夹、无自动管理的待办列表）同样的纪律适用——不要略读本步骤文档，不要捆绑批次，不要跳过底部的逐步骤内部合规检查。** **如果本轮对话始于压缩后的转录，压缩摘要不视为已阅读本步骤文档——在任何工具调用前现在完整 `Read()` 它。**

### 步骤 4b：批次之间验证翻译

`validate_translations.py` 在步骤 4 中**每批之后**运行，以便在操作者继续之前捕获截断的翻译。此处曾经存在的最终应用前检查现在在步骤 5（`apply_translations_textmatch.py`）内部自动调用，因此最后一批之后没有单独的步骤 4b 命令——步骤 5 会自动触发它。

逐批调用（在步骤 4 中每批后仍需要）：

```bash
python <skill-path>/scripts/validate_translations.py <workdir>/paragraphs.json
```

脚本报告：
- **PASS**：比率可接受——继续。
- **WARN**（退出码 1）：某些段落比率较低——审查并在确实不完整时重新翻译；允许继续。
- **BLOCK**（退出码 2）：一个或多个段落严重过短——在继续前重新翻译。

**应用前门禁（TC 文档）和应用后标记检查在步骤 5 内部自动运行。** `apply_translations_textmatch.py` 在开始时自动调用 `validate_en_runs.py`（定义部分加粗斜体门禁）+ `validate_segment_shapes.py` + `validate_reject_all.py`（仅限 TC 文档），在结束时自动调用 `validate_apply.py --strict`。操作者运行一个命令（步骤 5）即可免费获得全部五个门禁——它们没有单独的命令，也没有跳过它们的标志。

如需在步骤 5 之前进行手动预检（可选——门禁会自动触发）：

```bash
python <skill-path>/scripts/validate_segment_shapes.py <workdir>/paragraphs.json
python <skill-path>/scripts/validate_reject_all.py <workdir>/paragraphs.json
```

每个门禁捕获的内容：

* **`validate_segment_shapes.py`** 逐对并逐片段扫描 `en_segments` 中的 XML 边界风险形状——冠词或介词位于错误的片段、数字恰好落在 TC 边界上、两个字母字符跨越边界且无空白碰撞（非拉丁文字陷阱）、横跨边界的双空格、仅含裸冠词的 ins/del、内部 camelCase 碰撞。每次命中都会指出规则名称、指向违规边界并建议改写。
* **`validate_reject_all.py`** 从 `en_segments` 重建 accept-all 和 reject-all 视图，并扫描两者的机械可读性缺陷——双冠词（`the respective the`）、重复词、孤立介词、标点后接字母连写碰撞、双空格、空括号/引号以及禁用搭配列表。命中表明冠词 / 介词 / 空白字符位于 TC 边界的错误一侧；改写规则见步骤 4 下的"拒绝全部语法"小节。

### 步骤 4c：解决损坏的交叉引用

源 `.doc` 文件经常包含损坏的域代码，在 Word 中渲染为"Error: Reference source not found"（错误：找不到引用源），如果不处理会存活到翻译中。扫描 `paragraphs.json` 中任何包含此字符串（或其源语言对应词）的 `text` 字段。对于每次出现：

1. **从上下文识别预期目标。**在定义段落中模式是"`[Defined Term]` has the meaning set out in Clause Error: Reference source not found"——目标条款通常可以从术语本身推断（如 "FAC" → 最终验收条款、"Liquidated Damages" → 延误违约金条款）。
2. **仅替换 `en` 字段**为正确的条款编号（如 "Clause 8.1"）。不要修改 `text` 字段——文本匹配依赖它保持原样。
3. **如果目标确实有歧义**，将错误标记渲染为 "[cross-reference to be confirmed]"（待确认的交叉引用），而非保留原始错误文本。

### 步骤 4d：词典合规扫描（应用前）——强制性

在将翻译应用到文档 XML 之前，对 `paragraphs.json` 运行自动化词典合规扫描。扫描执行参考词典和语言子词典的"避免"列，标记起草期间溜进 `en` / `en_deleted` / `en_segments` 字段的任何仿译或硬性规则违反。

```bash
python <skill-path>/scripts/lexicon_compliance.py <workdir>/paragraphs.json --stage pre-apply
```

脚本从 JSON 自动检测源语言；如需要可用 `--language <name>` 覆盖，或使用 `--language none` 仅应用语言无关规则。退出码 0 = 干净，1 = 阻塞性违规，2 = I/O 错误。

**脚本退出码为 1 时不要继续步骤 5。**对于每个阻塞性发现：

1. 重新打开发现中引用的子词典文件。
2. 定位"避免"行。
3. 从同一行选择正确的表达，并修补 `paragraphs.json` 中的 `en`（如适用也包括 `en_segments`）。
4. 重新运行合规扫描直到退出码为 0。

警告会打印但不阻塞——审查它们以排除依赖上下文的误报（如故意引用法规时使用 "Article N"）。

### 状态文件（`.validate-state.json`）说明
`validate_translations.py` 在工作目录中写入状态文件，以强制逐批上限并审计批次覆盖。两条操作说明：

1. **不要 `rm` 状态文件**来"重置"验证器。沙箱可能以 `Operation not permitted`（不允许操作）拒绝删除，因为该文件是由验证器以受限权限创建的。如果你需要开始一轮全新的验证，让状态文件留在原处即可——验证器会更新它。如果你确实需要重置，在工作目录内使用 `python -c "import os; os.remove('.validate-state.json')"`，这在 shell `rm` 无效的沙箱中可以工作。
2. **状态文件是文档范围的。**每份文档有自己的工作目录；状态文件位于其中。开始新文档时，新工作目录会获得新状态文件。不要将状态文件从一份文档的工作目录复制到另一份。

## 内部合规检查 — 04b-translate-gates

在进入下一步之前，确认：

- [ ] 你在每批后运行了 `validate_translations.py`（强制性）
- [ ] 你解决了步骤 4c 标记的任何交叉引用
- [ ] 你运行了词典合规扫描（步骤 4d）并处理了任何命中
- [ ] 你未通过传递覆盖标志跳过任何门禁

如果任何检查不确定，停止。重新阅读本文件。不要继续。

**下一步：** `skill-docs/05-apply.md`
