# -*- coding: utf-8 -*-
"""
扫描件版式测量：输出可据以重建 Word 的全部参数。
用法: python measure_scan.py <扫描件.pdf> [起始页=0]

输出：
  1. 是否扫描件（文本层长度 / 内嵌图尺寸）
  2. 每行墨迹行带 (y0, y1, x左, x右)  —— 用于推字号、行距、页边距、缩进
  3. 行距直方图 —— 众数即正文行距，用于反推字号
  4. 疑似下划线的细行带及其分段 —— 用于数填空线长度
"""
import sys
import numpy as np
import fitz

DPI = 300            # 扫描件标准分辨率；1pt = DPI/72 px
S = 72.0 / DPI


def load(path, pageno=0, dpi=DPI):
    pg = fitz.open(path)[pageno]
    pix = pg.get_pixmap(dpi=dpi)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n)
    gray = img[:, :, :3].mean(axis=2)
    return pg, gray < 150, S          # gray/dark 掩膜


def bands(dark, s=S, min_h=0.4):
    """返回 [(y0, y1, xL, xR)] 墨迹行带（pt）"""
    rl = dark.sum(axis=1)
    out, inb = [], False
    for i, v in enumerate(rl):
        if v > 0 and not inb:
            start, inb = i, True
        elif v == 0 and inb:
            out.append((start, i)); inb = False
    if inb:
        out.append((start, len(rl)))
    res = []
    for a, b in out:
        if (b - a) * s < min_h:
            continue
        cl = dark[a:b].sum(axis=0)
        nz = np.nonzero(cl > 0)[0]
        if not len(nz):
            continue
        res.append((round(a * s, 1), round(b * s, 1),
                    round(nz[0] * s, 1), round(nz[-1] * s, 1)))
    return res


def runs(dark, y0, y1, gap=2.0, s=S):
    """某一行带内的横向墨迹分段 [(x0, x1, 宽)]，gap 为合并阈值(pt)"""
    sub = dark[int(y0 / s):int(y1 / s)]
    cl = sub.sum(axis=0)
    segs, inb = [], False
    for i, v in enumerate(cl):
        if v > 0 and not inb:
            start, inb = i, True
        elif v == 0 and inb:
            segs.append([start * s, i * s]); inb = False
    if inb:
        segs.append([start * s, len(cl) * s])
    if not segs:
        return []
    m = [segs[0]]
    for a, b in segs[1:]:
        if a - m[-1][1] < gap:
            m[-1][1] = b
        else:
            m.append([a, b])
    return [(round(a, 1), round(b, 1), round(b - a, 1)) for a, b in m]


def main(path, pageno=0):
    pg, dark, s = load(path, pageno)
    txt = pg.get_text()
    print(f"页面: {pg.rect.width:.1f} × {pg.rect.height:.1f} pt")
    print(f"文本层: {len(txt)} 字符  →  {'扫描件（需重建）' if len(txt) < 20 else '有文本层（可直接抽取）'}")
    for im in pg.get_images(full=True)[:3]:
        print(f"内嵌图: {im[2]}×{im[3]} px  编码={im[8]}")

    bs = bands(dark, s)
    print(f"\n墨迹行带 {len(bs)} 条  (y0, y1, x左, x右)")
    for b in bs:
        print(f"   y {b[0]:7.1f}–{b[1]:7.1f}   x {b[2]:7.1f} → {b[3]:7.1f}"
              f"   高{b[1]-b[0]:5.1f}  左距{b[2]:6.1f}  右距{pg.rect.width-b[3]:6.1f}")

    # 行距直方图
    tops = [b[0] for b in bs]
    d = [round(tops[i+1]-tops[i], 1) for i in range(len(tops)-1)]
    pitch = [x for x in d if 5 < x < 40]
    if pitch:
        vals, cnt = np.unique(np.round(pitch), return_counts=True)
        mode = vals[np.argmax(cnt)]
        # 行距 ≠ 字号：这里是"行高"，别拿它反推字号到处方大小。
        # 字号必须用 identify_font.py 的字形/字宽匹配来定。
        print(f"\n行距众数 ≈ {mode:.0f}pt  →  正文行高 {mode:.0f}pt")
        print(f"   ⚠️ 行距只用于设置「固定行距」，**不可**由它反推字号（行距/字号比随文档而异）")
        print(f"   全部行距样本: {sorted(set(pitch))}")

    # 细行带 = 疑似下划线
    thin = [b for b in bs if b[1]-b[0] < 3.5 and (b[3]-b[2]) > 20]
    print(f"\n疑似下划线行带 {len(thin)} 条（分段长度可换算填空字数，半角_=0.5em）")
    for b in thin:
        segs = runs(dark, b[0], b[1], gap=2.0, s=s)
        tot = sum(x[2] for x in segs)
        print(f"   y={b[0]:7.1f}  x {b[2]:.1f}→{b[3]:.1f}  总长{tot:.1f}pt"
              f"  ≈{tot/7.5:.1f}个半角_ (按15pt估)")
        if len(segs) > 1:
            print(f"        分段: {[(x[0], x[1]) for x in segs]}")
        # 检查是否连续（无周期亮缝）
        seg = dark[int(b[0]/s):int(b[1]/s)]
        cl = seg.sum(axis=0)
        flat = cl[int(b[2]/s):int(b[3]/s)]
        gaps = int((flat == 0).sum())
        print(f"        缝隙像素 {gaps} 个 → {'连续直线' if gaps <= 2 else '有间断（可能是全角下划线，会排成短横！）'}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0)
