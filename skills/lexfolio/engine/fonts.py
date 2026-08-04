# -*- coding: utf-8 -*-
"""
Font manager: registers dual-track fonts, builds font families, and handles
CJK / Latin mixed-script text formatting.

Usage:
    font_mgr = FontManager(theme)
    font_mgr.register_all()
    text = font_mgr.format_mixed_text("Example Law Firm")
"""

import re
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from engine.theme import ThemeLoader


# CJK range: common Han + fullwidth punctuation + fullwidth symbols
_CJK_PATTERN = re.compile(
    r'([\u4e00-\u9fff\u3000-\u303f\uff00-\uffef'  # CJK Unified + fullwidth punct
    r'\u3400-\u4dbf'  # CJK Extension A
    r'\u2e80-\u2eff'  # CJK Radicals Supplement
    r'\u2f00-\u2fdf'  # Kangxi Radicals
    r'\u2000-\u206f'  # General Punctuation (some fullwidth)
    r'\u3040-\u309f'  # Hiragana
    r'\u30a0-\u30ff'  # Katakana
    r'\uac00-\ud7af'  # Hangul
    r']+)'
)

# Latin range
_LATIN_PATTERN = re.compile(r'([A-Za-z0-9]+)')

# CJK fullwidth punctuation (for punctuation compression; matched before CJK)
_PUNCT_CJK = re.compile(
    r'([\uff0c'           # comma
    r'\u3002'             # full stop
    r'\uff1b'             # semicolon
    r'\uff1a'             # colon
    r'\u3001'             # ideographic comma
    r'\uff01'             # exclamation
    r'\uff1f'             # question mark
    r'\u201c\u201d'       # double quotation marks
    r'\u2018\u2019'       # single quotation marks
    r'\u300a\u300b'       # title marks
    r'\u3010\u3011'       # brackets
    r'\uff08\uff09'       # parentheses
    r'\u2014'             # dash
    r'\u2026'             # ellipsis
    r'\u3008-\u300f'      # supplementary brackets
    r'\uff0e'             # fullwidth full stop
    r']+)'
)


