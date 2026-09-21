#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
record2evidence.py — 录屏转证据截图 + 一面4块 A4 排版（一条命令跑完全流程）

用法:
    python3 record2evidence.py 录屏.mp4 -o 输出目录 [选项]

流程: ffprobe 侦察 → ffmpeg 密集抽帧 → 逐帧小步长滚动偏移累加 → 按内容窗口自动分段选链
      → 拼小样图 + 衔接量报告(人工复核) → 一面4块 A4 PDF + 自检

核心定则(2026-08-30 用户拍板):
    1. 每帧都是原始完整截图，绝不裁剪
    2. 相邻两张图重叠约一行多(默认165px)
    3. 推进量不得超过固定UI之间的内容窗口高度，否则漏内容

依赖: ffmpeg/ffprobe, numpy, Pillow, reportlab, pypdf (管理版 python 均已内置)
"""
import argparse, json, os, shutil, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

# ---------------- 参数 ----------------
def parse_args():
    ap = argparse.ArgumentParser(description="录屏转证据截图+一面4块A4排版")
    ap.add_argument("video", help="输入录屏路径 (mp4/mov)")
    ap.add_argument("-o", "--outdir", default=None, help="输出目录 (默认: ~/Desktop/录屏证据_<视频名>)")
    ap.add_argument("--fps", type=int, default=15, help="密集抽帧帧率 (默认15)")
    ap.add_argument("--overlap", type=int, default=165, help="相邻帧目标衔接/重叠像素 (默认165≈一行多,该视频实测实际衔接159-163px)")
    ap.add_argument("--per-page", type=int, default=4, choices=(1, 2, 4, 6), help="每页图片数 (默认4；6=3列×2行省纸版式：肩并肩放大3%%单张6.18cm，左装订边1.3cm)")
    ap.add_argument("--img-scale", type=float, default=None, help="图片放大系数 (默认：6块版式=1.03 定稿值，其他版式=1.0；放大宽度由边距消化，绝不压叠)")
    ap.add_argument("--shift-cap", type=float, default=0.6, help="单帧shift搜索上限/屏高 (默认0.6)")
    ap.add_argument("--mae-cut", type=float, default=18.0, help="场景切换MAE阈值 (默认18)")
    ap.add_argument("--min-seg", type=float, default=0.5, help="最短内容段时长秒，短于此判为过渡动画丢弃 (默认0.5)")
    ap.add_argument("--fixed-top", default=None,
                    help="手动覆盖固定UI顶部像素; 支持按组: '2:140' 或 '1:147,2:140' (白底文章页方差检测会失效, 用两帧逐行差异法量出后传入)")
    ap.add_argument("--fixed-bottom", default=None,
                    help="手动覆盖固定UI底部像素; 支持按组: '2:150' 或 '1:139,2:150'")
    return ap.parse_args()


def parse_fixed_override(val):
    """'2:140' → {2:140}; '1:147,2:140' → {1:147,2:140}; '140' → None(全组统一,由调用方处理)"""
    if val is None:
        return {}
    m = {}
    for part in val.split(","):
        part = part.strip()
        if ":" in part:
            g, v = part.split(":")
            m[int(g)] = int(v)
        else:
            m["__all__"] = int(part)
    return m

# ---------------- 基础 ----------------
def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"[命令失败] {' '.join(cmd)}\n{r.stderr[:500]}")
    return r.stdout

def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_entries",
               "format=duration:stream=width,height", "-of", "json", path])
    d = json.loads(out)
    w = h = None
    for s in d.get("streams", []):
        if s.get("width"):
            w, h = s["width"], s["height"]; break
    return float(d["format"]["duration"]), w, h

# ---------------- 滚动偏移 ----------------
class Frames:
    def __init__(self, paths):
        self.paths = paths
        self._c = {}
        self.H = None
    def gray(self, i):
        if i not in self._c:
            a = np.asarray(Image.open(self.paths[i]).convert("L"), dtype=np.float32)
            self._c[i] = a
            self.H = a.shape[0]
            if len(self._c) > 24:   # 只缓存最近帧，控制内存
                for k in list(self._c)[:-24]:
                    del self._c[k]
        return self._c[i]

# ---------------- 编码黑边检测与裁除 ----------------
def detect_and_trim_padding(paths):
    """视频编码器会把画面补齐到 8/16 倍数(如 589→592)，补出的纯黑边烙在每帧边缘。
    这里只裁掉编码补边，恢复真实屏幕区域，屏幕内容一个像素不动。"""
    samples = [paths[0], paths[len(paths) // 2], paths[-1]]
    cuts = []
    W0, H0 = Image.open(paths[0]).size
    for p in samples:
        a = np.asarray(Image.open(p).convert("L"), dtype=np.float32)
        H, W = a.shape
        colb, rowb = a.mean(axis=0), a.mean(axis=1)
        l = next((i for i in range(20) if colb[i] > 100), 0)
        t = next((i for i in range(20) if rowb[i] > 100), 0)
        r = next((W - 1 - i for i in range(20) if colb[W - 1 - i] > 100), W - 1) + 1
        b = next((H - 1 - i for i in range(20) if rowb[H - 1 - i] > 100), H - 1) + 1
        cuts.append((l, t, r, b))
    if len(set(cuts)) != 1:
        print("    (!) 三帧边界不一致，保守起见不裁")
        return (0, 0, W0, H0)
    l, t, r, b = cuts[0]
    if (l, t, r, b) == (0, 0, W0, H0):
        return (l, t, r, b)
    for p in paths:
        Image.open(p).crop((l, t, r, b)).save(p)
    return (l, t, r, b)

def shift_of(a, b, cap):
    """b 相对 a 的向下滚动推进像素(内容上移)。搜索上限 cap*H 防满屏假对齐。"""
    H = a.shape[0]
    limit = int(H * cap)
    best, bd = 0, np.abs(a - b).mean()
    s = 2
    while s < limit:
        d = np.abs(a[s:, :] - b[:H - s, :]).mean()
        if d < bd:
            bd, best = d, s
        s += 2
    for s2 in range(max(0, best - 2), min(limit, best + 3)):  # 细化
        d = np.abs(a[s2:, :] - b[:H - s2, :]).mean() if s2 else np.abs(a - b).mean()
        if d < bd:
            bd, best = d, s2
    return best, float(bd)

# ---------------- 内容窗口测量 ----------------
def content_window(fr, seg):
    """段内固定UI(状态栏/导航栏/输入框)不随滚动移动；按行方差找出内容窗口。"""
    if seg[1] - seg[0] < 2:
        # 单帧段(整段无滚动: 末尾静止查看图片/页面等)没有跨帧行方差可比,
        # 行方差全为 0 会被误判为"整屏都是固定区",算出负窗口导致后续越界崩溃。
        # 无法判定固定区时按整帧处理(2026-09-19 实测)。
        return fr.H, 0, 0
    idx = np.linspace(seg[0], seg[1] - 1, min(15, seg[1] - seg[0])).astype(int)
    mat = np.stack([fr.gray(i) for i in idx])
    rowstd = mat.std(axis=0).mean(axis=1)
    fixed = rowstd < 5
    H = fr.H
    top = 0
    while top < H and fixed[top]:
        top += 1
    bot = H - 1
    while bot > 0 and fixed[bot]:
        bot -= 1
    return bot - top + 1, top, H - 1 - bot

# ---------------- 选链 ----------------
def build_chain(fr, adv, mae, seg, W, overlap):
    """段内从首个稳定帧起累加推进，达 (W-overlap) 选帧；末帧并入(若推进过小则替换)。"""
    start = seg[0]
    i = start
    while i < min(seg[1] - 2, start + 20) and mae[i] >= 10:
        i += 1  # 跳过段首过渡/加载帧
    chain = [i]
    acc = 0.0
    T = W - overlap
    while i < seg[1] - 1:
        acc += adv[i]
        if acc >= T:
            chain.append(i + 1)
            acc = 0.0
        i += 1
    last = seg[1] - 1
    if chain[-1] != last:
        gap = sum(adv[chain[-1]:last])
        # gap 小 = 末帧与上一选中帧几乎同画面 → 替换而非追加。
        # 不可加 len(chain)>1 限制：段内推进为 0(整段无滚动,如末尾点开图片静止查看)时
        # chain 只有首帧,该限制会让替换失效,把完全相同的末帧当新帧追加 → 排版出现重复图,
        # 长图拼接时 tops 越界崩溃(2026-09-19 实测)。链只有首帧时同样应替换。
        if gap < 0.15 * W:
            chain[-1] = last      # 末帧与上一选中帧几乎相同 → 替换
        else:
            chain.append(last)    # 正常收尾
    return chain

# ---------------- 排版 ----------------
# 版式参数：per_page → (列, 行, 页面方向)。6 = 3列×2行（微信截图打印宽约6cm，18cm并排放得下A4）
LAYOUTS = {
    1: (1, 1, "P"), 2: (2, 1, "P"), 4: (2, 2, "P"), 6: (3, 2, "P"),
}

def layout(pdf_path, groups, per_page, img_scale=1.0):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from pypdf import PdfReader
    cols, rows, orient = LAYOUTS[per_page]
    PW, PH = landscape(A4) if orient == "L" else A4
    if per_page == 6:
        # 3列×2行：肩并肩无缝隙，且放大时绝不压叠——多余宽度由边距消化（收边距），而非图压图
        # 用户 2026-08-31 定稿：左装订边 1.6cm；img_scale>1 时左边距优先收（可小到 0.63cm）
        BASE_L, BASE_R, MIN_M = 45.4, 39.7, 18.0   # pt：基准边距(1.6/1.4cm)与边距下限(0.63cm)
        extra = (PW - BASE_L - BASE_R) * (img_scale - 1)   # 放大需要的额外宽度
        room = (BASE_L - MIN_M) + (BASE_R - MIN_M)
        if extra > room:
            img_scale = 1 + room / (PW - BASE_L - BASE_R)  # 封顶防压叠（≈1.084）
            extra = (PW - BASE_L - BASE_R) * (img_scale - 1)
            print(f"[提示] img_scale 超出无压叠上限，已自动降至 {img_scale:.3f}")
        M_L = BASE_L - extra * 0.55   # 左边距多收一点（用户要求左侧可放小）
        M_R = BASE_R - extra * 0.45
        M_T, M_B = 14, 20
        G = 0                                      # 肩并肩，无缝隙
        CW = (PW - M_L - M_R - (cols - 1) * G) / cols   # = 170pt × img_scale，图恰好占满不压叠
        CH = (PH - M_T - M_B - (rows - 1) * G) / rows
        x0, y_top = M_L, PH - M_T
    else:
        M, G = 20, 12
        M_B = M
        CW = (PW - 2 * M - G) / 2
        CH = (PH - 2 * M - G - 24) / 2
        x0, y_top = M, PH - M
    font = None
    for p, n in [("/System/Library/Fonts/PingFang.ttc", "PingFang"),
                 ("/System/Library/Fonts/STHeiti Light.ttc", "STHeiti")]:
        try:
            pdfmetrics.registerFont(TTFont(n, p)); font = n; break
        except Exception:
            continue
    c = canvas.Canvas(pdf_path, pagesize=(PW, PH))
    page = 0
    global_seq = 0  # 跨页连续序号（每张图右下角 1,2,3…）
    for gname, frames in groups:
        for s in range(0, len(frames), per_page):
            batch = frames[s:s + per_page]
            page += 1
            # 第一遍：先画全部图片（格子已按 img_scale 扩大且不压叠，图片自适应格子即可）
            placed = []
            for i, p in enumerate(batch):
                iw, ih = Image.open(p).size
                sc = min(CW / iw, CH / ih)  # 格子已含放大（6块模式边距消化宽度），图片等比适配格子
                dw, dh = iw * sc, ih * sc
                col, row = i % cols, i // cols
                x = x0 + col * (CW + G) + (CW - dw) / 2
                y = y_top - (row + 1) * CH - row * G + (CH - dh) / 2
                c.drawImage(p, x, y, width=dw, height=dh)
                global_seq += 1
                placed.append((global_seq, x, y, dw, dh))
            # 第二遍：图全部画完后统一写编号，保证编号永远在最上层
            for tag, x, y, dw, dh in placed:
                s_tag = str(tag)
                tw = c.stringWidth(s_tag, font, 11)
                pad = 3
                bx = x + dw - tw - 2 * pad   # 紧贴图右下角内侧
                by = y + 2
                c.setFillColorRGB(1, 1, 1)
                c.rect(bx, by, tw + 2 * pad, 11 + 2 * pad, stroke=0, fill=1)
                c.setFillColorRGB(0, 0, 0)
                c.setFont(font, 11)
                c.drawString(bx + pad, by + pad, s_tag)
            # 页面底部「组号-页号」页码已取消（用户 2026-08-31：图片已有右下角顺序编号，页面页码冗余）
            c.showPage()
    c.save()
    n = len(PdfReader(pdf_path).pages)
    assert n == page, f"页数不符 {n}!={page}"
    return n

# ---------------- 主流程 ----------------
def main():
    args = parse_args()
    video = os.path.abspath(args.video)
    name = os.path.splitext(os.path.basename(video))[0]
    outdir = args.outdir or os.path.join(os.path.expanduser("~/Desktop"), f"录屏证据_{name}")
    rawdir = os.path.join(outdir, "_raw")
    os.makedirs(rawdir, exist_ok=True)

    dur, w, h = probe(video)
    print(f"[1/6] 侦察: {dur:.1f}s {w}x{h}")

    run(["ffmpeg", "-y", "-v", "error", "-i", video,
         "-vf", f"fps={args.fps}", "-q:v", "1",
         os.path.join(rawdir, "f_%05d.png")])
    paths = sorted(os.path.join(rawdir, f) for f in os.listdir(rawdir) if f.endswith(".png"))
    print(f"[2/6] 密集抽帧 {args.fps}fps: {len(paths)} 帧")

    l, t, r, b = detect_and_trim_padding(paths)
    W0, H0 = Image.open(paths[0]).size
    print(f"    编码黑边裁除: 左{l} 上{t} 右{W0-r} 下{H0-b} → 内容区 {r-l}x{b-t} (仅去编码补边,屏幕内容未动)")

    fr = Frames(paths)
    cap = args.shift_cap
    adv = np.zeros(len(paths)); mae = np.zeros(len(paths))
    for i in range(len(paths) - 1):
        adv[i], mae[i] = shift_of(fr.gray(i), fr.gray(i + 1), cap)
    print("[3/6] 逐帧滚动偏移计算完成")

    # 场景切换: 原地内容突变(shift≈0 且 MAE 高)
    cuts = [i + 1 for i in range(len(paths) - 1) if adv[i] < 8 and mae[i] > args.mae_cut]
    segs, prev = [], 0
    for cpt in cuts:
        if cpt - prev >= args.min_seg * args.fps:
            segs.append((prev, cpt)); prev = cpt
        else:
            prev = cpt if cpt - prev < args.min_seg * args.fps else prev
    segs.append((prev, len(paths)))
    segs = [s for s in segs if s[1] - s[0] >= args.min_seg * args.fps]

    # —— 缺口安全校验(2026-09-19 新增): 被丢弃的碎片段，必须仍被"上一保留段末帧 → 下一保留段首帧"
    #    的重叠覆盖；否则说明中间内容没被采到。典型成因：快速滚动区间的帧间位移超过 shift 搜索上限
    #    (0.6 屏) → 饱和返回 0 → 被误判成"场景切换" → 整段静默丢弃。
    #    命中即把缺口区间恢复为独立段：宁可多一段，不可漏内容。
    recovered = []
    for k in range(len(segs) - 1):
        a, b = segs[k][1] - 1, segs[k + 1][0]     # 上一段末帧索引 / 下一段首帧索引
        if a + 1 == b:
            continue                               # 两段相邻，无缺口
        Wk = content_window(fr, segs[k])[0]
        gap = int(round(sum(adv[a:b])))
        if gap > Wk - 100:                         # 重叠不足 100px = 有内容缺口(定则2)
            print(f"    (!) 组{k+1}末帧→组{k+2}首帧 推进{gap}px ≥ 窗口{Wk}−100px: "
                  f"帧{a+2}-{b} 可能含未采内容 → 已恢复为独立段(宁多不漏)")
            recovered.append((a + 1, b))
    if recovered:
        segs = sorted(segs + recovered)
    print(f"[4/6] 分段: {len(segs)} 个内容段 (切换点帧号 {cuts})")

    groups, report = [], ["帧A -> 帧B : 推进px  衔接px  备注"]
    ft_map, fb_map = parse_fixed_override(args.fixed_top), parse_fixed_override(args.fixed_bottom)
    for gi, seg in enumerate(segs, 1):
        W, fixed_top, fixed_bottom = content_window(fr, seg)
        # 手动覆盖(按组或全组): 白底页面方差检测失效时使用; 覆盖后重算内容窗口
        ft = ft_map.get(gi, ft_map.get("__all__"))
        fb = fb_map.get(gi, fb_map.get("__all__"))
        if ft is not None or fb is not None:
            fixed_top = ft if ft is not None else fixed_top
            fixed_bottom = fb if fb is not None else fixed_bottom
            W = fr.H - fixed_top - fixed_bottom
            print(f"    组{gi}: 手动固定区 上{fixed_top}/下{fixed_bottom} → 内容窗口{W}px")
        chain = build_chain(fr, adv, mae, seg, W, args.overlap)
        groups.append((str(gi), [paths[i] for i in chain]))
        report.append(f"\n—— 组{gi} (帧{seg[0]+1}-{seg[1]}, 内容窗口{W}px, 固定UI上{fixed_top}/下{fixed_bottom}) ——")
        for k in range(len(chain) - 1):
            a, b = chain[k], chain[k + 1]
            total = int(sum(adv[a:b])); ov = W - total
            note = "OK" if 40 <= ov <= 3 * args.overlap else "衔接偏大(录屏此处滚动慢,素材决定)"
            if total >= W:
                note = "!! 超窗口有漏 content 风险"
            report.append(f"{os.path.basename(paths[a])} -> {os.path.basename(paths[b])} : {total}  {ov}  {note}")
        report.append(f"末帧 {os.path.basename(paths[chain[-1]])} (组收尾)")

    # 小样图
    sheet_dir = os.path.join(outdir, "小样图复核")
    shutil.rmtree(sheet_dir, ignore_errors=True); os.makedirs(sheet_dir)
    TW, TH, C, R = 296, 640, 2, 3
    flat = [(gn, p) for gn, fs in groups for p in fs]
    for s in range(0, len(flat), C * R):
        batch = flat[s:s + C * R]
        im = Image.new("RGB", (TW * C + 30, TH * R + 40), "white")
        d = ImageDraw.Draw(im)
        for i, (gn, p) in enumerate(batch):
            t = Image.open(p).resize((TW, TH))
            x, y = 10 + (i % C) * (TW + 10), 10 + (i // C) * (TH + 10)
            im.paste(t, (x, y))
            d.rectangle([x, y, x + TW, y + TH], outline="#888", width=1)
            d.text((x + 4, y + 2), f"组{gn} {os.path.basename(p)}", fill="red")
        im.save(os.path.join(sheet_dir, f"sheet_{s // (C*R) + 1}.png"))

    pdf = os.path.join(outdir, f"录屏证据_{name}_一面{args.per_page}块.pdf")
    # img_scale 默认值：6块版式定稿 1.03（用户 2026-08-31 拍板：6块一律放大3%），其他版式 1.0
    img_scale = args.img_scale if args.img_scale is not None else (1.03 if args.per_page == 6 else 1.0)
    n_pages = layout(pdf, groups, args.per_page, img_scale)

    with open(os.path.join(outdir, "选帧报告.txt"), "w") as f:
        f.write("\n".join(report))
    json.dump({gn: fs for gn, fs in groups},
              open(os.path.join(outdir, "selection.json"), "w"), ensure_ascii=False, indent=1)

    total_imgs = sum(len(fs) for _, fs in groups)
    print(f"[5/6] 排版: {pdf}")
    print(f"[6/6] 自检: {n_pages}页 / {total_imgs}帧 / 分{len(groups)}组  大小 {os.path.getsize(pdf)/1048576:.2f}MB")
    print(f"→ 请人工复核: {sheet_dir}  (小样图过一遍内容连续性)")
    print(f"→ 衔接量明细: {os.path.join(outdir, '选帧报告.txt')}")
    print("→ 还可以生成「完整聊天长图」（内容一条不漏的整条长图，证完整性）：询问用户是否需要，")
    print("  需要则执行: python3 " + os.path.join(os.path.dirname(os.path.abspath(__file__)), "long_image.py") + f" {outdir}")

if __name__ == "__main__":
    main()
