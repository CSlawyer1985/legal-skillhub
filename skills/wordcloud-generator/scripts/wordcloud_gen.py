# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
"""
wordcloud_gen.py — Word cloud generator built from first principles.

First principles
----------------
A word cloud is a space-filling layout of words sized by a weight. The
`wordcloud` library places the largest words first, spiraling from the
center, into a canvas; an optional *mask* restricts WHERE words may land.

CRITICAL, NON-OBVIOUS FACT (discovered the hard way, 2026-08-06):
In wordcloud 1.9.x the mask is consumed as a baseline offset
    img_array = img_grey + boolean_mask      # boolean_mask = (mask == 255)
The sampler prefers the lowest-occupancy region, so words actually land in
the part of the canvas where `mask == 0`. Therefore, to make words FILL a
shape, the shape's INTERIOR must be 0 and the EXTERIOR must be 255 —
the exact opposite of the naive "mask==255 means inside" intuition. Get
this backwards and you get a hollow shape with words floating around it.

This script bakes in the correct convention, so callers just describe the
shape (heart / circle / star / or a white-on-black image) and words fill it.

Usage
-----
    python wordcloud_gen.py --input data.json --shape heart --output out.png
    python wordcloud_gen.py --input speech.txt --shape circle --output out.png
    python wordcloud_gen.py --input data.json --shape custom --mask shape.png \
        --colors cat.json --output out.png

Input (`--input`):
    .json  -> list of {"word","weight","category"?}, OR
              dict {word: weight}, OR dict {word: {"weight":n,"category":c}}
    .txt   -> raw text; tokens counted (jieba if available, else regex split);
              --stopwords filters noise tokens (e.g. 我们/没有/因为);
              --userdict loads a jieba dict so domain terms survive segmentation

Shape (`--shape`): heart | circle | star | diamond | triangle | pentagon |
    hexagon | ring | cloud | drop | arrow | rect | text | custom
    - built-in geometry (heart/circle/star/diamond/triangle/pentagon/hexagon/
      ring/cloud/drop/arrow) needs no image;
    - `rect` + `--width/--height` gives a PPT-ratio rectangle (e.g. 16 9);
    - `text` + `--text "中国"` renders that text as the mask (微词云「自定义文字」,
      中文/英文皆可, 1~3 chars best);
    - `custom` + `--mask image` accepts ANY image (white-on-black / black-on-white
      / transparent PNG; orientation auto-detected — no manual inversion).

Colors: `--theme` picks a named palette (rainbow/warm/cool/ocean/forest/sunset/
    festive/mono/business/lucky); `--colors` overrides categories; `--colormap`
    sets the matplotlib gradient.

Density: `--repeat` fills gaps with small repeats; `--prefer-horizontal` (default
    0.65) controls word orientation mix for tighter packing; `--relative-scaling`
    (default 0.32) tunes size contrast between big and small words.

For Chinese brand names (德恒无锡 / 腾讯 / 阿里巴巴): do NOT use text mask.
Instead make the brand name the highest-weight words in a dense cloud
(see SKILL.md "品牌大字模式" for examples).

Colors (`--colors`): optional JSON {category: [r,g,b]}. If words carry a
    category, they are colored by it; otherwise a matplotlib colormap is used.
"""

import argparse
import json
import os
import re
import random
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from matplotlib.path import Path as MPath
from wordcloud import WordCloud


# ── Default categorical palette (override per skill/user via --colors) ──
DEFAULT_PALETTE = {
    "欧洲": (65, 105, 225),
    "亚太": (46, 139, 87),
    "美洲": (220, 20, 60),
    "中东": (25, 25, 112),
    "其他": (105, 105, 105),
}

