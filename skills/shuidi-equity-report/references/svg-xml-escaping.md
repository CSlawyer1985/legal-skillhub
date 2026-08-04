# SVG & XML Escaping Pitfall

## Problem
SVG is strict XML. The `&` character in `<text>` elements causes `rsvg-convert` to fail with:
```
xmlParseEntityRef: no name
```

## Trigger (common in Chinese reports)
- "全资 & 控股" 
- "8英寸 & 12英寸"

## Fix

### v3.0 (auto-fixed in generate_equity_report.py)
The `generate_svg()` method in v3.0:
1. Calls `validate_svg()` after writing — uses `ElementTree.parse()`
2. On failure, auto-repairs: `re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', content)`
3. Re-validates before proceeding

### Manual fix (pre-v3.0 / ad-hoc scripts)
```python
svg_content = svg_content.replace(' & ', ' &amp; ')
```

### Prevention
Use `+` or `·` instead of `&` in SVG labels.
Example: `全资+控股` / `8英寸·12英寸` → no XML conflict.
