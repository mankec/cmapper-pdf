import os
from pathlib import Path

import pymupdf

from pdf.constants import SOFT_HYPHEN_HEX_ESCAPE
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


def get_word_blocks(
    filename_or_stream: str | bytes, pno: str | int
) -> list[list[dict[str, str]]]:
    pdflib: PymupdfLib = PdfLibFactory(PdfLib.PYMUPDF)
    pdflib.open(filename_or_stream)
    page = pdflib.get_page(pno)
    exclude_images = pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES
    page_text = page.get_text("dict", flags=exclude_images)

    blocks = []

    for block in page_text["blocks"]:
        block_list = []

        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].split(" ")

                for word in text:
                    if not word:
                        continue

                    if block_list:
                        last_word = block_list[-1]
                        value = last_word["value"]

                        if value.endswith(SOFT_HYPHEN_HEX_ESCAPE):
                            # This happens when there's a line break in original PDF
                            # TODO: See if \n can be omitted
                            last_word["value"] = value + "\n" + word
                            continue

                        if word == ".":
                            # Avoid remapping dots
                            last_word["value"] = value + word
                            continue

                    block_list.append({"value": word, "font": span["font"]})

        blocks.append(block_list)

    return blocks


def get_page_text(filename_or_stream: str | bytes, pno: str | int) -> str:
    pdflib: PymupdfLib = PdfLibFactory(PdfLib.PYMUPDF)
    pdflib.open(filename_or_stream)
    page = pdflib.get_page(pno)

    return page.get_text()

