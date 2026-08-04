<div align="center">

# patent-mining-disclosure-skill：专利挖掘交底书生成 Skill

> 面向技术项目、软件系统与产品方案的 AI Agent 专利挖掘与专利交底书生成工具：支持专利点清单、相似专利查新、商业秘密取舍、说明书式技术交底书、流程图/架构图、Word/PDF 导出和自动生图。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-mermaid%2Fmmdc-339933.svg)](https://nodejs.org/)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Workflow-green)](https://agentskills.io)
[![GitHub stars](https://img.shields.io/github/stars/AqooDer/patent-mining-disclosure-skill?style=social)](https://github.com/AqooDer/patent-mining-disclosure-skill/stargazers)

项目名称：**patent-mining-disclosure-skill**  
中文名称：**专利挖掘交底书生成 Skill**  
关键词：patent mining、patent disclosure、patent drafting、专利挖掘、专利点分析、专利查新、技术交底书、专利说明书、Word 导出、PDF 导出、自动生图、Agent Skill

[一句话说明](#一句话说明) · [核心能力](#核心能力) · [和原始版本的差异](#和原始版本的差异) · [工作流](#工作流) · [安装](#安装) · [使用](#使用) · [工具链](#工具链) · [致谢与来源](#致谢与来源)

如果这个项目对你有帮助，欢迎在 GitHub 给它点一个 [Star](https://github.com/AqooDer/patent-mining-disclosure-skill)。

</div>

---

## 一句话说明

`patent-mining-disclosure-skill` 是一个用于技术项目、软件系统与产品方案的 AI Agent Skill，可从代码和文档中自动盘点专利点、进行相似专利查新和商业秘密取舍，并生成包含流程图、架构图、发明人信息的专利技术交底书，支持 Markdown、Word、PDF 和自动生图交付。

## 核心能力

这个仓库不是单纯把材料改写成一份交底书，而是把“能不能写专利、写哪几个、哪些不该公开、怎么查新、怎么成稿、怎么交付”做成一条可复用流程。

<table>
<colgroup>
<col width="1%">
<col>
</colgroup>
<thead>
<tr><th align="left" nowrap width="1%">能力</th><th align="left">说明</th></tr>
</thead>
<tbody>
<tr><td nowrap width="1%"><strong>项目扫描</strong></td><td>扫描代码、设计文档、Word、PPT 等材料；<code>.docx</code> / <code>.pptx</code> 会先转 Markdown 再进入分析。</td></tr>
<tr><td nowrap width="1%"><strong>专利点盘点</strong></td><td>先输出专利点资产清单，而不是直接写交底书；清单包含可申请点、暂不适合申请点、建议商业秘密保护点、评分和原因。</td></tr>
<tr><td nowrap width="1%"><strong>轻量查新</strong></td><td>资产清单阶段对候选点做轻量相似专利初筛，优先 Google Patents / 国知局 / WebSearch，记录相似风险和可区分点。</td></tr>
<tr><td nowrap width="1%"><strong>深度查新</strong></td><td>用户确认要写的点后，再进入深度查新；支持国知局公布公告站工具链，并把可核验链接和区别分析写入背景技术。</td></tr>
<tr><td nowrap width="1%"><strong>秘密保护</strong></td><td>用户可把某些技术点标记为不写或商业秘密保护；流程会避免把这些内容公开化写入交底书正文。</td></tr>
<tr><td nowrap width="1%"><strong>说明书式成稿</strong></td><td>正文按技术领域、背景技术、发明内容、附图说明、具体实施方式、摘要组织；重点补足技术思路、步骤、模块、参数、异常分支和替代实施方式。</td></tr>
<tr><td nowrap width="1%"><strong>附图生成</strong></td><td>所有流程图、系统结构图先用 mermaid 表达；Word 可选择本地 PNG、专利附图风格生图提示词，或调用 OpenAI-compatible 图片接口自动生成并插入。</td></tr>
<tr><td nowrap width="1%"><strong>Word / PDF</strong></td><td>支持 Markdown 或 Word 二选一；Word 可继续导出 PDF。正文标题下支持写入发明人/发明者元信息。</td></tr>
<tr><td nowrap width="1%"><strong>版本化目录</strong></td><td>每轮交付写入 <code>vN-说明-时间戳/</code> 目录，并维护 <code>版本索引.md</code>，避免多版文件平铺混在一起。</td></tr>
<tr><td nowrap width="1%"><strong>迭代留档</strong></td><td>补材料、纠错、强化权利要求取向时，不覆盖旧稿；每轮输出到新版本目录，并追加修订对话记录。</td></tr>
</tbody>
</table>

## 和原始版本的差异

本版本在原有交底书生成思路上做了较大扩展，重点差异如下：

| 方向 | 本版本增强 |
|------|------------|
| 专利挖掘 | 从“候选点讨论”升级为“专利点资产清单 + 评分 + 取舍确认”。 |
| 是否可写 | 增加“暂不适合申请”和“建议商业秘密保护”的判断，不再默认所有技术都写成专利。 |
| 相似检索 | 在资产清单阶段加入轻量相似专利初筛；确认成案后再做深度查新。 |
| 正文结构 | 从普通交底模板强化为接近专利说明书的技术正文，尤其扩写“发明内容”和“具体实施方式”。 |
| 附图 | 支持 mermaid 本地渲染、专利附图风格生图提示词、自动调用图片接口生成 PNG 并插入 Word。 |
| 交付物 | 支持 Markdown / Word，Word 可继续导出 PDF；文件名统一使用案件名 + 时间戳，并按 `vN-说明-时间戳/` 版本目录归档。 |
| 元信息 | 支持发明人/发明者字段，未知时不编造，只写 `[待填写]`。 |
| 迭代 | 支持合并、纠错、修订记录、`版本索引.md` 和多版本目录留档。 |

## 工作流

```text
输入项目路径 / 技术主题
        ↓
Step 1  确认技术主题、权利要求倾向、不公开边界、发明人
        ↓
Step 2  扫描代码与文档，Office 材料先转 Markdown
        ↓
Step 3  形成候选专利点
        ↓
Step 4  输出资产清单：评分、轻量查新、可申请/不适合/商业秘密建议
        ↓
用户确认写哪些、不写哪些、秘密保护哪些
        ↓
Step 5  深度查新与差异化分析
        ↓
Step 6  摘要预览与方向确认
        ↓
Step 7  生成说明书式技术交底书，按 vN 版本目录处理附图并导出 Markdown / Word / PDF
        ↓
Step 8  内部自检并修订
        ↓
后续迭代：补材料 / 纠错 / 强化保护范围，另存到新 vN 目录并记录修订日志
```

## 安装

### Claude Code

```bash
mkdir -p .claude/skills
git clone <本仓库 URL> .claude/skills/patent-mining-disclosure-skill
```

### Cursor

将仓库完整内容放到 Cursor 的 skills 目录，或直接用 Cursor 打开本仓库。常见路径：

```bash
mkdir -p ~/.cursor/skills
git clone <本仓库 URL> ~/.cursor/skills/patent-mining-disclosure-skill
```

说明：`SKILL.md` 中的 `name` 为 `patent-mining-disclosure-skill`，仓库名和安装目录也建议保持 `patent-mining-disclosure-skill`，便于用户通过 “patent mining skill / patent disclosure skill / 专利挖掘 skill / 专利交底书 skill” 检索到本项目。

## 依赖

基础转换能力：

```bash
pip install -r requirements.txt
```

国知局公布公告站查新工具：

```bash
pip install -r tools/requirements-cnipa.txt
python -m playwright install chromium
```

mermaid 图示渲染：

```bash
cd tools
npm install
```

若 `mmdc` 提示找不到 Chrome：

```bash
npx puppeteer browsers install chrome-headless-shell
```

PDF 导出依赖 LibreOffice / soffice。macOS 可安装 LibreOffice，脚本会优先查找 PATH 上的 `soffice`，也兼容 `/Applications/LibreOffice.app/Contents/MacOS/soffice`。

## 使用

在 Agent 中自然语言触发即可：

```text
请阅读 /path/to/project 的代码，先盘点专利点，做相似专利初筛，然后让我选择写哪些。
```

确认清单后继续：

```text
写 A、B、C 三个，输出 Word，图用自动生图，发明人为[待填写]，同时导出 PDF。
```

已有交底书要改时：

```text
基于这份 Word 补充样本泛化实施例，另存到下一个版本目录，并继续导出 PDF。
```

## 工具链

| 工具 | 用途 |
|------|------|
| `tools/docx_to_md.py` | Word 转 Markdown，并抽取图片，供扫描阶段读取。 |
| `tools/pptx_to_md.py` | PPT 转 Markdown，并抽取图片。 |
| `tools/cnipa_epub_search.py` | 国知局公布公告站检索与解析。 |
| `tools/mermaid_render.py` | mermaid 转 PNG / 生图提示词 / 自动生图，并生成 Word，可选 PDF。 |
| `tools/md_to_docx.py` | Markdown 转 Word，支持标题、表格、图片、公式和已渲染 mermaid 图。 |
| `tools/math_render.py` | LaTeX 公式转 PNG，供 Word 中稳定显示。 |
| `tools/iteration_dialog_log.py` | 迭代修订记录追加。 |

## 项目结构

```text
patent-mining-disclosure-skill/
├── SKILL.md
├── prompts/
│   ├── intake.md
│   ├── project_scan.md
│   ├── patent_points_analyzer.md
│   ├── prior_art_search.md
│   ├── disclosure_preview.md
│   ├── disclosure_builder.md
│   ├── disclosure_self_check.md
│   ├── versioned_output.md
│   ├── iteration_context.md
│   ├── merger.md
│   ├── correction_handler.md
│   └── template_reference.md
├── tools/
├── docs/
├── examples/
├── requirements.txt
├── INSTALL.md
└── LICENSE
```

## 运行效果

**初版生成**

![初版生成：outputs 目录下按版本保存的交底书、mermaid 图目录等](docs/效果例-初版生成.png)



## 支持作者

如果这个工作流帮你节省了整理专利交底书的时间，可以随缘支持。

<div align="left">

<table>
<tr>
<td valign="middle" align="left" style="padding-right: 16px;">

<img src="docs/thanks.jpg" alt="随缘支持" width="280" />

</td>
<td valign="middle" align="left">

<a href="https://www.star-history.com/?repos=AqooDer%2Fpatent-mining-disclosure-skill&type=date&legend=top-left">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=AqooDer/patent-mining-disclosure-skill&type=date&theme=dark&legend=top-left" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=AqooDer/patent-mining-disclosure-skill&type=date&legend=top-left" />
    <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=AqooDer/patent-mining-disclosure-skill&type=date&legend=top-left" width="600" />
  </picture>
</a>

</td>
</tr>
</table>

</div>

## 致谢与来源

本项目参考并基于开源项目 `handsomestWei/patent-disclosure-skill` 的思路和部分实现继续演进，感谢原作者提供的基础工作。当前版本在专利点资产清单、相似专利初筛、商业秘密取舍、说明书式交底正文、自动生图、Word / PDF 交付、发明人元信息和迭代留档等方向做了增强。

原项目采用 MIT License，相关版权声明保留在 [LICENSE](LICENSE) 中；本仓库后续增强部分由当前维护者继续维护。