class FontManager:
    """Manage font registration, font family setup, and CJK/Latin text formatting."""

    # Font registration name mapping (logical name -> registered name).
    # NOTE: the "founder" provider is kept as an alias of "noto" for backward
    # compatibility. The original Founder (FZ) commercial fonts were removed
    # for licensing reasons (they cannot be redistributed in an open-source
    # repository). Both providers now resolve to the same open-source Noto
    # fonts (OFL). Users can configure custom fonts via theme.json paths.
    _FONT_NAMES = {
        "noto": {
            "body":    {"regular": "NotoSerifSC-Regular", "bold": "NotoSerifSC-Bold"},
            "heading": {"regular": "NotoSansSC-Medium", "bold": "NotoSansSC-Bold", "light": "NotoSansSC-Light"},
            "quote":   {"regular": "NotoSerifSC-Regular"},
        },
        "founder": {
            "body":    {"regular": "NotoSerifSC-Regular", "bold": "NotoSerifSC-Bold"},
            "heading": {"regular": "NotoSansSC-Medium", "bold": "NotoSansSC-Bold", "light": "NotoSansSC-Light"},
            "quote":   {"regular": "NotoSerifSC-Regular"},
        },
    }

    # Latin fonts (shared by both providers)
    _LATIN_NAMES = {
        "regular": "EBGaramond-Regular",
        "bold":    "EBGaramond-Bold",
        "italic":  "EBGaramond-Italic",
    }

    def __init__(self, theme: ThemeLoader):
        self.theme = theme
        self._registered = False

    @property
    def provider(self) -> str:
        return self.theme.provider

    def register_all(self):
        """Register all fonts for the active provider + Latin fonts, and build families."""
        if self._registered:
            return

        paths = self.theme.get_font_paths()
        provider = self.provider

        # Register CJK fonts
        names_map = self._FONT_NAMES.get(provider, {})
        for role, variants in names_map.items():
            for variant, reg_name in variants.items():
                font_path = paths[role][variant]
                if not os.path.exists(font_path):
                    raise FileNotFoundError(f"Font file not found: {font_path}")
                self._safe_register(reg_name, font_path)

        # Register Latin fonts
        latin_paths = paths["latin"]
        for variant, reg_name in self._LATIN_NAMES.items():
            font_path = latin_paths[variant]
            if not os.path.exists(font_path):
                raise FileNotFoundError(f"Font file not found: {font_path}")
            self._safe_register(reg_name, font_path)

        # Build font families
        self._register_families(provider)
        self._registered = True

    @staticmethod
    def _safe_register(reg_name: str, font_path: str):
        """Register a TTF font, ignoring the "already registered" case."""
        try:
            pdfmetrics.registerFont(TTFont(reg_name, font_path))
        except Exception as e:
            if "already registered" not in str(e).lower():
                raise

    def body_font(self, bold: bool = False) -> str:
        """Return the registered body font name."""
        names = self._FONT_NAMES[self.provider]["body"]
        return names["bold"] if bold else names["regular"]

    def heading_font(self, level: int = 1) -> str:
        """Return the registered heading font name. Levels 1-2 use bold, level 3 regular."""
        names = self._FONT_NAMES[self.provider]["heading"]
        if level <= 2:
            return names["bold"]
        return names["regular"]

    def latin_font(self, bold: bool = False, italic: bool = False) -> str:
        """Return the registered Latin font name."""
        if italic:
            return self._LATIN_NAMES["italic"]
        if bold:
            return self._LATIN_NAMES["bold"]
        return self._LATIN_NAMES["regular"]

    def quote_font(self) -> str:
        """Return the registered quote-block font name."""
        return self._FONT_NAMES[self.provider]["quote"]["regular"]

    def meta_font(self) -> str:
        """Return the registered meta-info font name (heading light or regular)."""
        names = self._FONT_NAMES[self.provider]["heading"]
        return names.get("light", names["regular"])

    # Matches ReportLab inline markup: open / close / self-closing tags
    _TAG_RE = re.compile(r'</?[a-zA-Z][a-zA-Z0-9]*(?:\s+[^>]*)?\s*/?>')

    def format_mixed_text(self, text: str, role: str = "body", bold: bool = False) -> str:
        """Convert CJK/Latin mixed text into ReportLab markup.

        Inline tags (<b>, <i>, <font>, ...) are extracted first; font segmentation
        is applied only to the plain-text portions so tags are never split.

        Text inside <b> automatically switches to the bold font variant.
        """
        # Resolve CJK font names (regular + bold)
        if role == "heading":
            cjk_regular = self.heading_font(level=3)
            cjk_bold = self.heading_font(level=1)
        elif role == "quote":
            cjk_regular = self.quote_font()
            cjk_bold = cjk_regular  # quote blocks have no bold variant
        elif role == "meta":
            cjk_regular = self.meta_font()
            cjk_bold = cjk_regular
        else:
            cjk_regular = self.body_font(bold=False)
            cjk_bold = self.body_font(bold=True)

        # Resolve Latin font names (regular + bold)
        lat_regular = self.latin_font(bold=False)
        lat_bold = self.latin_font(bold=True)

        # Initial font (driven by the bold argument)
        cjk_font = cjk_bold if bold else cjk_regular
        lat_font = lat_bold if bold else lat_regular

        # CJK/Latin spacing config (pt)
        body_typo = self.theme._data.get("typography", {}).get("body", {})
        spacing_pt = body_typo.get("cjk_latin_spacing_pt", 2)
        body_size_pt = body_typo.get("font_size_pt", 10.5)

        # Punctuation compression config (body only; tables/headings/quotes skip it)
        punct_cfg = self.theme._data.get("typography", {}).get("punctuation_compression", {})
        if role == "body" and punct_cfg.get("enabled", True):
            punct_ratio = punct_cfg.get("ratio", 0.8)
        else:
            punct_ratio = 1.0

        # Track <b> state to switch to the bold font within bold spans
        in_bold = bold
        # Track <i> state
        in_italic = False

        # Split by ReportLab tags: tags kept verbatim, text gets font wrapping
        parts = []
        pos = 0
        for m in self._TAG_RE.finditer(text):
            tag_text = m.group()
            # Text before the tag -> font segmentation
            if m.start() > pos:
                parts.append(self._wrap_segments(
                    text[pos:m.start()], cjk_font, lat_font,
                    spacing_pt, body_size_pt, punct_ratio,
                ))
            # Detect <b> / </b> and toggle bold state
            tag_lower = tag_text.lower()
            if tag_lower.startswith('<b>') or tag_lower.startswith('<b '):
                in_bold = True
                cjk_font = cjk_bold
                lat_font = lat_bold
            elif tag_lower == '</b>':
                in_bold = False
                cjk_font = cjk_bold if bold else cjk_regular
                lat_font = lat_bold if bold else lat_regular
            # The tag itself -> keep verbatim
            parts.append(tag_text)
            pos = m.end()
        # Trailing text
        if pos < len(text):
            parts.append(self._wrap_segments(
                text[pos:], cjk_font, lat_font,
                spacing_pt, body_size_pt, punct_ratio,
            ))

        return "".join(parts)

    # -- Internal --------------------------------------------------

    @staticmethod
    def _wrap_segments(text: str, cjk_font: str, lat_font: str,
                       spacing_pt: float = 2, body_size_pt: float = 10.5,
                       punct_ratio: float = 1.0) -> str:
        """Segment plain text into CJK / Latin / punct / other and wrap in font tags.

        A controllable-width space (Latin font at spacing_pt size) is inserted at
        CJK<->Latin boundaries. Punctuation segments are shrunk by punct_ratio to
        achieve compression.
        """
        segments = FontManager._split_text(text)
        parts = []
        prev_type = None
        for seg_type, seg_text in segments:
            if not seg_text:
                continue
            # CJK<->Latin boundary: insert controllable spacing
            if prev_type in ("cjk", "latin") and seg_type in ("cjk", "latin") \
                    and prev_type != seg_type:
                parts.append('<font name="{}" size="{:.0f}"> </font>'.format(
                    lat_font, spacing_pt))
            # XML escape: prevent & and < from confusing the ReportLab XML parser
            seg_text = seg_text.replace("&", "&amp;").replace("<", "&lt;")
            if seg_type == "cjk":
                parts.append('<font name="{}">{}</font>'.format(cjk_font, seg_text))
            elif seg_type == "latin":
                parts.append('<font name="{}">{}</font>'.format(lat_font, seg_text))
            elif seg_type == "punct":
                # Punctuation compression: shrink the font size
                reduced = body_size_pt * punct_ratio
                parts.append('<font name="{}" size="{:.1f}">{}</font>'.format(
                    cjk_font, reduced, seg_text))
            else:
                parts.append('<font name="{}">{}</font>'.format(cjk_font, seg_text))
            prev_type = seg_type
        return "".join(parts)

    def _register_families(self, provider: str):
        """Build a font family for each group so ReportLab auto-maps bold/italic."""
        names = self._FONT_NAMES.get(provider, {})

        # Body family
        body = names.get("body", {})
        if "regular" in body and "bold" in body:
            self._safe_register_family(
                body["regular"],
                normal=body["regular"],
                bold=body["bold"],
            )

        # Heading family
        heading = names.get("heading", {})
        if heading:
            kwargs = {"normal": heading.get("regular", heading.get("bold", ""))}
            if "bold" in heading:
                kwargs["bold"] = heading["bold"]
            if "light" in heading:
                kwargs["italic"] = heading["light"]  # map light -> italic slot
            self._safe_register_family(
                heading.get("regular", heading["bold"]), **kwargs
            )

        # Latin family
        self._safe_register_family(
            self._LATIN_NAMES["regular"],
            normal=self._LATIN_NAMES["regular"],
            bold=self._LATIN_NAMES["bold"],
            italic=self._LATIN_NAMES["italic"],
        )

    @staticmethod
    def _safe_register_family(family_name: str, **kwargs):
        """Register a font family, ignoring errors (e.g. name collisions)."""
        try:
            pdfmetrics.registerFontFamily(family_name, **kwargs)
        except Exception:
            # Tolerate family-registration failures (non-fatal).
            pass

    @staticmethod
    def _split_text(text: str) -> list:
        """Split text into a list of (type, content) tuples.

        type is one of: "cjk" | "latin" | "punct" | "other"
        """
        if not text:
            return []

        segments = []
        pos = 0
        length = len(text)

        while pos < length:
            # Try CJK fullwidth punctuation first (enables compression)
            m_punct = _PUNCT_CJK.match(text, pos)
            if m_punct:
                segments.append(("punct", m_punct.group(1)))
                pos = m_punct.end()
                continue

            # Try CJK
            m_cjk = _CJK_PATTERN.match(text, pos)
            if m_cjk:
                segments.append(("cjk", m_cjk.group(1)))
                pos = m_cjk.end()
                continue

            # Try Latin
            m_lat = _LATIN_PATTERN.match(text, pos)
            if m_lat:
                segments.append(("latin", m_lat.group(1)))
                pos = m_lat.end()
                continue

            # Other characters (punctuation, whitespace, etc.)
            segments.append(("other", text[pos]))
            pos += 1

        return segments
