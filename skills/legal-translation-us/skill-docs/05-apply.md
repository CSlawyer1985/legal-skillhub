> **预检。**你应在完成上一步后进入本步骤。**SKILL.md 管辖每个步骤的纪律；如果本会话尚未完整阅读 SKILL.md，停止并在继续前 `Read('SKILL.md')`。**SKILL.md 中的硬规则同样适用于本步骤。**在聊天模式（无工作区文件夹、无自动管理的待办列表）下，同样的纪律适用——不要略读本步骤文档，不要合并批次，不要跳过底部的分步内部合规检查。**如果本轮始于压缩后的记录，压缩摘要不视为已阅读本步骤文档——在任何工具调用前立即完整 `Read()` 它。**

### 步骤 5：直接将翻译应用到原始文件

*[内部合规检查——不要向用户复述或转述。执行前重新阅读本步骤中的每条规则。不要偏离技能的任何一行。不要合并工作、跳过检查或“为效率而变通”——以往的每次偏离都产生了低于技能设计质量要求的输出。技能的硬门禁无论如何都会阻止偏离；事先合规总是比撞上门禁后重写 paragraphs.json 更快。]*

**区分技能门禁与脚本错误。**如果 `apply_translations_textmatch.py` 以代码 2 退出、抛出提及 `BLOCK` 的 `RuntimeError`，或打印 `SKILL GATE FIRED — INTENTIONAL BLOCK, NOT A SCRIPT ERROR` 横幅，那是门禁有意触发。脚本没有崩溃、没有截断、没有缺陷。阅读退出/抛出前紧邻打印的 BLOCK 消息——它准确告诉你哪个门禁触发（定义部分缺少 en_runs、逐批上限超限、validate_apply 标记不匹配、剥离后漂移等）以及如何修复 `paragraphs.json`。**不要通过以下方式绕过门禁：从绕过自动调用验证器的包装器调用 `textmatch_apply()`、抑制 `--strict` 标志，或修补脚本使其返回成功。**门禁存在是因为每次操作者绕过它们交付的输出都低于技能设计应达到的质量。修复根本问题并重新运行应用；这总是比变通方法更快。

```bash
python <skill-path>/scripts/apply_translations_textmatch.py \
  <original_source_language>.docx \
  <workdir>/paragraphs.json \
  <workdir>/final/word/document.xml
```

这是最重要的单一步骤。它一次完成所有事情：

1. 直接从源 .docx ZIP 读取原始 document.xml
2. 对 paragraphs.json 中的每个翻译条目，**匹配源语言文本**以找到正确的原始段落（自动处理任何索引偏移）
3. 仅用新的英文 run 替换 w:r（文本 run）元素
4. 保留所有段落属性（样式、编号、缩进、间距）
5. 恢复原始命名空间声明（防止 Word 中“unreadable content”错误）
6. **验证命名空间完整性**——扫描文档正文中任何已使用但未在根元素中声明的前缀，并注入缺失的声明。这捕获原始 .docx（尤其是 .doc→.docx 转换）在嵌入元素上使用 `a:` 或 `pic:` 等命名空间而未在根中声明的情形。没有此项，Word 将以 422/unreadable-content 错误拒绝打开文件。
7. **剥离语言标签**（`w:lang` 元素）——从 run 级和段落级属性中。源文档在每个 run 上携带 `w:lang val="it-IT"`（或类似）；如果这些存活进英文输出，Word 会在每个段落上显示“Changed to English (UK)”跟踪更改。移除 `w:lang` 让 Word 自动检测语言。
8. **剥离修订跟踪属性**（`w:rsidR`、`w:rsidRDefault`、`w:rsidRPr`、`w:rsidP` 等）——从所有元素中。这些导致 Word 在输出中将格式变更显示为跟踪更改。
9. **扫描源语言残留**——应用所有替换后，扫描整个输出 XML 中的常见源语言单词，并报告任何发现及其周围上下文。这捕获段落级替换遗漏的拆分 run 段落、结构化文档标签或嵌套元素中的文本。

脚本打印摘要，显示精确与偏移匹配及任何未匹配条目。目标：零样式/编号不匹配。

**辅助 XML 文件（编号、页眉/页脚、批注、脚注、尾注）在步骤 8 中单独翻译——见下文步骤 8。**步骤 5 只修改 `document.xml`。步骤 6 对 `document.xml` 后处理。步骤 7 重排 `document.xml` 中的定义。所有其他 XML 部件等到步骤 8。

## 内部合规检查 — 05-apply

在进入下一步骤前，确认：

- [ ] 你运行了 `apply_translations_textmatch.py` 并让它自动调用所有应用前门禁
- [ ] 除非粗体丢失确实可接受，否则你没有传递 `--allow-bold-loss`
- [ ] 你阅读了每个门禁输出（segment_shapes、reject_all、validate_en_runs、validate_apply）
- [ ] 没有门禁退出码 2 被抑制或绕过

如有任何检查不确定，停止。重新阅读本文件。不要继续。

**下一步：** `skill-docs/06-postprocess-and-reorder.md`
