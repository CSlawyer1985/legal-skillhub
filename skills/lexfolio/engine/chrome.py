# -*- coding: utf-8 -*-
"""
Page chrome: header and footer drawing.

Usage:
    chrome = PageChrome(theme, font_mgr, front_matter, total_pages)
    # Use within a BaseDocTemplate PageTemplate:
    PageTemplate(id='Cover',   frames=frame, onPage=chrome.on_cover_page)
    PageTemplate(id='Content', frames=frame, onPage=chrome.on_content_page)

Note: ReportLab's default unit is the point (pt); the canvas origin is at the
bottom-left corner.
"""

from reportlab.lib.units import mm
from reportlab.lib.colors import Color

from engine.theme import ThemeLoader
from engine.fonts import FontManager


class PageChrome:
    """Draw the page header and footer."""

    # Header text offset above the top margin
    _HEADER_OFFSET_PT = 14
    # Separator line offset above the top margin
    _SEPARATOR_OFFSET_PT = 10
    # Footer text offset below the bottom margin
    _FOOTER_OFFSET_PT = 18

    def __init__(
        self,
        theme: ThemeLoader,
        font_mgr: FontManager,
        front_matter: dict,
        total_pages: int = 0,
        cover_pages: int = 0,
    ):
        self.theme = theme
        self.font_mgr = font_mgr
        self.fm = front_matter
        self.total_pages = total_pages
        self.cover_pages = cover_pages

        self.colors = theme.get_colors()
        self.page_cfg = theme.get_page()
        self.hf_cfg = theme.get_typography().get("header_footer", {})
        self.cover_cfg = theme.get_cover_config()

        # Fonts
        self._meta_font = font_mgr.meta_font()
        self._latin_font = font_mgr.latin_font()
        self._font_size = self.hf_cfg.get("font_size_pt", 8)

    # -- PageTemplate callbacks ------------------------------------

    def on_cover_page(self, canvas, doc):
        """Cover page: draw no header or footer."""
        pass

    def on_content_page(self, canvas, doc):
        """Content page: draw the header and footer."""
        show_on_first = self.hf_cfg.get("show_on_first_page", True)
        is_first_content = canvas.getPageNumber() == (self.cover_pages + 1)
        if is_first_content and not show_on_first:
            return
        if self.hf_cfg.get("header_enabled", True):
            self._draw_header(canvas, doc)
        if self.hf_cfg.get("footer_enabled", True):
            self._draw_footer(canvas, doc)

    # -- Header ----------------------------------------------------

    def _draw_header(self, canvas, doc):
        """Draw the header: firm name on the left, identifier on the right, plus a separator."""
        c = canvas
        page_h = self.page_cfg["height_mm"] * mm
        margin_top = self.page_cfg["margin_top_mm"] * mm
        margin_left = self.page_cfg["margin_left_mm"] * mm
        margin_right = self.page_cfg["margin_right_mm"] * mm
        page_w = self.page_cfg["width_mm"] * mm

        # Text baseline Y
        text_y = page_h - margin_top + self._HEADER_OFFSET_PT
        # Separator line Y
        sep_y = page_h - margin_top + self._SEPARATOR_OFFSET_PT

        # -- Left: firm name --
        firm_cn = self.fm.get("firm_name_cn") or self.cover_cfg.get("firm_name_cn", "")
        c.saveState()
        c.setFont(self._meta_font, self._font_size)
        c.setFillColor(self.colors["text_light"])
        c.drawString(margin_left, text_y, firm_cn)
        c.restoreState()

        # -- Right: identifier text --
        right_text = self._get_header_right_text()
        if right_text:
            c.saveState()
            c.setFont(self._latin_font, self._font_size)
            c.setFillColor(self.colors["text_light"])
            c.drawRightString(page_w - margin_right, text_y, right_text)
            c.restoreState()

        # -- Separator line --
        sep_height = self.hf_cfg.get("separator_height_pt", 0.5)
        sep_color_name = self.hf_cfg.get("separator_color", "border")
        sep_color = self.colors.get(sep_color_name, self.colors["border"])

        c.saveState()
        c.setStrokeColor(sep_color)
        c.setLineWidth(sep_height)
        c.line(margin_left, sep_y, page_w - margin_right, sep_y)
        c.restoreState()

    # -- Footer ----------------------------------------------------

    def _draw_footer(self, canvas, doc):
        """Draw the footer: centered page number."""
        c = canvas
        margin_bottom = self.page_cfg["margin_bottom_mm"] * mm
        page_w = self.page_cfg["width_mm"] * mm
        center_x = page_w / 2

        text_y = margin_bottom - self._FOOTER_OFFSET_PT

        # Content page number = physical page number - cover page count
        physical = canvas.getPageNumber()
        page_num = physical - self.cover_pages
        total = self.total_pages - self.cover_pages

        fmt = self.hf_cfg.get("footer_format", "intl")

        if fmt == "chinese":
            # "page X of N" in CJK; labels come from theme.json i18n
            self._draw_mixed_footer(c, center_x, text_y, page_num, total)
        elif fmt == "number":
            # "— X —"
            text = "\u2014 {} \u2014".format(page_num)
            c.saveState()
            c.setFont(self._latin_font, self._font_size)
            c.setFillColor(self.colors["text_light"])
            c.drawCentredString(center_x, text_y, text)
            c.restoreState()
        else:
            # intl: "— X / N —" (default)
            self._draw_intl_footer(c, center_x, text_y, page_num, total)

    def _draw_intl_footer(self, canvas, center_x, text_y, page_num, total_pages):
        """Draw the international-format footer: — X / N —"""
        latin_font = self._latin_font
        fs = self._font_size
        gray = self.colors["text_light"]
        brand = self.colors["primary"]

        # Segmented draw: left "— X" gray, "/" brand color, "N —" gray
        slash = " / "
        left_part = "\u2014 {} ".format(page_num)
        right_part = " {} \u2014".format(total_pages)

        def est_width(text, font, size):
            canvas.setFont(font, size)
            return canvas.stringWidth(text, font, size)

        w_left = est_width(left_part, latin_font, fs)
        w_slash = est_width(slash, latin_font, fs)
        w_right = est_width(right_part, latin_font, fs)
        total_w = w_left + w_slash + w_right

        # Start drawing from half the total width left of center
        x = center_x - total_w / 2

        canvas.saveState()
        # Left segment
        canvas.setFont(latin_font, fs)
        canvas.setFillColor(gray)
        canvas.drawString(x, text_y, left_part)
        x += w_left
        # Slash (brand color)
        canvas.setFillColor(brand)
        canvas.drawString(x, text_y, slash)
        x += w_slash
        # Right segment
        canvas.setFillColor(gray)
        canvas.drawString(x, text_y, right_part)
        canvas.restoreState()

    def _draw_mixed_footer(self, canvas, center_x, text_y, page_num, total_pages):
        """Draw a CJK footer: "page X of N" using CJK + Latin mixed text.

        Label strings are read from theme.json's i18n section so no UI text is
        hardcoded in source.
        """
        cjk_font = self._meta_font
        lat_font = self._latin_font
        fs = self._font_size
        gray = self.colors["text_light"]
        brand = self.colors["primary"]

        i18n = self.theme.get_i18n()
        page_prefix = i18n.get("footer_page_prefix", "")
        page_suffix = i18n.get("footer_page_suffix", "")
        total_prefix = i18n.get("footer_total_prefix", "")
        total_suffix = i18n.get("footer_total_suffix", "")

        # Segments: CJK labels + Latin numbers/slash
        parts = [
            (cjk_font, page_prefix, gray),
            (lat_font, str(page_num), gray),
            (cjk_font, page_suffix, gray),
            (lat_font, " / ", brand),
            (cjk_font, total_prefix, gray),
            (lat_font, str(total_pages), gray),
            (cjk_font, total_suffix, gray),
        ]

        # Compute total width
        total_w = 0
        widths = []
        for font, text, _ in parts:
            w = canvas.stringWidth(text, font, fs)
            widths.append(w)
            total_w += w

        x = center_x - total_w / 2
        canvas.saveState()
        for i, (font, text, color) in enumerate(parts):
            canvas.setFont(font, fs)
            canvas.setFillColor(color)
            canvas.drawString(x, text_y, text)
            x += widths[i]
        canvas.restoreState()

    # -- Helpers ---------------------------------------------------

    def _get_header_right_text(self) -> str:
        """Return the header right-side text based on config."""
        mode = self.hf_cfg.get("header_right", "ref_no")

        # front_matter override
        fm_mode = self.fm.get("header_right", mode)

        if fm_mode == "none":
            return ""
        elif fm_mode == "confidential":
            conf = self.fm.get("confidential", False)
            if conf:
                return self.cover_cfg.get(
                    "confidential_text", "PRIVILEGED & CONFIDENTIAL"
                )
            return ""
        else:
            # ref_no (default)
            return self.fm.get("ref_no", "")
