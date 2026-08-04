# -*- coding: utf-8 -*-
"""
Theme loader: reads theme.json and provides structured access.

Usage:
    theme = ThemeLoader("path/to/theme.json")
    colors = theme.get_colors()      # active scheme colors
    fonts  = theme.get_font_paths()  # absolute font paths for active provider
"""

import copy
import json
import os
from reportlab.lib.colors import HexColor, Color


class ThemeLoader:
    """Load theme config from theme.json; supports scheme / provider / preset switching."""

    def __init__(self, theme_path: str = None):
        if theme_path is None:
            # Default: theme.json one level above engine/
            theme_path = os.path.join(self._project_root(), "theme.json")
        self.theme_path = os.path.abspath(theme_path)
        self._project_dir = os.path.dirname(self.theme_path)
        self._data = self._load()
        self._original = copy.deepcopy(self._data)  # kept for preset switching

        # Currently active scheme/provider/preset
        self._scheme = self._data["color"]["scheme"]
        self._provider = self._data["font"]["provider"]
        self._preset = "standard"

    # -- Public API ------------------------------------------------

    @property
    def project_dir(self) -> str:
        return self._project_dir

    @property
    def scheme(self) -> str:
        return self._scheme

    @property
    def provider(self) -> str:
        return self._provider

    def set_scheme(self, scheme: str):
        """Switch brand color scheme (A / B / C)."""
        if scheme not in self._data["color"]["schemes"]:
            raise ValueError(
                f"Unknown color scheme: {scheme}, available: "
                f"{list(self._data['color']['schemes'].keys())}"
            )
        self._scheme = scheme

    def set_provider(self, provider: str):
        """Switch font provider (noto / founder)."""
        if provider not in self._data["font"]["providers"]:
            raise ValueError(
                f"Unknown font provider: {provider}, available: "
                f"{list(self._data['font']['providers'].keys())}"
            )
        self._provider = provider

    @property
    def preset(self) -> str:
        return self._preset

    def set_preset(self, preset_name: str):
        """Switch typography preset. Re-merges overrides from the original config."""
        presets = self._original.get("typography_presets", {})
        if preset_name not in presets:
            available = list(presets.keys())
            raise ValueError(
                f"Unknown typography preset: {preset_name}, available: {available}"
            )

        # Reset from original data
        self._data = copy.deepcopy(self._original)
        self._scheme = self._data["color"]["scheme"]
        self._provider = self._data["font"]["provider"]

        # Merge preset overrides (standard has no overrides, returns directly)
        preset = presets[preset_name]
        overrides = preset.get("overrides", {})
        if overrides:
            self._deep_merge(overrides, self._data)

        self._preset = preset_name

    def list_presets(self) -> list:
        """List all available typography presets as [{name, label, category, description}, ...]."""
        presets = self._original.get("typography_presets", {})
        result = []
        for key, val in presets.items():
            result.append({
                "name": key,
                "label": val.get("label", key),
                "category": val.get("category", ""),
                "description": val.get("description", ""),
            })
        return result

    def get_preset(self) -> dict:
        """Return the full config of the current preset."""
        presets = self._original.get("typography_presets", {})
        return presets.get(self._preset, {})

    def load_template(self, template_name: str) -> dict:
        """Load a template JSON file and return its config dict.

        Guards against path traversal: only a bare name (no path separators,
        no dot-segments) is accepted.
        """
        if not template_name or template_name != os.path.basename(template_name) \
                or template_name in (".", ".."):
            available = self.list_templates()
            names = [t["name"] for t in available]
            raise ValueError(
                f"Unknown template: {template_name}, available: {names}"
            )
        templates_dir = os.path.join(self._project_dir, "templates")
        path = os.path.join(templates_dir, f"{template_name}.json")
        if not os.path.isfile(path):
            available = self.list_templates()
            names = [t["name"] for t in available]
            raise ValueError(
                f"Unknown template: {template_name}, available: {names}"
            )
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_templates(self) -> list:
        """List all available document templates as [{name, label, description}, ...]."""
        templates_dir = os.path.join(self._project_dir, "templates")
        result = []
        if os.path.isdir(templates_dir):
            for fname in sorted(os.listdir(templates_dir)):
                if fname.endswith(".json"):
                    path = os.path.join(templates_dir, fname)
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    result.append({
                        "name": data.get("name", fname[:-5]),
                        "label": data.get("label", ""),
                        "description": data.get("description", ""),
                    })
        return result

    def get_colors(self) -> dict:
        """Return the color dict for the active scheme.

        Returns:
            {
                "primary": Color,
                "secondary": Color,
                "accent": Color,
                "text": Color,
                "text_light": Color,
                "bg_subtle": Color,
                "bg_table": Color,
                "border": Color,
            }
        """
        scheme_data = self._data["color"]["schemes"][self._scheme]
        neutral = self._data["color"]["neutral"]

        return {
            "primary":   self._hex(scheme_data["primary"]),
            "secondary": self._hex(scheme_data["secondary"]),
            "accent":    self._hex(scheme_data["accent"]),
            "text":       self._hex(neutral["text"]),
            "text_light": self._hex(neutral["text_light"]),
            "bg_subtle":  self._hex(neutral["bg_subtle"]),
            "bg_table":   self._hex(neutral["bg_table"]),
            "border":     self._hex(neutral["border"]),
        }

    def get_color_with_opacity(self, color_name: str, opacity: float) -> Color:
        """Return a brand color with the given opacity (0.0 transparent ~ 1.0 opaque)."""
        colors = self.get_colors()
        base = colors.get(color_name)
        if base is None:
            raise ValueError(f"Unknown color name: {color_name}")
        return Color(base.red, base.green, base.blue, opacity)

    def get_font_paths(self) -> dict:
        """Return absolute font paths for the active provider.

        Returns:
            {
                "body":    {"regular": "/abs/path/xxx.ttf", "bold": "..."},
                "heading": {"regular": "...", "bold": "...", "light": "..."},
                "quote":   {"regular": "..."},
                "latin":   {"regular": "...", "bold": "...", "italic": "..."},
            }
        """
        provider_data = self._data["font"]["providers"][self._provider]
        result = {}
        for role, variants in provider_data.items():
            result[role] = {}
            for variant, rel_path in variants.items():
                abs_path = os.path.join(self._project_dir, rel_path.replace("/", os.sep))
                result[role][variant] = os.path.abspath(abs_path)
        return result

    def get_typography(self) -> dict:
        """Return typography params (raw dict, units in pt / chars)."""
        return self._data["typography"]

    def get_page(self) -> dict:
        """Return page setup params."""
        return self._data["page"]

    def get_brand_rules(self) -> dict:
        """Return brand color usage rules."""
        return self._data["brand_rules"]

    def get_table_config(self) -> dict:
        """Return table style config."""
        return self._data.get("table", {})

    def get_footnote_config(self) -> dict:
        """Return footnote config."""
        return self._data.get("footnote", {})

    def get_cover_config(self) -> dict:
        """Return cover page config."""
        return self._data.get("cover", {})

    def get_i18n(self) -> dict:
        """Return i18n label strings (footer labels, cover meta labels).

        Keys: footer_page_prefix, footer_page_suffix,
              footer_total_prefix, footer_total_suffix,
              meta_addressee_label, meta_author_label, meta_date_label.
        Returns an empty dict if the section is absent.
        """
        return self._data.get("i18n", {})

    def get_raw(self) -> dict:
        """Return the full theme dict (use sparingly; prefer the accessors above)."""
        return self._data

    # -- Internal --------------------------------------------------

    @staticmethod
    def _project_root() -> str:
        """Infer project root: one level above engine/."""
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _load(self) -> dict:
        with open(self.theme_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _hex(hex_str: str) -> Color:
        """#RRGGBB -> ReportLab Color."""
        return HexColor(hex_str)

    @staticmethod
    def _deep_merge(source: dict, target: dict):
        """Deep-merge source into target (mutates target in place).

        Nested dicts are merged recursively; other types overwrite.
        """
        for key, value in source.items():
            if (isinstance(value, dict) and key in target
                    and isinstance(target[key], dict)):
                ThemeLoader._deep_merge(value, target[key])
            else:
                target[key] = value
