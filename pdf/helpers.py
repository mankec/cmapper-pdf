import os
from pathlib import Path

from pdf.factories import PdfLib, PdfLibFactory
from pdf.libs import PymupdfLib
from project.settings import MEDIA_ROOT, IS_TEST, TMPDIR



def clear_user_pdf() -> None:
    joined = os.path.join(MEDIA_ROOT, "user", "pdf")
    fd = Path(joined)
    for file in fd.iterdir():
        if file.name == ".gitkeep":
            continue
        file.unlink()


def upload_pdf_path(_, filename: str) -> str:
    basename = filename.split("/")[-1]
    upload_dirs = os.path.join("user", "pdf")
    if IS_TEST:
        if not Path(TMPDIR).exists():
            Path(TMPDIR).mkdir()
        upload_dirs = os.path.join("tmp", upload_dirs)
    return os.path.join(upload_dirs, basename)


def uploaded_pdf_path(filename: str) -> str:
    return os.path.join(MEDIA_ROOT, upload_pdf_path(None, filename))


def to_char(hex_digits: str) -> str:
    return chr(int(hex_digits, 16))


def to_unicode(char: str) -> str:
    utf_8_encoding = hex(ord(char))
    return utf_8_encoding.replace("x", "").zfill(4).upper()


def chunked_list(text: str, chunk_size: int) -> list:
    # Use this only when you know exact length of text and you want equal or close to equal chunks
    chunked = []
    from_idx = 0
    to_idx = chunk_size

    while to_idx <= len(text):
        chunked.append(text[from_idx:to_idx])

        from_idx = to_idx
        to_idx += chunk_size

    return chunked


def get_page_text(filename_or_stream: str, pno: int | str) -> str:
    pdflib: PymupdfLib = PdfLibFactory(PdfLib.PYMUPDF)
    pdflib.open(filename_or_stream)
    page = pdflib.get_page(pno)

    return page.get_text()
