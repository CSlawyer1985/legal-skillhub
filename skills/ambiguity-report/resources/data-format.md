# 标准规范模式

本技能中的每个渲染器都消费相同的 JSON 规范。本文件记录该模式。

规范有六个顶层键，除 `meta`、`source` 和 `scenarios` 外均可选：

```json
{
  "meta":        { ... },          // required
  "design":      { ... },          // optional — defaults supplied
  "source":      { ... },          // required
  "families":    [ ... ],          // optional — auto-derived from scenarios if omitted
  "scenarios":   [ ... ],          // required
  "coverage_list": [ ... ],        // optional
  "methodology": { ... }           // optional
}
```

在调用任何渲染器前将规范保存到 `<output-dir>/spec.json`。规范是唯一事实来源，用调整后的设计重新渲染速度快。

## `meta` — 必需

识别被审查的文档并提供标题/页脚文案。

```json
{
  "title": "Tex. Ins. Code § 101.051",
  "subtitle": "Conduct That Constitutes the Business of Insurance",
  "kicker": "Interpretive-Ambiguity Stress-Test",
  "page_subtitle": "Seven places in § 101.051 where the statute is unclear enough to produce litigation, with both sides' arguments and a likely outcome for each.",
  "audit_date": "27 May 2026",
  "profile": "statute",
  "brand_short": "Tex. Ins. § 101.051",
  "brand_sub": "Ambiguity Stress-Test"
}
```

- `title`：文档的简短引用名（用于标题、面包屑导航）。
- `subtitle`：说明文档内容的一行说明。
- `kicker`：主标题上方的眉题文字（小型大写、强调色）。
- `page_subtitle`：用于落地页/封面的单句推介语。
- `audit_date`：审查运行日期。自由格式字符串。
- `profile`：`contract`、`statute`、`regulation`、`opinion` 之一。决定部分默认文案。
- `brand_short`、`brand_sub`：用于导航栏/页脚/封面幻灯片。

## `design` — 可选，提供默认值

视觉标记。全部可选；应用合理的默认值。

```json
{
  "accent_color": "#8b3a1f",
  "accent_soft": "#c47e5a",
  "accent_deep": "#6b2d18",
  "dept_color": "#2c4a6e",
  "dept_bg": "#eef3f9",
  "adv_color": "#8b3a1f",
  "adv_bg": "#fbf0ea",
  "background_color": "#fbf8f1",
  "card_color": "#ffffff",
  "panel_color": "#f3ede0",
  "text_color": "#1f1b16",
  "highlight_color": "#fdf2c4",
  "primary_font": "Fraunces",
  "body_font": "Inter",
  "serif_font": "Crimson Pro",
  "family_palette": {
    "scope":      { "bg": "#dceadb", "fg": "#2c5a2c" },
    "vague":      { "bg": "#fadeb9", "fg": "#7a4a14" },
    "def":        { "bg": "#e4d4ee", "fg": "#523072" },
    "mensrea":    { "bg": "#f6d3d3", "fg": "#862828" },
    "conflict":   { "bg": "#cee0e8", "fg": "#1c485a" },
    "conlaw":     { "bg": "#eed1e0", "fg": "#6a2249" },
    "discretion": { "bg": "#ddd9f1", "fg": "#38346e" }
  }
}
```

**单色快捷方式。** 如果用户只想更改强调色，设置 `accent_color` 并保留其余部分。当用户未提供 `accent_soft`（例如与白色 60% 混合）和 `accent_deep`（例如与黑色 80% 混合）时，技能应计算它们，但忠实的默认做法是让用户显式提供。

**类别调色板扩展。** 如果场景使用了默认调色板中没有的缺陷类别，在 `family_palette` 下添加带 `bg` 和 `fg` 的新键。类别调色板颜色应为满足 WCAG-AA 对比度的浅/深色对。

## `source` — 必需

被审查的文本，拆分为可寻址单元。

