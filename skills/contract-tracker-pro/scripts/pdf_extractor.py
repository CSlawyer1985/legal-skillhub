"""
PDF Text Extractor for Contract Tracker Pro
Extracts text from contract PDF files
"""

import logging
from typing import Optional
import io

logger = logging.getLogger(__name__)

# Try pdfplumber first (better for tables), fall back to PyPDF2
try:
    import pdfplumber

    PDF_LIBRARY = "pdfplumber"

    def extract_text(pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber."""
        with pdfplumber.open(pdf_path) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        return "\n\n".join(pages)

    def get_page_count(pdf_path: str) -> int:
        """Get number of pages in PDF."""
        with pdfplumber.open(pdf_path) as pdf:
            return len(pdf.pages)

    def extract_page_text(pdf_path: str, page_number: int) -> str:
        """Extract text from a specific page (1-indexed)."""
        with pdfplumber.open(pdf_path) as pdf:
            if 1 <= page_number <= len(pdf.pages):
                return pdf.pages[page_number - 1].extract_text() or ""
        return ""

except ImportError:
    try:
        import PyPDF2

        PDF_LIBRARY = "PyPDF2"

        def extract_text(pdf_path: str) -> str:
            """Extract text from PDF using PyPDF2."""
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
            return "\n\n".join(pages)

        def get_page_count(pdf_path: str) -> int:
            """Get number of pages in PDF."""
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                return len(reader.pages)

        def extract_page_text(pdf_path: str, page_number: int) -> str:
            """Extract text from a specific page (1-indexed)."""
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                if 0 <= page_number - 1 < len(reader.pages):
                    return reader.pages[page_number - 1].extract_text() or ""
            return ""

    except ImportError:
        PDF_LIBRARY = None

        def extract_text(pdf_path: str) -> str:
            raise ImportError(
                "Neither pdfplumber nor PyPDF2 is installed. "
                "Please install one of them: pip install pdfplumber"
            )

        def get_page_count(pdf_path: str) -> int:
            raise ImportError(
                "Neither pdfplumber nor PyPDF2 is installed. "
                "Please install one of them: pip install pdfplumber"
            )

        def extract_page_text(pdf_path: str, page_number: int) -> str:
            raise ImportError(
                "Neither pdfplumber nor PyPDF2 is installed. "
                "Please install one of them: pip install pdfplumber"
            )


def extract_tables(pdf_path: str) -> list:
    """
    Extract tables from PDF (pdfplumber only).
    Returns list of tables, each table is a list of rows (list of cells).
    """
    if PDF_LIBRARY != "pdfplumber":
        logger.warning("Table extraction only available with pdfplumber")
        return []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_tables = []
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)
        return all_tables
    except Exception as e:
        logger.error(f"Table extraction failed: {e}")
        return []
