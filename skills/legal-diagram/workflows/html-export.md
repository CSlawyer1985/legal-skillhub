# HTML 导出工作流

可选。通过 `render_html.py` 从 Mermaid 块和 FigureDescription 构建独立的论文式图形 HTML。由 `direct.md` 和 `tutorial.md` 调用。

## 第 1 步——选择加入

调用方传入 `html_export=true` → 跳过提示。否则在宿主支持结构化选择时呈现结构化选择，或以纯文本编号列表呈现：**HTML 报告**（推荐）/ **不，只要图表**。停止并等待回复。用户回复中的路径捕获输出路径。

## 第 2 步——收集输入

从调用方收集 `semantic_map_json`（由 `workflows/generation.md` 第 3.5 步传入）。缺失或为空时，默认为 `'{}'`——着色 JS 优雅空操作，图例隐藏。

确定 Mermaid 资源模式。优先使用 assets/vendor/mermaid.min.js 处的随附文件（技能根目录相对路径，不提交；按需通过 `python scripts/fetch_mermaid.py` 或 `render_html.py --fetch-engine` 自动获取）。缺失时，除非用户或调用方明确接受 CDN 回退，否则不加载网络 JavaScript；CLI 标志 `--allow-cdn`，固定到 `render_html.py` `MERMAID_VERSION` 中的版本（Mermaid 11.x）。

## 第 2a 步——构建 FigureDescription

字段和按类型的内容来自 `shared/figure-description-schema.md`。
- `title`：`<matter_name> — <category_label>`；回退 `<category_label> — <YYYY-MM-DD>`。
- `matter_context`：matter_type + 法域（如有）+ 一行当事方摘要。
- `caption`：按类型的一行模式。
- `overview`：3 句话（展示什么、为什么对该事项类型重要、支持什么决策）。
- `how_to_read`：按类型的图例。
- `observations`：扫描 Mermaid 块的结构，产生 3-5 条通俗语言要点。
- `caveats`：事项类型基础集 + 图表类型补充 + 日期有效性说明。

## 第 3 步——输出路径

验证用户指定的路径，否则 `./diagrams/`（不存在时创建；否则使用当前目录）。文件名 `<matter_slug>_<diagram_type>_<YYYYMMDD>.html`。冲突时追加 `_2`、`_3`。

## 第 4 步——检测运行时并渲染

**先检测上下文。** 检查 `render_html.py` 是否可达：运行 `python scripts/check_setup.py` 或测试 `python --version`。两条路径：

**渲染检查（Tier-0，尽力而为）。** 渲染之前，确认围栏 Mermaid 块预览无“Syntax error”（参见 `workflows/generation.md` 第 3.4 步）。在网页应用中这是工件预览；在 CLI 上它与导出使用的引擎相同且固定版本。

### 4a — CLI / 本地 Python 可用

转发 `workflows/generation.md` 移交的所有内容，而非剥离后的子集：

`python scripts/render_html.py --mermaid-block <block> --figure-desc <JSON> --output-path <path> --semantic-map '<semantic_map_json>' --digest-table '<digest_rows_json>' --source-path '<source_path>' --ui-lang <en|fr>`

- `--digest-table` / `--source-path`：每当第 3.6 步构建了 `digest_rows` 时必需。省略它们会静默丢弃源文档验证表（证据链）。当报告与其源文件并排交付时，添加 `--relative-links`。
- `--ui-lang`：从事项语言推导（提取的 `language_profile`，否则使用提示语言）。主导法语的注意事项使用 `fr`，否则使用 `en`。省略它会在法语事项上强制英文界面和 `html lang=en`，破坏 SKILL.md 承诺的本地化。
- `--allow-cdn`：仅在明确批准网络加载 Mermaid 后追加。

脚本返回 `{ok, output_path, file_size_kb}`。`PermissionError` → 建议替代路径，提供重试。脚本未找到或 jinja2 缺失 → 显示消息，回退到 4b。

### 4b — 网页应用 / 无本地 Python

不要自由手写页面。自由手写构建几乎无法再现模板的任何加固（透明黑色画布、无平移/缩放、无对比度切换、解析脆弱的源码）——这正是破坏评审的导出。将 `assets/html_template.html` 作为字面脚手架，仅替换数据：