```json
{
  "name": "Sec. 101.051. Conduct That Constitutes the Business of Insurance",
  "sections": [
    {
      "id": "a",
      "label": "(a)",
      "subhead": "Definition",
      "text": "In this section, \"medical expense\" includes ...",
      "emphasize": ["medical expense"],
      "subprovisions": []
    },
    {
      "id": "b",
      "subhead": "Acts that constitute the business of insurance in this state",
      "subprovisions": [
        { "id": "b1", "label": "(b)(1)", "text": "making or proposing to make ..." },
        { "id": "b2", "label": "(b)(2)", "text": "...", "emphasize": ["as a vocation"] }
      ]
    }
  ]
}
```

**章节模型。** 章节可以是带文本和 ID 的顶层条款，也可以是仅含标题的分组，其下列出 `subprovisions`。两种形态均有效。子条款本身可以包含 `subprovisions`（例如 (b)(6) 包含 (b)(6)(A) … (b)(6)(I)）——该模式递归。

**ID。** 每个可寻址单元都需要唯一 ID。方案由审查决定，但应保持稳定——场景锚定到这些 ID。惯用选择：
- 法规：不带括号的分项标记——`a`、`b1`、`b6B`、`c`。
- 合同：带下划线的条款编号——`s2_1`、`s2_1_a`。
- 规章：段号——`p_a`、`p_b_1`。
- 意见书：段落或判旨片段——`holding_1`、`p_3`、`dictum_2`。

**`emphasize` 数组。** `text` 内应以斜体渲染的子字符串。谨慎使用——只用于歧义核心处的词语。

## `families` — 可选

场景使用的缺陷类别。如果省略，技能从场景的 `families` 数组推导类别并使用默认标签。

```json
[
  {
    "key": "scope",
    "label": "Scope / coverage",
    "description": "Does the statute reach this actor or this conduct at all? In public law, whether the text applies is often the whole fight.",
    "diagnostic": "Can I draw a colorable line excluding a real-world actor or activity from the statute's domain entirely?"
  }
]
```

按键的默认标签（省略 families 时使用）：

| Key | Label |
|-----|-------|
| `scope` | 范围/覆盖 |
| `vague` | 含糊术语 |
| `def` | 定义边界 |
| `mensrea` | 主观要件（mens rea）缺口 |
| `conflict` | 跨条款冲突 |
| `conlaw` | 合宪性回避 |
| `discretion` | 无标准的裁量 |
| `contradiction` | 内部矛盾 |
| `gap` | 缺口/沉默 |

一个场景可以列出多个类别——渲染时显示所有标签。

## `scenarios` — 必需

核心分析。每个场景是一条结构化记录。

```json
{
  "id": 1,
  "title": "Health care sharing ministry as \"funding mechanism\"",
  "tagline": "A pooled-funds ministry collects monthly contributions from 50,000 Texas members. Is it insurance, or is it religious cost-sharing the statute was not aimed at?",
  "anchors": ["b7"],
  "families": ["scope"],
  "situation": "A nondenominational ministry headquartered in Tennessee enrolls 50,000 Texas members ...",
  "positions": [
    {
      "label": "Position A",
      "actor": "Texas Department of Insurance",
      "argument": "The ministry contracts to provide reimbursement for medical expenses ..."
    },
    {
      "label": "Position B",
      "actor": "Ministry",
      "argument": "No contract exists. Sharing is morally binding only ..."
    }
  ],
  "weak_point": "\"By another method\" supplies no limiting principle ...",
  "likely_outcome": "The Legislature's later Chapter 1681 carveout presupposes ...",
  "redraft": "Add: <strong>\"Contracting to provide,\" in this section, includes ...</strong>"
}
```

**字段含义。**
- `id`：整数 1..N，单调递增。在标题中渲染为"S-N"。
- `title`：完整描述性标题，可比标签行更长。
- `tagline`：不超过两句话，用于卡片/封面/幻灯片标题。
- `anchors`：场景所依附的源 ID 数组。至少一个。
- `families`：缺陷类别键数组。至少一个。
- `situation`：3-6 句话，铺陈争议背景。中立、事实性。
- `positions`：恰好两个对立立场的数组。每个有 `label`（默认"Position A" / "Position B"）、`actor`（持有该立场的现实主体）和 `argument`（最强版本的解读）。
- `weak_point`：一句话指出文本缺陷。
- `likely_outcome`：预测的解决结果及驱动该结果的法理。
- `redraft`：拟议的修改文本。可包含 HTML `<strong>` 和 `<em>` 标签；渲染器酌情去除或保留。

