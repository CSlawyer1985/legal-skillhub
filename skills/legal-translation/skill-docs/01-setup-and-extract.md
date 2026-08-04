> **预检。**进入本步骤前应已完成上一步骤。**SKILL.md 管辖每一步的纪律；如果本会话中尚未完整阅读 SKILL.md，停止并先 `Read('SKILL.md')` 再继续。** SKILL.md 中的硬性规则同样适用于本步骤。**在聊天模式中（无工作区文件夹、无自动管理的待办列表）同样的纪律适用——不要略读本步骤文档，不要捆绑批次，不要跳过底部的逐步骤内部合规检查。** **如果本轮对话始于压缩后的转录，压缩摘要不视为已阅读本步骤文档——在任何工具调用前现在完整 `Read()` 它。**

### 步骤 1：设置和解包

*[内部合规检查——不要向用户复述或转述。在执行前重新阅读本步骤中的每一条规则。不要偏离技能的任何一行。不要捆绑工作、跳过检查或"为效率而解释"——每一次此前的偏离都产生了低于技能设计应交付质量水平的输出。无论如何，技能的硬性门禁都会阻止偏离；提前合规总比撞上门禁并重写 paragraphs.json 更快。]*

#### 步骤 1a — 聊天模式用户警告（rev41）——强制性

**在做任何其他事情之前检测你的宿主环境**：
- 满足以下任一条件则为 **Cowork 模式**：你的 `<application_details>` 系统块命名为 "Cowork mode"；存在可用的 `mcp__cowork__*` MCP 工具（如 `mcp__cowork__create_artifact`、`mcp__cowork__request_cowork_directory`）；或 `<env>` 报告已选择的工作区文件夹。
- 上述均不满足则为 **聊天模式**。

**如果你处于聊天模式，在任何工具调用前向用户逐字发布以下警告。** 根据用户在本会话中提交翻译的文档数量调整 `this document` / `these N documents`（1 份 → "this document"；≥2 份 → "these N documents"，如 "these 3 documents"）：

> 请注意，您现在正在使用 Claude Chat 翻译本文档。在聊天模式中我偏离和漂移出技能的风险更高，可能影响翻译质量。我建议在使用 legal-translation 技能翻译文档时始终使用 Cowork。

（当范围内有 ≥2 份文档时的复数形式：将 `to translate this document` 替换为 `to translate these N documents`。其他内容保持逐字不变。）

**每会话发布一次**该警告，而非每份文档一次。发布后继续步骤 1。在步骤 11a（尽职调查审计）传递 `--mode chat`，以便审计在检测到漂移时可以向其报告附加 Cowork 建议。

**如果你处于 Cowork 模式**（或存在 `mcp__cowork__*` 工具），**不要发布任何关于步骤 1a、警告或聊天/Cowork 检测的消息。**不要宣布你正在跳过该警告。不要提及你检测到了 Cowork。不要说"我处于 Cowork 模式，所以我会跳过聊天模式警告"。直接静默进入步骤 1b——用户不需要知道这次检查发生了。步骤 1a 在 Cowork 中是无操作；在向用户叙述进度时，将整个小节视为不存在。

#### 步骤 1b — 设置工作目录并转换源文件

**如果脚本以 `SyntaxError`、`NameError` 失败或打印 `FILE INTEGRITY CHECK FAILED — script truncated`（文件完整性检查失败——脚本被截断）横幅，说明安装副本在市场传输期间被截断。**打包的 `.skill` / `.zip` 归档是完整的；只有本地安装被切断。从归档重新安装技能。完整性检查在每次 CLI 调用 apply / extract / validate 脚本时运行，因此截断会在任何步骤开始时被发现，而非在过程中神秘地失败。不要通过编辑脚本绕过完整性检查失败——而是重新安装归档。

```bash
mkdir -p <workdir>
```

如果输入是 `.doc`，先转换：
```bash
python <docx-skill-path>/scripts/office/soffice.py <input>.doc --format docx
```

docx 技能路径位于 `mnt/.claude/skills/docx/scripts/office/`。

**在 `.doc` → `.docx` 转换之后：**LibreOffice 可能引入原始 `.doc` 中不可见的修订标记（`<w:ins>`、`<w:del>` 元素）。这些转换伪影将作为修订追踪出现在翻译后的输出中。运行转换清理脚本以接受任何此类伪影：

```bash
python <skill-path>/scripts/clean_conversion_artifacts.py <converted>.docx
```

这接受插入（解开 `<w:ins>`，保留内容）、移除删除（完全剥离 `<w:del>`）并移除移动标记——但仅当原始文件预期为无有意修订追踪的干净文档时。如果原始文件有意包含修订追踪（如红线稿），跳过此步骤以在翻译中保留它们。

**不要**在应用步骤（步骤 5）期间剥离修订标记——那会破坏含修订追踪文档中有意的修订追踪。

### 步骤 2：提取带格式元数据的段落

