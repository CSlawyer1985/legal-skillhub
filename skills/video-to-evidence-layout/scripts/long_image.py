#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
long_image.py — 完整聊天长图生成（video-to-evidence-layout 配套独立脚本）

用法:
    python3 long_image.py <record2evidence 输出目录> [--trim-bottom 3]

前置: 主脚本 record2evidence.py 已跑完——需要其 selection.json 与 _raw/ 中间帧;
      人工复核确认前请勿删除 _raw/（已删则重跑主脚本）。

拼接定则(2026-08-30 用户终裁):
    段起点: 帧1 = y 0 (保留状态栏+标题栏); 帧2+ = fixed_top + 与上帧衔接量(跳过重叠区)
    段终点: 内容窗口下沿向上裁 3px 白线 (--trim-bottom, 用户终裁 3px; 曾试 5px 嫌大)
    画布背景: 微信灰 #EDEDED
    内容窗口/衔接量全部从选中帧自适应重算, 不写死分辨率
    校验: 缝 ±1 行 std>40 = 内容行直连无亮线; 总高与理论值对照打印
"""
import argparse, json, os, sys
from collections import Counter
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from record2evidence import Frames, shift_of, content_window


def parse_args():
    ap = argparse.ArgumentParser(description="从主脚本输出目录生成完整聊天长图")
    ap.add_argument("outdir", help="record2evidence.py 的输出目录 (含 selection.json 与 _raw/)")
    ap.add_argument("--trim-bottom", type=int, default=3,
                    help="段底裁除白线像素 (用户终裁 3px)")
    ap.add_argument("--shift-cap", type=float, default=0.6,
                    help="单帧shift搜索上限/屏高 (与主脚本一致, 勿改大——见坑①)")
    ap.add_argument("--fixed-top", default=None,
                    help="手动覆盖固定UI顶部像素; 支持按组: '2:140' 或 '1:147,2:140' (与主脚本保持一致)")
    ap.add_argument("--fixed-bottom", default=None,
                    help="手动覆盖固定UI底部像素; 支持按组: '2:150' 或 '1:139,2:150'")
    return ap.parse_args()


def parse_fixed_override(val):
    """'2:140' → {2:140}; '1:147,2:140' → {1:147,2:140}; '140' → 全组统一"""
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


def fno(p):
    """从 f_00001.png 解析帧号"""
    return int("".join(ch for ch in os.path.basename(p) if ch.isdigit()))


def main():
    args = parse_args()
    outdir = os.path.abspath(args.outdir)
    sel_path = os.path.join(outdir, "selection.json")
    rawdir = os.path.join(outdir, "_raw")
    if not os.path.exists(sel_path):
        sys.exit(f"[缺少] {sel_path} — 请先跑 record2evidence.py")
    if not os.path.isdir(rawdir):
        sys.exit(f"[缺少] {rawdir}/ — 人工复核确认前请勿删除中间帧; 已删则重跑主脚本")

    groups = json.load(open(sel_path))  # {组号: [选中帧绝对路径,...]}
    all_raw = sorted((os.path.join(rawdir, f) for f in os.listdir(rawdir) if f.endswith(".png")),
                     key=fno)
    if not all_raw:
        sys.exit("[空] _raw/ 无帧 — 已删除则重跑主脚本")
    F = Frames(all_raw)
    idx_of = {fno(p): k for k, p in enumerate(all_raw)}
    print(f"[1/3] 载入 {len(all_raw)} 中间帧, {len(groups)} 组选中链")

    # 预扫: 单帧静止段(整段无滚动)没有跨帧行方差可比, 自测不出固定区, 会退化成整帧输出
    # (多带状态栏与输入框区)。从其余组取"众数固定区"兜底(2026-09-19 实测)。
    win_cnt = Counter()
    for gn2 in sorted(groups, key=int):
        ch2 = groups[gn2]
        if len(ch2) < 2:
            continue
        i2 = [idx_of[fno(p)] for p in ch2]
        _W2, ft2, fb2 = content_window(F, (i2[0], i2[-1] + 1))
        if ft2 or fb2:
            win_cnt[(ft2, fb2)] += 1
    common_fixed = None
    if win_cnt:
        (ft_c, fb_c), n_c = win_cnt.most_common(1)[0]
        if n_c >= 2:                  # 至少两组一致才敢外推, 防单一误检被放大
            common_fixed = (ft_c, fb_c)
            print(f"    预扫: 同界面固定区众数 上{ft_c}/下{fb_c}({n_c} 组一致) → 供单帧静止段沿用")

    for gn in sorted(groups, key=int):
        chain = groups[gn]
        sel_idx = [idx_of[fno(p)] for p in chain]

        # 内容窗口(自适应) + 段底裁线; 手动覆盖(按组或全组)后重算
        W, fixed_top, fixed_bottom = content_window(F, (sel_idx[0], sel_idx[-1] + 1))
        ft_map, fb_map = parse_fixed_override(args.fixed_top), parse_fixed_override(args.fixed_bottom)
        gn_int = int(gn)
        ft = ft_map.get(gn_int, ft_map.get("__all__"))
        fb = fb_map.get(gn_int, fb_map.get("__all__"))
        if ft is not None or fb is not None:
            fixed_top = ft if ft is not None else fixed_top
            fixed_bottom = fb if fb is not None else fixed_bottom
            W = F.H - fixed_top - fixed_bottom
            print(f"    (手动固定区 上{fixed_top}/下{fixed_bottom} → 内容窗口{W}px)")
        elif len(sel_idx) < 2 and common_fixed:
            fixed_top, fixed_bottom = common_fixed
            W = F.H - fixed_top - fixed_bottom
            print(f"    (单帧静止段 无跨帧方差可比 → 沿用同界面固定区 "
                  f"上{fixed_top}/下{fixed_bottom} → 内容窗口{W}px)")
        bot = F.H - 1 - fixed_bottom
        bottom_cut = bot + 1 - args.trim_bottom
        print(f"[2/3] 组{gn}: 内容窗口{W}px (固定UI上{fixed_top}/下{fixed_bottom}), 段底裁{args.trim_bottom}px")

        # 相邻选中帧间总推进 = 逐帧小步长累加(全屏搜索必假对齐——坑①)
        totals = []
        for k in range(len(sel_idx) - 1):
            acc = 0.0
            for i in range(sel_idx[k], sel_idx[k + 1]):
                s, _ = shift_of(F.gray(i), F.gray(i + 1), args.shift_cap)
                acc += s
            totals.append(int(round(acc)))
            print(f"    帧{k+1}->帧{k+2}: 推进{totals[-1]}px 衔接{W - totals[-1]}px")

        tops = [0] + [fixed_top + (W - t) for t in totals]
        if any(tp < 0 for tp in tops):
            sys.exit("[!] 存在推进超过内容窗口的衔接(超窗口漏内容风险) — 请查看选帧报告的 !! 标注")

        segs = []
        for k, p in enumerate(chain):
            if tops[k] >= bottom_cut:
                # 与上一帧推进≈0(同画面重复)时 tops 会顶到/越过段底,拼进去既是重复内容又会 crop 越界
                print(f"    [跳过] 帧{k+1}(推进{totals[k-1] if k else 0}px)与上帧同画面,不入长图")
                continue
            im = Image.open(p)
            segs.append(im.crop((0, tops[k], im.width, bottom_cut)))
        total_h = sum(s.height for s in segs)
        long_im = Image.new("RGB", (segs[0].width, total_h), (237, 237, 237))
        y = 0
        for s in segs:
            long_im.paste(s, (0, y))
            y += s.height

        # 缝验证: 白线特征 = 明显亮于画布灰(定则4)。原先的 mean>228 会把微信灰底
        # (实测 234/std≈0)整片误报成白线; 画布填充色与微信聊天页底色同为 #EDEDED(237),
        # 真正的白线行实测 240-242。故以 237+2 为界(2026-09-19 修正)。
        BG = 237.0
        ga = np.asarray(long_im.convert("L"), dtype=np.float32)
        y = 0
        for k in range(len(segs) - 1):
            y += segs[k].height
            up, dn = ga[y - 1], ga[y]
            white = ((up.mean() > BG + 2 and up.std() < 10)
                     or (dn.mean() > BG + 2 and dn.std() < 10))
            print(f"    缝{k+1} y={y}: 上行mean={up.mean():.0f}/std={up.std():.0f} "
                  f"下行mean={dn.mean():.0f}/std={dn.std():.0f} "
                  + ("⚠ 疑似白线,请人工看图" if white else "✓ 无白线"))

        theo = int(sum(totals) + W + fixed_top - len(segs) * args.trim_bottom)
        print(f"[3/3] 总高 {total_h}px (理论 {theo}px, 差 {total_h - theo}px 属测量口径)")

        name = "聊天记录完整长图.png" if len(groups) == 1 else f"聊天记录完整长图_组{gn}.png"
        out_path = os.path.join(outdir, name)
        long_im.save(out_path)
        print(f"→ {out_path}\n")


if __name__ == "__main__":
    main()
