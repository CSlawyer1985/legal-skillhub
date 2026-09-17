# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
#!/usr/bin/env /usr/bin/python3
# -*- coding: utf-8 -*-
"""
发票PDF智能合并脚本
将发票PDF拼版到A4纸上，支持发票+行程单的上下布局
保持文字可选中，自动删除空白尾页，落单发票只占上半张

用法：
  python merge_invoices.py <输入文件夹> <输出文件夹>
"""

import sys
import os
import re
import fitz  # PyMuPDF
from collections import defaultdict

# ── 常量 ──────────────────────────────────────────────────────────────────────
A4_W   = 595.28   # A4 宽度 (pt)
A4_H   = 841.89   # A4 高度 (pt)
HALF_H = A4_H / 2

# 12306 火车票按真实车票尺寸缩放（蓝磁票约 85.6mm×54mm ≈ 243×153pt，横版）
TICKET_W = 243.0
TICKET_H = 153.0

# 左侧预留财务归档打孔区（约 2.5cm ≈ 71pt），火车票一律右移、避开打孔位
PUNCH_MARGIN = 71.0


def get_content_bottom(page) -> float:
    """
    检测页面实际内容底部坐标（跳过尾部空白）。
    用 get_text("dict") 获取所有文字/图片块的 bbox，
    返回最大的 y1 坐标；若页面完全空白则返回 0。
    """
    blocks = page.get_text("dict").get("blocks", [])
    if not blocks:
        return 0.0
    bottom = 0.0
    for b in blocks:
        if b["type"] == 0:          # 文字块
            bottom = max(bottom, b["bbox"][3])
        elif b["type"] == 1:        # 图片块
            bottom = max(bottom, b["bbox"][3])
    return bottom


def is_trivial_page(page, min_lines: int = 3) -> bool:
    """
    判断页面是否只有无意义内容（如仅有页码）。
    若页面文字行数 ≤ min_lines 且内容仅含「页码/第X页」等，视为废页。
    """
    lines = [l.strip() for l in page.get_text().split("\n") if l.strip()]
    if len(lines) > min_lines:
        return False
    # 仅页码类内容（支持"页码：1/1"、"页码： 1 / 1"、"第1页"、"Page 2"等格式）
    page_pat = re.compile(r"^(第?\s*\d+\s*[/\s]*页?|页码\s*[:：]\s*[\d\s/]+|Page\s*\d+)$")
    return all(page_pat.match(l) for l in lines)


def _overlay_widget_annotations(page, src, src_page_idx: int,
                                 offset_x: float, offset_y: float,
                                 scale: float, zoom: float = 4.0):
    """
    检测源页面中的表单字段（widget annotations），例如电子印章/电子签章，
    将它们渲染为高分辨率图像覆盖到目标页面的对应位置上。
    
    这是因为部分PDF的电子印章作为widget annotation实现，
    show_pdf_page() 可能会遗漏它们。
    """
    src_page = src[src_page_idx]
    widgets = list(src_page.widgets()) if src_page.widgets() else []
    for w in widgets:
        rect = w.rect
        if rect.is_empty or rect.is_infinite:
            continue
        # 渲染该区域为高分辨率pixmap
        pix = src_page.get_pixmap(
            matrix=fitz.Matrix(zoom, zoom),
            clip=rect
        )
        # 计算目标位置
        sx = offset_x + rect.x0 * scale
        sy = offset_y + rect.y0 * scale
        sx2 = offset_x + rect.x1 * scale
        sy2 = offset_y + rect.y1 * scale
        page.insert_image(
            fitz.Rect(sx, sy, sx2, sy2),
            pixmap=pix,
            overlay=True
        )