# ── Named color themes (微词云「主题」的本地化实现) ──
# value = (colormap_name | None, category_palette | None)
# colormap 用于无分类模式；palette 用于按 category 上色。
THEMES = {
    "rainbow":  ("gist_rainbow", None),
    "warm":     ("autumn", None),
    "cool":     ("cool", None),
    "ocean":    ("winter", None),
    "forest":   ("summer", None),
    "sunset":   ("plasma", None),
    "festive":  ("Set1", None),
    "mono":     ("Greys", None),
    "business": (None, {
        "欧洲": (31, 78, 160), "亚太": (0, 128, 160), "美洲": (0, 90, 200),
        "中东": (70, 110, 180), "其他": (120, 140, 170)}),
    "lucky":    (None, {
        "欧洲": (200, 30, 40), "亚太": (220, 120, 20), "美洲": (190, 50, 60),
        "中东": (170, 40, 50), "其他": (210, 160, 60)}),
}

# ── Chinese stop words (微词云对中文友好的关键：去掉虚词噪声) ──
# 仅作用于 .txt 原始文本模式；JSON 模式保留用户列出的每个词。
CN_STOPWORDS = set(
    "的 了 和 是 在 我 有 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 会 着 没有 看 好 自己 这 那 与 及 "
    "我们 你们 他们 她们 它们 这个 那个 这些 那些 因为 所以 如果 但是 而且 然后 已经 可以 应该 需要 通过 "
    "对于 关于 以及 或者 这种 那种 一些 这样 那样 什么 怎么 为什么 一个 一种 进行 成为 由于 根据 按照".split()
)


def _try_font(fp, size=10):
    """Open a PIL font if possible. .ttc/.otc collections need an explicit face
    index on some systems (PingFang.ttc fails to open at all on macOS 26), so we
    probe face 0..5. Returns the font object or None."""
    if not fp or not os.path.exists(fp):
        return None
    try:
        return ImageFont.truetype(fp, size)
    except Exception:
        pass
    for idx in range(0, 6):
        try:
            return ImageFont.truetype(fp, size, index=idx)
        except Exception:
            continue
    return None


