import os
import shutil
import tempfile

import pymupdf
from pymupdf import Document, Page
from django.core.files import File
from django.contrib.sessions.backends.base import SessionBase

from project.settings import TMPDIR
from pdf.helpers import save_pdf_to_storage
from pdf.constants import PDF_EXT


PDF_SAMPLE_JIBBERISH_ON_READ =  os.path.join("pdf", "samples", "jibberish-on-read.pdf")


def create_pdf(name: str) -> Document:
    doc = pymupdf.open()
    doc.new_page()
    doc.save(name)
    doc.close()
    return pymupdf.open(name)


def write_pdf(page: Page, text: str, x: int = 10, y: int = 10) -> None:
    page.insert_text([x, y], text)


def remove_tmpdir() -> None:
    try:
        shutil.rmtree(TMPDIR)
    except FileNotFoundError:
        pass


def upload_pdf(session: SessionBase, page_blocks: list) -> None:
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