def place_single_invoice(pdf_path: str, output_path: str) -> bool:
    """
    将单个发票放到上半张 A4（与合并时大小一致），下半留空。
    自动检测并覆盖电子印章（widget annotation），保留文字可选中。
    """
    try:
        doc  = fitz.open()
        src  = fitz.open(pdf_path)
        page = doc.new_page(width=A4_W, height=A4_H)

        src_page = src[0]
        margin   = 8
        target   = fitz.Rect(margin, margin, A4_W - margin, HALF_H - margin)

        scale_w = target.width  / src_page.rect.width
        scale_h = target.height / src_page.rect.height
        scale   = min(scale_w, scale_h)

        sw = src_page.rect.width  * scale
        sh = src_page.rect.height * scale
        x  = (A4_W - sw) / 2
        y  = (HALF_H - sh) / 2

        # 先用 show_pdf_page 保留文字可选中
        page.show_pdf_page(fitz.Rect(x, y, x + sw, y + sh), src, 0)

        # 再检测并覆盖电子印章等widget annotation
        _overlay_widget_annotations(page, src, 0, x, y, scale)

        doc.save(output_path)
        doc.close(); src.close()
        return True
    except Exception as e:
        print(f"  ❌ 处理落单发票失败 {pdf_path}: {e}")
        return False


def merge_two_pdfs(pdf1_path: str, pdf2_path: str,
                   output_path: str, layout: str = "vertical") -> bool:
    """
    将两个 PDF 拼合到一张 A4 纸上（保持文字可选中）。
    layout: "vertical"（上下）或 "horizontal"（左右）
    自动检测并覆盖电子印章（widget annotation）。
    """
    try:
        doc  = fitz.open()
        pdf1 = fitz.open(pdf1_path)
        pdf2 = fitz.open(pdf2_path)
        page = doc.new_page(width=A4_W, height=A4_H)

        if layout == "vertical":
            # 上半
            r1 = fitz.Rect(0, 0, A4_W, HALF_H)
            # 下半
            r2 = fitz.Rect(0, HALF_H, A4_W, A4_H)
        else:
            r1 = fitz.Rect(0, 0, A4_W / 2, A4_H)
            r2 = fitz.Rect(A4_W / 2, 0, A4_W, A4_H)

        page.show_pdf_page(r1, pdf1, 0)
        page.show_pdf_page(r2, pdf2, 0)

        # 覆盖widget annotations（电子印章等）
        p1_page = pdf1[0]
        p1_scale_w = r1.width / p1_page.rect.width
        p1_scale_h = r1.height / p1_page.rect.height
        p1_scale = min(p1_scale_w, p1_scale_h)
        _overlay_widget_annotations(page, pdf1, 0, r1.x0, r1.y0, p1_scale)

        p2_page = pdf2[0]
        p2_scale_w = r2.width / p2_page.rect.width
        p2_scale_h = r2.height / p2_page.rect.height
        p2_scale = min(p2_scale_w, p2_scale_h)
        _overlay_widget_annotations(page, pdf2, 0, r2.x0, r2.y0, p2_scale)

        doc.save(output_path)
        doc.close(); pdf1.close(); pdf2.close()
        return True
    except Exception as e:
        print(f"  ❌ 合并失败: {e}")
        return False


def merge_train_tickets(ticket_paths: list, output_path: str,
                        per_page: int = 2) -> bool:
    """
    将 12306 火车票按「真实车票尺寸」（约 8.5cm×5.4cm）缩放到 A4 上，
    一上一下竖向排版：每页至多 per_page 张，第 1 张在上半页、第 2 张在下半页，
    各自在其半页内居中；不足 per_page 张时只占上半页。
    这样沿 A4 水平中线「对半居中」裁剪，正好得到每张独立凭证。
    保留文字可选中，并覆盖电子印章等 widget annotation。
    """
    try:
        doc = fitz.open()
        n_pages = (len(ticket_paths) + per_page - 1) // per_page
        for i in range(0, len(ticket_paths), per_page):
            batch = ticket_paths[i:i + per_page]
            page = doc.new_page(width=A4_W, height=A4_H)
            slot_h = A4_H / per_page
            for j, tp in enumerate(batch):
                src = fitz.open(tp)
                sp = src[0]
                scale = min(TICKET_W / sp.rect.width,
                            TICKET_H / sp.rect.height)
                sw = sp.rect.width * scale
                sh = sp.rect.height * scale
                # 左侧预留打孔区，票在剩余宽度内居中（右移）
                usable_w = A4_W - PUNCH_MARGIN
                x = PUNCH_MARGIN + (usable_w - sw) / 2
                y = j * slot_h + (slot_h - sh) / 2
                page.show_pdf_page(fitz.Rect(x, y, x + sw, y + sh), src, 0)
                _overlay_widget_annotations(page, src, 0, x, y, scale)
                src.close()
        doc.save(output_path)
        doc.close()
        print(f"  ✅ {os.path.basename(output_path)} "
              f"({len(ticket_paths)}张车票, {n_pages}页, 真实车票尺寸, 上下排版)")
        return True
    except Exception as e:
        print(f"  ❌ 火车票合并失败: {e}")
        return False


