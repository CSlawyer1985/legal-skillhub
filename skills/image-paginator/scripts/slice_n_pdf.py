#!/usr/bin/env python3
"""
slice-n-pdf: Tile long image(s) into a numbered grid PDF.

Completely independent implementation using fpdf2 for PDF generation
and a stride-based tiling algorithm with adaptive tail merging.
"""

import math, os, shutil, sys, tempfile
from pathlib import Path
from typing import List, Tuple

from PIL import Image as PILImage, ImageDraw, ImageFont, ImageFile
from fpdf import FPDF

ImageFile.LOAD_TRUNCATED_IMAGES = True


# ── Font resolver ──────────────────────────────────────────────
def _pick_font(size: int = 44):
    for p in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\msyh.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]:
        try:
            return ImageFont.truetype(p, size)
        except (OSError, IOError):
            pass
    return ImageFont.load_default()


# ── Image stitching (multi-source) ────────────────────────────
def stitch(sources: List[str]) -> PILImage.Image:
    """Load multiple images, normalise to widest width, stack vertically."""
    imgs: List[PILImage.Image] = []
    for p in map(Path, sources):
        if not p.is_file():
            sys.exit(f"File not found: {p}")
        imgs.append(PILImage.open(p).convert("RGB"))

    target_w = max(im.width for im in imgs)
    strips: List[PILImage.Image] = []
    for im in imgs:
        if im.width != target_w:
            ratio = target_w / im.width
            im = im.resize((target_w, int(im.height * ratio)), PILImage.LANCZOS)
        strips.append(im)

    canvas_h = sum(s.height for s in strips)
    canvas = PILImage.new("RGB", (target_w, canvas_h))
    y = 0
    for s in strips:
        canvas.paste(s, (0, y))
        y += s.height
        s.close()
    return canvas


