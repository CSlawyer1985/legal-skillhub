> **预检。**你应在完成上一步后进入本步骤。**SKILL.md 管辖每个步骤的纪律；如果本会话尚未完整阅读 SKILL.md，停止并在继续前 `Read('SKILL.md')`。**SKILL.md 中的硬规则同样适用于本步骤。**在聊天模式（无工作区文件夹、无自动管理的待办列表）下，同样的纪律适用——不要略读本步骤文档，不要合并批次，不要跳过底部的分步内部合规检查。**如果本轮始于压缩后的记录，压缩摘要不视为已阅读本步骤文档——在任何工具调用前立即完整 `Read()` 它。**

### 步骤 1：设置和解包

*[内部合规检查——不要向用户复述或转述。执行前重新阅读本步骤中的每条规则。不要偏离技能的任何一行。不要合并工作、跳过检查或“为效率而变通”——以往的每次偏离都产生了低于技能设计质量要求的输出。技能的硬门禁无论如何都会阻止偏离；事先合规总是比撞上门禁后重写 paragraphs.json 更快。]*

#### 步骤 1a — 聊天模式用户警告（rev41）— 强制

**在做任何其他事之前，检测你的宿主环境**：
- **Cowork 模式**：满足以下任一条件——你的 `<application_details>` 系统块标明“Cowork mode”；有 `mcp__cowork__*` MCP 工具可用（如 `mcp__cowork__create_artifact`、`mcp__cowork__request_cowork_directory`）；或 `<env>` 报告已选择工作区文件夹。
- **聊天模式**：以上均不满足。

**如果你处于聊天模式，在任何工具调用前，逐字向用户发布以下警告。**根据用户在本会话中提交翻译的文档数量调整 `this document` / `these N documents`（1 份 → “this document”；≥2 份 → “these N documents”，例如“these 3 documents”）：

> Please be aware that you are now using Claude Chat to translate this document. The risk of me deviating and drifting from the skill is higher in Chat and might impact the quality of the translation. I recommend to always use Cowork when translating documents using the legal-translation skill.

（范围内 ≥2 份文档时用复数形式：将 `to translate this document` 替换为 `to translate these N documents`。其余内容逐字保留。）

**每个会话发布一次**该警告，而非每份文档一次。发布后继续步骤 1。在步骤 11a（勤勉审计）时传递 `--mode chat`，以便审计在检测到漂移时可在报告中附加 Cowork 建议。

**如果你处于 Cowork 模式**（或存在 `mcp__cowork__*` 工具），**不要发布任何关于步骤 1a、警告或聊天/Cowork 检测的消息。**不要宣布你跳过警告。不要提及你检测到 Cowork。不要说“我处于 Cowork 模式，所以跳过聊天模式警告。”直接静默进入步骤 1b——用户不需要知道这次检查发生过。步骤 1a 在 Cowork 模式下是空操作；向用户叙述进度时，将整个小节视为不存在。

#### 步骤 1b — 设置工作目录并转换源文件

**如果脚本以 `SyntaxError`、`NameError` 失败，或打印 `FILE INTEGRITY CHECK FAILED — script truncated` 横幅，说明安装副本在市场传输中被截断。**打包的 `.skill` / `.zip` 压缩包完好；只是本地安装被切断。从压缩包重新安装技能。完整性检查在每次通过命令行调用应用/提取/验证脚本时运行，因此截断在任何步骤开始时即被发现，而不会在中途神秘失败。不要通过编辑脚本绕过完整性检查失败——重新安装压缩包。

```bash
mkdir -p <workdir>
```

如果输入是 `.doc`，先转换：
```bash
python <docx-skill-path>/scripts/office/soffice.py <input>.doc --format docx
```

docx 技能路径为 `mnt/.claude/skills/docx/scripts/office/`。

**`.doc` → `.docx` 转换后：**LibreOffice 可能引入原始 `.doc` 中不可见的修订标记（`<w:ins>`、`<w:del>` 元素）。这些转换痕迹会作为跟踪更改出现在翻译输出中。运行转换清理脚本以接受任何此类痕迹：

```bash
python <skill-path>/scripts/clean_conversion_artifacts.py <converted>.docx
```

这接受插入（展开 `<w:ins>`，保留内容）、删除删除（完全剥离 `<w:del>`）并移除移动标记——但仅当原始文件预期为无有意跟踪更改的干净文档时才如此。如果原始文件有意包含跟踪更改（例如红线稿），跳过此步骤以在翻译中保留它们。

**不要**在应用步骤（步骤 5）中剥离修订标记——那会破坏含有意跟踪更改文档中的跟踪更改。

### 步骤 2：提取带格式元数据的段落

*[内部合规检查——不要向用户复述或转述。执行前重新阅读本步骤中的每条规则。不要偏离技能的任何一行。不要合并工作、跳过检查或“为效率而变通”——以往的每次偏离都产生了低于技能设计质量要求的输出。技能的硬门禁无论如何都会阻止偏离；事先合规总是比撞上门禁后重写 paragraphs.json 更快。]*

