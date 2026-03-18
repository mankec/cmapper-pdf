from pathlib import Path

import pymupdf
from pymupdf import Document, Page
from pdf.helpers import uploaded_pdf_path


def create_pdf(name: str) -> Document:
    doc = pymupdf.open()
    doc.new_page()
    doc.save(name)
    doc.close()
    return pymupdf.open(name)


def write_pdf(page: Page, text: str, x: int = 10, y: int = 10) -> None:
    page.insert_text([x, y], text)


def remove_pdf(name: str) -> None:
    Path(
        uploaded_pdf_path(name)
    ).unlink()
