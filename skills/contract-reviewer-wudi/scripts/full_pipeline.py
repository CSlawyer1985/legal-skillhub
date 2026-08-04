#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docx 工作流引擎
整合所有子引擎的完整合同审查流程：
  1. .doc → .docx 自动转换
  2. 解压 docx
  3. 应用修订和批注
  4. 重新打包为 docx
  5. 生成清洁版
  6. 清理临时文件
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

# 注册命名空间
import xml.etree.ElementTree as ET
ET.register_namespace('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
ET.register_namespace('r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
ET.register_namespace('w14', 'http://schemas.microsoft.com/office/word/2010/wordml')
ET.register_namespace('w15', 'http://schemas.microsoft.com/office/word/2012/wordml')
ET.register_namespace('wpc', 'http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas')
ET.register_namespace('mc', 'http://schemas.openxmlformats.org/markup-compatibility/2006')
ET.register_namespace('wpg', 'http://schemas.microsoft.com/office/word/2010/wordprocessingGroup')
ET.register_namespace('wps', 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape')


# ============================================================
# 工具函数
# ============================================================

def log(msg, level="INFO"):
    print(f"[{level}] {msg}", file=sys.stderr)


def run_cmd(cmd, cwd=None):
    """执行 shell 命令"""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        log(f"命令失败: {cmd}", "ERROR")
        log(f"错误: {result.stderr}", "ERROR")
        return False
    return True


# ============================================================
# .doc → .docx 转换
# ============================================================

def convert_doc_to_docx(doc_path: Path) -> Optional[Path]:
    """将 .doc 转换为 .docx，使用 macOS 的 textutil 或 Python-docx"""
    if doc_path.suffix.lower() != '.doc':
        return doc_path  # 非 .doc 文件直接返回

    docx_path = doc_path.with_suffix('.docx')

    # 检查是否已存在 .docx
    if docx_path.exists():
        log(f"使用已有的 .docx: {docx_path}")
        return docx_path

    log(f"检测到 .doc 文件，尝试转换: {doc_path}")

    # 尝试 textutil（macOS 内置）
    if sys.platform == 'darwin':
        try:
            result = subprocess.run(
                ['textutil', '-convert', 'docx', '-output', str(docx_path), str(doc_path)],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0 and docx_path.exists():
                log(f"textutil 转换成功: {docx_path}")
                return docx_path
        except Exception as e:
            log(f"textutil 转换失败: {e}")

    # 尝试 LibreOffice
    soffice = shutil.which('soffice')
    if soffice:
        try:
            result = subprocess.run(
                [soffice, '--headless', '--convert-to', 'docx', '--outdir',
                 str(doc_path.parent), str(doc_path)],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                log(f"LibreOffice 转换成功: {docx_path}")
                return docx_path
        except Exception as e:
            log(f"LibreOffice 转换失败: {e}")

    log("无法转换 .doc 文件，请手动转换为 .docx 后重试", "ERROR")
    return None


# ============================================================
# docx 解压与打包
# ============================================================

def unpack_docx(docx_path: Path, output_dir: Path) -> bool:
    """解压 docx 文件"""
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    try:
        with zipfile.ZipFile(docx_path, 'r') as zf:
            zf.extractall(output_dir)
        log(f"解压成功: {output_dir}")
        return True
    except Exception as e:
        log(f"解压失败: {e}", "ERROR")
        return False


def pack_docx(doc_dir: Path, output_path: Path) -> bool:
    """打包 docx 文件"""
    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(doc_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(doc_dir)
                    zf.write(file_path, arcname)
        log(f"打包成功: {output_path}")
        return True
    except Exception as e:
        log(f"打包失败: {e}", "ERROR")
        return False


# ============================================================
# 修订与批注
# ============================================================

def apply_changes(doc_dir: Path, changes_json: Path,
                  original_docx: Optional[Path] = None) -> dict:
    """
    应用修订和批注。

    步骤 3.5（内置预检验）：
      - 格式错误（扁平 vs 标准）→ 自动转换并覆盖原文件
      - 匹配失败（score < 15）→ 自动修正段落索引 + 生成 _fixed.json，退出让用户用修正版重跑
      - 全部通过 → 继续执行 apply_changes.py

    参数:
      doc_dir: unpack 后的 docx 目录（含 word/document.xml）
      changes_json: changes.json 路径
      original_docx: 原始 docx 路径（用于预检验；默认取 doc_dir 同级的 .docx 文件）
    """
    sys.path.insert(0, str(Path(__file__).parent))
    from apply_changes import apply_changes as _apply_changes

    json_path  = Path(changes_json).resolve()
    json_dir   = json_path.parent

    # 推断原始 docx 路径（优先用显式传入的，否则取 unpack 同级的同名 docx）
    if original_docx:
        docx_path = Path(original_docx).resolve()
    else:
        # unpack_dir 通常是 .tmp_unpack/，同级找同名 .docx
        docx_candidates = list(json_dir.glob('*.docx'))
        docx_path = docx_candidates[0] if docx_candidates else None

    # ── 预检验（静默模式，不打断正常流程）───────────────────────
    try:
        from preflight_check import (
            detect_json_format, normalize_changes,
            try_match, get_paragraphs, run_preflight
        )
        import json

        raw = json.loads(json_path.read_text(encoding='utf-8'))
        fmt = detect_json_format(raw)

        # 扁平结构 → 直接覆盖为标准格式
        if fmt == 'flat':
            log("⚠️  检测到扁平格式，自动转换为标准格式...")
            normalized = normalize_changes(raw)
            json_path.write_text(
                json.dumps(normalized, ensure_ascii=False, indent=2), encoding='utf-8')
            log(f"  → 已覆盖为标准格式: {json_path.name}")
            raw = normalized

        # 有原始 docx 才做匹配度检查
        if docx_path and docx_path.exists():
            paras  = get_paragraphs(docx_path)
            issues = []

            for src_key in ('revisions', 'comments'):
                for item in raw.get(src_key, []):
                    idx  = item.get('paragraph_index')
                    orig = item.get('original_text', item.get('highlight_text', ''))
                    para_text = next((p['text'] for p in paras if p['index'] == idx), '')
                    score, reason = try_match(para_text, orig)
                    if score < 15:
                        issues.append((idx, orig[:40], reason))

            if issues:
                log(f"⚠️  {len(issues)} 条匹配失败 → 自动生成修正版...")
                # 修正每条：扫描全文找最佳匹配段落
                for src_key in ('revisions', 'comments'):
                    for item in raw.get(src_key, []):
                        orig = item.get('original_text', item.get('highlight_text', ''))
                        best_idx, best_score = item.get('paragraph_index', 0), 0
                        for p in paras:
                            s, _ = try_match(p['text'], orig)
                            if s > best_score:
                                best_score, best_idx = s, p['index']
                        item['paragraph_index'] = best_idx

                fixed_path = json_dir / f"{json_path.stem}_fixed.json"
                fixed_path.write_text(
                    json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
                log(f"  → 已生成: {fixed_path.name}")
                return {
                    'success': False,
                    'error': (
                        f'{len(issues)} 条文本匹配失败，已生成 {fixed_path.name}。'
                        f'\n请重新运行 pipeline 使用修正版:\n'
                        f'  python3 full_pipeline.py <原文件.docx> {fixed_path}'
                    )
                }
        else:
            log("⚠️  未找到原始 docx，跳过预检验匹配验证")

    except Exception as e:
        log(f"⚠️  预检验跳过（不影响主流程）: {e}")

    # 预检验通过或跳过 → 执行实际写入
    return _apply_changes(doc_dir, changes_json, dry_run=False)


# ============================================================
# 生成清洁版
# ============================================================

def generate_clean(revised_path: Path, clean_path: Path) -> bool:
    """生成清洁版 - 带备用方案"""
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from generate_clean import process_docx as _process_docx
        _process_docx(str(revised_path), str(clean_path), mode='accept_and_remove_comments')
        return True
    except Exception as e:
        log(f"主清洁版生成失败: {e}", "WARN")
        # 备用方案：使用 LibreOffice 命令行
        try:
            import subprocess
            import tempfile
            import shutil
            with tempfile.TemporaryDirectory() as tmpdir:
                # 复制修订版到临时目录
                tmp_input = Path(tmpdir) / revised_path.name
                shutil.copy(revised_path, tmp_input)
                # 使用 LibreOffice 转换为 PDF 再转回 docx（会丢失修订痕迹）
                cmd = f'libreoffice --headless --convert-to docx --outdir "{tmpdir}" "{tmp_input}" 2>/dev/null'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    converted = Path(tmpdir) / tmp_input.stem.replace('-审查版', '') / '.docx'
                    if converted.exists():
                        shutil.copy(converted, clean_path)
                        log("使用 LibreOffice 备用方案生成清洁版", "INFO")
                        return True
        except FileNotFoundError:
            log("", "WARN")
            log("⚠️  未检测到 LibreOffice，无法自动生成清洁版", "WARN")
            log("", "WARN")
            log("请选择以下方案之一：", "WARN")
            log("  方案1 [推荐]: brew install libreoffice", "WARN")
            log("  方案2: 在 Word 中手动操作：审阅 → 接受 → 接受所有修订", "WARN")
            log("  方案3: 将修订痕迹版发给我，我帮你处理", "WARN")
            log("", "WARN")
            return False
        except Exception as e2:
            log(f"备用方案也失败: {e2}", "WARN")
        # 最终备用：提供手动指引
        log("", "WARN")
        log("⚠️  清洁版自动生成失败，请手动操作：", "WARN")
        log("  1. 在 Word 中打开修订批注版", "WARN")
        log("  2. 审阅 → 接受 → 接受所有修订", "WARN")
        log("  3. 另存为清洁版", "WARN")
        log("", "WARN")
        return False


# ============================================================
# PDF / 扫描件检测与处理
# ============================================================

def _detect_file_type(path: Path) -> str:
    """
    推断文件类型。
    返回: 'pdf_scanned' | 'pdf_text' | 'doc' | 'docx' | 'unknown'
    """
    suffix = path.suffix.lower()
    if suffix == '.pdf':
        # 读取 PDF 前1KB检测是否为文本型
        try:
            with open(path, 'rb') as f:
                header = f.read(1024)
            # 文本型 PDF 包含 BT...ET 文本块标记
            if b'BT' in header or b'/Type /Page' in header:
                return 'pdf_text'
            # 扫描型 PDF 可能是纯图像流
            if b'Image' in header or b'/Subtype /Image' in header:
                return 'pdf_scanned'
            return 'pdf_scanned'  # 默认保守处理
        except Exception:
            return 'pdf_scanned'
    elif suffix == '.doc':
        return 'doc'
    elif suffix == '.docx':
        return 'docx'
    return 'unknown'


def _process_scanned_pdf(pdf_path: Path, output_dir: Path) -> Optional[Path]:
    """
    将扫描件 PDF 转换为 docx。
    优先使用 macOS 原生 Vision 框架（无需安装 tesseract），
    失败则回退 pytesseract。
    返回生成的 docx 路径，或 None（失败）。
    """
    import platform
    sys_plat = platform.system()

    # ── 方案A：macOS Vision 框架（零依赖）────────────────
    if sys_plat == 'Darwin':
        try:
            _ocr_via_vision(pdf_path, output_dir)
            stem = pdf_path.stem
            docx_out = output_dir / f'{stem}-ocr.docx'
            if docx_out.exists():
                log(f"Vision OCR 成功: {docx_out}")
                return docx_out
        except Exception as e:
            log(f"Vision OCR 失败（尝试下一方案）: {e}")

    # ── 方案B：pytesseract（需 pip install）──────────────
    try:
        import pytesseract
        import fitz  # PyMuPDF
        from PIL import Image
        import pdf2image
        _ocr_via_tesseract(pdf_path, output_dir)
        stem = pdf_path.stem
        docx_out = output_dir / f'{stem}-ocr.docx'
        if docx_out.exists():
            log(f"Tesseract OCR 成功: {docx_out}")
            return docx_out
    except ImportError as ie:
        log(f"缺少依赖（tesseract/pytesseract/pymupdf）: {ie}", "WARN")
    except Exception as e:
        log(f"Tesseract OCR 失败: {e}", "WARN")

    return None


def _ocr_via_vision(pdf_path: Path, output_dir: Path):
    """
    使用 macOS Vision 框架对 PDF 逐页 OCR，
    生成 docx 文件。
    """
    import platform
    if platform.system() != 'Darwin':
        raise RuntimeError("Vision OCR 仅支持 macOS")

    try:
        import Vision
        import AppKit
        from PDFKit import PDFDocument
    except ImportError:
        raise RuntimeError("PyObjC Vision 未安装（pip install pyobjc-core pyobjc）")

    url = AppKit.NSURL.fileURLWithPath_(str(pdf_path))
    pdf_doc = PDFDocument.alloc().initWithURL_(url)
    if pdf_doc is None:
        raise RuntimeError(f"无法读取 PDF: {pdf_path}")

    pages = pdf_doc.pageCount()
    log(f"PDF 共 {pages} 页，开始 Vision OCR...")

    all_text = []
    for i in range(pages):
        page = pdf_doc.pageAtIndex_(i)
        media_box = page.boundsForBox_(0)  # kPDFDisplayBoxMediaBox

        # Render page to image (300 DPI)
        scale = 300 / 72.0
        width = int(media_box.size.width * scale)
        height = int(media_box.size.height * scale)
        if width <= 0 or height <= 0:
            continue

        img_rep = AppKit.NSBitmapImageRep.alloc()
        img_rep.initWithBitmapDataPixelsWide_high_perBandRow_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
            width, height, 1, 8, 4, False, False,
            AppKit.NSDeviceRGBColorSpace, 0, 32
        )

        img_rep.getBitmapDataRepresentation_(img_rep.bitmapImageRepresentationCache())
        # Use PDFKit's view to draw
        view_class = AppKit.NSView
        view = view_class.alloc().init()

        # Draw PDF page into bitmap
        NSGraphicsContext = AppKit.NSGraphicsContext
        ctx = NSGraphicsContext.graphicsContextWithBitmapImageRep_(img_rep)
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.setCurrentContext_(ctx)
        ctx.saveGraphicsState()
        ctx.translateXBy_yBy_(0, height)
        ctx.scaleXBy_yBy_(scale, -scale)
        page.drawWithBox_toContext_(0, ctx)
        ctx.restoreGraphicsState()
        NSGraphicsContext.restoreGraphicsState()

        img = NSBitmapImageRep_NSImage_(img_rep)

        # OCR with Vision
        VisionFramework = AppKit.NSVisionNotification
        request = AppKit.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(1)  # Accurate
        request.setRecognitionLanguages_(['zh-Hans', 'en-US'])
        request.setUsesLanguageCorrection_(True)

        handler = AppKit.VNImageRequestHandler.alloc().initWithData_options_(
            img.tiffRepresentation(), {}
        )
        handler.performRequests_error_([request], None)

        results = request.results()
        page_text = []
        for r in results or []:
            page_text.append(r.topCandidates_(1)[0].string())
        all_text.append('\n'.join(page_text))
        if (i + 1) % 5 == 0:
            log(f"  已处理 {i+1}/{pages} 页")

    # Write to docx
    stem = pdf_path.stem
    docx_out = output_dir / f'{stem}-ocr.docx'
    _write_text_to_docx('\n\n'.join(all_text), docx_out)
    log(f"Vision OCR 完成，共 {pages} 页，文本长度 {sum(len(t) for t in all_text)} 字符")


def NSBitmapImageRep_NSImage_(rep):
    """Convert NSBitmapImageRep to NSImage."""
    import AppKit
    img = AppKit.NSImage.alloc().init()
    img.addRepresentation_(rep)
    return img


def _ocr_via_tesseract(pdf_path: Path, output_dir: Path):
    """使用 pytesseract + PyMuPDF 对 PDF OCR"""
    import pytesseract
    import fitz
    from PIL import Image
    import pdf2image

    doc = fitz.open(str(pdf_path))
    pages = doc.page_count
    log(f"PDF 共 {pages} 页，开始 Tesseract OCR...")

    all_text = []
    for i in range(pages):
        page = doc[i]
        mat = fitz.Matrix(2.0, 2.0)  # 2x resolution
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes('png')
        from io import BytesIO
        img = Image.open(BytesIO(img_data))
        text = pytesseract.image_to_string(img, lang='chi_sim+eng')
        all_text.append(text)
        if (i + 1) % 5 == 0:
            log(f"  已处理 {i+1}/{pages} 页")

    stem = pdf_path.stem
    docx_out = output_dir / f'{stem}-ocr.docx'
    _write_text_to_docx('\n\n'.join(all_text), docx_out)
    doc.close()
    log(f"Tesseract OCR 完成，共 {pages} 页")


def _write_text_to_docx(text: str, output_path: Path):
    """将纯文本写入 docx（零依赖：仅用标准库 zipfile + xml）"""
    body_xml = []
    for para in text.split('\n'):
        escaped = (para
                   .replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;'))
        body_xml.append(
            f'<w:p><w:pPr/><w:r><w:t xml:space="preserve">{escaped}</w:t></w:r></w:p>'
        )

    doc_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
            xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">
  <w:body>
    {''.join(body_xml)}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1800" w:bottom="1440" w:left="1800"/>
    </w:sectPr>
  </w:body>
</w:document>'''

    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml"
            ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''

    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>'''

    import zipfile
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('word/document.xml', doc_xml)
        zf.writestr('word/_rels/document.xml.rels', rels)


# ============================================================
# 修订模式注入
# ============================================================

def _enable_track_revisions(doc_dir: Path) -> None:
    """
    根据 Word 2016 原生 track changes 文档的真实 settings.xml 分析：
    - Word 2016 原生参考文档中 settings.xml 没有 <w:trackRevisions/>
      也没有 <w:revisionView>——Word 靠内容中的 w:del/w:ins 元素自动识别修订。
    - 本函数只做一件事：将 compat mode 设为 14（Word 2010 兼容），与 Word 原生一致。
    - 如果已经存在更低的 compat mode（14），不再重复修改。
    """
    settings_path = doc_dir / 'word' / 'settings.xml'
    if not settings_path.exists():
        return
    text = settings_path.read_text('utf-8')
    # 只保留 compat mode=14 的设置，去掉 trackRevisions/revisionView（如果之前加过）
    # 移除可能存在的旧版 trackRevisions 和 revisionView
    text = text.replace('<w:trackRevisions/>', '')
    text = text.replace('<w:revisionView w:markup="1" w:comments="1" w:attr="1" w:formatting="1" w:inkAnnotations="1"/>', '')
    # 把 compat mode 统一为 14
    text = re.sub(
        r'(<w:compatSetting w:name="compatibilityMode" w:uri="[^"]*" w:val=")15(")',
        r'\g<1>14\2',
        text
    )
    settings_path.write_text(text, 'utf-8')


# ============================================================
# 主工作流
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='合同审查完整工作流：解析 → 审核 → 生成修订批注版 → 生成清洁版'
    )
    parser.add_argument('input', help='输入文件 (.doc 或 .docx)')
    parser.add_argument('changes_json', help='变更指令 JSON 文件')
    parser.add_argument('--output-dir', '-o', help='输出目录（默认与输入文件同目录）')
    parser.add_argument('--suffix', default='-修订痕迹版', help='输出文件后缀（默认：-修订痕迹版）')
    parser.add_argument('--keep-tmp', action='store_true', help='保留临时解压目录')

    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        log(f"文件不存在: {input_path}", "ERROR")
        sys.exit(1)

    # 确定输出目录
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = input_path.parent

    output_dir.mkdir(parents=True, exist_ok=True)

    # 步骤 0：检测并处理 PDF / 扫描件
    detected_type = _detect_file_type(input_path)
    if detected_type == 'pdf_scanned':
        log("检测到 PDF 扫描件，调用 OCR 处理...")
        ocr_result = _process_scanned_pdf(input_path, output_dir)
        if ocr_result is None:
            log("PDF OCR 处理失败，请先将 PDF 转换为 docx 后重试", "ERROR")
            sys.exit(1)
        # OCR 成功后，用生成的 docx 继续流程
        input_path = ocr_result
        log(f"OCR 转换成功，使用生成的文件: {input_path}")

    # 步骤 1：.doc → .docx 转换
    log("步骤 1/7: 文件格式转换")
    working_docx = convert_doc_to_docx(input_path)
    if not working_docx:
        sys.exit(1)

    # 步骤 2：解压
    log("步骤 2/7: 解压 docx")
    unpack_dir = output_dir / '.tmp_unpack'
    if not unpack_docx(working_docx, unpack_dir):
        sys.exit(1)

    # 步骤 2.5: 读取修订痕迹（对方 Word 修订版）
    try:
        tracked = apply_changes_mod.parse_tracked_changes(source_docx)
        if tracked['total'] > 0:
            log(f"📋 修订痕迹: 检测到 {tracked['total']} 处变更 "
                f"({len(tracked['insertions'])} 处新增 / {len(tracked['deletions'])} 处删除)")
            for ins in tracked['insertions'][:3]:
                log(f"  ➕ [{ins['author']}] {ins['text']}")
            for d in tracked['deletions'][:3]:
                log(f"  ➖ [{d['author']}] {d['text']}")
    except Exception as e:
        log(f"⚠️ 修订痕迹读取失败（不影响正常流程）: {e}")

    # 步骤 3：应用修订和批注
    log("步骤 3/7: 应用修订和批注")
    changes_path = Path(args.changes_json).resolve()
    if not changes_path.exists():
        log(f"变更文件不存在: {changes_path}", "ERROR")
        sys.exit(1)

    result = apply_changes(unpack_dir, changes_path, original_docx=working_docx)
    if not result.get('success'):
        log(f"应用变更失败: {result}", "ERROR")
        sys.exit(1)

    # ── 启用修订模式（settings.xml 注入 trackRevisions）─────────
    _enable_track_revisions(unpack_dir)

    # 步骤 4：打包修订批注版
    log("步骤 4/7: 打包修订批注版")
    stem = input_path.stem
    revised_path = output_dir / f"{stem}{args.suffix}.docx"
    if not pack_docx(unpack_dir, revised_path):
        sys.exit(1)

    # 步骤 5：生成清洁版
    log("步骤 5/7: 生成清洁版")
    clean_path = output_dir / f"{stem}{args.suffix}-清洁版.docx"
    if not generate_clean(revised_path, clean_path):
        log("生成清洁版失败，继续生成修订批注版", "WARN")

    # 步骤 6：清理临时文件
    log("步骤 6/7: 清理临时文件")
    if not args.keep_tmp:
        shutil.rmtree(unpack_dir)
        # 删除中间转换的 .docx（如果是由 .doc 转换来的）
        if working_docx != input_path and working_docx.suffix == '.docx':
            # 不删除转换后的 docx，保留给用户使用
            pass

    # 步骤 6.5: 生成审核报告
    log("步骤 6.5/7: 生成审核报告")
    report_path = output_dir / f"{stem}-审核报告.md"
    generate_review_report(changes_path, result, report_path, input_path.name)

    # 步骤 6.6: 生成修订对比表（可选）
    try:
        from generate_comparison import generate_comparison_file
        comparison_path = output_dir / f"{stem}-修订对比.md"
        stance = args.stance if hasattr(args, 'stance') else '甲方'
        round_num = args.round if hasattr(args, 'round') else 1
        if generate_comparison_file(changes_path, comparison_path, stance, round_num):
            log(f"对比表已生成: {comparison_path.name}")
    except ImportError:
        log("generate_comparison.py 未找到，跳过对比表生成", "INFO")
    except Exception as e:
        log(f"对比表生成失败: {e}", "WARN")

    # 步骤 7：清理临时文件
    log("步骤 7/7: 清理临时文件")
    if not args.keep_tmp:
        shutil.rmtree(unpack_dir)
        # 删除中间转换的 .docx（如果是由 .doc 转换来的）
        if working_docx != input_path and working_docx.suffix == '.docx':
            # 不删除转换后的 docx，保留给用户使用
            pass

    # 输出结果
    print("\n" + "=" * 60)
    print("合同审查完成！")
    print("=" * 60)
    print(f"修订痕迹版: {revised_path}")
    if clean_path.exists():
        print(f"清洁版: {clean_path}")
    print(f"审核报告: {report_path}")
    print("-" * 60)
    print(f"修订: {result.get('total_revisions', 0)} 处")
    print(f"批注: {result.get('total_comments', 0)} 处")
    applied = [c for c in result.get('comments_added', []) if 'error' not in c]
    failed = [c for c in result.get('comments_added', []) if 'error' in c]
    if failed:
        print(f"批注失败: {len(failed)} 处（文本匹配问题）")
    print("=" * 60)


def generate_review_report(changes_json: Path, result: dict, output_path: Path, original_name: str):
    """自动生成审核报告"""
    try:
        with open(changes_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        revisions = data.get('revisions', [])
        comments = data.get('comments', [])
        
        # 统计风险等级
        high_risk = [r for r in revisions if r.get('severity') == '高风险']
        medium_risk = [r for r in revisions if r.get('severity') == '中风险']
        low_risk = [r for r in revisions if r.get('severity') == '低风险']
        
        report = f"""# 合同审核报告

**合同名称**: {original_name}  
**审核日期**: {datetime.now().strftime('%Y-%m-%d')}  
**审核人**: {data.get('author', 'AI审核')}

---

## 一、审核概况

本次审核共发现 **{len(revisions)}处修订建议**（含{len(comments)}条批注）：

| 风险等级 | 数量 | 说明 |
|---------|------|------|
| 🔴 **高风险** | {len(high_risk)}处 | 必须修改，可能导致重大损失或法律风险 |
| 🟡 **中风险** | {len(medium_risk)}处 | 建议修改，可能引发争议或不利解释 |
| 🟢 **低风险** | {len(low_risk)}处 | 可选修改，表述不当但不影响实质权利 |

---

## 二、高风险问题清单

"""
        
        newline = chr(10)
        for i, rev in enumerate(high_risk, 1):
            first_line = rev.get('comment', '').split(newline)[0].replace('【修订批注-高风险】', '').replace('【修订方式：', ' ').replace('】', '')
            report += f"""### {i}. {first_line}

**原文**: {rev.get('original_text', '')[:80]}...

**修订**: {rev.get('revised_text', '')[:80]}...

**风险说明**: {rev.get('comment', '').split(newline+newline)[-1] if (newline+newline) in rev.get('comment', '') else rev.get('comment', '')}

---

"""
        
        if medium_risk:
            report += "## 三、中风险问题清单\n\n"
            for i, rev in enumerate(medium_risk, 1):
                report += f"{i}. **{rev.get('original_text', '')[:40]}...** → {rev.get('revised_text', '')[:40]}...\n\n"
        
        if low_risk:
            report += "\n## 四、低风险问题清单\n\n"
            for i, rev in enumerate(low_risk, 1):
                report += f"{i}. {rev.get('original_text', '')[:40]}...\n\n"
        
        if comments:
            report += "\n## 五、待填项提示\n\n"
            for cmt in comments:
                report += f"- **第{cmt.get('paragraph_index')}段**: {cmt.get('comment', '')}\n"
        
        report += f"""

---

## 六、输出文件

| 文件 | 说明 |
|------|------|
| `{original_name.replace('.docx', '')}-修订痕迹版.docx` | 含修订痕迹（Track Changes）和批注气泡 |
| `{original_name.replace('.docx', '')}-审核报告.md` | 本报告 |

**使用说明**:
1. 在 Word 中打开"修订痕迹版"，在"审阅"选项卡中查看所有修订
2. 逐条审阅修订内容，选择"接受"或"拒绝"
3. 填写空白待填项（合同编号、日期、代表人信息等）
4. 接受所有修订后即为清洁版，可用于签署

---

**审核结论**: 本合同存在{len(high_risk)}处高风险问题，建议在签署前按修订意见修改完善。
"""
        
        output_path.write_text(report, encoding='utf-8')
        log(f"审核报告已生成: {output_path.name}")
    except Exception as e:
        log(f"生成审核报告失败: {e}", "WARN")


if __name__ == '__main__':
    main()
