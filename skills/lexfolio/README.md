# LexFolio

> Legal-grade Markdown-to-PDF typesetting with CJK-aware layout.

[English](README.md) | [中文](README_ZH.md)

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)

![Demo cover](docs/images/demo-preview.png)

## Features

- **CJK-aware typography** — mixed-script font pairing, punctuation compression, and widow/orphan control for Chinese legal text
- **Print-ready PDF output** — three-line tables, brand-color accents, and professional page geometry out of the box
- **Four document templates** — `opinion`, `memo`, `review`, and `analysis` for common legal deliverables
- **Eight typography presets** — `standard`, `executive`, `mobile`, `editorial`, `academic`, `deep`, `matrix`, and `redline`
- **Three brand color schemes** — configurable via `theme.json` or front matter
- **Markdown-native authoring** — headings, blockquotes, tables, bold/italic, and footnotes as plain Markdown
- **Butterick-grade defaults** — tuned against Clifford Chance, A&O Shearman, and King & Spalding opinion formats

---

## The Typography Problem in Legal Documents

Legal practice has long been trapped in the path-dependence of the typewriter era. Briefs, memos, and opinions are routinely produced with cramped margins, default system fonts, tight line spacing, and the indiscriminate use of ALL CAPS. The result is documents that fight the reader rather than serve them.

**Good typography is not decoration. It is cognitive ergonomics.**

As Matthew Butterick argues in *Typography for Lawyers*, professional typography minimizes visual fatigue so the reader's attention passes through the words without obstruction and lands directly on the legal reasoning. This is not aesthetic preference — it is professional duty. The U.S. Court of Appeals for the Seventh Circuit officially advises lawyers against Times New Roman because judges cannot retain brief content during rapid scanning.

LexFolio is built on this foundation.

---

## Design Principles

LexFolio's typesetting engine is engineered against four pillars drawn from Butterick's framework and validated against the visual standards of **Clifford Chance**, **A&O Shearman**, and **King & Spalding**.

### 1. Font Strategy and Hierarchy

Proportional serif typefaces are non-negotiable for body text. LexFolio ships with **Noto Serif SC** (body) and **Noto Sans SC** (headings) — establishing a clean sans/serif contrast that mirrors the hierarchy recommended for modern legal practice. For Latin text, **EB Garamond** provides the scholarly weight favored in academic and judicial writing.

| Role | Typeface | Rationale |
|---|---|---|
| Body (CJK) | Noto Serif SC | Readable serif, wider letter spacing |
| Headings (CJK) | Noto Sans SC | Crisp sans-serif for structural contrast |
| Body (Latin) | EB Garamond | Historical gravitas, judicial familiarity |

### 2. Spatial Geometry

Line length is the most overlooked variable in legal documents. Default 1-inch margins produce lines of 90+ characters, causing the eye to lose its place on return. LexFolio defaults to:

