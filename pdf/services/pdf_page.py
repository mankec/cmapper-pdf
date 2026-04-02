import pymupdf

from pdf.constants import SOFT_HYPHEN_HEX_ESCAPE
from pdf.factories import PdfLib, PdfLibFactory
from pdf.libs import PymupdfLib


class PdfPage:
    DEFAULT_PNO = 1
    TEXT_FORMAT_DICT = "dict"

    def __init__(self, filename_or_stream: str | bytes, pno: str | int) -> None:
        self.filename_or_stream = filename_or_stream
        self.pno = pno

    def get_word_blocks(self) -> list[list[dict[str, str]]]:
        pdflib: PymupdfLib = PdfLibFactory(PdfLib.PYMUPDF)
        pdflib.open(self.filename_or_stream)
        page = pdflib.get_page(self.pno)
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
        pdflib: PymupdfLib = PdfLibFactory(PdfLib.PYMUPDF)
        pdflib.open(self.filename_or_stream)
        page = pdflib.get_page(self.pno)

        return page.get_text()
