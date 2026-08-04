# -*- coding: utf-8 -*-
"""
Cover page builder: produces ReportLab flowables for a cover page or a memo
header, based on document type.

Usage:
    cover_builder = CoverBuilder(theme, font_mgr, styles)
    flowables = cover_builder.build(front_matter, available_width)

Supported doc_type values:
    opinion  -> full cover (firm name + EN name + brand line + title + meta + confidential)
    draft    -> simplified cover (same but no EN name; bottom marker is "DRAFT")
    memo     -> no cover; a memo header table (TO / FROM / DATE / RE) is prepended
    review   -> no cover; content starts immediately
    analysis -> no cover; content starts immediately

Cover visual style (cover_style field):
    standard -> white background + brand-color accents (default)
    color    -> brand-primary full-bleed background + white text + accent decoration

Note: ReportLab's default unit is the point (pt); all numeric values are used as-is.
"""

from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Flowable, NextPageTemplate
)
from reportlab.lib.units import mm
from reportlab.lib.colors import Color

from engine.theme import ThemeLoader
from engine.fonts import FontManager


class _ColorBg(Flowable):
    """Full-page background flowable: draws a filled rectangle over the content area.

    Its height is computed to fill from the current position to the page bottom.
    """

    def __init__(self, color, width, page_cfg):
        Flowable.__init__(self)
        self._color = color
        self._width = width
        self._page_cfg = page_cfg

    def wrap(self, availWidth, availHeight):
        page_h = (
            self._page_cfg["height_mm"]
            - self._page_cfg["margin_top_mm"]
            - self._page_cfg["margin_bottom_mm"]
        ) * mm
        # Occupy all space from the current position to the page bottom (4pt safety margin)
        h = min(page_h, availHeight + self._cur_y() + 4)
        return (self._width, h)

    def _cur_y(self):
        """Return the current flowable's y coordinate on the page."""
        try:
            return self._frame._y1
        except AttributeError:
            return 0

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(self._color)
        c.rect(0, 0, self._width, self.height, fill=1, stroke=0)
        c.restoreState()