*[内部合规检查——不要向用户复述或转述。在执行前重新阅读本步骤中的每一条规则。不要偏离技能的任何一行。不要捆绑工作、跳过检查或"为效率而解释"——每一次此前的偏离都产生了低于技能设计应交付质量水平的输出。无论如何，技能的硬性门禁都会阻止偏离；提前合规总比撞上门禁并重写 paragraphs.json 更快。]*

```bash
python <skill-path>/scripts/extract_paragraphs.py <original>.docx <workdir>/paragraphs.json
```

注意：此脚本直接从 .docx ZIP 读取——无需单独解包。

**关键：多 w:t 运行。**在 .doc→.docx 转换中，LibreOffice 经常产生条款编号和正文共享单个 `<w:r>` 元素、由 `<w:tab/>` 分隔的运行：如 `<w:t>11.3.1</w:t><w:tab/><w:t>Il 10% del Corrispettivo...</w:t>`。提取脚本必须从每个运行的所有 `w:t` 子元素收集文本（而不仅仅是第一个）。使用 `r.find('{W}t')` 会静默丢弃第一个 `w:t` 之后的所有文本——这是一个数据丢失缺陷，可能使整个商业条款（付款里程碑、金融方同意权）对译者不可见。修补后的脚本遍历每个 `w:r` 的所有子元素，从每个 `w:t` 收集文本，同时跳过 `w:tab` 和 `w:br` 元素（它们在应用步骤期间保留在 XML 中）。不要在提取文本中为 `w:tab`/`w:br` 插入制表符或换行字符——应用脚本的 `get_paragraph_text()` 无分隔符地连接 `w:t` 文本，因此插入分隔符会导致文本匹配失败。

这将创建 JSON 数组，其中每个条目包含：
- `idx` — 提取时的段落索引
- `text` — 源语言的完整段落文本（来自 `w:t` 元素——即已接受/可见文本，包括 `w:ins` 包装器内的文本，但不包括 `w:del` 包装器内的文本）
- `runs` — 带格式（粗体、斜体、字体、字号）的字符范围数组
- `style` — 段落样式名称
- `en` — 待填写英文翻译
- `en_runs` — 可选：英文文本的显式格式说明
- `deleted_text` —（仅限 TC 段落）来自 `w:del` 包装器内 `w:delText` 元素的删除线文本。仅在段落包含修订追踪时存在。
- `has_track_changes` —（仅限 TC 段落）如果段落包含 `w:ins`、`w:del`、`w:moveFrom` 或 `w:moveTo` 标记则为 `true`
- `en_deleted` — 待填写 `deleted_text` 的英文翻译（见下文"修订追踪段落"）

`idx` 字段在提取期间分配，可能无法完美匹配原始 document.xml 段落索引。这是预期且无害的——应用步骤按文本内容匹配，而非按索引。

#### 脚注、尾注和批注——强制性

.docx 将脚注、尾注和批注存储在 `word/document.xml` 旁的**单独 XML 文件**中：

- `word/footnotes.xml` — 脚注内容（正文中由 `<w:footnoteReference>` 引用）
- `word/endnotes.xml` — 尾注内容
- `word/comments.xml` — 批注内容（页边注释）

**这些文件包含主提取脚本不覆盖的可翻译文本。**如果你只提取和翻译 `document.xml`，脚注/尾注/批注将在输出中停留在源语言——这是一个高严重性缺陷。

提取正文段落后，检查源 .docx 是否包含这些文件中的任何一个：

```python
import zipfile
with zipfile.ZipFile('<original>.docx') as z:
    for name in ['word/footnotes.xml', 'word/endnotes.xml', 'word/comments.xml']:
        if name in z.namelist():
            print(f'FOUND: {name} — must extract and translate')
```

对于每个存在且包含实质性文本的文件（脚注 ID -1 和 0 是标准空分隔符/续接条目——跳过它们），使用与 `document.xml` 相同的方法提取段落：查找所有 `<w:p>` 元素，从所有运行中收集 `<w:t>` 文本。将它们存储在每份 XML 一个单独的 JSON 文件中（如 `footnotes.json`、`endnotes.json`、`comments.json`），结构同 `paragraphs.json`。

**与正文一起翻译这些内容**——它们计入你的批次总数，并受同样的 35 段批次限制。将它们纳入验证运行。

## 内部合规检查 — 01-setup-and-extract

在进入下一步之前，确认：

- [ ] 你使用 soffice 将 .doc → .docx 转换（如需要），而非 pandoc
- [ ] 你检查了 `clean_conversion_artifacts.py` 的作者/比率输出，且未在红线稿上运行它
- [ ] 你使用 `extract_paragraphs.py` 生成了 `paragraphs.json`
- [ ] 你未手动编辑 document.xml 或跳过步骤 1 的完整性检查
- [ ] **如果这是本会话中的第二份或更后的文档：**你重新 `Read('SKILL.md')`，并将在到达每个步骤文件时重新 `Read()` 它；你未在假设上一份文档的阅读内容仍然有效的情况下跳过按文档刷新

如果任何检查不确定，停止。重新阅读本文件。不要继续。

**下一步：** `skill-docs/03-lexicons-and-segments.md`
