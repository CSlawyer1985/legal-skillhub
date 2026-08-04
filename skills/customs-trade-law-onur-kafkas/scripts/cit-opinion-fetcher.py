#!/usr/bin/env python3
"""
CIT Slip Opinion PDF Fetcher & Text Extractor

Downloads and extracts text from Court of International Trade slip opinion
PDFs published at cit.uscourts.gov. Part of the trade-law plugin.

Usage:
  python3 cit-opinion-fetcher.py <slip-op-number>
  python3 cit-opinion-fetcher.py <url-to-pdf>
  python3 cit-opinion-fetcher.py <local-file.pdf>

Examples:
  python3 cit-opinion-fetcher.py 26-11
  python3 cit-opinion-fetcher.py 26-10
  python3 cit-opinion-fetcher.py https://www.cit.uscourts.gov/sites/cit/files/26-11.pdf
  python3 cit-opinion-fetcher.py /path/to/local/opinion.pdf

Output:
  Extracted text from the PDF, printed to stdout. Includes metadata header
  with page count and source URL.

Dependencies:
  pymupdf (pip install pymupdf)
"""

import sys
import urllib.request
import urllib.error
import tempfile
import os

try:
    import pymupdf
except ImportError:
    print("ERROR: pymupdf is required. Install with: pip install pymupdf", file=sys.stderr)
    sys.exit(1)


CIT_BASE_URL = "https://www.cit.uscourts.gov/sites/cit/files"


def fetch_pdf(source: str) -> tuple[str, str]:
    """
    Resolve source to a local PDF path.

    Args:
        source: Slip op number (e.g. "26-11"), URL, or local file path.

    Returns:
        Tuple of (local_file_path, source_description).
        If the file was downloaded to a temp location, caller must clean up.
    """
    # Local file
    if os.path.isfile(source):
        return source, f"Local file: {source}"

    # Full URL
    if source.startswith("http://") or source.startswith("https://"):
        url = source
    else:
        # Slip opinion number → URL
        url = f"{CIT_BASE_URL}/{source}.pdf"

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "TradeClassificationResearchTool/1.0"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(tmp.name, "wb") as f:
                f.write(resp.read())
    except urllib.error.HTTPError as e:
        os.unlink(tmp.name)
        print(f"ERROR: HTTP {e.code} fetching {url}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        os.unlink(tmp.name)
        print(f"ERROR: Could not reach {url}: {e.reason}", file=sys.stderr)
        sys.exit(1)

    return tmp.name, f"Source: {url}"


def extract_text(pdf_path: str) -> tuple[str, int]:
    """
    Extract text from a PDF file using pymupdf.

    Returns:
        Tuple of (extracted_text, page_count).
    """
    doc = pymupdf.open(pdf_path)
    page_count = len(doc)
    pages = []

    for page_num in range(page_count):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            pages.append(f"--- Page {page_num + 1} ---\n{text}")

    doc.close()
    return "\n\n".join(pages), page_count


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    source = sys.argv[1]
    is_temp = False

    try:
        pdf_path, source_desc = fetch_pdf(source)
        is_temp = pdf_path != source and not source.startswith("http")

        # If we downloaded it, mark for cleanup
        if source != pdf_path:
            is_temp = True

        text, page_count = extract_text(pdf_path)

        # Output with metadata header
        print(f"{'=' * 80}")
        print(f"CIT SLIP OPINION — TEXT EXTRACTION")
        print(f"{source_desc}")
        print(f"Pages: {page_count}")
        print(f"{'=' * 80}\n")
        print(text)

    finally:
        # Clean up temp file if we downloaded one
        if is_temp and os.path.exists(pdf_path):
            os.unlink(pdf_path)


if __name__ == "__main__":
    main()
