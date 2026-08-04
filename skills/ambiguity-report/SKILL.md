---
name: ambiguity-report
description: 将法律文本（合同、法规、规章或司法意见）的诠释性歧义审查转化为精美的交付物。可生成多页面网站（默认）、单页面交互式网站、Microsoft Word 文档、PowerPoint 演示文稿或 LaTeX/PDF。当用户持有压力测试结果、歧义审查或"这将在何处被诉"场景分析，并希望发布、演示或分享时使用。触发词包括"发布审查报告"、"据此制作报告"、"将其转化为网站/演示文稿/简报/Word 文档"、"制作 Netlify 网站"、"制作这些歧义点的幻灯片"、"渲染场景"、"打包这份压力测试"、"生成 LaTeX 版本"等。与歧义压力测试技能（底层分析）配套使用，但也适用于任何结构化或半结构化的歧义分析。视觉设计有明确风格倾向，但用户可覆盖颜色、字体和品牌标识。大多数格式需要 Python 和可写的文件系统；单文件 HTML 在主机两者皆无时仍可运行。
metadata:
  author: "Seth J. Chandler"
  author_link: "https://legaled.ai"
  license: "Apache-2.0"
  version: "2026-07-29"
  jurisdiction: "All"
  language: "English"
  requires: "Python 3（仅标准库）；docx 和 pptx 技能用于生成这两种格式；编译 PDF 需要 LaTeX 发行版"
---

# 歧义报告

将法律文本的诠释性歧义分析转化为六种格式之一的美观交付物：多页面网站（默认）、单页面交互式网站、单文件 HTML、Microsoft Word 文档、PowerPoint 演示文稿或用于生成 PDF 的 LaTeX 源文件。

**在承诺某种格式之前，先了解当前主机能做什么。** 六种格式中有四种存在主机可能无法满足的要求，如果在规范构建完成后才发现，会浪费用户的努力。先运行第 3 阶段的能力检查。

本技能的核心洞见：**数据在各格式间是相同的，渲染方式则不同。** 歧义分析是一组场景——每个场景包含情境、两种对立立场、文本中的弱点、可能的结果以及拟议的改写文本——并锚定于源文本的条款。一旦该数据被捕获到标准规范中，正确的格式便取决于交付物的用途。

## 工作流程

本技能包含四个阶段。第 1-3 阶段为准备阶段；第 4 阶段为渲染阶段。

- **第 1 阶段——识别输入。** 确定用户交来的是哪种类型的分析。三种常见形态：(a) `ambiguity-stress-test` 技能的结构化 Markdown 输出；(b) 较为非正式的报告或备忘录，已识别出场景但七个规范字段未全部填写；(c) 原始散文，指出了一些歧义点但完全未按场景格式组织。每种形态的策略不同——见 `resources/parsing-unstructured.md`。
- **第 2 阶段——构建标准规范。** 将输入转换为每个渲染器都可消费的结构化 JSON 规范。模式定义见 `resources/data-format.md`。缺失字段填写默认值而非阻塞在完整性上，并向用户展示推断出的内容以便其更正。
- **第 3 阶段——选择格式与设计。** 与用户确认所需格式（默认：多页面网站）。记录任何设计覆盖项（强调色、字体、品牌标识）。大多数用户只关心格式和强调色；其他几乎所有事项都有合理的默认值。
- **第 4 阶段——渲染。** 委托给正确的渲染器。网站和 LaTeX 路径使用随附的生成脚本（`scripts/generate_site.py` 和 `scripts/generate_latex.py`）。Word 和 PowerPoint 路径委托给现有的 `docx` 和 `pptx` 技能，内容按相应格式结构化。格式特定的指南见 `resources/format-{website,docx,pptx,latex}.md`。

## 第 1 阶段——识别输入

查看用户提供的内容。注意三种特征：

**特征 A——结构化压力测试输出。** 带"## Scenarios"等章节标题的 Markdown，以及位于"### S-1 —"等标题下的单个场景，每个场景包含带标签的字段（"**Anchors:**"、"**Defect family:**"、"**Weak point:**"、"**Likely outcome:**"、"**Redraft:**"）。通常由歧义压力测试技能生成。这是简单情形——直接解析为标准规范。

