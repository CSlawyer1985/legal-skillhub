# -*- coding: utf-8 -*-
"""
渲染校对：把重建的 docx 转 PDF，与原件 PDF 逐行对表 + 校验每视觉行宽度。

用法:
  python verify_layout.py <原件.pdf> <重建.docx> [--outdir .]

做三件事：
  A. 用 LibreOffice 渲染 docx（独立 UserInstallation，避免静默失败）
  B. 提渲染 PDF 的文字坐标（能一眼看出哪段多了一行）
  C. 提两份 PDF 的墨迹行带做对表
"""
import os
import subprocess
import sys
import tempfile

import numpy as np

SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
# 600dpi：300dpi 下 0.6pt 的下划线只有 2.5px，会与相邻文字行并带，
# 造成一堆假的「Δy 超限」。细横线必须提高渲染分辨力才能分开。
DPI, S = 600, 72.0 / 600


def render(docx, outdir):
    """LibreOffice 兜底渲染。

    ⚠️ 能不用就别用：实测同一份文件（律协附件3）LibreOffice 会制造两类假失配——
       ① 表格整体下移 29.4pt（Word 166.3pt / LO 197.4pt / 扫描件 168.0pt）
       ② 表头长格折成 4 行（Word 与扫描件均为 3 行）
       据此改文档会改坏。正确做法：先跑
         python3 ~/.workbuddy/skills/word-to-pdf-macos/scripts/batch_word_to_pdf.py <docx>
       再调 main(orig, docx, outdir, rendered_pdf=<Word 导出的 pdf>) 直接比对。
    """
    prof = tempfile.mkdtemp(prefix="lo_vfy_")
    print("[警告] 正在用 LibreOffice 渲染：表格纵向位置与折行数不可信，"
          "不要据此修改文档（见 SKILL.md 第 4 步）。")
    subprocess.run([SOFFICE, f"-env:UserInstallation=file://{prof}",
                    "--headless", "--convert-to", "pdf",
                    "--outdir", outdir, docx],
                   capture_output=True, timeout=180)
    pdf = os.path.join(outdir, os.path.splitext(os.path.basename(docx))[0] + ".pdf")
    if not os.path.exists(pdf):
        raise RuntimeError("LibreOffice 未产出 PDF —— 检查是否复用了被占用的配置目录")
    return pdf


def text_lines(pdf):
    import fitz
    pg = fitz.open(pdf)[0]
    out = []
    for b in pg.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b["lines"]:
            t = "".join(s["text"] for s in l["spans"])
            if not t.strip():
                continue
            x0 = min(s["bbox"][0] for s in l["spans"])
            x1 = max(s["bbox"][2] for s in l["spans"])
            y0 = min(s["bbox"][1] for s in l["spans"])
            fonts = {s["font"] for s in l["spans"]}
            out.append((y0, x0, x1, t, fonts))
    return out


def ink_bands(pdf):
    # 用 Otsu 而非硬阈值 <150：抗锯齿的灰边会被硬阈值算成墨，
    # 实测硬阈值下重建版多出 13 条假带（31 vs 18），全是"Δy 超限"假警报。
    dark = ink(pdf, dpi=DPI)
    rl = dark.sum(axis=1)
    res, inb = [], False
    for i, v in enumerate(rl):
        if v > 0 and not inb:
            start, inb = i, True
        elif v == 0 and inb:
            # 至少 3 行才算一条带：否则抗锯齿的孤立行会被当成带，
            # 凭空多出十几条"Δy 超限"的假失配（实测 31 条 vs 真实 18 条）
            if i - start >= 6:   # ≥0.72pt 才算带
                cl = dark[start:i].sum(axis=0)
                nz = np.nonzero(cl > 0)[0]
                if len(nz):
                    res.append((round(start * S, 1), round(nz[0] * S, 1),
                                round(nz[-1] * S, 1)))
            inb = False
    return res


