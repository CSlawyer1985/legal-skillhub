> **预检。**你应在完成上一步后进入本步骤。**SKILL.md 管辖每个步骤的纪律；如果本会话尚未完整阅读 SKILL.md，停止并在继续前 `Read('SKILL.md')`。**SKILL.md 中的硬规则同样适用于本步骤。**在聊天模式（无工作区文件夹、无自动管理的待办列表）下，同样的纪律适用——不要略读本步骤文档，不要合并批次，不要跳过底部的分步内部合规检查。**如果本轮始于压缩后的记录，压缩摘要不视为已阅读本步骤文档——在任何工具调用前立即完整 `Read()` 它。**

### 步骤 4b：批次之间验证翻译

`validate_translations.py` 在步骤 4 的**每个批次**后运行，在操作者继续前捕获截断的翻译。此前位于此处的最终应用前遍次现在在步骤 5（`apply_translations_textmatch.py`）内部自动调用，因此最后一个批次后没有单独的步骤 4b 命令——步骤 5 自动触发它。

逐批调用（步骤 4 中每个批次后仍需要）：

```bash
python <skill-path>/scripts/validate_translations.py <workdir>/paragraphs.json
```

脚本报告：
- **PASS**：比率可接受——继续。
- **WARN**（退出码 1）：有些段落比率偏低——审查并确实不完整时重新翻译；允许继续。
- **BLOCK**（退出码 2）：一个或多个段落严重过短——继续前重新翻译。

**应用前门禁（含跟踪更改的文档）和应用后标记检查在步骤 5 内部自动运行。**`apply_translations_textmatch.py` 在开始时自动调用 `validate_en_runs.py`（定义部分粗斜体门禁）+ `validate_segment_shapes.py` + `validate_reject_all.py`（仅含跟踪更改的文档），在结束时调用 `validate_apply.py --strict`。操作者运行一个命令（步骤 5）即免费获得全部五个门禁——没有单独的对应命令，也没有跳过它们的标志。

如需在步骤 5 前手动预检（可选——门禁会自动触发）：

```bash
python <skill-path>/scripts/validate_segment_shapes.py <workdir>/paragraphs.json
python <skill-path>/scripts/validate_reject_all.py <workdir>/paragraphs.json
```

每个门禁捕获什么：

* **`validate_segment_shapes.py`** 成对且逐段扫描 `en_segments` 中的 XML 边界风险形状——冠词或介词落在错误段中、数字正好坐在跟踪更改边界上、两个字母字符跨边界无空白碰撞（非拉丁文字陷阱）、双空格横跨边界、仅含裸冠词的 ins/del、内部驼峰式冲突。每个命中点名规则、指向违规边界并建议重写。
* **`validate_reject_all.py`** 从 `en_segments` 重建接受全部和拒绝全部视图，并扫描两者中的机械可读性缺陷——双冠词（`the respective the`）、重复词、孤立介词、标点后接字母粘连冲突、双空格、空括号/引号、禁用搭配列表。命中表明冠词/介词/空白字符位于跟踪更改边界的错误一侧；重写规则见步骤 4 下“拒绝全部的语法”小节。

### 步骤 4c：解决断裂的交叉引用

源 `.doc` 文件经常包含断裂的域代码，在 Word 中渲染为“Error: Reference source not found”，如果不处理会存活进翻译。扫描 `paragraphs.json` 中任何包含该字符串（或其源语言等价物）的 `text` 字段。对每处：

1. **从上下文识别预期目标。**在定义段落中，模式是“`[Defined Term]` has the meaning set out in Section Error: Reference source not found”（美式默认）/“…in Clause Error: Reference source not found”（英式）——目标部分通常可从术语本身推断（例如“FAC”→最终验收部分，“Liquidated Damages”→延误违约金部分）。
2. **仅替换 `en` 字段**为正确的部分编号（例如美式默认下“Section 8.1”；`--variant uk` 下“Clause 8.1”）。不要修改 `text` 字段——文本匹配依赖它保持原样。
3. **如果目标确实有歧义**，将错误标记渲染为“[cross-reference to be confirmed]”，而非携带原始错误文本。

### 步骤 4d：词汇表合规扫描（应用前）— 强制

在将翻译应用到文档 XML 之前，对 `paragraphs.json` 运行自动词汇表合规扫描。扫描强制参考词汇表和语言子词汇表的“避免”列，标记起草期间溜进 `en` / `en_deleted` / `en_segments` 字段的任何借译或硬规则违规。

```bash
python <skill-path>/scripts/lexicon_compliance.py <workdir>/paragraphs.json --stage pre-apply
```

脚本从 JSON 自动检测源语言；必要时用 `--language <name>` 覆盖，或用 `--language none` 只应用语言无关规则。退出码 0 = 干净，1 = 阻止性违规，2 = 输入/输出错误。

**脚本退出 1 时不要继续步骤 5。**对每个阻止性发现：

1. 重新打开发现中引用的子词汇表文件。
2. 定位“避免”行。
3. 从同一行选择正确表达，修补 `paragraphs.json` 中的 `en`（适用时也包括 `en_segments`）。
4. 重新运行合规扫描直到退出码 0。

警告会打印但不会阻止——审查它们以排除依赖上下文的误报（例如有意引用使用“Article N”的法规）。

### 状态文件（`.validate-state.json`）说明
`validate_translations.py` 在工作目录中写入状态文件，以强制执行逐批上限并审计批次覆盖。两条操作说明：

1. **不要 `rm` 状态文件**以“重置”验证器。沙箱可能以 `Operation not permitted` 拒绝删除，因为该文件由验证器以受限权限创建。如果需要开始新的验证遍次，让状态文件留在原地就够了——验证器会更新它。如果确实需要重置，从工作目录内使用 `python -c "import os; os.remove('.validate-state.json')"`，这在沙箱中有效，而 shell `rm` 不行。
2. **状态文件按文档作用域。**每份文档有自己的工作目录；状态文件位于其中。开始新文档时，新工作目录获得新状态文件。不要将状态文件从一份文档的工作目录复制到另一份。

## 内部合规检查 — 04b-translate-gates

在进入下一步骤前，确认：

- [ ] 你在每个批次后运行了 `validate_translations.py`（强制）
- [ ] 你解决了步骤 4c 标记的任何交叉引用
- [ ] 你运行了词汇表合规扫描（步骤 4d）并对任何命中采取了行动
- [ ] 你没有通过传递覆盖标志跳过任何门禁

如有任何检查不确定，停止。重新阅读本文件。不要继续。

**下一步：** `skill-docs/05-apply.md`