# ── Tile cutter (stride-based, adaptive tail) ─────────────────
def cut_tiles(
    img: PILImage.Image,
    tile_px: int = 2000,
    bleed_px: int = 200,
    work_dir: str = "/tmp",
) -> List[str]:
    """
    Cut image into vertical tiles using a forward-stepping stride.

    Unlike overlap-and-backtrack, this walks forward by (tile - bleed)
    each step.  The final short tile is merged into its predecessor
    to avoid tiny orphan slices.
    """
    w, h = img.size
    step = tile_px - bleed_px
    cuts: List[Tuple[int, int]] = []  # (top, bottom)

    y = 0
    while y < h:
        bot = min(y + tile_px, h)
        cuts.append((y, bot))
        if bot >= h:
            break
        y += step

    # Merge orphan tail (< 40% of tile) into previous cut
    if len(cuts) >= 2:
        last_top, last_bot = cuts[-1]
        if (last_bot - last_top) < tile_px * 0.4:
            prev_top, _ = cuts[-2]
            cuts[-2] = (prev_top, last_bot)
            cuts.pop()

    font = _pick_font(48)
    paths: List[str] = []
    for idx, (top, bot) in enumerate(cuts):
        region = img.crop((0, top, w, bot)).convert("RGB")

        # Draw index badge
        draw = ImageDraw.Draw(region)
        label = str(idx + 1)
        bb = draw.textbbox((0, 0), label, font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        pad = 10
        bx, by = 10, 10
        draw.rounded_rectangle(
            [(bx, by), (bx + tw + pad * 2, by + th + pad * 2)],
            radius=8, fill=(255, 255, 255, 220), outline=(80, 80, 80), width=2,
        )
        draw.text((bx + pad, by + pad), label, fill=(20, 20, 20), font=font)

        out = os.path.join(work_dir, f"t{idx + 1:03d}.png")
        region.save(out, "PNG")
        paths.append(out)

    print(f"  Image {w}×{h} → {len(paths)} tiles (tile={tile_px}, bleed={bleed_px})")
    return paths


# ── PDF builder (fpdf2) ───────────────────────────────────────
class TilePDF(FPDF):
    """Custom FPDF that arranges tile images into a uniform grid."""

    def __init__(self, pw: float, ph: float, cols: int, rows: int,
                 gutter: float, edge: float, numbered: bool = True):
        super().__init__(unit="pt", format=(pw, ph))
        self.cols = cols
        self.rows = rows
        self.gutter = gutter
        self.edge = edge
        self.numbered = numbered
        self.set_auto_page_break(auto=False)

        usable_w = pw - 2 * edge
        usable_h = ph - 2 * edge
        self.cell_w = (usable_w - (cols - 1) * gutter) / cols
        self.cell_h = (usable_h - (rows - 1) * gutter) / rows

    def place_tiles(self, tiles: List[str], dest: str):
        per_page = self.cols * self.rows
        pages = math.ceil(len(tiles) / per_page)
        idx = 0

        for pg in range(pages):
            self.add_page()
            # white background
            self.set_fill_color(255, 255, 255)
            self.rect(0, 0, self.w, self.h, style="F")

            for r in range(self.rows):
                for c in range(self.cols):
                    if idx >= len(tiles):
                        idx += 1
                        continue

                    # cell origin (fpdf y-axis goes downward)
                    x0 = self.edge + c * (self.cell_w + self.gutter)
                    y0 = self.edge + r * (self.cell_h + self.gutter)

                    # light background for the cell
                    self.set_fill_color(240, 240, 240)
                    self.rect(x0, y0, self.cell_w, self.cell_h, style="F")

                    # fit image inside cell preserving aspect ratio
                    im = PILImage.open(tiles[idx])
                    iw, ih = im.size
                    scale = min(self.cell_w / iw, self.cell_h / ih)
                    dw, dh = iw * scale, ih * scale
                    dx = x0 + (self.cell_w - dw) / 2
                    dy = y0 + (self.cell_h - dh) / 2

                    tmp = os.path.join(tempfile.gettempdir(), f"_tp_{idx}.jpg")
                    im.convert("RGB").save(tmp, "JPEG", quality=92)
                    im.close()
                    self.image(tmp, x=dx, y=dy, w=dw, h=dh)

                    idx += 1

            if self.numbered:
                label = f"- {pg + 1} -"
                self.set_font("Helvetica", size=10)
                self.set_text_color(128, 128, 128)
                tw = self.get_string_width(label)
                self.set_xy((self.w - tw) / 2, self.h - 18)
                self.cell(tw, 10, label, align="C")
                self.set_text_color(0, 0, 0)

            self._cleanup_temps(max(0, idx - per_page), idx)

        self.output(dest)
        self._cleanup_temps(0, idx)

    def _cleanup_temps(self, lo: int, hi: int):
        for i in range(lo, hi):
            p = os.path.join(tempfile.gettempdir(), f"_tp_{i}.jpg")
            if os.path.exists(p):
                os.remove(p)


# ── CLI ───────────────────────────────────────────────────────
def main():
    ap = (
        __import__("argparse")
        .ArgumentParser(
            description="Tile long image(s) into a numbered grid PDF.",
        )
    )
    ap.add_argument("sources", nargs="+", help="Input image path(s).")
    ap.add_argument("-o", "--output", default="output.pdf", help="Output PDF name.")
    ap.add_argument("-d", "--dest", required=True, help="Output directory.")
    ap.add_argument("--tile", type=int, default=2000, help="Tile height in px (default 2000).")
    ap.add_argument("--bleed", type=int, default=200, help="Bleed / overlap in px (default 200).")
    ap.add_argument("--cols", type=int, default=2, help="Grid columns (default 2).")
    ap.add_argument("--rows", type=int, default=2, help="Grid rows (default 2).")
    ap.add_argument("--gutter", type=int, default=40, help="Gap between cells in px (default 40).")
    ap.add_argument("--edge", type=int, default=25, help="Page margin in px (default 25).")
    ap.add_argument("--no-numbers", action="store_true", help="Omit page numbers.")
    ap.add_argument("--clean", action="store_true", help="Remove tile images after build.")
    args = ap.parse_args()

    # ── 参数校验 ────────────────────────────────────────────────
    errors = []
    if args.tile < 100:
        errors.append(f"--tile ({args.tile}) must be ≥ 100 pixels.")
    if args.bleed < 0:
        errors.append(f"--bleed ({args.bleed}) must be ≥ 0.")
    if args.tile <= args.bleed:
        errors.append(f"--tile ({args.tile}) must be strictly greater than --bleed ({args.bleed}).")
    if args.cols < 1 or args.cols > 10:
        errors.append(f"--cols ({args.cols}) must be between 1 and 10.")
    if args.rows < 1 or args.rows > 10:
        errors.append(f"--rows ({args.rows}) must be between 1 and 10.")
    if args.gutter < 0:
        errors.append(f"--gutter ({args.gutter}) must be ≥ 0.")
    if args.edge < 0:
        errors.append(f"--edge ({args.edge}) must be ≥ 0.")
    if errors:
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        sys.exit(1)
    print("  ✓ Arguments validated OK")


    dest = Path(args.dest).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)
    pdf_path = dest / args.output
    tmp = dest / "_tiles"

    try:
        tmp.mkdir(parents=True, exist_ok=True)
        combined = stitch(args.sources)
        tiles = cut_tiles(combined, tile_px=args.tile, bleed_px=args.bleed, work_dir=str(tmp))
        combined.close()

        if not tiles:
            sys.exit("No tiles produced.")

        first = PILImage.open(tiles[0])
        tile_w = first.width
        first.close()

        builder = TilePDF(
            pw=tile_w,
            ph=args.tile,
            cols=args.cols, rows=args.rows,
            gutter=args.gutter, edge=args.edge,
            numbered=not args.no_numbers,
        )

        builder.place_tiles(tiles, str(pdf_path))

        if args.clean:
            shutil.rmtree(tmp, ignore_errors=True)

        n_pages = math.ceil(len(tiles) / (args.cols * args.rows))
        print(f"\n✓ Done  |  {len(args.sources)} image(s) → {len(tiles)} tiles → "
              f"{n_pages} page(s) → {pdf_path}")
        if args.clean:
            print("  Temporary tiles cleaned up.")

    except Exception as exc:
        print(f"\n✗ Failed: {exc}", file=sys.stderr)
        import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
