import tempfile
from pathlib import Path

import pymupdf
from pymupdf import Document, Page
from django.core.files import File
from django.contrib.sessions.backends.base import SessionBase

from pdf.helpers import uploaded_pdf_path, save_pdf_to_storage
from pdf.constants import PDF_EXT


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


def upload_pdf_without_form(session: SessionBase, page_blocks: list) -> Document:
    with tempfile.NamedTemporaryFile(suffix=f".{PDF_EXT}") as tmpfile:
        pdf = create_pdf(tmpfile.name)

    pdf.new_page()
    page = pdf[0]
    for idx, block in enumerate(page_blocks):
        x = 10
        y = (idx + 1) * 20
        write_pdf(page, block, x, y)

    pdf.saveIncr()
    pdf.close()

    file = File(open(pdf.name, "rb"))
    path = save_pdf_to_storage(file)
    session["uploaded_pdf_path"] = path
    session.save()
    return pdf
