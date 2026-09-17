"""OCR scanned PDFs — PaddleOCR (primary) + PyMuPDF page renderer.

Usage: python ocr_pdf.py <path_to_scanned_pdf> [dpi]
Output: Extracted text from all pages

Dependencies: pip install pymupdf paddlepaddle paddleocr
"""

import sys, os, tempfile, uuid
import fitz  # pymupdf


_ENGINE_CACHE = {}


def _paddle_texts(result):
    """兼容 PaddleOCR 2.x / 3.x 两种返回结构，抽出纯文本。"""
    if not result:
        return ''
    lines = []

    def walk(node):
        # 3.x: OCRResult / dict，含 rec_texts
        try:
            if hasattr(node, 'get') or isinstance(node, dict):
                txts = node.get('rec_texts')
                if txts:
                    lines.extend([t for t in txts if t])
                    return
        except Exception:
            pass
        # 2.x: [box, (text, score)]
        if isinstance(node, (list, tuple)):
            if (len(node) == 2 and isinstance(node[1], (list, tuple))
                    and node[1] and isinstance(node[1][0], str)):
                lines.append(node[1][0])
                return
            for sub in node:
                walk(sub)

    walk(result)
    return '\n'.join(lines)


def get_ocr_engine():
    """Try PaddleOCR first, then Windows OCR as fallback（引擎全局复用）。"""
    if 'fn' in _ENGINE_CACHE:
        return _ENGINE_CACHE['fn']
    # Try PaddleOCR (best Chinese OCR)
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        PaddleOCR = None

    if PaddleOCR is not None:
        engine = None
        # 3.x 已移除 show_log/use_angle_cls；且 Windows 上 oneDNN 后端会抛
        # NotImplementedError: ConvertPirAttribute2RuntimeAttribute
        # → 必须 enable_mkldnn=False。逐档降级尝试。
        for kwargs in (
            {'lang': 'ch', 'enable_mkldnn': False,
             'use_doc_orientation_classify': False,
             'use_doc_unwarping': False,
             'use_textline_orientation': False},
            {'lang': 'ch', 'enable_mkldnn': False},
            {'lang': 'ch'},
            {'lang': 'ch', 'show_log': False},
            {},
        ):
            try:
                engine = PaddleOCR(**kwargs)
                break
            except Exception:
                continue
        if engine is not None:
            print('[OCR Engine: PaddleOCR]')

            def recognize(img_path):
                res = None
                if hasattr(engine, 'predict'):
                    try:
                        res = engine.predict(img_path)
                    except Exception:
                        res = None
                if res is None:
                    for kw in ({}, {'cls': False}):
                        try:
                            res = engine.ocr(img_path, **kw)
                            break
                        except Exception:
                            continue
                return _paddle_texts(res)

            _ENGINE_CACHE['fn'] = recognize
            return recognize

    # Fallback: Windows OCR via PowerShell
    print('[OCR Engine: Windows OCR (PaddleOCR not installed)]')
    import subprocess
    def recognize(img_path):
        ps = f'''
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$f = [Windows.Storage.StorageFile]::GetFileFromPathAsync('{img_path}').GetAwaiter().GetResult()
$s = $f.OpenAsync([Windows.Storage.FileAccessMode]::Read).GetAwaiter().GetResult()
$d = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($s).GetAwaiter().GetResult()
$b = $d.GetSoftwareBitmapAsync().GetAwaiter().GetResult()
$e = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages().GetAwaiter().GetResult()
if ($null -eq $e) {{ $e = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage("zh-Hans").GetAwaiter().GetResult() }}
if ($null -ne $e) {{ $e.RecognizeAsync($b).GetAwaiter().GetResult().Text }} else {{ '' }}
'''
        try:
            r = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                             capture_output=True, text=True, timeout=120,
                             encoding='gbk', errors='replace')
            return r.stdout.strip() if r.returncode == 0 else ''
        except Exception:
            return ''
    _ENGINE_CACHE['fn'] = recognize
    return recognize


def pdf_to_images(pdf_path: str, dpi=200):
    """Render PDF pages as images."""
    doc = fitz.open(pdf_path)
    img_paths = []
    uid = uuid.uuid4().hex[:8]
    for i in range(len(doc)):
        page = doc[i]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        path = os.path.join(tempfile.gettempdir(), f'ocr_{uid}_p{i}.png')
        pix.save(path)
        img_paths.append(path)
    doc.close()
    return img_paths


def ocr_pdf(pdf_path: str, dpi=200):
    """PDF → images → OCR → text."""
    recognize = get_ocr_engine()
    print(f'Rendering {pdf_path}...')
    imgs = pdf_to_images(pdf_path, dpi)
    print(f'{len(imgs)} pages, OCR...')

    all_text = []
    for i, img in enumerate(imgs):
        print(f'  Page {i+1}/{len(imgs)}')
        text = recognize(img)
        all_text.append(f'--- Page {i+1} ---\n{text}')
        try: os.remove(img)
        except: pass

    return '\n\n'.join(all_text)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python ocr_pdf.py <path_to_pdf> [dpi]")
        sys.exit(1)
    pdf_path = sys.argv[1]
    dpi = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    if not os.path.exists(pdf_path):
        print(f'File not found: {pdf_path}')
        sys.exit(1)
    result = ocr_pdf(pdf_path, dpi)
    print(result)
