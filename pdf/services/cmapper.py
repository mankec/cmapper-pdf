import pymupdf
from django.core.files import File


class Cmapper:
    DEFAULT_PNO = 1
    TEXT_FORMAT_BLOCKS = "blocks"

    def __init__(self, file: File, page: str | int) -> None:
        self.file = file

        # Convert to proper number since first number is 1 instead of 0, because of UX
        self.page = int(page) - 1

    def get_page_blocks(self) -> str:
        doc = pymupdf.open(self.file)
        page = doc[self.page]
        blocks = page.get_text(self.TEXT_FORMAT_BLOCKS)

        # (x0, y0, x1, y1, "lines in the block", block_no, block_type)
        # We only care about "lines in the block"
        blocks = [block[4:-2] for block in blocks]

        # Split block into words so they can be selected separately
        return [block[0].split(" ") for block in blocks]