def find_chinese_font():
    # Local bundled fonts first (for self-use; excluded from SkillHub publish
    # via .gitignore so no commercial-font redistribution risk).
    # NOTE: must verify the font actually OPENS — merely existing is not enough
    # (e.g. PingFang.ttc raises "cannot open resource" on some macOS builds and
    # silently falls back to a bitmap font that cannot render CJK).
    here = os.path.dirname(os.path.abspath(__file__))
    local_fonts = os.path.normpath(os.path.join(here, "..", "assets", "fonts"))
    candidates = [
        os.path.join(local_fonts, "msyh.ttf"),
        os.path.join(local_fonts, "msyhbd.ttf"),
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/Supplemental/STHeiti Medium.ttc",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for fp in candidates:
        if _try_font(fp) is not None:
            return fp
    return None


# ── Shape masks: interior = 0, exterior = 255 (words land where mask == 0) ──
def _filled_to_mask(filled_bool, size=None):
    """Convert an interior=True boolean grid into wordcloud's mask (interior 0).
    `size` is accepted for backwards compatibility but unused (output shape
    follows `filled_bool`)."""
    return (~filled_bool).astype(np.uint8) * 255


def make_heart_mask(size=1000):
    t = np.linspace(0, 2 * np.pi, 4000)
    x = 16 * np.sin(t) ** 3
    y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
    x = (x - x.min()) / (x.max() - x.min())
    y = (y - y.min()) / (y.max() - y.min())
    m = 0.05
    x = m + x * (1 - 2 * m)
    y = m + y * (1 - 2 * m)
    verts = np.column_stack([x * size, (1 - y) * size])  # flip y: lobes up
    path = MPath(verts)
    gx, gy = np.meshgrid(np.arange(size), np.arange(size))
    pts = np.column_stack([gx.ravel(), gy.ravel()])
    filled = path.contains_points(pts).reshape(size, size)
    return _filled_to_mask(filled, size)


def make_circle_mask(size=1000):
    Y, X = np.mgrid[0:size, 0:size]
    cy = cx = size // 2
    r = size // 2 * 0.92
    inside = (X - cx) ** 2 + (Y - cy) ** 2 <= r * r
    return _filled_to_mask(inside, size)


def make_star_mask(size=1000, points=5, ratio=0.45):
    R = size * 0.46
    r = R * ratio
    cx = cy = size // 2
    verts = []
    for i in range(points * 2):
        ang = np.pi / 2 + i * np.pi / points  # start at top
        rad = R if i % 2 == 0 else r
        verts.append((cx + rad * np.cos(ang), cy - rad * np.sin(ang)))
    verts.append(verts[0])
    path = MPath(verts)
    gx, gy = np.meshgrid(np.arange(size), np.arange(size))
    pts = np.column_stack([gx.ravel(), gy.ravel()])
    filled = path.contains_points(pts).reshape(size, size)
    return _filled_to_mask(filled, size)


def make_custom_mask(image_path, size=1000, mask_mode="auto"):
    """Auto-convert an arbitrary image into the shape-interior boolean grid.

    Orientation is auto-detected so the caller does NOT need to pre-invert:
      - transparent PNG   -> opaque pixels = shape
      - light background  -> dark pixels = shape
      - dark background   -> light pixels = shape
    Pass mask_mode=light/dark/alpha to force a choice when auto mis-reads
    (e.g. a photo with a busy / non-uniform background).
    """
    img = Image.open(image_path).convert("RGBA")
    arr = np.array(img)
    alpha = arr[:, :, 3]

    if mask_mode in ("auto", "alpha") and alpha.min() < 250:
        inside = alpha > 128                       # silhouette = opaque region
    else:
        gray = arr[:, :, :3].mean(axis=2).astype(np.uint8)
        if mask_mode == "light":
            inside = gray < 128
        elif mask_mode == "dark":
            inside = gray > 128
        else:  # auto: read orientation from corner brightness
            corner = _corner_brightness(gray)
            inside = gray < 128 if corner > 128 else gray > 128

    # aspect-preserving resize (avoid squishing wide/short shapes) then invert
    H, W = inside.shape
    scale = size / max(W, H)
    tw, th = max(1, int(round(W * scale))), max(1, int(round(H * scale)))
    inside = np.array(Image.fromarray((inside * 255).astype(np.uint8))
                      .resize((tw, th))) > 128
    return _filled_to_mask(inside)


def _corner_brightness(gray):
    """Median brightness of the four corner patches — a cheap background proxy."""
    H, W = gray.shape
    m, n = max(1, H // 10), max(1, W // 10)
    patches = [gray[0:m, 0:n], gray[0:m, -n:], gray[-m:, 0:n], gray[-m:, -n:]]
    return int(np.median(np.concatenate([p.ravel() for p in patches])))


def _already_cutout(image_path):
    """Heuristic: an image already carrying transparency is a ready silhouette."""
    try:
        img = Image.open(image_path)
        if img.mode != "RGBA":
            return False
        alpha = np.array(img.split()[-1])
        return bool((alpha < 250).any())
    except Exception:
        return False


def make_polygon_mask(n_sides, size=1000, rot=np.pi / 2):
    """Regular n-gon via matplotlib path (reused for diamond/triangle/...)."""
    R = size * 0.46
    cx = cy = size // 2
    verts = [(cx + R * np.cos(rot + i * 2 * np.pi / n_sides),
              cy - R * np.sin(rot + i * 2 * np.pi / n_sides))
             for i in range(n_sides)]
    verts.append(verts[0])
    path = MPath(verts)
    gx, gy = np.meshgrid(np.arange(size), np.arange(size))
    pts = np.column_stack([gx.ravel(), gy.ravel()])
    filled = path.contains_points(pts).reshape(size, size)
    return _filled_to_mask(filled, size)


def make_ring_mask(size=1000, outer=0.92, inner=0.55):
    Y, X = np.mgrid[0:size, 0:size]
    cy = cx = size // 2
    R = size // 2 * outer
    r = R * inner
    d2 = (X - cx) ** 2 + (Y - cy) ** 2
    inside = (d2 <= R * R) & (d2 >= r * r)
    return _filled_to_mask(inside, size)


def _mask_from_predicate(pred, size=1000):
    """Rasterize a vectorized predicate(nx, ny) -> boolean grid into a mask."""
    Y, X = np.mgrid[0:size, 0:size]
    inside = pred(X / size, Y / size)
    return _filled_to_mask(inside, size)


def _cloud_pred(nx, ny):
    circles = [(0.30, 0.58, 0.22), (0.50, 0.62, 0.26), (0.70, 0.58, 0.22),
               (0.40, 0.50, 0.20), (0.60, 0.50, 0.20), (0.50, 0.42, 0.24)]
    inside = np.zeros_like(nx, dtype=bool)
    for cx, cy, r in circles:
        inside |= (nx - cx) ** 2 + (ny - cy) ** 2 <= r * r
    return inside & (ny <= 0.82)


def _drop_pred(nx, ny):
    circle = (nx - 0.5) ** 2 + (ny - 0.45) ** 2 <= 0.30 ** 2
    # triangle apex (0.5,0.95), base (0.2,0.45)-(0.8,0.45)
    def sign(ax, ay, bx, by, cx2, cy2):
        return (ax - bx) * (cy2 - by) - (ay - by) * (cx2 - bx)
    d1 = sign(nx, ny, 0.2, 0.45, 0.8, 0.45)
    d2 = sign(nx, ny, 0.8, 0.45, 0.5, 0.95)
    d3 = sign(nx, ny, 0.5, 0.95, 0.2, 0.45)
    has_neg = (d1 < 0) | (d2 < 0) | (d3 < 0)
    has_pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
    tri = ~(has_neg & has_pos)
    return circle | tri


def _arrow_pred(nx, ny):
    shaft = (nx >= 0.38) & (nx <= 0.62) & (ny >= 0.10) & (ny <= 0.55)
    head = (ny >= 0.55) & (ny <= 0.92) & \
           (np.abs(nx - 0.5) <= 0.30 * (0.92 - ny) / 0.37)
    return shaft | head


def make_rect_mask(size=1000, w_ratio=1.0, h_ratio=1.0):
    Y, X = np.mgrid[0:size, 0:size]
    cx = cy = size // 2
    m = 0.05
    usable = size * (1 - 2 * m)
    if w_ratio >= h_ratio:
        W, H = usable, usable * (h_ratio / w_ratio)
    else:
        H, W = usable, usable * (w_ratio / h_ratio)
    inside = (np.abs(X - cx) <= W / 2) & (np.abs(Y - cy) <= H / 2)
    return _filled_to_mask(inside, size)


def make_text_mask(text, size=1000, font_path=None):
    """Render TEXT (1~3 chars best, 微词云「自定义文字」) as the mask shape.

    Black text on white canvas -> interior = dark pixels. Works for Chinese
    and English as long as `font_path` points at a CJK-capable font (which
    also covers Latin glyphs)."""
    img = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(img)

    def load(sz):
        f = _try_font(font_path, sz) if font_path else None
        return f or ImageFont.load_default()

    margin = 0.10
    maxw = size * (1 - 2 * margin)
    maxh = size * (1 - 2 * margin)
    fs = int(size * 0.9)
    font = load(fs)
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if w > 0 and h > 0:
        fs = max(8, int(fs * min(maxw / w, maxh / h)))
        font = load(fs)
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - w) / 2 - bbox[0]
    y = (size - h) / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=0)
    inside = np.array(img) < 128
    return _filled_to_mask(inside, size)