**特征 B——半结构化报告。** 以散文形式编号的歧义点或问题，每个附带一两段解释。七个规范字段可能不齐全——"情境"和"弱点"可能合并；改写文本可能完全缺失。提取现有内容，标记缺失项，并推断合理的默认值或询问用户。见 `resources/parsing-unstructured.md`。

**特征 C——原始散文。** 讨论"此文本含糊之处"的备忘录、草稿或记录。没有正式的场景结构。技能必须做更多工作：识别候选歧义点、拆分为离散场景、为每个场景提出缺陷类别。在渲染前与用户确认提取结果——渲染输出的质量不会超过其结构。

在以上三种情形中，都需要识别源文本（被审查的法规/合同/规章/意见）。如果输入不包含完整源文本，请用户提供。技能可以在没有源文本的情况下渲染场景，但结果会弱得多——源文本是文档的骨架。

## 第 2 阶段——构建标准规范

规范的完整模式见 `resources/data-format.md`。顶层结构：

```
{
  "meta": { title, subtitle, kicker, audit_date, profile, brand_short, brand_sub },
  "design": { accent_color, accent_soft, dept_color, adv_color, ... },
  "source": { name, sections: [ { id, label, subhead, text, subprovisions: [...] } ] },
  "families": [ { key, label, description, diagnostic } ],
  "scenarios": [ { id, title, tagline, anchors, families, situation, positions, weak_point, likely_outcome, redraft } ],
  "coverage_list": [ { label, note } ],
  "methodology": { workflow, filter, profile, scope, research, provenance }
}
```

迭代式构建：从源文本和场景（最重要的两项）开始，然后在输入提供了或用户需要时添加可选部分（缺陷类别、覆盖清单、方法论）。`families` 块可从场景中使用的类别键自动推导；提供默认标签表，并允许用户覆盖描述。

**锚点 ID。** 每个场景链接到源文本的一条或多条条款。锚点 ID 必须与 `source.sections` 中分配给条款的 ID 一致。使用一致的方案——法规按分项标记（`a`、`b1`、`b2`、`b6B`、`c`）；合同按条款编号（`s2_1`、`s2_1_a`）；意见书按段落或判旨片段（`p3`、`holding_1`）。

在渲染前将规范保存到 `<output-dir>/spec.json`。这使得渲染具有确定性和可重跑性——用户想要调整设计时无需重建分析。

## 第 3 阶段——选择格式与设计

### 能力检查——首先执行

在提供任何选项之前先确定主机能做什么。三个问题，只需回答一次：

1. **能否运行 Python 3 并写入文件？** 两个网站渲染器和 LaTeX 渲染器是随附脚本；没有脚本执行能力和可写目录，它们都无法运行。
2. **`docx` 和 `pptx` 技能是否可用？** 这两种格式委托给它们。
3. **是否安装了 LaTeX 发行版？** 仅当用户需要编译后的 PDF 而非 `.tex` 源文件时才相关。

不要猜测。在能力不确定时，最廉价的测试是尝试该能力的最小版本。然后只向用户提供能够实际完成的格式，并简要说明其他格式不可用的原因——"此处没有 Python，所以多页面网站不可行；单文件 HTML 在单页中提供相同内容"远比五分钟后才失败的用户体验好。

如果除纯文本外什么都做不了，如实说明，而不是半渲染。开头就被告知的用户可以另寻他处；结尾才被告知的用户已经失去了工作成果。

### 六种选项

| 格式 | 要求 | 适用场景 |
|--------|----------|-------------|
| 多页面网站（可用时默认） | Python 3 + 文件系统 | 每个场景有可引用的 URL；适合读者会回访的参考网站；可部署到 Netlify 或任何静态托管。 |
| 单页面交互式网站 | Python 3 + 文件系统 | 一次查看所有内容的仪表板视图；点击交叉链接；适合内部工具或展览品。 |
| 单文件 HTML | 无 | 一个自包含的 `.html` 文件，无需脚本直接写入。通用后备方案，也是交付物需要通过电子邮件发送或被不愿解压文件夹的人打开时的正确选择。见 `resources/format-inline-html.md`。 |
| Microsoft Word 文档 | `docx` 技能 | 在 Word 中阅读的诉讼律师或立法者；可用修订模式审阅；可打印。 |
| PowerPoint 演示文稿 | `pptx` 技能 | 会议、继续法律教育（CLE）、路演——每张幻灯片一个场景，类别颜色位于色带上，演讲者备注承载分析内容。 |
| LaTeX 源文件 | Python 3 + 文件系统 | 面向学术受众的排版交付物；分析内容置于脚注；投稿级排版质量。生成 `.tex`；在用户机器上编译为 PDF 需要 LaTeX 发行版。在确认已安装之前，不要承诺 PDF。 |

