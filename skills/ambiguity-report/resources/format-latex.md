# 格式——LaTeX → PDF

LaTeX 路径生成可编译为精美 PDF 的自包含 `.tex` 文件。适合学术受众、法律评论投稿或任何排版质量重要的场景。

## 生成器

```bash
python scripts/generate_latex.py \
  --spec <output-dir>/spec.json \
  --out <output-dir>/report.tex
```

该脚本生成一个带全部内联前言（无需 `\input` 外部文件）的单个 `.tex` 文件。用户用自己偏好的 LaTeX 引擎编译——`latexmk -pdf`、`pdflatex`（交叉引用需运行两次），或需要非默认字体时用 `xelatex`。

## 文档类和宏包

默认：`article` 类，11pt，letterpaper。前言加载：

- `geometry` — 1in 页边距
- `xcolor` — 用于调色板
- `tcolorbox` — 用于双立场面板和改写文本醒目框
- `enumitem` — 用于更整洁的列表
- `titlesec` — 用于标题定制
- `hyperref` — 用于交叉引用和可点击锚点
- `microtype` — 用于排版润色
- `fontspec`（如果使用 xelatex）— 用于自定义字体；否则脚本使用 Latin Modern

颜色绑定到以规范键命名的 LaTeX 颜色定义（`accentColor`、`deptColor`、`advColor` 等）。类别颜色命名为 `famScopeBg`、`famScopeFg` 等。

## 文档结构

LaTeX 文档镜像网站的信息架构，但采用线性形式。

**标题块。**
```latex
\title{\textsc{\small Interpretive-Ambiguity Stress-Test}\\[1em]
       {\Huge \textsf{Where {\source name} will be fought over}}\\[0.5em]
       \large \textit{{page subtitle}}}
\date{{audit_date}}
```

**前置部分。**
- 标题。
- 简短的引导块（`meta.page_subtitle` 的一个段落）。
- 场景列表目录（自定义——不是标准的 `\tableofcontents`，而是带样式的列表）。

**第一部分——源文本。**
- `\section*{The source}` 配 `\addcontentsline`，使其出现在目录中。
- 使用 `\subsection` 渲染顶层章节，用缩进块渲染子条款。每条条款置于 `quote` 环境中，标签加粗。
- 有锚定的条款通过 `\marginpar` 获得页边编号徽章。徽章是带场景编号的 `\tcbox`。

**第二部分——场景。**
- `\section*{The {N} fights}`
- 每个场景：
  - `\subsection*{S-N · {title}}`
  - 下方斜体标签行。
  - 单行以 `\fbox` 包裹的小号文本呈现锚点和类别。
  - **情境：** 置于带细灰边框、沙色填充的 `tcolorbox` 中。
  - **双立场面板：** 两个并排的 `tcolorbox`（用 `tcbraster` 排版）。左侧：立场 A。右侧：立场 B。每个有彩色顶边框、`\textsc` 的主体名和论证正文。
  - **弱点：** 描述列表条目。`\textbf{Weak point.} \itshape ...`
  - **可能结果：** 相同模式。
  - **改写文本：** 黄色调的 `tcolorbox`，标签"Proposed amendment"小型大写，正文斜体。
  - 下一个场景前加 `\rule` 分隔线。

**第三部分——改写文本。**
- `\section*{Proposed amendments}`
- 关于该组合的简短引导。
- 每个场景的改写文本：
  - `\subsection*{R-N · {short title}}`
  - 标题下方斜体小型大写的目标条款。
  - 问题陈述。
  - 提案置于 `tcolorbox` 中（与场景内改写文本相同的样式）。

**第四部分——覆盖清单（如存在）。**
- `\section*{Additional ambiguities flagged}`
- `\description` 样式列表：粗体标签，然后是说明。

**第五部分——方法论（如存在）。**
- `\section*{Methodology}`
- 每个 `methodology.*` 键的子节。
- 来源行作为斜体页脚。

## 分析深度的脚注

在适当之处，将次要细节推到脚注而非挤占正文。例如，"可能结果"段落可以加脚注引用具体解释规则，或改写文本可以脚注注明语言来源。

这正是 LaTeX 的用武之地。尽情使用。

## 交叉引用

使用 `\label` 和 `\autoref`：
- 每个场景标题：`\label{scen:N}`
- 每条源条款：`\label{prov:ID}`，其中 ID 是规范中的条款 ID
- 每个改写文本标题：`\label{redraft:N}`

然后"see Scenario S-2"变成 `see \autoref{scen:2}`，hyperref 宏包使其在 PDF 中可点击。

## tcolorbox 样式

在前言中定义三个可复用的样式：

```latex
\tcbset{
  situationbox/.style={
    colback=panelColor, colframe=accentSoft,
    boxrule=0.5pt, arc=2pt,
    left=10pt, right=10pt, top=8pt, bottom=8pt,
  },
  positionA/.style={
    colback=deptBg, colframe=deptColor,
    boxrule=0pt, leftrule=0pt, rightrule=0pt, bottomrule=0pt, toprule=2pt,
    arc=2pt, left=10pt, right=10pt, top=8pt, bottom=8pt,
  },
  positionB/.style={
    colback=advBg, colframe=advColor,
    boxrule=0pt, leftrule=0pt, rightrule=0pt, bottomrule=0pt, toprule=2pt,
    arc=2pt, left=10pt, right=10pt, top=8pt, bottom=8pt,
  },
  redraftbox/.style={
    colback=redraftBg, colframe=redraftBorder,
    boxrule=0.5pt, arc=2pt,
    left=10pt, right=10pt, top=8pt, bottom=8pt,
  }
}
```

## 编译

生成器不编译 PDF。用户自行编译。建议：

```bash
latexmk -pdf report.tex
```

如果 `latexmk` 不可用：

```bash
pdflatex report.tex
pdflatex report.tex   # second pass for cross-references
```

如果编译失败（例如 `tcolorbox` 未安装），向用户呈现错误并建议安装缺失宏包。MacTeX / TeX Live 发行版默认包含 `tcolorbox`；非常精简的 LaTeX 安装可能没有。

## 备选文档类

默认是 `article`。未来扩展可提供：

- **Tufte-LaTeX** — 用于边注和更宽边距版式。分析有大量想放在页边空白处的评论时最佳。
- **Beamer** — 与 PowerPoint 相当的 LaTeX。除非用户明确想要 Beamer 输出，否则改用 pptx 路径。
- **Memoir** — 用于书级长度的交付物。对大多数歧义审查而言过度。

V1 目前不支持这些；如果用户要求其中之一，说明这是未来工作并提供 article 类输出。

## 字体定制

如果用户提供的 `design.primary_font` 是 LaTeX 能找到的（例如系统安装的 TrueType 字体），指示他们用 `xelatex` 而非 `pdflatex` 编译。脚本可以从字体选择中检测到这一点，并在 `.tex` 文件顶部添加注释：

```latex
% Compile with xelatex (custom fonts requested)
```

否则坚持使用 Latin Modern（pdflatex 的默认字体）。

## 此格式擅长的

LaTeX 生成排版精良的 PDF，打印清晰、嵌入交叉引用、天然支持脚注。交付物将被打印、存档或投稿期刊时最佳。

## 此格式不擅长的

LaTeX 不可交互。没有过滤、没有点击高亮、没有实时跨窗格联动。对于探索式阅读，网站远胜一筹。
