#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pdf_util.py — PDF 抽取页面 / 合并 / 加页码（合并卷宗合集用）

依赖 PyMuPDF(fitz)。仅「合并PDF」步骤需要；不合并时无需调用。
"""
import os, fitz, tempfile


def extract_pages(src_pdf, pages, out_pdf):
    """从 src_pdf 抽取 1-based 页码列表 pages，存为 out_pdf。"""
    doc = fitz.open(src_pdf)
    out = fitz.open()
    for pg in pages:
        if 1 <= pg <= len(doc):
            out.insert_pdf(doc, from_page=pg - 1, to_page=pg - 1)
    out.save(out_pdf)
    out.close()
    doc.close()


def merge_pdfs(file_list, out_pdf):
    """按 file_list 顺序合并为 out_pdf。"""
    out = fitz.open()
    for f in file_list:
        if not os.path.exists(f):
            continue
        d = fitz.open(f)
        out.insert_pdf(d)
        d.close()
    out.save(out_pdf)
    out.close()


_CJK_FONT_CANDIDATES = [
    r'C:/Windows/Fonts/simhei.ttf',
    r'C:/Windows/Fonts/simfang.ttf',
    r'C:/Windows/Fonts/msyh.ttc',
    r'C:/Windows/Fonts/simsun.ttc',
    r'/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
    r'/System/Library/Fonts/PingFang.ttc',
]


def _find_cjk_font():
    for f in _CJK_FONT_CANDIDATES:
        if os.path.exists(f):
            return f
    return None


def add_page_numbers(pdf_path, fmt="第{}页，共{}页", ascii_fmt="{}/{}"):
    """在每页页脚居中加页码。优先用 CJK 字体渲染「第X页，共Y页」；无 CJK 字体时退化为 ASCII。
    保存到临时文件再原子替换，规避 fitz 对同路径增量保存的「加密 / 必须增量」限制。"""
    doc = fitz.open(pdf_path)
    if doc.is_encrypted:
        try:
            doc.authenticate("")
        except Exception:
            pass
    cjk = _find_cjk_font()
    total = doc.page_count
    use_fmt = fmt if cjk else ascii_fmt
    for i, page in enumerate(doc):
        txt = use_fmt.format(i + 1, total)
        kw = dict(fontsize=9, color=(0, 0, 0))
        if cjk:
            kw['fontfile'] = cjk
            try:
                tw = fitz.Font(fontfile=cjk).text_width(txt, 9)
                x = page.rect.width / 2 - tw / 2
            except Exception:
                x = page.rect.width / 2 - 40
        else:
            tw = fitz.Font("helvetica").text_width(txt, 9)
            x = page.rect.width / 2 - tw / 2
        page.insert_text((x, page.rect.height - 30), txt, **kw)
    fd, tmp = tempfile.mkstemp(suffix='.pdf')
    os.close(fd)
    doc.save(tmp)
    doc.close()
    os.replace(tmp, pdf_path)


def to_pdf(src_path, out_pdf, word_app=None):
    """尽量把单份文件转成 PDF（供合并）。.pdf 直接复制；.doc/.docx 用 Word COM；图片用 fitz。
    word_app: 可选，复用已建立的 Word.Application 实例（合并时传入，避免反复启动/断开 COM 导致代理失效）。"""
    ext = src_path.lower().rsplit('.', 1)[-1]
    if ext == 'pdf':
        import shutil
        shutil.copy2(src_path, out_pdf)
        return out_pdf
    if ext in ('doc', 'docx'):
        return _doc_to_pdf_com(src_path, out_pdf, word_app)
    if ext in ('png', 'jpg', 'jpeg', 'bmp', 'tiff'):
        src = fitz.open(src_path)
        try:
            pix = src.load_page(0).get_pixmap()
            d = fitz.open()
            # 新建与图片同尺寸的页面，避免拉伸变形
            d.new_page(width=pix.width, height=pix.height)
            d[0].insert_image(d[0].rect, pixmap=pix)
            d.save(out_pdf)
            d.close()
        finally:
            src.close()
        return out_pdf
    return None


def _doc_to_pdf_com(src_path, out_pdf, word_app=None):
    import win32com.client
    import pythoncom
    # 先尝试用传入的复用实例；若失败（如 RPC 服务器不可用）则新建一个本地实例重试一次
    attempts = []
    if word_app is not None:
        attempts.append(('reuse', word_app))
    attempts.append(('fresh', None))
    last_err = None
    for tag, app in attempts:
        wd = None
        own = False
        doc = None
        try:
            if app is None:
                pythoncom.CoInitialize()
                wd = win32com.client.Dispatch('Word.Application')
                wd.Visible = False
                own = True
            else:
                wd = app
            doc = wd.Documents.Open(src_path)
            doc.SaveAs(out_pdf, FileFormat=17)  # 17 = wdFormatPDF
            doc.Close()
            if own:
                wd.Quit()
            return out_pdf
        except Exception as e:
            last_err = e
            try:
                if doc is not None:
                    doc.Close()
            except Exception:
                pass
            if own and wd is not None:
                try:
                    wd.Quit()
                except Exception:
                    pass
            continue
    return f"[WORD转PDF失败:{last_err}]"