**设计标记。** 五个值覆盖 95% 的定制需求：`accent_color`（主品牌色——默认焦赭红橙）、`accent_soft`（较浅的互补色，未提供时自动推导）、`dept_color`（立场 A 侧面板——默认板岩蓝）、`adv_color`（立场 B 侧面板——通常呼应强调色）、`background_color`（默认暖奶油色）。网页字体默认 Fraunces / Inter / Crimson Pro，Word 使用系统衬线字体，LaTeX 使用 Latin Modern。缺陷类别调色板固定，但可通过 `design.family_palette` 覆盖。

如果用户指定了品牌背景——"用于企业审计"、"采用我们律所的颜色"、"面向州立法者"——将调色板与之匹配。企业审计用海军蓝 + 板岩蓝更显清爽；立法工作用较暖的默认配色更好；学术工作可偏向单色。

## 第 4 阶段——渲染

每种格式都有自己的参考文件，内含详细说明。渲染前阅读相应文件。大致调用方式：

**网站**（多页或单页）——随附脚本：
```bash
python scripts/generate_site.py \
  --spec <output-dir>/spec.json \
  --out <output-dir>/site \
  --mode multi    # or "single"
```
该脚本生成一个完整的静态网站（HTML + CSS），可直接上传到 Netlify。见 `resources/format-website.md`。

**单文件 HTML**——无脚本。根据规范直接编写一个自包含的 `.html` 文件，内联样式表和每个场景。这是 Python 不可用时的后备方案，也是交付物必须经电子邮件发送时的合理首选。完整说明见 `resources/format-inline-html.md`。

**Word 文档**——委托给 `docx` 技能。文档结构（标题页、执行摘要、法规整块呈现、场景作为二级章节、改写文本附录、方法论附录）见 `resources/format-docx.md`。通过 docx 技能的 python-docx 模式构建。

**PowerPoint 演示文稿**——委托给 `pptx` 技能。幻灯片结构（标题、法规概览、每张幻灯片一个场景并带类别颜色色带、改写文本幻灯片、方法论幻灯片）见 `resources/format-pptx.md`。演讲者备注承载分析内容。通过 pptx 技能的工具构建。

**LaTeX**——随附脚本：
```bash
python scripts/generate_latex.py \
  --spec <output-dir>/spec.json \
  --out <output-dir>/report.tex
```
该脚本使用 article 类和简洁的前言生成一个自包含的 `.tex` 文件。**交付物是 `.tex`。** 将其编译为 PDF 需要 LaTeX 发行版——`latexmk -pdf report.tex`，或运行两次 pdflatex。仅在存在发行版时尝试编译；否则交付 `.tex` 并如实说明其排版需要 LaTeX，而不是报告 PDF 编译失败。见 `resources/format-latex.md`。

**一次生成所有格式。** 如果用户要求一次调用生成所有格式，按顺序运行各渲染器并展示每个输出。当交付物面向混合受众时（诉讼律师想要 Word 文档、同事想要网站链接、会议需要演示文稿），这很有用。

## 输出组织

默认输出目录：工作区文件夹中的 `<source-name>-ambiguity/`（如果已连接工作区），否则位于临时输出文件夹中。其中：

```
<source-name>-ambiguity/
├── spec.json              # 标准规范——可重新渲染
├── site/                  # 如果请求了网站（多页或单页）
├── site.zip               # 网站文件夹，压缩后交付
├── report.html            # 如果请求了单文件 HTML
├── report.docx            # 如果请求了 Word
├── deck.pptx              # 如果请求了 PowerPoint
├── report.tex             # 如果请求了 LaTeX
└── report.pdf             # 仅当存在 LaTeX 发行版且编译成功时
```

通过主机提供的任何机制将每个生成的文件交付给用户——如果有文件展示或发送工具则使用之，否则如实陈述输出路径。

