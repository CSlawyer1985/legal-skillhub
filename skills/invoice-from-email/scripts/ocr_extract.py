# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能三级 PDF 文本提取脚本（MinerU 降级备选）

自动选择最佳可用方法提取 PDF 文字：
  Level 1 — PyMuPDF 直接读文字层（零额外依赖，覆盖 90%+ 电子发票）
  Level 2 — Tesseract OCR（需 brew install tesseract tesseract-lang，~50MB）
  Level 3 — PaddleOCR（需完整安装 PaddlePaddle+PaddleOCR，~600MB，最佳中文精度）

用法：
  python ocr_extract.py <pdf_path> <output_md_path>

输出格式与 MinerU 一致（纯文本 Markdown），供上游工作流解析。
"""

import sys
import os
import fitz  # PyMuPDF


# ── Level 1: PyMuPDF 直接文字层提取 ──────────────────────────────────────────

def extract_text_layer(pdf_path: str) -> str:
    """
    读取 PDF 内嵌文字层（非 OCR，直接取文字）。
    绝大多数中国电子发票是文字型 PDF，此方法秒级提取。
    返回空字符串表示无文字层（可能是扫描件）。
    """
    doc = fitz.open(pdf_path)
    parts = []
    for i, page in enumerate(doc):
        text = page.get_text().strip()
        if text:
            parts.append(f"## 第 {i + 1} 页\n\n{text}")
    doc.close()
    return "\n\n".join(parts)


def is_text_rich(text: str, min_chars: int = 80) -> bool:
    """判断提取的文字是否足够丰富（排除纯空白/乱码页）。"""
    return len(text.strip()) >= min_chars


# ── Level 2: Tesseract OCR ───────────────────────────────────────────────────

def _tesseract_available() -> bool:
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def extract_tesseract(pdf_path: str, dpi: int = 300) -> str:
    """
    用 Tesseract OCR 识别（需 tesseract + chi_sim 语言包）。
    dpi=300 是 Tesseract 推荐的最低精度。
    """
    import pytesseract
    from PIL import Image
    import io

    doc = fitz.open(pdf_path)
    parts = []
    for i, page in enumerate(doc):
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img, lang="chi_sim+eng").strip()
        if text:
            parts.append(f"## 第 {i + 1} 页\n\n{text}")
    doc.close()
    return "\n\n".join(parts)


# ── Level 3: PaddleOCR ───────────────────────────────────────────────────────

def _paddleocr_available() -> bool:
    try:
        from paddleocr import PaddleOCR
        return True
    except ImportError:
        return False


def _get_paddleocr():
    """单例模式加载 PaddleOCR，首次调用下载模型（约 10-30 秒）。"""
    if not hasattr(_get_paddleocr, "_ocr"):
        from paddleocr import PaddleOCR
        _get_paddleocr._ocr = PaddleOCR(lang="ch")
    return _get_paddleocr._ocr


def extract_paddleocr(pdf_path: str, dpi: int = 200) -> str:
    """
    用 PaddleOCR v6 识别（需 PaddlePaddle + PaddleOCR，~600MB）。
    中文精度最高，适合复杂布局的扫描件。
    """
    doc = fitz.open(pdf_path)
    ocr = _get_paddleocr()
    parts = []
    for i, page in enumerate(doc):
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        result = ocr.ocr(pix.tobytes("png"))
        if not result or not result[0]:
            continue
        lines = [line[1][0] for line in result[0] if line[1][1] > 0.5]
        if lines:
            parts.append(f"## 第 {i + 1} 页\n\n" + "\n".join(lines))
    doc.close()
    return "\n\n".join(parts)


# ── 主逻辑：自动三级降级 ─────────────────────────────────────────────────────

def extract_pdf(pdf_path: str) -> tuple:
    """
    自动选择最佳方法提取 PDF 文字。
    返回 (text, method_name)。
    """
    # Level 1: PyMuPDF 文字层（最快，零依赖）
    text = extract_text_layer(pdf_path)
    if is_text_rich(text):
        return text, "PyMuPDF 文字层"

    # Level 2: Tesseract（轻量，需独立安装）
    if _tesseract_available():
        text = extract_tesseract(pdf_path)
        if is_text_rich(text, min_chars=30):
            return text, "Tesseract OCR"

    # Level 3: PaddleOCR（重量，最佳中文精度）
    if _paddleocr_available():
        text = extract_paddleocr(pdf_path)
        if is_text_rich(text, min_chars=30):
            return text, "PaddleOCR"

    return "", "（所有方法均失败）"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2]

    if not os.path.exists(pdf_path):
        print(f"❌ 文件不存在: {pdf_path}")
        sys.exit(1)

    filename = os.path.basename(pdf_path)
    print(f"🔍 提取: {filename}")

    text, method = extract_pdf(pdf_path)
    print(f"  📍 方法: {method}")

    if not text.strip():
        print(f"  ❌ 提取失败，输出空文件")
        text = f"# {filename}\n\n（{method}）\n"

    # 写入 Markdown 输出
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {filename}\n\n")
        f.write(f"（提取方法: {method}）\n\n")
        f.write(text)

    print(f"  ✅ 输出: {output_path} ({len(text)} 字符)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