**内联 HTML。** `situation`、`weak_point`、`likely_outcome`、`redraft` 以及 positions 内的 `argument` 字段可包含 `<em>` 和 `<strong>` 标签。渲染器在 HTML 和 LaTeX 中保留它们，在 docx 中转换为斜体/粗体 run，并在 pptx 中应用文本格式。

## `coverage_list` — 可选

其他被标记但未发展成完整场景的歧义点。在网站中渲染为小卡片网格，在 docx/LaTeX 中渲染为项目符号。

```json
[
  {
    "label": "(a) 'professional mental health'",
    "note": "Does 'professional' require state licensure? Ejusdem generis with the listed licensed professions favors a licensure reading; the text does not say."
  }
]
```

## `methodology` — 可选

审查方法论——分析如何生成、过滤掉了什么、审查不做什么。在网站中渲染为"方法"页面，在 docx 和 LaTeX 中渲染为附录，在 pptx 中渲染为结尾幻灯片。

```json
{
  "workflow":   ["Para 1 of workflow description...", "Para 2..."],
  "filter":     ["Para 1 of canon-filter description..."],
  "profile":    ["Para describing which audit profile was used and why..."],
  "scope":      ["Para describing what the audit does and does not cover..."],
  "research":   ["Para describing assumed law, cite-checking, research notes..."],
  "provenance": "One-sentence provenance line"
}
```

每个键是一个段落字符串数组（`provenance` 除外，它是单个字符串）。渲染器在章节内拼接段落。

## 验证

在调用渲染器之前，对规范做健全性检查：

- 每个场景中的每个锚点必须与 `source.sections`（递归）中的 ID 匹配。在此处捕捉拼写错误。
- 每个场景中的每个类别键必须在 `families` 中定义，或者是上述默认键之一。
- 场景的 ID 应为 1..N，无缺口且无重复。
- `positions` 数组必须恰好包含两个条目。

如果验证失败，修复规范（不要渲染无效的规范）。渲染器可能不检查，而缺失的锚点会静默产生损坏的链接。

## 示例：最小规范

能生成可用网站的最小规范：

```json
{
  "meta": {
    "title": "Sample Contract § 7",
    "subtitle": "Termination for Convenience",
    "audit_date": "May 2026",
    "profile": "contract"
  },
  "source": {
    "name": "Section 7. Termination for Convenience.",
    "sections": [
      { "id": "s7_1", "label": "7.1", "text": "Either party may terminate this agreement at any time with thirty (30) days' written notice." }
    ]
  },
  "scenarios": [
    {
      "id": 1,
      "title": "Pretextual termination during performance",
      "tagline": "When can 'at any time' be challenged as bad faith?",
      "anchors": ["s7_1"],
      "families": ["vague"],
      "situation": "Buyer terminates the supply agreement two weeks before a scheduled delivery for which Supplier has already incurred non-recoverable costs ...",
      "positions": [
        { "label": "Buyer", "actor": "Buyer", "argument": "The contract says 'at any time' — no qualifier, no good-faith requirement." },
        { "label": "Supplier", "actor": "Supplier", "argument": "Texas law implies a duty of good faith into every contract; 'at any time' cannot be read to authorize pretextual termination calculated to avoid post-performance obligations." }
      ],
      "weak_point": "The clause says 'at any time' but does not address whether the right is subject to the implied duty of good faith and fair dealing.",
      "likely_outcome": "Most jurisdictions read 'at any time' against the backdrop of UCC § 1-304 and implied good-faith duties, which means the bare textual reading does not survive — but courts split on what 'good faith' requires when the contract is silent.",
      "redraft": "Add to § 7.1: <strong>The party exercising the right of termination under this Section need not have cause; provided, however, that termination during a period in which the other party has incurred non-recoverable costs in good-faith performance shall entitle the other party to recover such costs.</strong>"
    }
  ]
}
```

即使没有 `families` 块、没有 `coverage_list`、没有 `methodology`，渲染器也能生成整洁的网站或文档。可选部分存在时增加深度；缺失时优雅降级。
