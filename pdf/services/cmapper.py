import tempfile
import shutil
import re
import math
from typing import Iterator, Self
from concurrent.futures import ProcessPoolExecutor

import pikepdf
from pikepdf import Pdf
from pikepdf import Object

from pdf.services.pdf_page_reader import PdfPageReader
from pdf.helpers import to_char, to_unicode, chunked_list, uploaded_pdf_path


class Cmapper:
    def __init__(self, filename: str, pno: str | int) -> None:
        self.filename = uploaded_pdf_path(filename)

        # Convert to proper number since first number is 1 instead of 0, because of UX
        self.pno = int(pno) - 1
        self.reader = PdfPageReader(filename, pno)

    def extract_mapped_chars(self, word: str, font_name: str | None) -> list[dict[str, str]]:
        pdf = pikepdf.open(self.filename, allow_overwriting_input=True)
        page = pdf.pages[self.pno]
        fonts = page.Resources.Font
        mapped_chars: dict[str, str] = {}

        font = next(
            font for font in fonts
            if str(fonts[font].DescendantFonts[0].BaseFont).lstrip("/") == font_name
        )

        stm = fonts[font].get("/ToUnicode")
        if not stm:
            return
        data = stm.read_bytes()
        cmap = data.decode()
        extracted = _Extractor(self.reader, pdf, fonts, font, cmap).extract(word)
        if extracted:
            mapped_chars |= extracted

        multiple_chars = {}
        for char in mapped_chars.keys():
            if len(char) > 1:
                start_idx = word.index(char)
                multiple_chars[start_idx] = char

        # It cannot be dictionary because some chars show multiple times
        skip_idxs = []
        mapped_chars_list: list[dict[str, str]] = []
        for idx, char in enumerate(list(word)):
            if idx in skip_idxs:
                continue

            chars = multiple_chars.get(idx)

            if chars:
                to_idx = idx + len(chars)
                skip_idxs = range(idx + 1, to_idx)
                char = word[idx:to_idx]

            info = mapped_chars[char]
            mapped_chars_list.append(
                { "char": char, "glyph_id": info["glyph_id"], "font": info["font"] }
            )

        return mapped_chars_list


class _Extractor():
    SINGLE_UNICODE_LENGTH = 4
    IGNORE_CHARS = ["."]

    def __init__(
        self, reader: PdfPageReader, pdf: Pdf, fonts: Object, font: str, cmap: str
    ) -> None:
        self.reader: PdfPageReader = reader
        self.pdf = pdf
        self.fonts = fonts
        self.font = font
        self.cmap = cmap

    def update_cmap(self, lines: list) -> None:
        self.cmap = "\n".join(lines)
        data = self.cmap.encode("utf-8")
        stream = self.pdf.make_stream(data)
        self.fonts[self.font].ToUnicode = stream
        self.pdf.save(self.pdf.filename, linearize=False)

    def extract(self, word: str) -> dict[str, str] | None:
        baselines = self.cmap.splitlines()
        mappings: list[str] = re.findall(r"<\w{4}> <\w{4,}>", self.cmap)

        decoded_mappings = {}
        for mapping in mappings:
            splitted = mapping.split(" ")
            glyph_id = splitted[0].strip("<>")
            charcode = splitted[1].strip("<>")

            if len(charcode) == self.SINGLE_UNICODE_LENGTH:
                char = to_char(charcode)
            else:
                charcodes = chunked_list(charcode, self.SINGLE_UNICODE_LENGTH)
                char = "".join(to_char(charcode) for charcode in charcodes)

            # Use Glyph ID because sometimes multiple Glyph IDs point to the same char
            decoded_mappings[glyph_id] = char

        mappings_dict: dict[str, str] = {}

        glyph_ids = [
            glyph_id for glyph_id, char in decoded_mappings.items()
            if char in word
        ]

        for glyph_id in glyph_ids:
            char = decoded_mappings[glyph_id]

            if char in self.IGNORE_CHARS:
                continue

            mappings_dict[glyph_id] = { "char": char }

        mappings = []

        for glyph_id, info in mappings_dict.items():
            char = info["char"]
            charcodes = [to_unicode(char) for char in char]
            mapping = f"<{glyph_id}> <{"".join(charcodes)}>"
            mappings.append(mapping)

        result: dict[str, str] = {}

        extended = []

        with ProcessPoolExecutor(max_workers=8) as ex:
            chunks = [(mappings[i::4], self.clone()) for i in range(4)]
            futures = [
                ex.submit(
                    worker, clone.pdf.filename, clone.reader.pno, clone.font, word, baselines, mappings
                ) for mappings, clone in chunks
            ]
            for fut in futures:
                extended.extend(fut.result())

        for mapping in extended:
            splitted = mapping.split(" ")
            glyph_id = splitted[0].strip("<>")
            charcode = splitted[1].strip("<>")

            if len(charcode) == self.SINGLE_UNICODE_LENGTH:
                char = to_char(charcode)
            else:
                charcodes = chunked_list(charcode, self.SINGLE_UNICODE_LENGTH)
                char = "".join(to_char(charcode) for charcode in charcodes)

            result[char] = { "font": self.font, "glyph_id": glyph_id }

        self.update_cmap(baselines)

        return result

    def clone(self) -> Self:
        tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        shutil.copy(self.pdf.filename, tmpfile.name)

        pdf = pikepdf.open(tmpfile.name, allow_overwriting_input=True)
        page = pdf.pages[self.reader.pno]
        fonts = page.Resources.Font
        reader = PdfPageReader(tmpfile.name, self.reader.pno)
        clone = _Extractor(reader, pdf, fonts, self.font, self.cmap)

        return clone


# Process pool

def worker(
    filename: str, pno: int, font: str, word: str, lines: list[str], mappings: list[str]
) -> list[str]:
    return list(find_corresponding_mappings_in_process(
            filename, pno, font, word, lines, mappings
        )
    )


def find_corresponding_mappings_in_process(
    filename: str, pno: int, font: str, word: str, lines: list[str], mappings: list[str]
) -> Iterator[str]:
    args = (filename, pno, font, word, lines)

    if len(mappings) == 1:
        yield mappings[0]
        return

    half = math.ceil(len(mappings)/2)
    first_half = mappings[:half]
    second_half = mappings[half:]

    in_first_half = check_half_in_process(*args, first_half)
    in_second_half = check_half_in_process(*args, second_half)

    if in_first_half:
        yield from find_corresponding_mappings_in_process(*args, first_half)

    if in_second_half:
        yield from find_corresponding_mappings_in_process(*args, second_half)


def check_half_in_process(
    filename: str, pno: int, font: str, word: str, lines: list[str], subtract: list[str]
) -> bool:
    subtracted = [line for line in lines if line not in set(subtract)]
    update_cmap_in_process(filename, pno, font, subtracted)
    text = PdfPageReader(filename, pno, uploaded=False).get_page_text()

    return word not in text


def update_cmap_in_process(filename: str, pno: int, font: str, lines: list) -> None:
    with pikepdf.open(filename, allow_overwriting_input=True) as pdf:
        cmap = "\n".join(lines)
        data = cmap.encode("utf-8")
        page = pdf.pages[pno]
        fonts = page.Resources.Font
        stream = pdf.make_stream(data)
        fonts[font].ToUnicode = stream
        pdf.save(filename, linearize=False)
