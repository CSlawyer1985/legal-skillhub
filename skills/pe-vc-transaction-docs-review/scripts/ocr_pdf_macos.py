#!/usr/bin/env python3
"""OCR image/scanned PDFs with Poppler pdftoppm and macOS Vision."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def find_pdftoppm() -> str | None:
    env_path = os.environ.get("PDFTOPPM")
    home = Path.home()
    candidates = [
        env_path,
        shutil.which("pdftoppm"),
        str(home / ".cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pdftoppm"),
        "/opt/homebrew/bin/pdftoppm",
        "/usr/local/bin/pdftoppm",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


def natural_page_key(path: Path) -> list[object]:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.name)]


def fail(code: str, message: str, next_step: str, return_code: int) -> int:
    print(f"[{code}] {message} Next step: {next_step}", file=sys.stderr)
    return return_code


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--max-pages", type=int, default=0, help="0 means all pages")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--allow-partial", action="store_true", help="Return success even if one or more pages fail OCR.")
    args = ap.parse_args()

    pdf = args.pdf.expanduser()
    if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
        return fail("OCR-INPUT-001", f"PDF not found or not a PDF: {pdf}.", "Provide an existing PDF file.", 2)
    if args.max_pages < 0:
        print("--max-pages must be zero or greater.", file=sys.stderr)
        return 2
    if args.dpi < 72 or args.dpi > 600:
        print("--dpi must be between 72 and 600.", file=sys.stderr)
        return 2
    pdftoppm = find_pdftoppm()
    if not pdftoppm:
        return fail(
            "OCR-TOOL-001",
            "The PDF-to-image tool is unavailable.",
            "Use the bundled Codex runtime, install Poppler, or provide a searchable PDF or Word source.",
            2,
        )
    swift = shutil.which("swift")
    if not swift:
        return fail(
            "OCR-TOOL-002",
            "macOS Vision OCR is unavailable because Swift was not found.",
            "Run on macOS with /usr/bin/swift, or provide a searchable PDF or Word source.",
            2,
        )
    swift_script = Path(__file__).with_name("ocr_vision.swift")

    with tempfile.TemporaryDirectory(prefix="vcpe_pdf_ocr_") as td:
        prefix = Path(td) / "page"
        cmd = [pdftoppm, "-png", "-r", str(args.dpi)]
        if args.max_pages > 0:
            cmd += ["-f", "1", "-l", str(args.max_pages)]
        cmd += [str(pdf), str(prefix)]
        proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
        if proc.returncode != 0:
            return fail(
                "OCR-CONVERT-001",
                proc.stderr.strip() or "PDF page conversion failed.",
                "Check whether the PDF is damaged or encrypted, then provide a decrypted or native source file.",
                1,
            )
        images = sorted(Path(td).glob("page-*.png"), key=natural_page_key)
        if not images:
            return fail(
                "OCR-CONVERT-002",
                "No page images were generated.",
                "Provide a valid, decrypted PDF or the original Word file.",
                1,
            )
        chunks: list[str] = []
        failed_pages: list[int] = []
        for i, image in enumerate(images, start=1):
            ocr = subprocess.run([swift, str(swift_script), str(image)], text=True, capture_output=True, check=False)
            if ocr.returncode != 0:
                failed_pages.append(i)
                chunks.append(f"\n===== PAGE {i} OCR FAILED =====\n{ocr.stderr.strip()}\n")
            else:
                chunks.append(f"\n===== PAGE {i} =====\n{ocr.stdout.strip()}\n")
        text = "\n".join(chunks).strip() + "\n"

    if args.output:
        try:
            args.output.expanduser().write_text(text, encoding="utf-8")
        except OSError as exc:
            return fail(
                "OCR-OUTPUT-001",
                f"Could not write OCR output: {exc}",
                "Choose a writable output path and rerun OCR.",
                2,
            )
    else:
        print(text)
    if failed_pages:
        print(
            f"[OCR-PARTIAL-001] OCR failed on page(s): {', '.join(str(page) for page in failed_pages)}. "
            "Next step: provide clearer scans or a searchable PDF/Word source for those pages; do not treat the file as fully reviewed.",
            file=sys.stderr,
        )
        return 0 if args.allow_partial else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
