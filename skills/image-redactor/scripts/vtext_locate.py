"""竖排文字定位 —— image-redactor 的 OCR 盲区兜底

场景：组织架构图 / 思维导图导出的图里，节点文字常为竖排（正立汉字纵向堆叠，或整体旋转 90°）。
macOS Vision OCR 对这类文本会整列漏识，拿不到 bbox。
本模块完全不依赖 OCR，用纯像素投影定位「方框边界 → 每个字的格子 → 目标字的精确矩形」。

命令行：
    python3 vtext_locate.py 图.png --box 990,580,1090,880              # 列出框内每个字的格子
    python3 vtext_locate.py 图.png --box 990,580,1090,880 --target 5-7  # 取第 5~7 字，输出矩形
    python3 vtext_locate.py 图.png --box 990,580,1090,880 --axis x      # 横排文字同样适用

作为库：
    from vtext_locate import find_frame, char_runs, char_cells, target_rect, diff_outside
"""

# 法律科技实务工具 · 维护者陆凌燕律师（北京德恒·无锡）

import sys

import numpy as np
from PIL import Image

THR_INK = 150     # 判定"这是文字墨迹"的灰度阈值（可放宽到 200 抓抗锯齿边缘）
THR_LINE = 120    # 判定"这是框线"的灰度阈值
INSET = 5         # 框内缩像素，用于把框线本身排除在文字区之外


def load_gray(path):
    return np.array(Image.open(path).convert("L")).astype(int)


def find_frame(gray, x0, y0, x1, y1, thr=THR_LINE, ratio=0.9, band=0.5):
    """在窗口内找矩形框的四条边，返回 (left, top, right, bottom)；找不到返回 None。

    竖排文字节点通常画在带边框的矩形里，框线是最稳的定位锚点。
    **关键：只在窗口中段的 band 比例区间内做投影**——若拿整个窗口算占比，
    框线只覆盖窗口的一部分，占比会被稀释到阈值以下（实测 250/300=0.83 就漏检）。
    中段窄带里框线占比≈100%；穿过文字的横排笔画只污染个别行，取 min/max 仍能得到真实边界。
    """
    h, w = y1 - y0, x1 - x0
    by0, by1 = y0 + int(h * (0.5 - band / 2)), y0 + int(h * (0.5 + band / 2))
    sub = gray[by0:by1, x0:x1]
    col_ratio = (sub < thr).sum(axis=0) / max(by1 - by0, 1)
    vx = [x0 + i for i, v in enumerate(col_ratio) if v >= ratio]
    if len(vx) < 2:
        return None
    left, right = min(vx), max(vx)
    bx0 = left + int((right - left) * (0.5 - band / 2))
    bx1 = max(left + int((right - left) * (0.5 + band / 2)), bx0 + 1)
    sub2 = gray[y0:y1, bx0:bx1]
    row_ratio = (sub2 < thr).sum(axis=1) / max(bx1 - bx0, 1)
    hy = [y0 + i for i, v in enumerate(row_ratio) if v >= ratio]
    if len(hy) < 2:
        return None
    return (left, min(hy), right, max(hy))


def _inner(frame, inset=INSET):
    left, top, right, bottom = frame
    return left + inset, top + inset, right - inset + 1, bottom - inset + 1


def _runs(profile, min_px=1, gap=3):
    """把一维投影切成连续段，返回 [(start, end), ...]（闭区间）。"""
    runs, cur = [], None
    for i, v in enumerate(profile):
        if v >= min_px:
            if cur is None:
                cur = [i, i]
            else:
                cur[1] = i
        elif cur is not None and (i - cur[1]) > gap:
            runs.append(tuple(cur))
            cur = None
    if cur is not None:
        runs.append(tuple(cur))
    return runs


