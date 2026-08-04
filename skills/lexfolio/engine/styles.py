# -*- coding: utf-8 -*-
"""
Style factory: builds the full set of ReportLab ParagraphStyle objects from
theme.json parameters.

Usage:
    factory = StyleFactory(theme, font_mgr)
    styles = factory.create_all()
    # styles["body"], styles["h1"], styles["h2"], ...
"""

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT

from engine.theme import ThemeLoader
from engine.fonts import FontManager


class StyleFactory:
    """Build the full set of ParagraphStyle objects from theme.json params."""

    def __init__(self, theme: ThemeLoader, font_mgr: FontManager):
        self.theme = theme
        self.font_mgr = font_mgr
        self.colors = theme.get_colors()
        self.typo = theme.get_typography()

    def create_all(self) -> dict:
        """Build and return all ParagraphStyle objects.

        Returns:
            dict[str, ParagraphStyle] with keys:
            "body", "h1", "h2", "h3", "quote", "quote_case", "quote_law",
            "opinion", "meta", "table_header", "table_cell",
            "cover_firm", "cover_english", "cover_title",
            "cover_meta", "cover_confidential", "cover_bottom_firm",
            "memo_header_label", "memo_header_value"
        """
        styles = {
            "body":         self._body(),
            "h1":           self._heading(1),
            "h2":           self._heading(2),
            "h3":           self._heading(3),
            "quote":        self._quote(),
            "quote_case":   self._quote(),          # case quote: same as default quote
            "quote_law":    self._quote_law(),       # law quote: serif + thin top/bottom rules
            "opinion":      self._opinion(),         # opinion: brand-color top bar
            "meta":         self._meta(),
            "table_header": self._table_header(),
            "table_cell":   self._table_cell(),
        }
        # Cover page / memo header styles
        styles.update(self._cover_styles())
        return styles

    # -- Body ------------------------------------------------------

    def _body(self) -> ParagraphStyle:
        t = self.typo["body"]
        font_name = self.font_mgr.body_font()
        indent_pt = t["first_line_indent_chars"] * t["font_size_pt"]

        # Allow presets to override alignment (e.g. academic uses left-align)
        align_str = t.get("alignment", "justify")
        alignment = TA_LEFT if align_str == "left" else TA_JUSTIFY

        return ParagraphStyle(
            "body",
            fontName=font_name,
            fontSize=t["font_size_pt"],
            leading=t["line_height_pt"],
            firstLineIndent=indent_pt,
            spaceBefore=t["space_before_pt"],
            spaceAfter=t["space_after_pt"],
            textColor=self.colors["text"],
            alignment=alignment,
            wordWrap="CJK",
        )

    # -- Headings --------------------------------------------------

    def _heading(self, level: int) -> ParagraphStyle:
        key = "heading_{}".format(level)
        t = self.typo[key]
        font_name = self.font_mgr.heading_font(level)

        return ParagraphStyle(
            "h{}".format(level),
            fontName=font_name,
            fontSize=t["font_size_pt"],
            leading=t["line_height_pt"],
            firstLineIndent=0,
            spaceBefore=t["space_before_pt"],
            spaceAfter=t["space_after_pt"],
            textColor=self.colors["text"],
            alignment=TA_LEFT,
            keepWithNext=True,
            wordWrap="CJK",
        )

    # -- Quote blocks ----------------------------------------------

    def _quote(self) -> ParagraphStyle:
        t = self.typo["quote"]
        font_name = self.font_mgr.quote_font()

        return ParagraphStyle(
            "quote",
            fontName=font_name,
            fontSize=t["font_size_pt"],
            leading=t["line_height_pt"],
            firstLineIndent=0,
            leftIndent=t["left_indent_pt"],
            rightIndent=t["right_indent_pt"],
            spaceBefore=t["space_before_pt"],
            spaceAfter=t["space_after_pt"],
            textColor=self.colors["text"],
            alignment=TA_JUSTIFY,
            wordWrap="CJK",
        )

    def _quote_law(self) -> ParagraphStyle:
        """Law-quote style: serif (not kai), indented, no shading."""
        t = self.typo.get("quote_law", self.typo["quote"])
        font_name = self.font_mgr.body_font()  # serif

        return ParagraphStyle(
            "quote_law",
            fontName=font_name,
            fontSize=t["font_size_pt"],
            leading=t["line_height_pt"],
            firstLineIndent=0,
            leftIndent=t.get("left_indent_pt", 28),
            rightIndent=t.get("right_indent_pt", 24),
            spaceBefore=t.get("space_before_pt", 10),
            spaceAfter=t.get("space_after_pt", 10),
            textColor=self.colors["text"],
            alignment=TA_JUSTIFY,
            wordWrap="CJK",
        )

    def _opinion(self) -> ParagraphStyle:
        """Opinion-paragraph style: same as body with larger space-before."""
        t = self.typo.get("opinion", {})
        body_t = self.typo["body"]
        font_name = self.font_mgr.body_font()
        indent_pt = body_t["first_line_indent_chars"] * body_t["font_size_pt"]

        return ParagraphStyle(
            "opinion",
            fontName=font_name,
            fontSize=body_t["font_size_pt"],
            leading=body_t["line_height_pt"],
            firstLineIndent=indent_pt,
            spaceBefore=t.get("space_before_pt", 10),
            spaceAfter=t.get("space_after_pt", 3),
            textColor=self.colors["text"],
            alignment=TA_JUSTIFY,
            wordWrap="CJK",
        )

    # -- Meta info -------------------------------------------------

    def _meta(self) -> ParagraphStyle:
        t = self.typo["meta"]
        font_name = self.font_mgr.meta_font()

        return ParagraphStyle(
            "meta",
            fontName=font_name,
            fontSize=t["font_size_pt"],
            leading=t["line_height_pt"],
            firstLineIndent=0,
            spaceBefore=t["space_before_pt"],
            spaceAfter=t["space_after_pt"],
            textColor=self.colors["text_light"],
            alignment=TA_LEFT,
            wordWrap="CJK",
        )

    # -- Table -----------------------------------------------------

    def _table_header(self) -> ParagraphStyle:
        table_cfg = self.theme.get_table_config()
        font_name = self.font_mgr.heading_font(level=2)

        return ParagraphStyle(
            "table_header",
            fontName=font_name,
            fontSize=table_cfg.get("font_size_pt", 10.5),
            leading=table_cfg.get("line_height_pt", 16),
            firstLineIndent=0,
            textColor=self.colors["text"],
            alignment=TA_CENTER,
            wordWrap="CJK",
        )

    def _table_cell(self) -> ParagraphStyle:
        table_cfg = self.theme.get_table_config()
        font_name = self.font_mgr.body_font()

        return ParagraphStyle(
            "table_cell",
            fontName=font_name,
            fontSize=table_cfg.get("font_size_pt", 10.5),
            leading=table_cfg.get("line_height_pt", 16),
            firstLineIndent=0,
            textColor=self.colors["text"],
            alignment=TA_LEFT,
            wordWrap="CJK",
        )

    # -- Cover page + memo header ----------------------------------

    def _cover_styles(self) -> dict:
        """Build all ParagraphStyle objects needed for the cover page and memo header."""
        cover_cfg = self.theme.get_cover_config()
        heading_bold = self.font_mgr.heading_font(level=1)
        heading_regular = self.font_mgr.heading_font(level=3)
        latin_regular = self.font_mgr.latin_font(bold=False)
        meta_font = self.font_mgr.meta_font()

        title_size = cover_cfg.get("title_font_size_pt", 20)
        firm_size = cover_cfg.get("firm_font_size_pt", 18)
        meta_size = cover_cfg.get("meta_font_size_pt", 10)

        return {
            # Firm name (CN) - top of cover
            "cover_firm": ParagraphStyle(
                "cover_firm",
                fontName=heading_bold,
                fontSize=firm_size,
                leading=firm_size * 1.6,
                firstLineIndent=0,
                textColor=self.colors["text"],
                alignment=TA_CENTER,
                wordWrap="CJK",
            ),
            # English name - below the firm name
            "cover_english": ParagraphStyle(
                "cover_english",
                fontName=latin_regular,
                fontSize=10,
                leading=14,
                firstLineIndent=0,
                textColor=self.colors["text_light"],
                alignment=TA_CENTER,
            ),
            # Document title - large, center of cover
            "cover_title": ParagraphStyle(
                "cover_title",
                fontName=heading_bold,
                fontSize=title_size,
                leading=title_size * 1.5,
                firstLineIndent=0,
                textColor=self.colors["text"],
                alignment=TA_CENTER,
                wordWrap="CJK",
            ),
            # Metadata (ref no, addressee, author, date)
            "cover_meta": ParagraphStyle(
                "cover_meta",
                fontName=meta_font,
                fontSize=meta_size,
                leading=meta_size * 1.8,
                firstLineIndent=0,
                textColor=self.colors["text"],
                alignment=TA_LEFT,
                wordWrap="CJK",
            ),
            # Confidential marker - bottom of cover
            "cover_confidential": ParagraphStyle(
                "cover_confidential",
                fontName=latin_regular,
                fontSize=8,
                leading=12,
                firstLineIndent=0,
                textColor=self.colors["accent"],
                alignment=TA_CENTER,
            ),
            # Bottom firm name - very bottom of cover
            "cover_bottom_firm": ParagraphStyle(
                "cover_bottom_firm",
                fontName=heading_regular,
                fontSize=8,
                leading=12,
                firstLineIndent=0,
                textColor=self.colors["text_light"],
                alignment=TA_CENTER,
                wordWrap="CJK",
            ),
            # Draft watermark label (used by the simplified cover)
            "cover_draft_label": ParagraphStyle(
                "cover_draft_label",
                fontName=heading_bold,
                fontSize=8,
                leading=12,
                firstLineIndent=0,
                textColor=self.colors["accent"],
                alignment=TA_CENTER,
            ),
            # Memo header label column (TO / FROM / DATE / RE)
            "memo_header_label": ParagraphStyle(
                "memo_header_label",
                fontName=latin_regular,
                fontSize=10,
                leading=16,
                firstLineIndent=0,
                textColor=self.colors["text_light"],
                alignment=TA_LEFT,
            ),
            # Memo header value column
            "memo_header_value": ParagraphStyle(
                "memo_header_value",
                fontName=self.font_mgr.body_font(),
                fontSize=10.5,
                leading=16,
                firstLineIndent=0,
                textColor=self.colors["text"],
                alignment=TA_LEFT,
                wordWrap="CJK",
            ),
        }