**交付前压缩网站文件夹。** 多页面网站有数十个文件，向在聊天窗口中工作的人交付松散目录本身就是一种小挫败。在 `site/` 旁边生成 `site.zip`，交付压缩包，并指出 `site/index.html` 为入口点。用户可以解压并将文件夹拖到 Netlify Drop，或上传到任何静态托管服务进行部署。单文件 HTML 不需要这些——它设计上就是一个文件。

## 本技能不做什么

- 它不执行歧义分析本身。那是 `ambiguity-stress-test` 的工作。本技能将分析转化为交付物；它不从未经加工的法律文本生成场景。
- 它不编辑源文本——只引用它。
- 它不验证引文或检查现行法律。如果底层分析依赖的判例可能已发生变化，技能应在方法论部分添加研究说明，但本身无法确认时效性。引文核查是另一次独立工作。
- 它不生成印刷版面。LaTeX 路径生成屏幕可读的 PDF；印刷专用版面（小册子格式、法院提交格式）属于 `scotus-amicus` 等更专业技能的范畴。

## 当用户要求设计调整时

使用新的设计标记从保存的 `spec.json` 重新渲染。不要重新解析输入。这正是规范文件值得保存的原因——设计迭代快速且确定。

## 随附资源

只阅读工作实际需要的两三个文件；不要全部阅读。

- `resources/data-format.md` — 标准规范模式。在第 2 阶段构建规范前阅读。
- `resources/parsing-unstructured.md` — 从结构化程度较低的输入中提取场景的启发式方法。如果输入属于特征 B 或 C，在第 1 阶段阅读。
- `resources/format-website.md` — 网站渲染器的工作原理、部署到 Netlify、设计系统。
- `resources/format-inline-html.md` — 单文件 HTML 后备方案，无需脚本直接编写。当主机无法运行 Python，或交付物必须作为单个附件传输时阅读。
- `resources/format-docx.md` — Word 文档结构，委托给 docx 技能。
- `resources/format-pptx.md` — PowerPoint 结构，委托给 pptx 技能。
- `resources/format-latex.md` — LaTeX 前言、文档类、编译。
- `scripts/generate_site.py` — 网站渲染器。Python 3，仅标准库。
- `scripts/generate_latex.py` — LaTeX 渲染器。Python 3，仅标准库。
- `assets/site-style.css` 和 `assets/latex-preamble.tex` — 两个渲染器读取的样式表。`generate_site.py` 相对于自身位置解析 `assets/site-style.css`，因此请保持 `scripts/` 和 `assets/` 文件夹为同级目录。

## 限制与风险

本技能为他人产生的分析做排版。它不评估该分析是否正确，而精美的交付物会使薄弱审查看起来权威可信。其产出不构成法律意见。

**它继承了输入中的每一个缺陷。** 错误的场景会与正确的场景渲染得一样精美。在字段缺失处，技能会填写默认值并展示推断的内容——在传阅结果前阅读这些说明。

**它不核查引文或时效性。** 如果底层分析依赖的判例已发生变化，交付物将复现该错误。方法论部分可以承载研究说明；技能本身无法确认任何事项。

**大多数格式需要有能力的主机。** 两个网站渲染器和 LaTeX 渲染器都是写文件的 Python 脚本；Word 和 PowerPoint 委托给 `docx` 和 `pptx` 技能。如果这些都不可用，单文件 HTML 仍然可用且无需任何条件——这就是为什么第 3 阶段的能力检查在格式对话之前而非之后进行。

**PDF 需要 LaTeX 发行版。** 脚本生成 `.tex`；编译为 PDF 需要机器上安装 `latexmk`、`pdflatex` 或 `xelatex`。没有发行版时，`.tex` 文件仍然是交付物——不要将其呈现为失败。

**脚本生成的网站从 Google Fonts 加载字体。** 这些页面在打开时会调用外部服务，离线或在受限网络下回退到系统字体。在重要场合——保密审计、隔离网络审查——要么用本地字体栈覆盖规范中的字体标记，要么使用单文件 HTML，它设计上不嵌入网页字体且不发出任何外部请求。

**引用的源文本随交付物一同传播。** 渲染后的审查会复现其所分析文书的段落。发布网站或分享基于保密草稿制作的演示文稿前请先检查。

两个脚本仅使用 Python 标准库。它们不进行任何网络调用、不产生任何子进程，并且只写入调用方指定的输出目录内。