def merge_invoice_itinerary(invoice_path: str,
                             itinerary_path: str,
                             output_path: str) -> bool:
    """
    发票（小）+ 行程单（大/A4）→ 上下布局拼合
    上半：发票自适应缩放
    下半：行程单按原始尺寸铺排（多页行程单自动续页）
    最后自动删除仅有页码的空白尾页
    """
    try:
        doc      = fitz.open()
        inv      = fitz.open(invoice_path)
        itin     = fitz.open(itinerary_path)
        inv_page = inv[0]

        # 第 1 页：上半放发票
        p_out = doc.new_page(width=A4_W, height=A4_H)

        # ── 上半：发票 ──
        margin    = 8
        target    = fitz.Rect(margin, margin, A4_W - margin, HALF_H - margin)
        scale     = min(target.width  / inv_page.rect.width,
                        target.height / inv_page.rect.height)
        sw = inv_page.rect.width  * scale
        sh = inv_page.rect.height * scale
        x  = (A4_W - sw) / 2
        y  = (HALF_H - sh) / 2
        p_out.show_pdf_page(fitz.Rect(x, y, x + sw, y + sh), inv, 0)

        # 覆盖发票上的电子印章等widget annotation
        _overlay_widget_annotations(p_out, inv, 0, x, y, scale)

        # ── 下半起：铺排行程单 ──
        remaining_y   = HALF_H
        page_idx      = 0
        total_pages   = 1

        while page_idx < len(itin):
            src_page    = itin[page_idx]
            content_btm = get_content_bottom(src_page)
            src_y       = 0.0

            while True:
                avail    = A4_H - remaining_y
                src_rem  = content_btm - src_y
                if src_rem <= 0.5:
                    break
                copy_h = min(avail, src_rem)

                clip = fitz.Rect(src_page.rect.x0,
                                 src_page.rect.y0 + src_y,
                                 src_page.rect.x1,
                                 src_page.rect.y0 + src_y + copy_h)
                dest = fitz.Rect(0, remaining_y,
                                 A4_W, remaining_y + copy_h)
                p_out.show_pdf_page(dest, itin, page_idx, clip=clip)
                src_y       += copy_h
                remaining_y += copy_h

                if remaining_y >= A4_H - 0.5 and src_y < content_btm - 0.5:
                    p_out = doc.new_page(width=A4_W, height=A4_H)
                    total_pages += 1
                    remaining_y = 0.0

            page_idx += 1
            if page_idx < len(itin):
                p_out = doc.new_page(width=A4_W, height=A4_H)
                total_pages += 1
                remaining_y = 0.0

        # ── 删除空白尾页 ──
        if len(doc) > 1 and is_trivial_page(doc[-1]):
            doc.delete_page(-1)
            total_pages -= 1

        doc.save(output_path)
        doc.close(); inv.close(); itin.close()
        print(f"  ✅ {os.path.basename(output_path)} ({total_pages}页)")
        return True

    except Exception as e:
        print(f"  ❌ 合并失败 {invoice_path} + {itinerary_path}: {e}")
        return False


def _extract_group_key(filename: str) -> str:
    """
    从文件名提取分组标识，用于将同一行程的发票和行程单配对。
    优先级：
      1. 【...】括号内文字（如「打车服务-2024年6月」）
      2. 去掉「电子发票.pdf」「电子行程单.pdf」「电子普通发票.pdf」等后缀
    返回的 key 相同 = 同一组
    """
    # 尝试提取【】内的文字作为分组 key
    bracket_match = re.search(r'【([^】]+)】', filename)
    if bracket_match:
        return bracket_match.group(1).strip()

    # 回退：去掉常见后缀，取剩余部分作为 key
    base = re.sub(
        r'(电子发票|电子行程单|电子普通发票|行程报销单)\.pdf$',
        '', filename, flags=re.IGNORECASE
    ).rstrip('-_. ')
    return base or filename