class CoverBuilder:
    """Build cover-page or memo-header flowables according to doc_type."""

    def __init__(self, theme: ThemeLoader, font_mgr: FontManager, styles: dict):
        self.theme = theme
        self.font_mgr = font_mgr
        self.styles = styles
        self.colors = theme.get_colors()
        self.page_cfg = theme.get_page()
        self.brand_rules = theme.get_brand_rules()
        self.cover_cfg = theme.get_cover_config()

    def build(self, front_matter: dict, available_width: float) -> list:
        """Return cover-page flowables based on doc_type and cover_style.

        Returns an empty list when no cover is needed (review / analysis).
        """
        doc_type = front_matter.get("doc_type", "review")
        cover_style = front_matter.get("cover_style", "standard")

        if doc_type in ("opinion", "draft"):
            if cover_style == "color":
                return self._build_color_cover(front_matter, available_width)
            elif doc_type == "opinion":
                return self._build_full_cover(front_matter, available_width)
            else:
                return self._build_draft_cover(front_matter, available_width)
        elif doc_type == "memo":
            return self._build_memo_header(front_matter, available_width)
        else:
            # review / analysis - no cover
            return []

    # -- Full cover (opinion) --------------------------------------

    def _build_full_cover(self, fm: dict, width: float) -> list:
        """Build the full cover page (legal opinion)."""
        story = []
        content_h = self._content_height_pt()
        top_sp, mid_sp, bot_sp = self._cover_spacers(content_h)

        # -- Top region: firm name + EN name --
        story.append(Spacer(1, top_sp))

        firm_cn = fm.get("firm_name_cn") or self.cover_cfg.get("firm_name_cn", "")
        if firm_cn:
            story.append(Paragraph(firm_cn, self.styles["cover_firm"]))

        firm_en = fm.get("firm_name_en") or self.cover_cfg.get("firm_name_en", "")
        if firm_en:
            story.append(Paragraph(firm_en, self.styles["cover_english"]))

        # -- Brand-color decoration line --
        story.append(Spacer(1, 20))
        line_width = width * self.brand_rules.get("title_line_width_ratio", 0.6)
        line_height = self.brand_rules.get("cover_line_height_pt", 1)
        story.append(HRFlowable(
            width=line_width,
            thickness=line_height,
            color=self.colors["primary"],
            spaceBefore=2,
            spaceAfter=8,
            hAlign="CENTER",
        ))

        # -- Title --
        title = fm.get("title", "")
        if title:
            formatted_title = self.font_mgr.format_mixed_text(
                title, role="heading", bold=True
            )
            story.append(Paragraph(formatted_title, self.styles["cover_title"]))

        # -- Middle whitespace --
        story.append(Spacer(1, mid_sp))

        # -- Metadata region --
        for item in self._meta_items(fm):
            formatted = self.font_mgr.format_mixed_text(item, role="meta")
            story.append(Paragraph(formatted, self.styles["cover_meta"]))

        # -- Bottom whitespace (fills the remainder) --
        story.append(Spacer(1, bot_sp))

        # -- Bottom region: decoration line + confidential marker + firm name --
        story.append(HRFlowable(
            width=line_width,
            thickness=line_height,
            color=self.colors["primary"],
            spaceBefore=2,
            spaceAfter=6,
            hAlign="CENTER",
        ))

        confidential = fm.get("confidential", True)
        if confidential:
            conf_text = self.cover_cfg.get(
                "confidential_text", "PRIVILEGED & CONFIDENTIAL"
            )
            story.append(Paragraph(conf_text, self.styles["cover_confidential"]))

        if firm_cn:
            story.append(Paragraph(firm_cn, self.styles["cover_bottom_firm"]))

        # End of cover: switch to the content template and break the page
        story.append(NextPageTemplate("Content"))
        story.append(PageBreak())
        return story

    # -- Simplified cover (draft) ----------------------------------

    def _build_draft_cover(self, fm: dict, width: float) -> list:
        """Build the simplified cover page (legal-analysis draft).

        Compared with the full cover: no EN name; the bottom marker is "DRAFT".
        """
        story = []
        content_h = self._content_height_pt()
        top_sp, mid_sp, bot_sp = self._cover_spacers(content_h)

        # -- Top region: firm name (no EN name) --
        story.append(Spacer(1, top_sp))

        firm_cn = fm.get("firm_name_cn") or self.cover_cfg.get("firm_name_cn", "")
        if firm_cn:
            story.append(Paragraph(firm_cn, self.styles["cover_firm"]))

        # -- Brand-color decoration line --
        story.append(Spacer(1, 20))
        line_width = width * self.brand_rules.get("title_line_width_ratio", 0.6)
        line_height = self.brand_rules.get("cover_line_height_pt", 1)
        story.append(HRFlowable(
            width=line_width,
            thickness=line_height,
            color=self.colors["primary"],
            spaceBefore=2,
            spaceAfter=8,
            hAlign="CENTER",
        ))

        # -- Title --
        title = fm.get("title", "")
        if title:
            formatted_title = self.font_mgr.format_mixed_text(
                title, role="heading", bold=True
            )
            story.append(Paragraph(formatted_title, self.styles["cover_title"]))

        # -- Middle whitespace --
        story.append(Spacer(1, mid_sp))

        # -- Metadata region --
        for item in self._meta_items(fm):
            formatted = self.font_mgr.format_mixed_text(item, role="meta")
            story.append(Paragraph(formatted, self.styles["cover_meta"]))

        # -- Bottom whitespace --
        story.append(Spacer(1, bot_sp))

        # -- Bottom region: decoration line + draft marker --
        story.append(HRFlowable(
            width=line_width,
            thickness=line_height,
            color=self.colors["primary"],
            spaceBefore=2,
            spaceAfter=6,
            hAlign="CENTER",
        ))

        draft_text = self.cover_cfg.get("draft_text", "DRAFT")
        story.append(Paragraph(draft_text, self.styles["cover_draft_label"]))
        if firm_cn:
            story.append(Paragraph(firm_cn, self.styles["cover_bottom_firm"]))

        # End of cover: switch to the content template and break the page
        story.append(NextPageTemplate("Content"))
        story.append(PageBreak())
        return story

    # -- Brand-color cover -----------------------------------------

    def _build_color_cover(self, fm: dict, width: float) -> list:
        """Full-bleed brand cover: primary background, white text, accent/secondary decoration.

        Both opinion and draft use this layout; doc_type selects the bottom marker.
        """
        story = []
        content_h = self._content_height_pt()
        top_sp, mid_sp, bot_sp = self._cover_spacers(content_h)
        doc_type = fm.get("doc_type", "opinion")

        # Color definitions
        bg = self.colors["primary"]
        text_white = Color(1, 1, 1)
        text_light = self._light_color(self.colors["text_light"], 0.85)
        line_color = self.colors["accent"]
        conf_color = self.colors["accent"]
        bottom_firm_color = text_light

        # -- Full-bleed background block (drawn first, covers the whole page) --
        story.append(_ColorBg(bg, width, self.page_cfg))

        # -- Top region: firm name + EN name --
        story.append(Spacer(1, top_sp))

        firm_cn = fm.get("firm_name_cn") or self.cover_cfg.get("firm_name_cn", "")
        firm_style = self.styles["cover_firm"].clone(
            "cover_firm_inv", textColor=text_white
        )
        if firm_cn:
            story.append(Paragraph(firm_cn, firm_style))

        if doc_type == "opinion":
            firm_en = fm.get("firm_name_en") or self.cover_cfg.get("firm_name_en", "")
            en_style = self.styles["cover_english"].clone(
                "cover_english_inv", textColor=text_light
            )
            if firm_en:
                story.append(Paragraph(firm_en, en_style))

        # -- Decoration line (accent color) --
        story.append(Spacer(1, 20))
        line_width = width * self.brand_rules.get("title_line_width_ratio", 0.6)
        line_height = self.brand_rules.get("cover_line_height_pt", 1)
        story.append(HRFlowable(
            width=line_width,
            thickness=line_height,
            color=line_color,
            spaceBefore=2,
            spaceAfter=8,
            hAlign="CENTER",
        ))

        # -- Title (large, white) --
        title = fm.get("title", "")
        if title:
            formatted_title = self.font_mgr.format_mixed_text(
                title, role="heading", bold=True
            )
            title_style = self.styles["cover_title"].clone(
                "cover_title_inv", textColor=text_white
            )
            story.append(Paragraph(formatted_title, title_style))

        # -- Middle whitespace --
        story.append(Spacer(1, mid_sp))

        # -- Metadata region (light-colored text) --
        meta_style = self.styles["cover_meta"].clone(
            "cover_meta_inv", textColor=text_light
        )
        for item in self._meta_items(fm):
            formatted = self.font_mgr.format_mixed_text(item, role="meta")
            story.append(Paragraph(formatted, meta_style))

        # -- Bottom whitespace --
        story.append(Spacer(1, bot_sp))

        # -- Bottom region: decoration line + marker + firm name --
        story.append(HRFlowable(
            width=line_width,
            thickness=line_height,
            color=line_color,
            spaceBefore=2,
            spaceAfter=6,
            hAlign="CENTER",
        ))

        if doc_type == "draft":
            draft_text = self.cover_cfg.get("draft_text", "DRAFT")
            draft_style = self.styles["cover_draft_label"].clone(
                "cover_draft_inv", textColor=conf_color
            )
            story.append(Paragraph(draft_text, draft_style))
        else:
            confidential = fm.get("confidential", True)
            if confidential:
                conf_text = self.cover_cfg.get(
                    "confidential_text", "PRIVILEGED & CONFIDENTIAL"
                )
                conf_style = self.styles["cover_confidential"].clone(
                    "cover_conf_inv", textColor=conf_color
                )
                story.append(Paragraph(conf_text, conf_style))

        bottom_style = self.styles["cover_bottom_firm"].clone(
            "cover_bf_inv", textColor=bottom_firm_color
        )
        if firm_cn:
            story.append(Paragraph(firm_cn, bottom_style))

        # End of cover: switch to the content template and break the page
        story.append(NextPageTemplate("Content"))
        story.append(PageBreak())
        return story

    # -- Memo header -----------------------------------------------

    def _build_memo_header(self, fm: dict, width: float) -> list:
        """Build the memo header table (TO / FROM / DATE / RE), prepended to content."""
        label_style = self.styles["memo_header_label"]
        value_style = self.styles["memo_header_value"]

        rows = []

        addressee = fm.get("addressee", "")
        if addressee:
            formatted = self.font_mgr.format_mixed_text(addressee, role="body")
            rows.append([
                Paragraph("TO:", label_style),
                Paragraph(formatted, value_style),
            ])

        author = fm.get("author", "")
        if author:
            formatted = self.font_mgr.format_mixed_text(author, role="body")
            rows.append([
                Paragraph("FROM:", label_style),
                Paragraph(formatted, value_style),
            ])

        date = fm.get("date", "")
        if date:
            formatted = self.font_mgr.format_mixed_text(date, role="body")
            rows.append([
                Paragraph("DATE:", label_style),
                Paragraph(formatted, value_style),
            ])

        title = fm.get("title", "")
        if title:
            formatted = self.font_mgr.format_mixed_text(title, role="body")
            rows.append([
                Paragraph("RE:", label_style),
                Paragraph(formatted, value_style),
            ])

        if not rows:
            return []

        # Column widths: label column fixed at 60pt, value column takes the rest
        label_w = 60
        value_w = width - label_w

        # Style
        border_color = self.colors["border"]
        primary_color = self.colors["primary"]

        table_style = TableStyle([
            # Bottom line (brand color, slightly thicker)
            ('LINEBELOW', (0, -1), (-1, -1), 0.75, primary_color),
            # Top line (thin gray)
            ('LINEABOVE', (0, 0), (-1, 0), 0.5, border_color),
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            # No vertical lines, no inner horizontal lines
            ('LINEBEFORE', (0, 0), (-1, -1), 0, Color(0, 0, 0, 0)),
            ('LINEAFTER', (0, 0), (-1, -1), 0, Color(0, 0, 0, 0)),
            ('LINEBELOW', (0, 0), (-1, -2), 0, Color(0, 0, 0, 0)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ])

        table = Table(rows, colWidths=[label_w, value_w], style=table_style)

        return [
            Spacer(1, 6),
            table,
            Spacer(1, 16),
        ]

    # -- Helpers ---------------------------------------------------

    def _meta_items(self, fm: dict) -> list:
        """Build the cover metadata list from front matter, using i18n labels.

        Returns a list of strings: [ref_no, "label: addressee", "label: author", ...].
        Labels are read from theme.json's i18n section so no UI text is hardcoded.
        """
        i18n = self.theme.get_i18n()
        items = []

        ref_no = fm.get("ref_no", "")
        if ref_no:
            items.append(ref_no)

        addressee = fm.get("addressee", "")
        if addressee:
            items.append("{}{}".format(i18n.get("meta_addressee_label", ""), addressee))

        author = fm.get("author", "")
        if author:
            items.append("{}{}".format(i18n.get("meta_author_label", ""), author))

        date = fm.get("date", "")
        if date:
            items.append("{}{}".format(i18n.get("meta_date_label", ""), date))

        return items

    def _content_height_pt(self) -> float:
        """Compute the available content-area height (pt) for the current page setup."""
        return (
            self.page_cfg["height_mm"]
            - self.page_cfg["margin_top_mm"]
            - self.page_cfg["margin_bottom_mm"]
        ) * mm

    def _cover_spacers(self, content_h: float) -> tuple:
        """Compute the three cover Spacer heights, auto-fitting the page.

        On small pages (e.g. landscape A4) the whitespace ratio is reduced to keep
        the cover content from overflowing onto a second page.
        Returns (top_spacer, mid_spacer, bot_spacer).
        """
        # Estimated fixed content height (firm+EN+line+title+meta+bottom)
        # Conservative: includes all paragraph spacing and decoration elements.
        est_content = 290

        # Max total whitespace = min(58% of page height, page height - fixed content - safety)
        max_spacer_total = content_h * 0.58
        available = content_h - est_content - 30  # 30pt safety margin
        spacer_total = min(max_spacer_total, max(available, 60))

        # Proportional split: top 31%, mid 21%, bot 48%
        top = spacer_total * 0.31
        mid = spacer_total * 0.21
        bot = spacer_total * 0.48
        return (top, mid, bot)

    @staticmethod
    def _light_color(base_color: Color, factor: float = 0.5) -> Color:
        """Lighten a color toward white. factor: 0=original, 1=pure white."""
        r = base_color.red + (1 - base_color.red) * factor
        g = base_color.green + (1 - base_color.green) * factor
        b = base_color.blue + (1 - base_color.blue) * factor
        return Color(r, g, b)