def ink(doc, dpi=DPI):
    """二值墨迹掩膜"""
    import fitz
    pg = fitz.open(doc)[0]
    pix = pg.get_pixmap(dpi=dpi)
    g = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n)[:, :, 0].astype(np.float64)
    # Otsu
    h = np.bincount(g.ravel().astype(np.uint8), minlength=256).astype(float)
    tot = g.size
    sa = float(np.dot(np.arange(256), h))
    sb = wb = 0.0
    best, thr = -1.0, 127
    for i in range(256):
        wb += h[i]
        if wb == 0:
            continue
        wf = tot - wb
        if wf == 0:
            break
        sb += i * h[i]
        v = wb * wf * ((sb / wb) - ((sa - sb) / wf)) ** 2
        if v > best:
            best, thr = v, i
    return g < thr


def compare(orig, pdf):
    """三类稳健指标。

    ⚠️ 不要用「行带条数是否相等」或「按序号的 Δy」当验收线：
       下划线与文字会并带，条数天然不等，按序号对齐会整体错位——
       这正是最容易误判成"版面走样"的假警报。
    """
    A, B = ink(orig), ink(pdf)
    H, W = min(A.shape[0], B.shape[0]), min(A.shape[1], B.shape[1])
    A, B = A[:H, :W], B[:H, :W]
    ar, br = A.any(axis=1), B.any(axis=1)
    ac, bc = A.any(axis=0), B.any(axis=0)
    row_iou = np.logical_and(ar, br).sum() / np.logical_or(ar, br).sum()
    col_iou = np.logical_and(ac, bc).sum() / np.logical_or(ac, bc).sum()
    corr = np.corrcoef(A.sum(axis=1).astype(float), B.sum(axis=1).astype(float))[0, 1]
    return row_iou, col_iou, corr


def band_offsets(orig, pdf):
    """重建的每条墨迹带在原件里找最近带，返回 Δy 列表。

    只看这个方向：**重建 → 原件**。反向（原件→重建）在并带时必然出现
    "原件有、重建无"的假失配，不能作为判据。
    """
    A, B = ink_bands(orig), ink_bands(pdf)
    ay = [b[0] for b in A]
    return [min(abs(y - t) for t in ay) for y, _, _ in B], A, B


def main(orig, docx, outdir=".", rendered_pdf=None):
    # rendered_pdf: 用 Word 导出的 PDF（首选，见 render() 的警告）。
    # 不传才退回 LibreOffice —— 那种情况下表格纵向位置与折行数别当真。
    pdf = rendered_pdf or render(docx, outdir)
    tl = text_lines(pdf)
    print(f"渲染 PDF: {pdf}" + ("   [Word 原生渲染]" if rendered_pdf else "   [LibreOffice，仅供参考]"))
    print(f"\n【A. 渲染版文字行 {len(tl)} 行】  y / x0→x1 / 宽 / 字体")
    for y, x0, x1, t, fonts in tl:
        show = t if len(t) <= 30 else f"{t[:12]}…[{len(t)}字符]…{t[-8:]}"
        print(f"  y={y:7.1f}  x {x0:6.1f}→{x1:6.1f}  w={x1-x0:6.1f}  "
              f"{','.join(sorted(fonts))}")
        print(f"           {show}")

    print("\n【B. 稳健几何指标】")
    ri, ci, corr = compare(orig, pdf)
    d, A, B = band_offsets(orig, pdf)
    d = np.array(d)
    print(f"  行墨迹投影 IoU      {ri:.3f}")
    print(f"  列墨迹投影 IoU      {ci:.3f}   ← 反映行宽/填空线长度")
    print(f"  逐行墨迹相关        {corr:.4f}  ← 反映纵向位置，做版本 A/B 对比最灵")
    print(f"  重建带→原件最近带  均 {d.mean():.2f}pt  最大 {d.max():.2f}pt  "
          f"超 4pt 的 {int((d > 4).sum())}/{len(d)} 条")
    print(f"  原件 {len(A)} 带 / 重建 {len(B)} 带"
          f"（条数不等属正常：文字与下划线会并带）")
    print("\n验收线：均 Δy ≤ 2pt、最大 ≤ 4pt、超 4pt 的 0 条；"
          "字宽（文本层逐字 origin 或列投影）与原件差 ≤ 0.1pt。")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    od, rendered = ".", None
    for a in sys.argv[1:]:
        if a.startswith("--outdir="):
            od = a.split("=", 1)[1]
        elif a.startswith("--rendered="):
            rendered = a.split("=", 1)[1]
    main(args[0], args[1], od, rendered)