def build_mask(shape, mask_path=None, size=1000, mask_mode="auto",
               text=None, width=None, height=None, font_path=None):
    if shape == "heart":
        return make_heart_mask(size)
    if shape == "circle":
        return make_circle_mask(size)
    if shape == "star":
        return make_star_mask(size)
    if shape == "diamond":
        return make_polygon_mask(4, size, np.pi / 2)
    if shape == "triangle":
        return make_polygon_mask(3, size, np.pi / 2)
    if shape == "pentagon":
        return make_polygon_mask(5, size, np.pi / 2)
    if shape == "hexagon":
        return make_polygon_mask(6, size, np.pi / 2)
    if shape == "ring":
        return make_ring_mask(size)
    if shape == "cloud":
        return _mask_from_predicate(_cloud_pred, size)
    if shape == "drop":
        return _mask_from_predicate(_drop_pred, size)
    if shape == "arrow":
        return _mask_from_predicate(_arrow_pred, size)
    if shape == "rect":
        return make_rect_mask(size, width or 1.0, height or 1.0)
    if shape == "text":
        if not text:
            raise ValueError("--text is required when --shape=text")
        return make_text_mask(text, size, font_path)
    if shape == "custom":
        if not mask_path:
            raise ValueError("--mask is required when --shape=custom")
        return make_custom_mask(mask_path, size, mask_mode)
    raise ValueError(f"unknown shape: {shape}")


