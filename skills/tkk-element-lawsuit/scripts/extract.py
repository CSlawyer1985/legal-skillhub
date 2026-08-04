#!/usr/bin/env python3
"""Extract CSS, HTML body, and JS from the monolithic HTML file into separate files."""
import re, sys

html_path = sys.argv[1] if len(sys.argv) > 1 else "assets/bude-convert-v10.2-reference.html"
out_css = sys.argv[2] if len(sys.argv) > 2 else "assets/css/style.css"
out_js = sys.argv[3] if len(sys.argv) > 3 else "assets/js/app.js"
out_html = sys.argv[4] if len(sys.argv) > 4 else "assets/index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract <style>...</style>
style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
if style_match:
    css = style_match.group(1).strip()
    with open(out_css, 'w', encoding='utf-8') as f:
        f.write(css)
    print(f"Extracted CSS ({len(css)} chars) -> {out_css}")
else:
    print("WARNING: No <style> block found!")

# Extract <script>...</script> (the main one, not CDN refs)
# Find the inline script (not external src)
scripts = list(re.finditer(r'<script[^>]*>(.*?)</script>', content, re.DOTALL))
inline_scripts = [(m, m.group(1)) for m in scripts if 'src=' not in m.group(0) and m.group(1).strip()]

for i, (m, js) in enumerate(inline_scripts):
    js_content = js.strip()
    if len(js_content) > 1000:  # Main app script
        with open(out_js, 'w', encoding='utf-8') as f:
            f.write(js_content)
        print(f"Extracted JS ({len(js_content)} chars) -> {out_js}")
        break
else:
    print("WARNING: No large inline script found!")

# Build modular index.html
# Keep external CDN scripts, replace inline <style> with <link>, inline <script> with <script src>
html_index = content

# Replace <style>...</style> with <link>
html_index = re.sub(
    r'<style>.*?</style>',
    '<link rel="stylesheet" href="css/style.css">',
    html_index, count=1, flags=re.DOTALL
)

# Replace large inline <script>...</script> with <script src>
html_index = re.sub(
    r'<script>(.*?)</script>',
    '<script src="js/app.js"></script>',
    html_index, count=1, flags=re.DOTALL
)

# Update title to reflect modular version
html_index = html_index.replace(
    '<title>BUDE · 要素式起诉状转换工具</title>',
    '<title>BUDE · 要素式起诉状转换工具 (模块化版)</title>'
)

with open(out_html, 'w', encoding='utf-8') as f:
    f.write(html_index)
print(f"Created modular HTML ({len(html_index)} chars) -> {out_html}")
print("Done!")
