from pathlib import Path

import pymupdf
from pymupdf import Document

from pdf.constants import SOFT_HYPHEN_HEX_ESCAPE
from pdf.helpers import uploaded_pdf_path


class PdfPage:
    DEFAULT_PNO = 1
    TEXT_FORMAT_DICT = "dict"

    def __init__(self, filename_or_stream: str | bytes, pno: str | int) -> None:
        self.filename_or_stream = filename_or_stream

        # Convert to proper number since first number is 1 instead of 0, because of UX
        self.pno = int(pno) - 1

    def get_word_blocks(self) -> list[list[dict[str, str]]]:
        doc = self._open_pdf()
        page = doc.load_page(self.pno)
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

    def get_page_text(self) -> str:
        if isinstance(self.filename_or_stream, str):
            doc = pymupdf.open(self.filename)
        else:
            doc = pymupdf.open(stream=self.filename_or_stream)

        return doc.load_page(self.pno).get_text()

    def _open_pdf(self) -> Document:
        if isinstance(self.filename_or_stream, str):
            if Path(self.filename_or_stream).exists():
                doc = pymupdf.open(self.filename_or_stream)
            else:
                filename = uploaded_pdf_path(self.filename_or_stream)
                doc = pymupdf.open(filename)
        else:
            doc = pymupdf.open(stream=self.filename_or_stream)

        return doc