# ── Input parsing ──
def load_data(input_path, stopwords=None, userdict_path=None, lang="auto"):
    """Return list of dicts: {word, weight, category}. Bad entries are skipped
    with a warning instead of crashing (robust against hand-written JSON).
    stopwords/userdict_path/lang apply to the .txt (raw text) mode only."""
    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".json":
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        out = []

        def add(word, weight, category):
            if not word or not str(word).strip():
                print(f"  skip: empty/None word (weight={weight!r})")
                return
            try:
                w = float(weight)
            except (TypeError, ValueError):
                print(f"  skip: non-numeric weight for '{word}': {weight!r}")
                return
            if w <= 0:
                print(f"  skip: non-positive weight for '{word}': {w}")
                return
            out.append({"word": str(word), "weight": w, "category": category})

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    add(item.get("word"), item.get("weight", 1), item.get("category"))
                else:
                    add(item, 1.0, None)
        elif isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict):
                    add(k, v.get("weight", 1), v.get("category"))
                else:
                    add(k, v, None)
        else:
            raise ValueError("JSON must be a list or dict")
        return out
    if ext == ".txt":
        return count_text(input_path, stopwords, userdict_path, lang)
    raise ValueError(f"unsupported input type: {ext}")


def count_text(input_path, stopwords=None, userdict_path=None, lang="auto"):
    """Tokenize raw text (jieba if available, else regex) and count frequency.

    lang:
      - zh/en  -> force jieba (Chinese) or english regex + lowercase;
      - auto   -> jieba if importable (handles mixed zh/en), else english regex.
    stopwords: tokens to drop. userdict_path: jieba dict for domain terms."""
    stopwords = stopwords or set()
    text = open(input_path, "r", encoding="utf-8").read()
    use_jieba = lang != "en"
    try:
        if use_jieba:
            import jieba
            if userdict_path:
                jieba.load_userdict(userdict_path)
            words = [w for w in jieba.cut(text)
                     if len(w.strip()) > 1 and w.strip() not in stopwords]
        else:
            raise ImportError
    except Exception:
        words = [w for w in re.findall(r"[A-Za-z]+", text)
                 if w.lower() not in stopwords]
    if lang == "en":
        words = [w.lower() for w in words]
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return [{"word": k, "weight": float(v), "category": None}
            for k, v in freq.items()]


# ── Coloring ──
def build_color_func(entries, palette, colormap):
    word_color = {}
    has_cat = any(e["category"] for e in entries)
    if has_cat:
        cats = sorted({e["category"] for e in entries if e["category"]})
        cat_color = {}
        for i, c in enumerate(cats):
            if palette and c in palette:
                cat_color[c] = palette[c]
            else:
                # spread categories across the colormap
                rgb = tuple(int(255 * x) for x in colormap(i / max(1, len(cats) - 1)))
                cat_color[c] = rgb
        for e in entries:
            if e["category"]:
                word_color[e["word"]] = cat_color[e["category"]]
    else:
        n = len(entries)
        for i, e in enumerate(entries):
            if colormap is not None:
                word_color[e["word"]] = tuple(int(255 * x)
                                              for x in colormap(i / max(1, n - 1)))
            else:
                word_color[e["word"]] = (40, 40, 40)

    def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        base = word_color.get(word, (40, 40, 40))
        r = min(255, max(0, base[0] + random.randint(-18, 18)))
        g = min(255, max(0, base[1] + random.randint(-18, 18)))
        b = min(255, max(0, base[2] + random.randint(-18, 18)))
        return (r, g, b)

    return color_func