```bash
python <skill-path>/scripts/extract_paragraphs.py <original>.docx <workdir>/paragraphs.json
```

注意：该脚本直接从 .docx ZIP 读取——无需单独解包。

**关键：多 w:t run。**在 .doc→.docx 转换中，LibreOffice 经常产生条款编号和正文共用一个 `<w:r>` 元素的 run，以 `<w:tab/>` 分隔：例如 `<w:t>11.3.1</w:t><w:tab/><w:t>Il 10% del Corrispettivo...</w:t>`。提取脚本必须从每个 run 的**所有** `w:t` 子元素收集文本（而非仅第一个）。使用 `r.find('{W}t')` 会静默丢弃第一个 `w:t` 之后的所有文本——这是一种数据丢失缺陷，可能使整个商业条款（付款里程碑、金融当事方同意权）对翻译者不可见。已修补的脚本遍历每个 `w:r` 的所有子元素，从每个 `w:t` 元素收集文本，同时跳过 `w:tab` 和 `w:br` 元素（它们在应用步骤期间保留在 XML 中）。**不要**在提取的文本中为 `w:tab`/`w:br` 插入制表符或换行符——应用脚本的 `get_paragraph_text()` 无分隔符地拼接 `w:t` 文本，因此插入分隔符会导致文本匹配失败。

这会创建一个 JSON 数组，每个条目包含：
- `idx` — 提取时的段落索引
- `text` — 源语言的完整段落文本（来自 `w:t` 元素——即已接受/可见文本，包括 `w:ins` 包装内的文本，但排除 `w:del` 包装内的文本）
- `runs` — 带格式（粗体、斜体、字体、字号）的字符范围数组
- `style` — 段落样式名称
- `en` — 待填写的英文翻译
- `en_runs` — 可选：英文文本的显式格式指令
- `deleted_text` — （仅限跟踪更改段落）来自 `w:del` 包装内 `w:delText` 元素的带删除线文本。仅当段落包含跟踪更改时存在。
- `has_track_changes` — （仅限跟踪更改段落）段落包含 `w:ins`、`w:del`、`w:moveFrom` 或 `w:moveTo` 标记时为 `true`
- `en_deleted` — 待填写的 `deleted_text` 英文翻译（见下文“跟踪更改段落”）

`idx` 字段在提取时分配，可能无法与原始 document.xml 段落索引完美匹配。这是预期且无害的——应用步骤按文本内容匹配，而非按索引。

#### 脚注、尾注和批注 — 强制

.docx 将脚注、尾注和批注存储在 `word/document.xml` 旁的**单独 XML 文件**中：

- `word/footnotes.xml` — 脚注内容（正文中由 `<w:footnoteReference>` 引用）
- `word/endnotes.xml` — 尾注内容
- `word/comments.xml` — 批注内容（页边注释）

**这些文件包含主提取脚本不覆盖的可翻译文本。**如果只提取并翻译 `document.xml`，脚注/尾注/批注将在输出中保持源语言——高严重度缺陷。

提取主正文段落后，检查源 .docx 是否包含这些文件中的任何一个：

```python
import zipfile
with zipfile.ZipFile('<original>.docx') as z:
    for name in ['word/footnotes.xml', 'word/endnotes.xml', 'word/comments.xml']:
        if name in z.namelist():
            print(f'FOUND: {name} — must extract and translate')
```

对每个存在且包含实质性文本的文件（脚注 ID -1 和 0 是标准的空分隔符/延续条目——跳过它们），使用与 `document.xml` 相同的方法提取段落：查找所有 `<w:p>` 元素，从所有 run 收集 `<w:t>` 文本。将它们按每个 XML 存储到单独的 JSON 文件中（例如 `footnotes.json`、`endnotes.json`、`comments.json`），结构与 `paragraphs.json` 相同。

**与主正文一起翻译这些**——它们计入批次总量，并受同样的 35 段批处理上限约束。将其纳入验证运行。

## 内部合规检查 — 01-setup-and-extract

在进入下一步骤前，确认：

- [ ] 你使用 soffice（而非 pandoc）完成了 .doc → .docx 转换（如需要）
- [ ] 你检查了 `clean_conversion_artifacts.py` 的作者/比率输出，且未对红线稿运行它
- [ ] 你用 `extract_paragraphs.py` 生成了 `paragraphs.json`
- [ ] 你未手动编辑 document.xml，也未跳过步骤 1 的完整性检查
- [ ] **如果这是本会话的第二份或后续文档：**你已重新 `Read('SKILL.md')`，且将在到达每个步骤文件时重新 `Read()`；你未以“上一份文档的阅读仍然有效”为由跳过每文档刷新

如有任何检查不确定，停止。重新阅读本文件。不要继续。

**下一步：** `skill-docs/03-lexicons-and-segments.md`
