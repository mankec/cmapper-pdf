import pymupdf

from pdf.helpers import uploaded_pdf_path
from pdf.constants import SOFT_HYPHEN_HEX_ESCAPE

class PdfPageReader:
    DEFAULT_PNO = 1
    TEXT_FORMAT_BLOCKS = "blocks"

    def __init__(self, filename: str, pno: str | int, stream = None, uploaded=True) -> None:
        if uploaded:
            self.filename = uploaded_pdf_path(filename)
        else:
            self.filename = filename
        self.stream = stream

        # Convert to proper number since first number is 1 instead of 0, because of UX
        self.pno = int(pno) - 1

    def get_word_blocks(self) -> list[list[dict[str, str]]]:
        doc = pymupdf.open(self.filename)
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

                        block_list.append({"value": word, "font": span["font"]})

            blocks.append(block_list)

        return blocks

    def get_page_text(self) -> str:
        if self.stream:
            doc = pymupdf.open(stream=self.stream)
        else:
            doc = pymupdf.open(self.filename)
        page = doc.load_page(self.pno)
        return page.get_text()