def main():
    ap = argparse.ArgumentParser(description="First-principles word cloud generator")
    ap.add_argument("--input", required=True, help=".json or .txt data file")
    ap.add_argument("--output", required=True, help="output PNG path")
    ap.add_argument("--shape", default="heart",
                    choices=["heart", "circle", "star", "diamond", "triangle",
                             "pentagon", "hexagon", "ring", "cloud", "drop",
                             "arrow", "rect", "text", "custom"])
    ap.add_argument("--mask", default=None, help="mask image for --shape=custom (orientation auto-detected)")
    ap.add_argument("--mask-mode", default="auto",
                    choices=["auto", "light", "dark", "alpha"],
                    help="custom mask orientation: auto (detect from image) / "
                         "light (dark shape on light bg) / dark (light shape on dark bg) / "
                         "alpha (transparent PNG, opaque=shape)")
    ap.add_argument("--text", default=None,
                    help="text rendered as the mask when --shape=text "
                         "(微词云「自定义文字」; 1~3 chars best, 中文/英文皆可)")
    ap.add_argument("--width", type=float, default=None,
                    help="rect width ratio for --shape=rect (e.g. 16 with --height 9 = 16:9)")
    ap.add_argument("--height", type=float, default=None,
                    help="rect height ratio for --shape=rect")
    ap.add_argument("--theme", default=None, choices=list(THEMES),
                    help="named color theme (微词云「主题」): " + "/".join(THEMES))
    ap.add_argument("--colors", default=None, help="JSON {category:[r,g,b]} override")
    ap.add_argument("--colormap", default="viridis", help="matplotlib colormap name")
    ap.add_argument("--font", default=None, help="explicit .ttf/.ttc font path")
    ap.add_argument("--background", default="white", help="background color")
    ap.add_argument("--max-words", type=int, default=400)
    ap.add_argument("--min-font", type=int, default=6)
    ap.add_argument("--max-font", type=int, default=100)
    ap.add_argument("--prefer-horizontal", type=float, default=0.65,
                    help="ratio of horizontal words (0.0=all vertical, "
                         "0.65=default); lower values pack tighter by "
                         "allowing more orientations")
    ap.add_argument("--relative-scaling", type=float, default=0.32,
                    help="how prominence scales with weight "
                         "(0.0=uniform, 1.0=linear; lower=more even sizes)")
    ap.add_argument("--repeat", action="store_true", help="repeat words to fill gaps")
    ap.add_argument("--no-repeat", dest="repeat", action="store_false")
    ap.set_defaults(repeat=True)
    ap.add_argument("--title", default=None, help="optional caption at bottom")
    ap.add_argument("--lang", default="auto", choices=["auto", "zh", "en"],
                    help="text language for .txt mode: auto (jieba, mixed) / "
                         "zh (Chinese segmentation) / en (english, lowercased)")
    ap.add_argument("--stopwords", default=None,
                    help=".txt file with stop words, one per line (applies to --input .txt mode only)")
    ap.add_argument("--userdict", default=None,
                    help="jieba user dictionary path so domain terms survive segmentation (txt mode only)")
    ap.add_argument("--auto-cutout", action="store_true",
                    help="strip background from a PHOTO via rembg before masking "
                         "(needs rembg: pip install \"rembg[cpu,cli]\")")
    args = ap.parse_args()
    tmp_mask_path = None

    font_path = args.font or find_chinese_font()
    if not font_path:
        print("WARNING: no CJK font found; words may render as boxes.")

    # Stop words: user file (one per line) + wordcloud's built-in English set
    # + our Chinese set (微词云对中文友好的关键). Only .txt mode consumes them;
    # JSON mode keeps every word the user listed.
    stopwords = set()
    if args.stopwords:
        with open(args.stopwords, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w:
                    stopwords.add(w)
    try:
        from wordcloud import STOPWORDS
        stopwords |= set(STOPWORDS)
    except Exception:
        pass
    if args.lang in ("auto", "zh"):
        stopwords |= CN_STOPWORDS

    entries = load_data(args.input, stopwords, args.userdict, args.lang)
    if not entries:
        raise SystemExit("no words found in input")
    freq = {e["word"]: e["weight"] for e in entries}

    palette = DEFAULT_PALETTE.copy()
    if args.colors:
        with open(args.colors, "r", encoding="utf-8") as f:
            palette.update({k: tuple(v) for k, v in json.load(f).items()})

    # Named theme (微词云「主题」): override colormap (no-category) and/or palette.
    if args.theme:
        cmap_name, theme_palette = THEMES[args.theme]
        if cmap_name:
            args.colormap = cmap_name
        # user-supplied --colors takes precedence over the theme's palette
        if theme_palette and not args.colors:
            palette = dict(theme_palette)

    try:
        import matplotlib
        cmap = matplotlib.colormaps[args.colormap]
    except Exception:
        print(f"WARNING: unknown colormap '{args.colormap}', falling back to 'tab10'")
        cmap = matplotlib.colormaps["tab10"]

    color_func = build_color_func(entries, palette, cmap)

    # ── Auto background removal (rembg) for photos ──
    if args.auto_cutout and args.shape == "custom" and args.mask:
        if _already_cutout(args.mask):
            print("  auto-cutout: source already has transparency; using as-is.")
            args.mask_mode = "alpha"
        else:
            try:
                from rembg import remove
            except Exception:
                print("WARNING: --auto-cutout set but rembg not installed; "
                      "using the image directly. Install: "
                      'pip install "rembg[cpu,cli]"')
            else:
                print("  auto-cutout: stripping background via rembg ...")
                from PIL import Image
                try:
                    src = Image.open(args.mask).convert("RGB")
                    cut = remove(src)
                except Exception as exc:
                    print(f"WARNING: rembg failed ({exc!r}); using the image directly.")
                else:
                    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    cut.save(tmp.name, "PNG")
                    tmp_mask_path = tmp.name
                    args.mask = tmp.name
                    args.mask_mode = "alpha"

    mask = build_mask(args.shape, args.mask, size=1000, mask_mode=args.mask_mode,
                      text=args.text, width=args.width, height=args.height,
                      font_path=font_path)

    # "transparent" is handled by wordcloud as background_color=None + mode=RGBA.
    bg = None if args.background == "transparent" else args.background
    mode = "RGBA" if (bg is None or bg == "white") else "RGB"

    wc = WordCloud(
        font_path=font_path,
        background_color=bg,
        mask=mask,
        max_words=args.max_words,
        max_font_size=args.max_font,
        min_font_size=args.min_font,
        relative_scaling=args.relative_scaling,
        prefer_horizontal=args.prefer_horizontal,
        color_func=color_func,
        margin=1,
        scale=2,
        repeat=args.repeat,
        mode=mode,
    )
    wc.generate_from_frequencies(freq)

    fig, ax = plt_subplot()
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])  # fill the figure, no margin
    if args.title:
        plt_figtext(args.title, font_path)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    if bg is None:
        # transparent background: let wordcloud's own alpha survive savefig
        fig.patch.set_alpha(0)
        ax.patch.set_alpha(0)
        fig.savefig(args.output, dpi=200, bbox_inches="tight",
                    transparent=True, pad_inches=0)
    else:
        fig.savefig(args.output, dpi=200, bbox_inches="tight",
                    facecolor=bg, pad_inches=0)
    plt_close()
    if tmp_mask_path and os.path.exists(tmp_mask_path):
        try:
            os.remove(tmp_mask_path)
        except OSError:
            pass
    print(f"Saved: {args.output}  ({len(entries)} unique words, shape={args.shape})")


def plt_subplot():
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 9))
    return fig, ax


def plt_figtext(title, font_path=None):
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    kwargs = dict(ha="center", va="center", fontsize=10.5, color="#444444")
    if font_path and os.path.exists(font_path):
        kwargs["fontproperties"] = fm.FontProperties(fname=font_path)
    plt.figtext(0.5, 0.025, title, **kwargs)


def plt_close():
    import matplotlib.pyplot as plt
    plt.close()


if __name__ == "__main__":
    main()