1. **从模板逐字复制：** `<head>`（包括 `<meta name="color-scheme" content="light">`）、整个 `<style>` 块、所有控件/选项卡/图例标记以及整个 `<script>` 块（平移/缩放、语义着色、`enforceLabelsOnTop`、高对比度、翻转、全屏、编辑器、PNG/SVG 导出）。绝不手写重写 CSS、JS 或 Mermaid 主题。
2. **仅替换这些槽位：** `html lang`；`matter_title`、`matter_context`、`caption`、`overview`、`how_to_read`、每条观察和注意事项、每个摘要单元格；Mermaid 源码同时出现在 `<pre class="mermaid">`（HTML 转义）和 `<script id="mermaid-source" type="application/json">`（JSON 编码——JS 读取此存储区，而非 `<pre>`）；`<script id="semantic-map" type="application/json">`（JSON 编码）；Mermaid 引擎 `<script>`；以及 `ui.*` 界面字符串。
3. **转义检查清单**（手工完成模板的 Jinja `autoescape` + `tojson` 所做的工作）：对上述每个文本槽位进行 HTML 转义 `& < > " '`；对两个 `application/json` 存储区进行 JSON 编码（转义 `< > &`），确保内容中的 `</script>` 或引号无法逃逸；唯一的原始 HTML 槽位是固定的免责声明常量，绝不是事项文本。
4. **语言：** 选择与事项语言匹配的 `ui.*` 字符串集，并将 `<html lang>` 设置为匹配（主导法语的注意事项用 `fr`，否则用 `en`）。
5. **引擎：** 可用时嵌入随附的 Mermaid；固定的 CDN 脚本（`https://cdn.jsdelivr.net/npm/mermaid@<MERMAID_VERSION>/dist/mermaid.min.js`，与 `render_html.py` `MERMAID_VERSION` 同版本，Mermaid 11.x）仅在明确批准后使用。绝不硬编码旧版本；绝不切换到 ESM/`+esm` URL（脚手架加载经典 `<script>`）。

每个文件一张图（参见“多张图表”一节）。以 HTML 工件形式输出；面板允许用户复制、打开或下载。

## 第 4.5 步——渲染验证（Tier-1，可选）

**目的。** Tier-0（`workflows/generation.md` 第 3.4 步中的预览步骤）在生成前捕获解析失败。Tier-1 是导出后的门控，重新检查渲染后的 HTML 文件是否存在 Mermaid 解析错误，防范静态检查遗漏的特定版本边缘情况。

此步骤**按能力检测且完全可选。** 绝不让其缺失阻塞工作流；始终发出明确通知而非静默通过。

### 当 CLI 上可用 mmdc（mermaid-cli）时

运行：

```
python scripts/verify_render.py <output.html>
```

- 退出码 0（`clean` 或 `unverified`）— 继续到第 5 步。
- 退出码 2（`syntax_error`）— 显示错误消息，提供改进图表源码的选项，并且**不静默交付**。

### 当宿主提供无头浏览器但无 mmdc 时

若宿主提供无头浏览器或浏览器自动化驱动（Playwright、Puppeteer 或宿主提供的包装器），通过加载文件并检查 Mermaid 错误文本来验证。许多此类包装器仅支持 shell，因此请从您的 shell 运行检查，而非从 Python 子进程运行（子进程可能死锁）。两个步骤：导航到 `file://<abs-path-to-output.html>`，然后读取 `document.getElementById('diagramInner').textContent` 是否包含 `Syntax error`。

```bash
# 示例形态（替换为您的驱动）。在 Claude Code 中，捆绑的 agent-browser
# 包装器提供 navigate/eval 动词；其他宿主使用自己的驱动。
<driver> navigate "file://<abs-path-to-output.html>"
<driver> eval "document.getElementById('diagramInner').textContent.includes('Syntax error')"
```

若 eval 返回 `true`，则存在 Mermaid 解析错误——显示它并且不静默交付。

### 当无渲染器可用时

发出明确说明：“图表未经渲染验证——安装 `@mermaid-js/mermaid-cli`（`npm i -g @mermaid-js/mermaid-cli`）并重新运行 `python scripts/verify_render.py <output.html>` 以确认图表渲染正常。”

绝不将渲染器缺失视为静默通过。

### 网页应用路径（4b）

依赖 `workflows/generation.md` 第 3.4 步中的 Tier-0 工件预览。无服务端渲染器可用，因此跳过 Tier-1。导出前 Tier-0 必须已确认干净渲染。

---

## 多张图表

一个事项通常需要多张图表。模板按设计为每文件一张图：其 ID（`#diagramInner`、`#mermaid-source`、`#semantic-map`、`#editor`）都是单数的，因此将多个块堆叠到一页中只会连接第一个，并使其余块的平移/缩放、着色、编辑和导出失效。

- 将每张图表渲染为**自己的文件**：每张图循环一次第 4 步，文件名后缀 `_1`、`_2`、……。每个文件携带完整的框架、控件、对比度和缩放。
- 绝不自由手写将多个 `pre.mermaid` 块捆绑到一页中（评审者的 5 合 1 失败）。单一组合式多节页面需要将模板重写为按节限定作用域的 ID；这超出此处范围。
- 几何 `split` 判定（`workflows/generation.md` 第 3.4 步）产生 N 张图表；按此规则将它们导出为 N 个文件，由共享的源文档摘要表联结。

## 第 5 步——确认

**CLI 路径：** 打印“HTML exported to: `<path>`.”（HTML 已导出到：`<path>`。）
**网页应用路径：** 打印“HTML figure ready in the artifact panel — open, copy, or download from there.”（HTML 图形已在工件面板中就绪——可从中打开、复制或下载。）

HTML 嵌入转义后的图表源码、图形描述、ARIA 选项卡面板、带标签的胶囊控件（放大、缩小、重置、高对比度、翻转、全屏）、保存/导出菜单（PNG、SVG、HTML）以及用于调整 Mermaid 源码的高级编辑器披露区。当随附的 mermaid.min.js（技能根目录下的 assets/vendor/）嵌入导出时完全自包含；否则显示仅源码讲解面板，除非使用 `--allow-cdn`。描述生成后为静态内容。