- **45–90 character line length** (averaging 65, the comfort zone)
- **28mm side margins** (wider than Word's default, closer to the 1.5–2.0 inch standard)
- **120–145% line spacing** relative to font size (not the destructive 233% of Word's "double spacing")

Every preset in LexFolio is tuned to keep text within the cognitive reading band.

### 3. Restraint in Emphasis

ALL CAPS and underlining are visual noise — they destroy word outlines and slow reading. LexFolio enforces disciplined emphasis:

- **Bold** and **italic** only, never underlines or caps
- **Single space** after punctuation (no "rivers of white")
- **Non-breaking spaces** around §, ¶, and numerical ranges
- **Punctuation compression** — full-width CJK punctuation rendered at 80% size for tighter, more professional line breaks

### 4. Quotation Containers

Block quotations exceeding three lines receive distinct visual encapsulation — never just redundant quotation marks. LexFolio auto-detects the nature of each blockquote and applies the appropriate container:

| Type | Detection | Treatment |
|---|---|---|
| **Statute** (法条) | Starts with 第X条/款/项 | Song serif, no shading, thin rules above/below, indented |
| **Case law** (判例) | Starts with quotation mark | Kai serif, brand-color left rule, subtle background, indented |
| **General** | Fallback | Standard blockquote indent |

This visual separation lets the reader distinguish the lawyer's voice from the court's original text without breaking the argument's flow.

---

## Typesetting Matrix

LexFolio codifies three document families into nine production-ready specifications, each benchmarked against international top-tier firm practice.

| Family | Template | Presets | Cover | Benchmark |
|---|---|---|---|---|
| **Legal Opinions** | `opinion` | standard, academic, deep | Full branded cover | Clifford Chance opinion format |
| **Memoranda** | `memo` | executive, mobile, editorial | Memo header table | A&O Shearman internal memo |
| **Due Diligence / Review** | `review`, `analysis` | redline, matrix | None | King & Spalding DD report |

### Eight Typography Presets

| Preset | Character | Use Case |
|---|---|---|
| `standard` | Balanced defaults | General legal documents |
| `executive` | Large type, tight leading | Partner-level quick review |
| `mobile` | Wide margins, short lines | Small-screen reading |
| `editorial` | Magazine-grade hierarchy | Client-facing publications |
| `academic` | Left-aligned serif, wide right margin | Scholarly opinions |
| `deep` | Strong heading contrast | Multi-level long-form opinions |
| `matrix` | Landscape A4, dense tables | Clause-by-clause comparison |
| `redline` | Loose leading, generous spacing | Contract markup and annotation |

---

## Quick Start

### Install

```bash
pip install -e .
```

Or install dependencies manually:

```bash
pip install -r requirements.txt
```

### CLI Usage

```bash
# Convert a Markdown file to PDF
python run.py input.md

# Use a document template (opinion / memo / review / analysis)
python run.py input.md -t opinion

# Specify color scheme and typography preset
python run.py input.md -s B --preset executive

# Generate a demo PDF to see all features
python run.py --demo -t opinion

# List available presets or templates
python run.py --list-presets
python run.py --list-templates
```

### Python API

```python
from engine.api import md_to_pdf

# Basic conversion
md_to_pdf("input.md", "output.pdf")

# With options
md_to_pdf(
    "input.md",
    "output.pdf",
    color_scheme="B",
    preset="executive",
    template="opinion",
)
```

## Markdown Syntax

### Front Matter

```yaml
---
doc_type: opinion              # opinion | memo | review | analysis
title: Legal Analysis
author: Jane Doe
date: June 15, 2026
ref_no: LEGAL-OP-2026-015
addressee: XX Corp.
confidential: true
firm_name_cn: "Your Firm"      # override firm name per document
firm_name_en: "Your Firm"
color_scheme: B                # A | B | C
font_provider: noto            # noto (founder is an alias)
layout_preset: standard        # see preset table above
---
```

### Supported Syntax

| Syntax | Description |
|---|---|
| `# H1` / `## H2` / `### H3` | Three heading levels (H1 gets brand-color decoration line) |
| `> quote text` | Blockquote (auto-detects statute / case law / general) |
| `**Analysis**: ...` | Analysis paragraph with brand-color top bar |
| `\| table \|` | Three-line table with zebra stripes |
| `---` | Horizontal rule |
| `<!-- pagebreak -->` | Forced page break |
| `<!-- sigfooter -->` | Signature page footer decoration |
| `>right text` | Right-aligned paragraph (for signatures) |
| `^[1]^` | Footnote superscript (auto-placed before punctuation) |

## Customization

### Firm Branding

Set per-document in front matter:

```yaml
firm_name_cn: "Your Law Firm"
firm_name_en: "Your Law Firm"
```

Or globally in `theme.json` → `cover.firm_name_cn` / `firm_name_en`.

### Custom Color Scheme

Add a new scheme in `theme.json` → `color.schemes`:

```json
{
  "color": {
    "schemes": {
      "D": {
        "name": "Custom",
        "primary": "#1a1a2e",
        "secondary": "#16213e",
        "accent": "#0f3460"
      }
    }
  }
}
```

Then use it: `python run.py input.md -s D`

### Custom Fonts

Edit `theme.json` → `font.providers` to point to your own `.ttf` files. LexFolio's font manager handles CJK/Latin mixing automatically — no manual font-tagging in your Markdown.

## Font Licensing

LexFolio ships with **open-source fonts only** (SIL Open Font License):

| Font | License | Usage |
|---|---|---|
| Noto Serif SC | OFL | Body text |
| Noto Sans SC | OFL | Headings |
| EB Garamond | OFL | Latin text |

The `founder` font provider is kept as an alias of `noto` for backward compatibility. If you have licensed commercial fonts (Century Schoolbook, Palatino, Equity, Tiempos), configure them in `theme.json` — **do not** commit commercial fonts to a public repository.

## Project Structure

```
LexFolio/
├── engine/               # Core rendering engine
│   ├── api.py            # Public API: md_to_pdf()
│   ├── theme.py          # Theme/config loader
│   ├── fonts.py          # Font registration + CJK/Latin mixing
│   ├── styles.py         # ParagraphStyle factory
│   ├── parser.py         # Markdown → Block list
│   ├── renderer.py       # Block → ReportLab flowable
│   ├── cover.py          # Cover page builder
│   └── chrome.py         # Header / footer / page numbers
├── fonts/                # Open-source TTF fonts (OFL)
├── templates/            # Document template configs (JSON)
├── theme.json            # Master theme configuration
├── run.py                # CLI entry point
├── _demo.md              # Demo Markdown file
├── pyproject.toml        # Package config
└── requirements.txt      # Python dependencies
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the Apache License, Version 2.0 — see the [LICENSE](LICENSE) file for details.

Font files in `fonts/` are licensed under the SIL Open Font License 1.1.

## Acknowledgments

LexFolio's design philosophy is informed by:

- **Matthew Butterick**, *Typography for Lawyers* — the foundational text on legal typography
- The visual standards published by **Clifford Chance**, **A&O Shearman**, and **King & Spalding**
- The U.S. Courts' typography guidelines for appellate briefs