def char_runs(gray, frame, thr=THR_INK, min_px=1, gap=0, axis="y"):
    """原始墨迹段（**段数 ≠ 字数**，仅供刻画笔画分布，不要用来数第几个字）。

    笔画为横线的字在竖向投影里会被拆成多条细 run：「一」= 一条 h≈4 的细 run，
    「二」= 两条，与相邻字的间距也更大。自动剔除贴在框上的边框 run（墨迹横贯整个框宽）。
    """
    x0, y0, x1, y1 = _inner(frame)
    sub = gray[y0:y1, x0:x1]
    prof = (sub < thr).sum(axis=1 if axis == "y" else 0)
    out = []
    for s, e in _runs(prof, min_px, gap):
        if axis == "y":
            span = ink_span(gray, y0 + s, y0 + e + 1, x0, x1, thr=200, axis="x")
            full = (x1 - x0) * 0.9
        else:
            span = ink_span(gray, y0, y1, x0 + s, x0 + e + 1, thr=200, axis="y")
            full = (y1 - y0) * 0.9
        if span and (span[1] - span[0] + 1) >= full:
            continue                     # 边框线，丢弃
        out.append((y0 + s, y0 + e) if axis == "y" else (x0 + s, x0 + e))
    return out


def char_cells(gray, frame, thr=THR_INK, gap=0, axis="y"):
    """把墨迹段合并成**每个字**的区间，返回 [(start, end), ...]，长度 = 字数。

    合并规则：相邻两段若合并后的跨度不超过「最高单段高度 × 1.05」，即视为同一个字
    被拆开的笔画（「二」的上下两横、「一」单独成段）——汉字是等宽等高的，一个字
    不可能比单个完整字形还高，而相邻两字的跨度必然超过这个阈值（≈字形高 + 字间距）。

    不要用步距网格切字：网格相位会随字距累计漂移，「二」的第二横在 4 个字之后
    就会漂进下一格，反而把字切错。笔画合并只看局部、不累积误差。
    """
    runs = char_runs(gray, frame, thr=thr, gap=gap, axis=axis)
    if not runs:
        return []
    max_h = max(e - s + 1 for s, e in runs)
    limit = max_h * 1.05
    cells, cur = [], None
    for s, e in runs:
        if cur is None:
            cur = [s, e]
        elif e - cur[0] <= limit:
            cur[1] = e                     # 同一字被拆开的笔画
        else:
            cells.append(tuple(cur))
            cur = [s, e]
    cells.append(tuple(cur))
    return cells


def ink_span(gray, y0, y1, x0, x1, thr=200, axis="x"):
    """在窗口内求墨迹跨度，返回 (min, max)；无墨迹返回 None。"""
    sub = gray[y0:y1, x0:x1]
    prof = (sub < thr).sum(axis=0 if axis == "x" else 1)
    idx = [i for i, v in enumerate(prof) if v > 0]
    if not idx:
        return None
    return ((x0 if axis == "x" else y0) + idx[0], (x0 if axis == "x" else y0) + idx[-1])


def guess_orientation(gray, runs, frame, thr=THR_INK):
    """竖排节点的字是「正立」还是「整体旋转 90°」，返回 'upright' | 'rotated' | 'unknown'。

    判据（实测有效）：正立汉字的墨迹近似方形，x 跨度 ≈ y 跨度；横笔画字（「一」）
    更是「4px 厚、19px 宽」——x 跨度大于 y 跨度。若整体旋转 90°，横笔画变成竖笔画，
    每条 run 的 x 跨度会远小于 y 跨度。
    """
    if len(runs) < 2:
        return "unknown"
    x0, y0, x1, y1 = _inner(frame)
    ratios = []
    for s, e in runs:
        span = ink_span(gray, s, e + 1, x0, x1, thr=thr, axis="x")
        if span:
            ratios.append((span[1] - span[0] + 1) / (e - s + 1))
    if not ratios:
        return "unknown"
    return "upright" if sum(1 for r in ratios if r >= 0.5) / len(ratios) >= 0.5 else "rotated"


