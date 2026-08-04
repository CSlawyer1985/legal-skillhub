#!/usr/bin/env python3
"""Route scanned-PDF OCR to an available local macOS or cross-platform engine."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


MANUAL_GUIDANCE = (
    "请提供以下任一种替代材料：1. 带可搜索文字层的PDF；2. 原始Word文件；"
    "3. 更清晰、按页分拆的扫描件。该文件应标记为未实质审阅，并继续处理其他可读文件。 "
    "Provide one of: a searchable PDF, the original Word file, or clearer page-by-page scans."
)


def fail(code: str, message: str, next_step: str, return_code: int = 2) -> int:
    print(f"[{code}] {message} Next step: {next_step}", file=sys.stderr)
    return return_code


def available_engines() -> list[str]:
    engines = []
    if platform.system() == "Darwin" and shutil.which("swift") and shutil.which("pdftoppm"):
        engines.append("macos-vision")
    if shutil.which("ocrmypdf") and shutil.which("pdftotext"):
        engines.append("ocrmypdf")
    if shutil.which("tesseract") and shutil.which("pdftoppm"):
        engines.append("tesseract")
    return engines


def write_or_print(text: str, output: Path | None) -> int:
    if output:
        output.expanduser().write_text(text, encoding="utf-8")
    else:
        print(text, end="" if text.endswith("\n") else "\n")
    return 0


def run_macos(pdf: Path, output: Path | None, max_pages: int, dpi: int) -> int:
    command = [sys.executable, str(Path(__file__).with_name("ocr_pdf_macos.py")), str(pdf), "--dpi", str(dpi)]
    if max_pages:
        command += ["--max-pages", str(max_pages)]
    if output:
        command += ["--output", str(output)]
    return subprocess.run(command, check=False).returncode


def run_ocrmypdf(pdf: Path, output: Path | None) -> int:
    with tempfile.TemporaryDirectory(prefix="pevc_ocr_") as tmp:
        searchable = Path(tmp) / "searchable.pdf"
        generated = subprocess.run(
            ["ocrmypdf", "--skip-text", "--deskew", str(pdf), str(searchable)],
            text=True, capture_output=True, check=False,
        )
        if generated.returncode != 0:
            return fail("OCR-ENGINE-001", generated.stderr.strip() or "OCRmyPDF failed.", "Try Tesseract, macOS Vision, or provide a searchable PDF.", 1)
        extracted = subprocess.run(
            ["pdftotext", "-layout", str(searchable), "-"],
            text=True, capture_output=True, check=False,
        )
        if extracted.returncode != 0 or not extracted.stdout.strip():
            return fail("OCR-ENGINE-002", extracted.stderr.strip() or "OCR produced no searchable text.", "Provide clearer scans or the original Word file.", 1)
        return write_or_print(extracted.stdout, output)


def tesseract_language(requested: str) -> tuple[str, str | None]:
    listed = subprocess.run(["tesseract", "--list-langs"], text=True, capture_output=True, check=False)
    available = set(listed.stdout.split())
    wanted = [item for item in requested.split("+") if item in available]
    if not wanted and "eng" in available:
        return "eng", "Requested OCR languages were unavailable; fell back to English."
    return "+".join(wanted), None


def run_tesseract(pdf: Path, output: Path | None, max_pages: int, dpi: int, language: str) -> int:
    selected_language, warning = tesseract_language(language)
    if not selected_language:
        return fail("OCR-TOOL-003", "No requested Tesseract language data is installed.", "Install chi_sim and/or eng language data, or provide a searchable PDF.")
    if warning:
        print(f"[OCR-LANGUAGE-001] {warning}", file=sys.stderr)
    with tempfile.TemporaryDirectory(prefix="pevc_tesseract_") as tmp:
        prefix = Path(tmp) / "page"
        command = ["pdftoppm", "-png", "-r", str(dpi)]
        if max_pages:
            command += ["-f", "1", "-l", str(max_pages)]
        converted = subprocess.run(command + [str(pdf), str(prefix)], text=True, capture_output=True, check=False)
        if converted.returncode != 0:
            return fail("OCR-CONVERT-001", converted.stderr.strip() or "PDF page conversion failed.", "Provide a decrypted PDF or original Word file.", 1)
        pages = sorted(Path(tmp).glob("page-*.png"))
        chunks = []
        for number, image in enumerate(pages, start=1):
            result = subprocess.run(
                ["tesseract", str(image), "stdout", "-l", selected_language],
                text=True, capture_output=True, check=False,
            )
            if result.returncode != 0:
                return fail("OCR-ENGINE-003", result.stderr.strip() or f"Tesseract failed on page {number}.", "Provide clearer scans or another local OCR engine.", 1)
            chunks.append(f"===== PAGE {number} =====\n{result.stdout.strip()}")
        if not chunks:
            return fail("OCR-CONVERT-002", "No page images were generated.", "Provide a valid, decrypted PDF.", 1)
        return write_or_print("\n\n".join(chunks).strip() + "\n", output)


def run_engine(engine: str, pdf: Path, output: Path | None, max_pages: int, dpi: int, language: str) -> int:
    if engine == "macos-vision":
        return run_macos(pdf, output, max_pages, dpi)
    if engine == "ocrmypdf":
        if max_pages:
            return fail("OCR-INPUT-003", "--max-pages is not supported by the OCRmyPDF route.", "Use Tesseract/macOS Vision or omit --max-pages.")
        return run_ocrmypdf(pdf, output)
    return run_tesseract(pdf, output, max_pages, dpi, language)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, nargs="?")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--engine", choices=("auto", "macos-vision", "ocrmypdf", "tesseract"), default="auto")
    parser.add_argument("--max-pages", type=int, default=0)
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--language", default="chi_sim+eng")
    parser.add_argument("--list-engines", action="store_true")
    args = parser.parse_args()
    engines = available_engines()
    if args.list_engines:
        print(json.dumps({"available_engines": engines}, ensure_ascii=False))
        return 0
    if args.pdf is None:
        return fail("OCR-INPUT-001", "A PDF path is required.", "Provide an existing PDF file.")
    pdf = args.pdf.expanduser()
    if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
        return fail("OCR-INPUT-001", f"PDF not found or not a PDF: {pdf}.", "Provide an existing PDF file.")
    if args.max_pages < 0 or not 72 <= args.dpi <= 600:
        return fail("OCR-INPUT-002", "Invalid --max-pages or --dpi value.", "Use max-pages >= 0 and dpi between 72 and 600.")
    engine = args.engine
    if engine == "auto":
        if not engines:
            return fail("OCR-MANUAL-001", "No supported local OCR engine is available.", MANUAL_GUIDANCE)
        with tempfile.TemporaryDirectory(prefix="pevc_ocr_fallback_") as tmp:
            for index, candidate in enumerate(engines, start=1):
                attempt = Path(tmp) / f"attempt-{index}.txt"
                if run_engine(candidate, pdf, attempt, args.max_pages, args.dpi, args.language) == 0:
                    try:
                        extracted = attempt.read_text(encoding="utf-8")
                    except (OSError, UnicodeError):
                        extracted = ""
                    if extracted.strip():
                        return write_or_print(extracted, args.output)
                print(f"[OCR-FALLBACK-{index:03d}] {candidate} failed; trying the next local engine.", file=sys.stderr)
        return fail("OCR-MANUAL-001", "All available local OCR engines failed.", MANUAL_GUIDANCE, 1)
    if engine not in engines:
        return fail("OCR-TOOL-002", f"Requested OCR engine is unavailable: {engine}.", f"Available engines: {', '.join(engines) or 'none'}.")
    return run_engine(engine, pdf, args.output, args.max_pages, args.dpi, args.language)


if __name__ == "__main__":
    raise SystemExit(main())