def auto_merge_folder(input_dir: str, output_dir: str):
    """
    自动扫描输入文件夹，按**共同前缀**智能配对发票和行程单并合并。
    配对逻辑：
      - 提取每张 PDF 的「分组标识」（文件名中【】内的文字，或去后缀后的公共部分）
      - 同一标识下的「发票」+「行程单」→ 合并为一个 PDF（上下布局）
      - 无法配对的单独处理（只占上半张 A4）
      - 所有落单发票再自动合并：2 张拼一页 A4，最后一页只占上半张
    保证：一张发票对应一个行程，不会错位。
    """
    os.makedirs(output_dir, exist_ok=True)

    pdfs = sorted([f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")])
    if not pdfs:
        print(f"  ⚠️  {input_dir} 中没有 PDF 文件")
        return

    groups = defaultdict(list)
    solo_files = []   # 收集所有落单发票（非火车票）
    train_solo = []   # 收集 12306 火车票（纯数字文件名 → 按真实车票尺寸排版）

    for pdf_file in pdfs:
        key = _extract_group_key(pdf_file)
        groups[key].append(pdf_file)

    print(f"  📦 共识别 {len(groups)} 组")

    for group_key in sorted(groups.keys()):
        files_in_group = sorted(groups[group_key])

        # 在组内精确分类：用完整后缀判断
        inv_files   = [f for f in files_in_group if f.endswith("电子发票.pdf") or f.endswith("电子普通发票.pdf")]
        itin_files  = [f for f in files_in_group if "行程单" in f or "行程报销单" in f]
        other_files = [f for f in files_in_group if f not in inv_files and f not in itin_files]

        paired = min(len(inv_files), len(itin_files))

        for i in range(paired):
            name = group_key[:30]
            out = os.path.join(output_dir, f"{name}_合并.pdf")
            merge_invoice_itinerary(
                os.path.join(input_dir, inv_files[i]),
                os.path.join(input_dir, itin_files[i]),
                out
            )

        for f in inv_files[paired:] + other_files:
            # 12306 火车票：文件名是纯数字，按真实车票尺寸排版（不铺满A4）
            if re.match(r'^\d+\.pdf$', f):
                train_solo.append(f)
                print(f"  🎫 火车票: {f}")
                continue
            out = os.path.join(output_dir, f)
            place_single_invoice(os.path.join(input_dir, f), out)
            solo_files.append(f)
            print(f"  📄 落单: {f}")

    # 落单发票合并：2 张拼一页 A4，省纸
    if len(solo_files) >= 2:
        print(f"\n  📎 合并 {len(solo_files)} 张落单发票...")
        for i in range(0, len(solo_files) - 1, 2):
            f1 = solo_files[i]
            f2 = solo_files[i + 1]
            out_name = f"落单合并_{i//2 + 1}.pdf"
            out = os.path.join(output_dir, out_name)
            merge_two_pdfs(
                os.path.join(input_dir, f1),
                os.path.join(input_dir, f2),
                out, layout="vertical"
            )
            # 删除已合并的单独文件
            os.remove(os.path.join(output_dir, f1))
            os.remove(os.path.join(output_dir, f2))
            print(f"    ✅ {f1} + {f2} → {out_name}")
        # 最后一张落单的保留（已经是 half-page 格式）
        if len(solo_files) % 2 == 1:
            print(f"    📄 剩余 1 张落单: {solo_files[-1]}")

    # 12306 火车票：按真实车票尺寸（约 8.5×5.4cm）缩放到 A4，不铺满整页
    if train_solo:
        print(f"\n  🎫 合并 {len(train_solo)} 张 12306 火车票（真实车票尺寸，不铺满A4）...")
        for i in range(0, len(train_solo), 2):
            batch = train_solo[i:i + 2]
            out_name = f"12306火车票_合并_{i // 2 + 1}.pdf"
            merge_train_tickets(
                [os.path.join(input_dir, f) for f in batch],
                os.path.join(output_dir, out_name)
            )


# ── CLI 入口 ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    input_dir  = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.isdir(input_dir):
        print(f"❌ 输入文件夹不存在: {input_dir}")
        sys.exit(1)

    print(f"📂 输入: {input_dir}")
    print(f"📂 输出: {output_dir}")
    print("-" * 50)

    auto_merge_folder(input_dir, output_dir)
    print("\n✅ 完成！")
