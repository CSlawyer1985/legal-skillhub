# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.0] - 2026-06-30

### Added
- Initial public release of the LexFolio typesetting engine.
- Four document templates: `opinion`, `memo`, `review`, `analysis`.
- Three color schemes: deep blue + indigo, teal + amber, graphite + cobalt.
- Eight typography presets: `standard`, `executive`, `mobile`, `editorial`,
  `academic`, `deep`, `matrix` (landscape), `redline`.
- CJK + Latin mixed-script font management (Noto Serif SC + EB Garamond).
- Full-width CJK punctuation compression (configurable ratio).
- Two-pass rendering for accurate `page X / N` footers.
- YAML front matter support for per-document overrides (firm name, ref no,
  author, addressee, date, color scheme, preset, etc.).
- CLI entry point `lexfolio` with `--list-templates` / `--list-presets`.
- Apache-2.0 license.
- Bilingual README (English + Chinese) with typographic theory framing.

### Known Limitations
- No image embedding (`![alt](path)` syntax not yet supported).
- No automatic table of contents or PDF bookmark tree.
- `table.style`, `footnote`, and `cover.show_confidential` config options
  are declared in `theme.json` but not yet wired into the renderer.
- Table cell parsing does not handle escaped pipe characters (`\|`).

[1.7.0]: https://github.com/GantianBro/LexFolio/releases/tag/v1.7.0
