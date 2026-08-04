# -*- coding: utf-8 -*-
"""
Public API: Markdown -> PDF conversion entry point.

Usage:
    from engine.api import md_to_pdf
    output_path = md_to_pdf("input.md", "output.pdf")
"""

import os

from engine.theme import ThemeLoader
from engine.fonts import FontManager
from engine.styles import StyleFactory
from engine.parser import MarkdownParser
from engine.renderer import PDFRenderer


def md_to_pdf(
    input_path: str,
    output_path: str = None,
    color_scheme: str = None,
    font_provider: str = None,
    preset: str = None,
    template: str = None,
    theme_path: str = None,
) -> str:
    """Convert a Markdown file into a typeset PDF.

    Args:
        input_path:    Path to the Markdown input file.
        output_path:   Path for the generated PDF (default: same name with .pdf).
        color_scheme:  Color scheme override (A / B / C). None = theme.json default.
        font_provider: Font provider override (noto / founder). None = default.
        preset:        Typography preset override (standard/executive/mobile/
                       editorial/academic/deep/matrix/redline). None = standard.
        template:      Document template (opinion/memo/review/analysis); provides
                       type-specific defaults.
        theme_path:    Custom theme.json path. None = project default.

    Returns:
        Absolute path of the generated PDF file.
    """
    # 1. Resolve output path
    if output_path is None:
        base, _ = os.path.splitext(input_path)
        output_path = base + ".pdf"
    output_path = os.path.abspath(output_path)

    # 2. Load theme
    theme = ThemeLoader(theme_path)

    # 3. Read Markdown
    with open(input_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # 4. Parse Markdown (extract front matter)
    parser = MarkdownParser()
    blocks, front_matter = parser.parse(md_text)

    # 5. Load template (if any)
    tmpl = None
    if template:
        tmpl = theme.load_template(template)

    # 6. Resolve preset: CLI > front_matter > template default > theme.json default
    #    Must run before color/font overrides because set_preset resets base config.
    effective_preset = (preset
                        or front_matter.get("layout_preset")
                        or (tmpl and tmpl.get("default_preset")))
    if effective_preset:
        theme.set_preset(effective_preset)

    # 7. Resolve color_scheme: CLI > front_matter > template default > default
    effective_scheme = (color_scheme
                        or front_matter.get("color_scheme")
                        or (tmpl and tmpl.get("default_color_scheme")))
    if effective_scheme:
        theme.set_scheme(effective_scheme)

    # 8. Resolve font_provider: CLI > front_matter > template default > default
    effective_provider = (font_provider
                          or front_matter.get("font_provider")
                          or (tmpl and tmpl.get("default_font_provider")))
    if effective_provider:
        theme.set_provider(effective_provider)

    # 9. Template doc_type as front_matter fallback
    if tmpl and "doc_type" not in front_matter:
        front_matter["doc_type"] = tmpl["doc_type"]

    # 10. Template cover_fields as front_matter fallback
    if tmpl and tmpl.get("cover_fields"):
        for key, value in tmpl["cover_fields"].items():
            if key not in front_matter:
                front_matter[key] = value

    # 11. Register fonts
    font_mgr = FontManager(theme)
    font_mgr.register_all()

    # 12. Build styles
    style_factory = StyleFactory(theme, font_mgr)
    styles = style_factory.create_all()

    # 13. Render PDF
    renderer = PDFRenderer(theme, font_mgr, styles)
    renderer.render(blocks, output_path, front_matter=front_matter)

    return output_path
