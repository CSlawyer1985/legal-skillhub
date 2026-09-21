---
name: html-slides-studio
description: 'Create or revise high-aesthetic single-file HTML slide decks from a detailed outline, manuscript, or topic. Use when the user wants HTML slides instead of PPT, especially for strong visual design, front-end interaction, built-in edit mode, speaker notes, draggable/resizable images, or 16:9 HTML/PDF export. Follow a strict workflow: ask the user to choose one of four design languages, collect deck inputs, propose a page-by-page plan, wait for confirmation, then generate or revise the deck.'
---

# HTML Slides Studio

Assume the user already has material. Prefer transforming a detailed outline or manuscript into slides. Do not invent the entire talk unless the user explicitly asks.

Critical: this skill transforms existing material. Never invent the whole talk. Ask for missing structural details instead of hallucinating chapters.

Keep the skill portable. Use only relative paths inside the skill folder so the folder can be committed to GitHub or another repo as-is. The packaged trigger path is Codex, but the references, templates, and scaffold assets should stay reusable for adaptation into other coding-agent environments.

## First response

If the user has not already picked a design language, start by asking them to fill in this exact template:

```text
风格选择：[A / B / C / D]

演讲标题：
副标题/关键词：
演讲者：
时长：
听众：

大纲：
Part 1 - [标题]
  1.1 [小节]
  1.2 [小节]
Part 2 - [标题]
  2.1 [小节]
  ...

特殊要求：
```

Before the template, list the four design choices in one compact block:
- `A · Warm Editorial / 暖纸编辑`
- `B · Dark Terminal / 深空终端`
- `C · Swiss Grid / 包豪斯网格`
- `D · Japanese Ink / 日式墨稿`

If the user has already chosen a style or already supplied some fields, do not ask again for answered fields. Ask only for missing fields.

## Workflow

1. Determine the chosen style. Read [references/design-rules.md](references/design-rules.md).
2. Collect the missing deck inputs. Read [references/content-playbook.md](references/content-playbook.md).
3. Plan the deck before coding. Use the page-count rules and required page types in [references/content-playbook.md](references/content-playbook.md).
4. Present the full page-by-page plan and wait for user confirmation.
5. Only after confirmation, generate or revise the HTML deck. Read [references/implementation-rules.md](references/implementation-rules.md).
6. Start from the closest asset template:
   - `A`: `assets/template-a-warm-editorial.html` (fallback `assets/slides-template-v3.html`)
   - `B`: `assets/template-b-terminal.html`
   - `C`: `assets/template-c-swiss.html`
   - `D`: `assets/template-d-ink.html`
   `assets/slides-template-v3.html` is the generic edit/save/export-capable scaffold used by the scaffold scripts and as the fallback base for style A. Do not treat it as a dead asset.
7. Keep the result at or above the aesthetic and interaction quality of the user's approved reference deck. Do not regress to generic, lightweight, or template-looking slides.
8. Prefer HTML/CSS/JS edits over rebuilding from scratch when the user provides an existing deck.

## Content rules

- Treat the user's detailed outline or manuscript as the source of truth.
- Prefer slide bullets, short labels, grids, cards, quotes, tables, and visual hierarchy over long prose on slides.
- Keep each slide under 7 independent information blocks. Split dense material across multiple slides.
- Place prompt engineering or tactical wording inside the relevant demo section, not as disconnected opening theory, unless the user explicitly asks.
- Use speaker notes for full phrasing; keep slides concise.
- When content gaps exist, fill only local transitions or structural glue. Flag major missing content instead of hallucinating a whole chapter.

## Output rules

Generate a single self-contained HTML file unless the user explicitly asks for a multi-file build.

Default capabilities when useful:
- keyboard navigation
- staggered reveal only where the content benefits from sequencing, not on every slide
- page counter and navigation state
- built-in speaker notes
- optional edit mode for text
- automatic local autosave for edited decks
- `Ctrl+S` and a visible save button for full-document save
- full HTML serialization so edits persist to the whole file, not only the visible slide subtree
- direct file overwrite via File System Access API when available, download fallback otherwise
- image insertion plus drag/resize controls when the user needs ongoing revision
- print CSS for per-slide 16:9 PDF export

After generating, report:
- planned vs actual page count
- fonts used
- keyboard controls
- where to edit content, theme variables, and layout
- which save path is included: autosave only, direct file save, download fallback, or all of them
- whether a clean presentation-only variant or PDF-export variant was included

## Quality bar

- Do not use Bootstrap, Tailwind, or generic slide frameworks unless the user explicitly asks.
- Do not use Inter, Roboto, Arial, or system-ui as the main font.
- Do not let visual quality drop below the approved reference deck.
- Prefer a coherent system: typography, spacing, navigation, motion, and decorative details must feel designed together.
- Use restrained motion: `0.3s-0.5s`, `ease` or `cubic-bezier(0.4, 0, 0.2, 1)`. Do not use bounce or elastic easing.
- Use `clamp()` for type and spacing.
- Keep 16:9 full-viewport slides and hide overflow.
- For PDF export, include the print rules from [references/implementation-rules.md](references/implementation-rules.md).
