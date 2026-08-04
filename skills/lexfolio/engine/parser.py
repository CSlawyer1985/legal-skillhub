# -*- coding: utf-8 -*-
"""
Markdown parser: parses Markdown text line-by-line into a list of Block objects.

Usage:
    parser = MarkdownParser()
    blocks, front_matter = parser.parse(markdown_text)
"""

import re
from dataclasses import dataclass, field

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class Block:
    """A single document block (heading, paragraph, quote, table, etc.)."""
    type: str           # "heading" | "paragraph" | "quote" | "table" | "hr"
    content: str = ""   # text content (inline markup already converted to ReportLab)
    level: int = 0      # heading level (1-3)
    rows: list = field(default_factory=list)  # table only: list[list[str]]
    subtype: str = ""   # quote subtype: "case" / "law" / "general" / "opinion"


class MarkdownParser:
    """Parse Markdown line-by-line into a list of Block objects."""

    # Block-level patterns
    _RE_HEADING = re.compile(r'^(#{1,3})\s+(.+)$')
    _RE_HR = re.compile(r'^(\-{3,}|\*{3,}|_{3,})\s*$')
    _RE_PAGEBREAK = re.compile(r'^<!--\s*pagebreak\s*-->$')
    _RE_SIGFOOTER = re.compile(r'^<!--\s*sigfooter\s*-->$')
    _RE_QUOTE = re.compile(r'^>\s?(?!right\b)(.*)$')
    _RE_RIGHT = re.compile(r'^>right\s+(.+)$')
    _RE_TABLE_ROW = re.compile(r'^\|(.+)\|\s*$')
    _RE_TABLE_SEP = re.compile(r'^\|[\s\-:|]+\|\s*$')

    # Inline formatting
    _RE_BOLD = re.compile(r'\*\*(.+?)\*\*')
    _RE_ITALIC = re.compile(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)')

    # Footnote markers (uses \u escapes for CJK to keep source ASCII-clean)
    # \u6ce8 = "note" glyph (CN). ^[n]^ or ^[noteN]^ -> superscript
    _RE_FOOTNOTE_REF = re.compile(r'\^\[(\u6ce8?\d+)\]\^')
    _RE_FOOTNOTE_DEF = re.compile(r'^\[\^(\d+)\]:\s*', re.MULTILINE)  # [^n]: -> definition

    # Quote-block subtype detection (uses raw text, before _format_inline)
    _RE_CASE_QUOTE = re.compile(r'^[\u201c\u201d"]')         # starts with CN/EN double quote
    # \u7b2c = "article"; \u6761\u6b3e\u9879\u76ee\u7ae0\u8282 = clause/item/chapter/section
    _RE_LAW_QUOTE = re.compile(r'^\u7b2c.{1,6}[\u6761\u6b3e\u9879\u76ee\u7ae0\u8282]')

    # Opinion-paragraph detection (runs against _format_inline output)
    # \u5206\u6790\u610f\u89c1 = "analysis opinion"; \uff1a = fullwidth colon
    _RE_OPINION = re.compile(r'^<b>\u5206\u6790\u610f\u89c1</b>[\uff1a:]')

    def parse(self, text: str) -> tuple:
        """Parse Markdown text.

        Args:
            text: raw Markdown text.

        Returns:
            (blocks, front_matter)
            - blocks: list[Block]
            - front_matter: dict (YAML front matter; empty dict if absent)
        """
        lines = text.split('\n')
        front_matter, body_lines = self._extract_front_matter(lines)

        # Footnote marker preprocessing
        body_text = '\n'.join(body_lines)
        body_text = self._RE_FOOTNOTE_REF.sub(r'<super>\1</super>', body_text)
        body_text = self._RE_FOOTNOTE_DEF.sub(r'[\1] ', body_text)
        # Superscripts must sit before punctuation (CJK convention)
        body_text = re.sub(
            r'([\uff0c\u3002\uff1b\uff1a\u3001\uff01\uff1f'
            r'\u201d\u2019\u300b\u3011\uff09\u2026\u2014]+)'
            r'<super>(\u6ce8?\d+)</super>',
            r'<super>\2</super>\1',
            body_text,
        )
        body_lines = body_text.split('\n')

        blocks = self._parse_blocks(body_lines)
        return blocks, front_matter

    # -- YAML Front Matter -----------------------------------------

    def _extract_front_matter(self, lines: list) -> tuple:
        """Extract YAML front matter; return (dict, remaining_lines)."""
        if not lines or lines[0].strip() != '---':
            return {}, lines

        # Find the closing ---
        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                end_idx = i
                break

        if end_idx < 0:
            return {}, lines

        yaml_text = '\n'.join(lines[1:end_idx])
        remaining = lines[end_idx + 1:]

        if HAS_YAML:
            try:
                fm = yaml.safe_load(yaml_text) or {}
            except yaml.YAMLError:
                fm = {}
        else:
            # Fallback: minimal parsing when PyYAML is unavailable
            fm = self._simple_yaml_parse(yaml_text)

        return fm, remaining

    @staticmethod
    def _simple_yaml_parse(text: str) -> dict:
        """Minimal YAML parser (handles key: value only)."""
        result = {}
        for line in text.split('\n'):
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                key, _, value = line.partition(':')
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value:
                    result[key] = value
        return result

    # -- Block parsing ---------------------------------------------

    def _parse_blocks(self, lines: list) -> list:
        """Parse a list of lines into a list of Block objects."""
        blocks = []
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]
            stripped = line.strip()

            # Blank line: skip
            if not stripped:
                i += 1
                continue

            # Page break
            if self._RE_PAGEBREAK.match(stripped):
                blocks.append(Block(type="pagebreak"))
                i += 1
                continue

            # Signature-page footer ornament (symmetric with the cover footer)
            if self._RE_SIGFOOTER.match(stripped):
                blocks.append(Block(type="sigfooter"))
                i += 1
                continue

            # Horizontal rule
            if self._RE_HR.match(stripped):
                blocks.append(Block(type="hr"))
                i += 1
                continue

            # Heading
            m_heading = self._RE_HEADING.match(stripped)
            if m_heading:
                level = len(m_heading.group(1))
                content = self._format_inline(m_heading.group(2))
                blocks.append(Block(type="heading", content=content, level=level))
                i += 1
                continue

            # Right-aligned paragraph: >right prefix
            m_right = self._RE_RIGHT.match(stripped)
            if m_right:
                content = self._format_inline(m_right.group(1))
                blocks.append(Block(type="paragraph", content=content, subtype="right"))
                i += 1
                continue

            # Quote block: merge consecutive > lines
            if self._RE_QUOTE.match(stripped):
                quote_lines = []
                while i < n:
                    m_q = self._RE_QUOTE.match(lines[i].strip())
                    if m_q:
                        quote_lines.append(m_q.group(1))
                        i += 1
                    else:
                        break
                raw_content = '\n'.join(quote_lines)
                # Detect subtype first (on raw text, before _format_inline)
                if self._RE_CASE_QUOTE.match(raw_content):
                    sub = "case"
                elif self._RE_LAW_QUOTE.match(raw_content):
                    sub = "law"
                else:
                    sub = "general"
                content = self._format_inline(raw_content)
                blocks.append(Block(type="quote", content=content, subtype=sub))
                continue

            # Table: merge consecutive | lines
            if self._RE_TABLE_ROW.match(stripped):
                table_rows = []
                while i < n:
                    row_stripped = lines[i].strip()
                    m_row = self._RE_TABLE_ROW.match(row_stripped)
                    if m_row:
                        # Skip the separator row (|---|---|)
                        if not self._RE_TABLE_SEP.match(row_stripped):
                            cells = [self._format_inline(c.strip()) for c in m_row.group(1).split('|')]
                            table_rows.append(cells)
                        i += 1
                    else:
                        break
                if table_rows:
                    blocks.append(Block(type="table", rows=table_rows))
                continue

            # Plain paragraph: merge consecutive non-blank lines into one paragraph
            para_lines = []
            while i < n:
                line_stripped = lines[i].strip()
                if not line_stripped:
                    i += 1
                    break
                # Stop the paragraph if a heading/quote/table/hr starts
                if (self._RE_HEADING.match(line_stripped) or
                    self._RE_QUOTE.match(line_stripped) or
                    self._RE_TABLE_ROW.match(line_stripped) or
                    self._RE_HR.match(line_stripped)):
                    break
                para_lines.append(line_stripped)
                i += 1

            if para_lines:
                content = self._format_inline(''.join(para_lines))
                sub = "opinion" if self._RE_OPINION.match(content) else ""
                blocks.append(Block(type="paragraph", content=content, subtype=sub))

        return blocks

    # -- Inline formatting -----------------------------------------

    def _format_inline(self, text: str) -> str:
        """Convert Markdown inline formatting to ReportLab markup.

        Handles:
        - **bold** -> <b>bold</b>
        - *italic* -> <i>italic</i>
        - `code` -> <font face="Courier">code</font>
        """
        # Handle code first (so * inside code is not parsed)
        text = self._format_code(text)
        # Then bold (must precede italic so ** is not read as two *)
        text = self._RE_BOLD.sub(r'<b>\1</b>', text)
        # Then italic
        text = self._RE_ITALIC.sub(r'<i>\1</i>', text)
        return text

    @staticmethod
    def _format_code(text: str) -> str:
        """Convert `code` -> <font face="Courier">code</font>"""
        result = []
        parts = text.split('`')
        for idx, part in enumerate(parts):
            if idx % 2 == 0:
                result.append(part)
            else:
                result.append('<font face="Courier">{}</font>'.format(part))
        return ''.join(result)
