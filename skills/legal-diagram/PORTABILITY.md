# 可移植性

分类：独立（standalone）

本技能完全自包含。将整个文件夹单独复制到全新机器上任何 AI 助手的技能文件夹中，即可在无需兄弟技能、知识库或机器本地路径的情况下工作。提取、类型选择和 HTML 渲染都是基于文件系统的纯 Python 实现；不调用任何外部技能或文档工具。可选辅助组件（离线 Mermaid 引擎、无头浏览器渲染验证）在缺失时优雅降级。

## 可移植面

- `SKILL.md`、`PORTABILITY.md`、`legal-diagram-readme.md`、`LICENSE`
- `requirements.txt`、`constraints.txt`
- `workflows/`、`references/`、`shared/`、`assets/`
- `scripts/`，包括 `extraction/`、`normalize/` 和 `tests/`（含合成夹具和黄金快照）

## 复制时的要求

1. 将整个技能文件夹复制到宿主助手的技能文件夹中。在 Claude Code 中是 `~/.claude/skills/legal-diagram/`；其他宿主使用各自的技能位置。
2. 一次性安装 Python 依赖：`pip install -r requirements.txt -c constraints.txt`（发布验证版本），或省略 `-c constraints.txt` 以进行广泛兼容性测试。

## 必需运行时依赖

- 任何操作系统上的 Python 3.9+。
- Markdown、纯文本、粘贴文本、对话上下文和 Mermaid 块输出仅需 Python 标准库。`check_setup.py` 报告哪些可选库缺失以及哪些输入格式仍然可用。

## 可选依赖

- `python-docx`、`PyMuPDF`、`openpyxl`、`python-pptx`：二进制格式提取。缺失时这些格式不可用；Markdown、文本、粘贴输入和对话上下文仍然可用。
- `jinja2`：HTML 导出。缺失时，技能仍会输出围栏 Mermaid 块。
- **离线 Mermaid 引擎。** HTML 导出优先使用 `assets/vendor/mermaid.min.js` 处的随附包（不随仓库分发）。在线时按需使用 `python scripts/fetch_mermaid.py`（或 `render_html.py --fetch-engine`）随附引擎，固定到 `render_html.py` 中的 `MERMAID_VERSION`（Mermaid 11.x）。`check_setup.py` 和 `first_run.py` 仅报告该包是否存在；它们绝不在网络上获取。包缺失时，输出仅为源码，除非调用方使用 `--allow-cdn` 启用固定的 CDN 回退。
- **无头浏览器渲染验证（Tier-1）。** `scripts/verify_render.py` 确认导出的 HTML 渲染时无 Mermaid 错误。它通过 `--browser-adapter` 与环境无关；请自行提供驱动（Playwright、Puppeteer 或宿主提供的浏览器包装器）。省略它并依赖宿主内预览（Tier-0）。
- **mmdc 黄金渲染检查（Tier-2）。** 维护者/CI 检查，位于 pytest 标记之后；当 `mmdc` 缺失时自动跳过。

## 无知识库或个人路径依赖

不需要私有知识库、笔记系统或机器本地路径。对话输出保留在助手内；HTML 报告仅写入用户选择的路径或中性默认路径 `./diagrams/`。文件溯源默认记录基本名称；完整源路径需要显式选择加入 `--include-source-path`。

## 适配器说明

- **结构化选择界面。** 本技能使用用户决策门控（教程提示、构建模式、多文件范围、HTML 报告）。若宿主支持结构化选择则以结构化选择呈现；否则以纯文本编号列表呈现，然后等待回复。每个门控都是硬停点：绝不从措辞推断、绝不跳过、除用户输入的字面量标志外绝不预先作答。
- **首次运行状态。** `scripts/first_run.py` 记录教程是否已提供。状态路径依次解析 `$LEGAL_DIAGRAM_STATE`，然后 `~/.legal-diagram/state.json`。在只读或临时文件系统上，检测器返回 `unknown`；技能随后提供教程而非抑制，仅在已确认的 `returning` 状态下抑制。状态位于技能文件夹之外，因此软件包保持独立。使用 `$LEGAL_DIAGRAM_STATE` 覆盖路径以迁移或共享状态。
- **无头浏览器检查。** 渲染验证是有文档说明的 shell 步骤，不是从渲染器内部 shell 出的 Python 子进程（某些浏览器包装器仅支持 shell，Python 子进程可能死锁）。请从您的 shell 或宿主驱动运行验证器。
- **操作系统假设。** 纯 Python，跨平台。文档命令使用正斜杠路径；请适配您的 shell。不依赖特定操作系统、shell 或编辑器。

## 公共默认值

- `input_source` 默认仅包含基本名称；`--include-source-path` 是显式的可信本地选择加入。
- 文件解析对文件大小、PDF 页数、DOCX 段落/表格/表格行、PPTX 幻灯片/文本形状以及 XLSX 工作表/行/单元格设有默认上限。在可能进行部分解析时，达到上限会设置 `truncated=true` 并在清单中发出警告代码。
- HTML 导出写入 `./diagrams/`，除非用户提供路径。随附 Mermaid 和渲染验证是可选的，并带有明确通知降级为仅源码或 `unverified`。
