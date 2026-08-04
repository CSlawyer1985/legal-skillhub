# -*- coding: utf-8 -*-
"""
PDF renderer: converts a list of Block objects into ReportLab flowables and
emits a PDF file.

Usage:
    renderer = PDFRenderer(theme, font_mgr, styles)
    renderer.render(blocks, output_path, front_matter=front_matter)

Note: ReportLab's default unit is the point (pt); all numeric values are used as-is.
"""

import copy
import io
import re

from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import Color

from engine.theme import ThemeLoader
from engine.fonts import FontManager
from engine.parser import Block
from engine.cover import CoverBuilder
from engine.chrome import PageChrome


# Pattern used to count pages in a rendered PDF byte stream.
_RE_PDF_PAGES = re.compile(rb"/Type\s*/Page[^s]")


class PDFRenderer:
    """Render a list of Block objects into a PDF file."""

    def __init__(self, theme: ThemeLoader, font_mgr: FontManager, styles: dict):
        self.theme = theme
        self.font_mgr = font_mgr
        self.styles = styles
        self.colors = theme.get_colors()
        self.page_cfg = theme.get_page()
        self.brand_rules = theme.get_brand_rules()
        self.table_cfg = theme.get_table_config()

    def render(self, blocks: list, output_path: str, front_matter: dict = None):
        """Render the Block list into a PDF file.

        Args:
            blocks:       parsed Block list
            output_path:  PDF output path
            front_matter: Markdown front matter dict (carries doc_type and cover info)
        """
        self._front_matter = front_matter or {}

        # Page size
        page_size_name = self.page_cfg.get("size", "A4")
        if page_size_name == "A4_landscape":
            from reportlab.lib.pagesizes import landscape as _landscape
            page_size = _landscape(A4)
        else:
            page_size = A4

        # Margins
        margin_l = self.page_cfg["margin_left_mm"] * mm
        margin_r = self.page_cfg["margin_right_mm"] * mm
        margin_t = self.page_cfg["margin_top_mm"] * mm
        margin_b = self.page_cfg["margin_bottom_mm"] * mm

        # Available width
        self._available_width = (
            self.page_cfg["width_mm"] * mm - margin_l - margin_r
        )

        # Whether a cover page is present
        has_cover = False
        if front_matter:
            doc_type = front_matter.get("doc_type", "review")
            has_cover = doc_type in ("opinion", "draft")

        # Header / footer
        chrome = PageChrome(self.theme, self.font_mgr, front_matter or {})

        # Frame (content area)
        frame_w = self._available_width
        frame_h = (
            self.page_cfg["height_mm"] * mm - margin_t - margin_b
        )
        frame = Frame(
            margin_l, margin_b, frame_w, frame_h,
            id="normal",
        )

        # PageTemplate
        templates = []
        if has_cover:
            templates.append(PageTemplate(
                id="Cover", frames=[frame], onPage=chrome.on_cover_page,
            ))
            templates.append(PageTemplate(
                id="Content", frames=[frame], onPage=chrome.on_content_page,
            ))
        else:
            # No cover: use the Content template directly
            templates.append(PageTemplate(
                id="Content", frames=[frame], onPage=chrome.on_content_page,
            ))

        # -- Two-pass render: first pass counts total pages --
        story = self._build_full_story(blocks, front_matter)
        buf = io.BytesIO()
        doc1 = BaseDocTemplate(
            buf, pagesize=page_size,
            leftMargin=margin_l, rightMargin=margin_r,
            topMargin=margin_t, bottomMargin=margin_b,
        )
        doc1.addPageTemplates(templates)
        doc1.build(story)

        # Count pages from the rendered byte stream
        total_pages = len(_RE_PDF_PAGES.findall(buf.getvalue()))

        chrome.total_pages = total_pages
        chrome.cover_pages = 1 if has_cover else 0

        # -- Second pass: final output --
        story = self._build_full_story(blocks, front_matter)
        doc2 = BaseDocTemplate(
            output_path, pagesize=page_size,
            leftMargin=margin_l, rightMargin=margin_r,
            topMargin=margin_t, bottomMargin=margin_b,
        )
        # Recreate templates (doc1 has consumed the frame references)
        frame2 = Frame(margin_l, margin_b, frame_w, frame_h, id="normal")
        templates2 = []
        if has_cover:
            templates2.append(PageTemplate(
                id="Cover", frames=[frame2], onPage=chrome.on_cover_page,
            ))
            templates2.append(PageTemplate(
                id="Content", frames=[frame2], onPage=chrome.on_content_page,
            ))
        else:
            templates2.append(PageTemplate(
                id="Content", frames=[frame2], onPage=chrome.on_content_page,
            ))
        doc2.addPageTemplates(templates2)
        doc2.build(story)

    def _build_full_story(self, blocks: list, front_matter: dict = None) -> list:
        """Build the full flowable list (cover + body). Returns a fresh list each call."""
        story = []

        # Cover page / memo header
        if front_matter:
            cover_builder = CoverBuilder(self.theme, self.font_mgr, self.styles)
            cover_flowables = cover_builder.build(
                front_matter, self._available_width
            )
            story.extend(cover_flowables)

        # Body
        story.extend(self.build_story(blocks))
        return story

    def build_story(self, blocks: list) -> list:
        """Convert the Block list into a ReportLab flowable list.

        Widow/orphan control: a heading is wrapped with the following content
        block in a KeepTogether so the heading never sits alone at the page bottom.
        """
        # Content types that may be grouped with a heading
        _CONTENT_TYPES = {"paragraph", "quote", "table"}

        story = []
        i = 0
        n = len(blocks)

        while i < n:
            block = blocks[i]
            flowables = self._block_to_flowables(block)

            # Heading block: try to group with the next content block to avoid orphans
            if block.type == "heading" and i + 1 < n \
                    and blocks[i + 1].type in _CONTENT_TYPES:
                next_flowables = self._block_to_flowables(blocks[i + 1])
                combined = flowables + next_flowables
                story.append(KeepTogether(combined))
                i += 2
            # Heading with multiple flowables (e.g. H1 + decoration line): wrap itself
            elif block.type == "heading" and len(flowables) > 1:
                story.append(KeepTogether(flowables))
                i += 1
            else:
                story.extend(flowables)
                i += 1

        return story

    # -- Block -> Flowable conversion ------------------------------

    def _block_to_flowables(self, block: Block) -> list:
        # Opinion paragraph: brand-color top bar + body
        if block.type == "paragraph" and block.subtype == "opinion":
            return self._render_opinion(block)

        handlers = {
            "heading":   self._render_heading,
            "paragraph": self._render_paragraph,
            "quote":     self._render_quote,
            "table":     self._render_table,
            "hr":        self._render_hr,
            "pagebreak": self._render_pagebreak,
            "sigfooter": self._render_sigfooter,
        }
        handler = handlers.get(block.type)
        if handler:
            return handler(block)
        return []

    def _render_heading(self, block: Block) -> list:
        """Render a heading. H1 gets a brand-color decoration line."""
        result = []
        style_key = "h{}".format(block.level)
        style = self.styles[style_key]

        formatted_text = self.font_mgr.format_mixed_text(
            block.content, role="heading", bold=(block.level <= 2)
        )
        result.append(Paragraph(formatted_text, style))

        # H1 brand-color decoration line
        if block.level == 1:
            line_width = self._available_width * self.brand_rules["title_line_width_ratio"]
            line_height = self.brand_rules["title_line_height_pt"]
            result.append(Spacer(1, 4))
            result.append(HRFlowable(
                width=line_width,
                thickness=line_height,
                color=self.colors["primary"],
                spaceBefore=2,
                spaceAfter=8,
                hAlign="LEFT",
            ))
        return result

    def _render_paragraph(self, block: Block) -> list:
        """Render a body paragraph. subtype='right' aligns right."""
        formatted_text = self.font_mgr.format_mixed_text(
            block.content, role="body"
        )
        if block.subtype == "right":
            from reportlab.lib.enums import TA_RIGHT
            style = copy.copy(self.styles["body"])
            style.alignment = TA_RIGHT
            style.firstLineIndent = 0
            style.leftIndent = 0
            return [Paragraph(formatted_text, style)]
        return [Paragraph(formatted_text, self.styles["body"])]

    def _render_quote(self, block: Block) -> list:
        """Dispatch quote rendering by subtype."""
        if block.subtype == "law":
            return self._render_quote_law(block)
        else:
            return self._render_quote_case(block)  # case + general share this path

    def _render_quote_case(self, block: Block) -> list:
        """Render a case/general quote: brand-color left rule + light shading + kai font."""
        quote_style = self.styles["quote_case"]
        formatted_text = self.font_mgr.format_mixed_text(
            block.content, role="quote"
        )
        para = Paragraph(formatted_text, quote_style)

        border_width = self.brand_rules["quote_border_width_pt"]  # 3
        gap = 10
        content_width = self._available_width - border_width - gap

        quote_table = Table(
            [['', para]],
            colWidths=[border_width, content_width],
            style=TableStyle([
                # Left column: brand-color vertical rule
                ('BACKGROUND', (0, 0), (0, 0), self.colors["primary"]),
                ('LEFTPADDING', (0, 0), (0, 0), 0),
                ('RIGHTPADDING', (0, 0), (0, 0), 0),
                ('TOPPADDING', (0, 0), (0, 0), 0),
                ('BOTTOMPADDING', (0, 0), (0, 0), 0),
                # Right column: light shading
                ('BACKGROUND', (1, 0), (1, 0), self.colors["bg_subtle"]),
                ('LEFTPADDING', (1, 0), (1, 0), gap),
                ('RIGHTPADDING', (1, 0), (1, 0), 8),
                ('TOPPADDING', (1, 0), (1, 0), 8),
                ('BOTTOMPADDING', (1, 0), (1, 0), 8),
                # Remove all default borders
                ('LINEBEFORE', (0, 0), (-1, -1), 0, Color(0, 0, 0, 0)),
                ('LINEAFTER', (0, 0), (-1, -1), 0, Color(0, 0, 0, 0)),
                ('LINEABOVE', (0, 0), (-1, -1), 0, Color(0, 0, 0, 0)),
                ('LINEBELOW', (0, 0), (-1, -1), 0, Color(0, 0, 0, 0)),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]),
        )
        return [quote_table]

    def _render_quote_law(self, block: Block) -> list:
        """Render a law quote: serif font, no shading, thin top/bottom rules."""
        law_style = self.styles["quote_law"]
        formatted_text = self.font_mgr.format_mixed_text(
            block.content, role="body"  # use the body font (serif)
        )
        para = Paragraph(formatted_text, law_style)

        border_color = self.colors["border"]
        law_cfg = self.theme._data.get("typography", {}).get("quote_law", {})
        l_pad = law_cfg.get("left_indent_pt", 28)
        r_pad = law_cfg.get("right_indent_pt", 24)

        law_table = Table(
            [[para]],
            colWidths=[self._available_width],
            style=TableStyle([
                ('LINEABOVE', (0, 0), (-1, 0), 0.5, border_color),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, border_color),
                ('LEFTPADDING', (0, 0), (-1, -1), l_pad),
                ('RIGHTPADDING', (0, 0), (-1, -1), r_pad),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LINEBEFORE', (0, 0), (-1, -1), 0, Color(0, 0, 0, 0)),
                ('LINEAFTER', (0, 0), (-1, -1), 0, Color(0, 0, 0, 0)),
                ('BACKGROUND', (0, 0), (-1, -1), Color(0, 0, 0, 0)),
            ]),
        )
        return [law_table]

    def _render_opinion(self, block: Block) -> list:
        """Render an opinion paragraph: brand-color top bar + serif body."""
        opinion_style = self.styles["opinion"]
        formatted_text = self.font_mgr.format_mixed_text(
            block.content, role="body"
        )
        para = Paragraph(formatted_text, opinion_style)

        bar_height = self.brand_rules.get("opinion_bar_height_pt", 1)
        bar = HRFlowable(
            width="100%",
            thickness=bar_height,
            color=self.colors["primary"],
            spaceBefore=8,
            spaceAfter=2,
            hAlign="LEFT",
        )
        return [KeepTogether([bar, para])]

    def _render_table(self, block: Block) -> list:
        """Render a three-line table (with zebra striping + right-aligned numeric columns)."""
        if not block.rows:
            return []

        header_style = self.styles["table_header"]
        cell_style = self.styles["table_cell"]

        # Build table data
        table_data = []
        for row_idx, row in enumerate(block.rows):
            styled_row = []
            for cell_text in row:
                formatted = self.font_mgr.format_mixed_text(cell_text, role="table")
                style = header_style if row_idx == 0 else cell_style
                styled_row.append(Paragraph(formatted, style))
            table_data.append(styled_row)

        if not table_data:
            return []

        # Column widths (equal split); guard against an empty-row divide-by-zero
        n_cols = max((len(row) for row in table_data), default=1)
        if n_cols < 1:
            n_cols = 1
        col_width = self._available_width / n_cols

        # Detect numeric columns (skip header, inspect data rows)
        numeric_cols = self._detect_numeric_cols(block.rows, n_cols)

        # Header background: brand color primary x opacity
        opacity = self.table_cfg.get("header_bg_opacity", 0.10)
        header_bg = self.theme.get_color_with_opacity("primary", opacity)

        # Zebra color (even data rows)
        zebra_hex = self.table_cfg.get("zebra_even_color", "#F8F9FB")
        zebra_color = Color(
            int(zebra_hex[1:3], 16) / 255,
            int(zebra_hex[3:5], 16) / 255,
            int(zebra_hex[5:7], 16) / 255,
        )

        # Three-line table style
        border_color = self.colors["border"]
        top_line = self.table_cfg.get("top_line_pt", 0.75)
        header_line = self.table_cfg.get("header_line_pt", 0.5)
        bottom_line = self.table_cfg.get("bottom_line_pt", 0.75)
        v_pad = self.table_cfg.get("cell_padding_vertical_pt", 8)
        h_pad = self.table_cfg.get("cell_padding_horizontal_pt", 8)
        spacing_before = self.table_cfg.get("table_spacing_before_pt", 12)
        spacing_after = self.table_cfg.get("table_spacing_after_pt", 12)

        style_cmds = [
            # Top line
            ('LINEABOVE', (0, 0), (-1, 0), top_line, border_color),
            # Header bottom line
            ('LINEBELOW', (0, 0), (-1, 0), header_line, border_color),
            # Bottom line
            ('LINEBELOW', (0, -1), (-1, -1), bottom_line, border_color),
            # Header background
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), v_pad),
            ('BOTTOMPADDING', (0, 0), (-1, -1), v_pad),
            ('LEFTPADDING', (0, 0), (-1, -1), h_pad),
            ('RIGHTPADDING', (0, 0), (-1, -1), h_pad),
            # No vertical lines, no cell borders
            ('LINEBEFORE', (0, 0), (-1, -1), 0, Color(0, 0, 0, 0)),
            ('LINEAFTER', (0, 0), (-1, -1), 0, Color(0, 0, 0, 0)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        # Zebra striping: even data rows (header is row 0, data rows start at row 1)
        n_rows = len(table_data)
        for row_idx in range(2, n_rows, 2):  # row 2, 4, 6... (0-indexed)
            style_cmds.append(
                ('BACKGROUND', (0, row_idx), (-1, row_idx), zebra_color)
            )

        # Right-align numeric columns
        for col_idx in numeric_cols:
            if col_idx < n_cols:
                style_cmds.append(
                    ('ALIGN', (col_idx, 1), (col_idx, -1), 'RIGHT')
                )

        table_style = TableStyle(style_cmds)
        table = Table(table_data, colWidths=[col_width] * n_cols, style=table_style)
        return [Spacer(1, spacing_before), table, Spacer(1, spacing_after)]

    @staticmethod
    def _detect_numeric_cols(rows: list, n_cols: int) -> set:
        """Detect numeric columns: a column where over half the data cells are numeric."""
        _RE_NUMERIC = re.compile(
            r'^[\d,\uff0c.%\uff05]+$'   # digits + thousands separators + percent sign
        )
        if len(rows) <= 1:
            return set()

        data_rows = rows[1:]  # skip header
        n_data = len(data_rows)
        numeric_cols = set()

        for col in range(n_cols):
            count = 0
            for row in data_rows:
                if col < len(row):
                    text = row[col].strip()
                    if _RE_NUMERIC.match(text):
                        count += 1
            if count > n_data / 2:
                numeric_cols.add(col)

        return numeric_cols

    def _render_hr(self, block: Block) -> list:
        """Render a horizontal divider."""
        return [
            Spacer(1, 6),
            HRFlowable(
                width="100%",
                thickness=0.5,
                color=self.colors["border"],
                spaceBefore=4,
                spaceAfter=4,
            ),
        ]

    def _render_pagebreak(self, block: Block) -> list:
        """Render a forced page break."""
        return [PageBreak()]

    def _render_sigfooter(self, block: Block) -> list:
        """Render the signature-page footer: brand-color line + confidential marker + firm name."""
        cover_cfg = self.theme.get_cover_config()
        firm_cn = self._front_matter.get("firm_name_cn") or cover_cfg.get("firm_name_cn", "")

        # Line params match the cover
        line_width = self._available_width * self.brand_rules.get("title_line_width_ratio", 0.6)
        line_height = self.brand_rules.get("cover_line_height_pt", 1)

        result = []
        # Whitespace: keep the footer near the page bottom
        result.append(Spacer(1, 40))
        # Brand-color decoration line
        result.append(HRFlowable(
            width=line_width,
            thickness=line_height,
            color=self.colors["primary"],
            spaceBefore=2,
            spaceAfter=6,
            hAlign="CENTER",
        ))
        # Confidential marker
        confidential = cover_cfg.get("confidential_text", "PRIVILEGED & CONFIDENTIAL")
        result.append(Paragraph(confidential, self.styles["cover_confidential"]))
        # Firm name
        result.append(Paragraph(firm_cn, self.styles["cover_bottom_firm"]))
        return result
