import os
import shutil
import tempfile
from unittest.mock import patch

import pymupdf
from pymupdf import Document, Page
from django.core.files import File
from django.contrib.auth import get_user_model

from project.settings import TMPDIR
from pdf.constants import PDF_EXT
from pdf.models import Pdf
from user.models import CustomUser


PDF_SAMPLE_JIBBERISH_ON_READ =  os.path.join("pdf", "samples", "jibberish-on-read.pdf")

User = get_user_model()

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


def upload_pdf(user: CustomUser, page_blocks: list) -> None:
    with tempfile.NamedTemporaryFile(suffix=f".{PDF_EXT}") as tmpfile:
        doc = create_pdf(tmpfile.name)

    doc.new_page()
    page = doc[0]
    for idx, block in enumerate(page_blocks):
        x = 10
        y = (idx + 1) * 20
        write_pdf(page, block, x, y)

    doc.saveIncr()
    doc.close()

    file = File(open(doc.name, "rb"))
    pdf = Pdf.objects.create(file=file)
    user.pdf = pdf
    user.save()


def get_test_user() -> CustomUser:
    email = "test@example.com"
    return User.objects.get(email=email)


# This is ugly and hacky but it works and since this isn't a big project it's fine I guess. PR's are welcome though
def stub_request_user(user: CustomUser):
    return patch(
        "django.contrib.auth.middleware.get_user",
        return_value=user,
    )
