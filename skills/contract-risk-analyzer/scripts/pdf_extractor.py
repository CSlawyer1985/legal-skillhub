"""
PDF Text Extractor for Contract Risk Analyzer
Uses PyMuPDF (fitz) as primary, pdfplumber as fallback
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text(pdf_path: str) -> str:
    """
    Extract text from PDF file using PyMuPDF + pdfplumber fallback.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If PDF cannot be read
    """
    import os
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    text = _extract_with_pymupdf(pdf_path)
    if not text or len(text.strip()) < 50:
        logger.info("PyMuPDF extraction insufficient, trying pdfplumber")
        text = _extract_with_pdfplumber(pdf_path)

    if not text or len(text.strip()) < 50:
        raise ValueError(f"Could not extract text from PDF: {pdf_path}")

    return text


def _extract_with_pymupdf(pdf_path: str) -> str:
    """Extract text using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.warning("PyMuPDF not installed, skipping")
        return ""

    texts = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            if text:
                texts.append(text)
        doc.close()
    except Exception as e:
        logger.error(f"PyMuPDF extraction error: {e}")
        return ""

    return "\n".join(texts)


def _extract_with_pdfplumber(pdf_path: str) -> str:
    """Extract text using pdfplumber as fallback."""
    try:
        import pdfplumber
    except ImportError:
        logger.warning("pdfplumber not installed, skipping")
        return ""

    texts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    texts.append(text)
    except Exception as e:
        logger.error(f"pdfplumber extraction error: {e}")
        return ""

    return "\n".join(texts)


def get_page_count(pdf_path: str) -> int:
    """Get number of pages in PDF."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count
    except Exception:
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        except Exception:
            return 0


def extract_tables(pdf_path: str) -> list:
    """Extract tables from PDF if any."""
    try:
        import pdfplumber
    except ImportError:
        return []

    tables = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
    except Exception as e:
        logger.error(f"Table extraction error: {e}")

    return tables