def target_rect(gray, cells, frame, i_from, i_to, axis="y", pad=2, gap=0):
    """把「第 i_from ~ i_to 个字」（1 起算）换算成安全矩形 (x0, y0, x1, y1)。

    安全边界沿**阅读方向**留缓冲，且**只缓冲到相邻字的墨迹边缘 +1 像素**：
      - 横排文字防压到前一个字的右边缘；
      - 竖排文字防压到上一个字的下边缘（竖排各字左右居中、共用一个 x 区间，
        若按 x 方向避让会把矩形推到旁边的字身上，是典型的翻车点）。
    缓冲给太多会留下 1~2px 未覆盖的抗锯齿边缘，反而让自检「原字墨迹 100% 覆盖」不过。
    """
    sel = cells[i_from - 1:i_to]
    if not sel:
        return None
    x0, y0, x1, y1 = _inner(frame)
    if axis == "y":
        ry0, ry1 = sel[0][0], sel[-1][1]
        span = ink_span(gray, ry0, ry1 + 1, x0, x1, thr=200, axis="x")
        if not span:
            return None
        lo = y0 if i_from == 1 else max(y0, cells[i_from - 2][1] + 1 + gap)
        return (max(span[0] - pad, x0), max(ry0 - pad, lo),
                min(span[1] + pad + 1, x1), min(ry1 + pad + 1, y1))
    rx0, rx1 = sel[0][0], sel[-1][1]
    span = ink_span(gray, y0, y1, rx0, rx1 + 1, thr=200, axis="y")
    if not span:
        return None
    lo = x0 if i_from == 1 else max(x0, cells[i_from - 2][1] + 1 + gap)
    return (max(rx0 - pad, lo), max(span[0] - pad, y0),
            min(rx1 + pad + 1, x1), min(span[1] + pad + 1, y1))


def diff_outside(src, out, boxes, tol=10):
    """全图差异掩膜校验：返回 (框外改动像素数, 全图改动像素数)。框外应为 0。"""
    a = np.array(Image.open(src).convert("RGB")).astype(int)
    b = np.array(Image.open(out).convert("RGB")).astype(int)
    diff = np.abs(a - b).sum(axis=2) > tol
    mask = np.zeros(diff.shape, bool)
    for x0, y0, x1, y1 in boxes:
        mask[y0:y1, x0:x1] = True
    return int((diff & ~mask).sum()), int(diff.sum())


if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv or "--box" not in argv:
        print(__doc__)
        sys.exit(1)
    path = argv[0]
    gray = load_gray(path)
    box = [int(v) for v in argv[argv.index("--box") + 1].split(",")]
    axis = argv[argv.index("--axis") + 1] if "--axis" in argv else "y"

    frame = find_frame(gray, *box)
    if frame is None:
        frame = tuple(box)
        print("⚠️  窗口内没找到深色矩形框（无边框卡片/纯文字区），直接把窗口当框用。")
        print("    此时请确认窗口边界紧贴目标文字，留白过大不影响切字、但会影响矩形范围。")
    print(f"{path}  size={gray.shape[1]}x{gray.shape[0]}  axis={axis}")
    print(f"  方框边界 left={frame[0]} top={frame[1]} right={frame[2]} bottom={frame[3]}")

    runs = char_runs(gray, frame, axis=axis)
    cells = char_cells(gray, frame, axis=axis)
    print(f"  朝向：{guess_orientation(gray, runs, frame)}")
    print(f"  墨迹段 {len(runs)} 段（含横笔画字拆出的细段，**不是字数**）")
    print(f"  笔画合并后切出 {len(cells)} 个字：")
    for i, (s, e) in enumerate(cells, 1):
        print(f"    #{i}  {axis} {s}-{e}  长 {e - s + 1}px")

    if "--target" in argv:
        a, _, b = argv[argv.index("--target") + 1].partition("-")
        rect = target_rect(gray, cells, frame, int(a), int(b or a), axis=axis)
        print(f"  目标 #{a}-{b or a} 矩形 (x0,y0,x1,y1) = {rect}")
        print(f"  → redact('{path}', 'out.png', [{rect}])")
