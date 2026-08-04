#!/usr/bin/env python3
"""SVG→PNG渲染入口：自动探测无头浏览器（Chrome/Chromium/Edge），按SVG声明尺寸开窗截图。
用法: render_views.py <SVG目录>。exit 0=全部渲染, 3=失败/无渲染器。"""
import sys, re, subprocess, shutil
from pathlib import Path
CANDIDATES = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
 "/Applications/Chromium.app/Contents/MacOS/Chromium",
 "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
 shutil.which("google-chrome") or "", shutil.which("chromium") or ""]
def find_browser():
    for c in CANDIDATES:
        if c and Path(c).is_file(): return c
    return None
def main(target):
    br = find_browser()
    if not br: print("FAIL: 未找到无头浏览器（Chrome/Chromium/Edge），无法渲染PNG"); return 3
    svgs = sorted(Path(target).glob("*.svg"))
    if not svgs: print("FAIL: 目录无SVG"); return 3
    bad = 0
    for svg in svgs:
        m = re.search(r'width="(\d+)" height="(\d+)"', svg.read_text(encoding="utf-8"))
        png = svg.with_suffix(".png")
        subprocess.run([br,"--headless","--disable-gpu",f"--screenshot={png}",
            f"--window-size={m.group(1)},{m.group(2)}","--hide-scrollbars",f"file://{svg.resolve()}"],
            capture_output=True, timeout=120)
        ok = png.exists() and png.stat().st_size > 10240
        print(png.name, "ok" if ok else "FAIL")
        if not ok: bad += 1
    return 0 if bad==0 else 3
if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv)>1 else "."))
