import os
import io
import re
import math
from concurrent.futures import ProcessPoolExecutor

from pikepdf import Pdf, Object

from pdf.helpers import to_char, to_unicode, chunked_list
from pdf.factories import PdfLib, PdfLibFactory
from pdf.libs import PikepdfLib
from pdf.utils import get_page_text


class Cmapper:
    def __init__(self, filename_or_stream: str | bytes, pno: str | int):
        self.filename_or_stream = filename_or_stream
        self.pno = int(pno)

        pdflib: PikepdfLib = PdfLibFactory(PdfLib.PIKEPDF)
        self.pdf = pdflib.open(self.filename_or_stream, allow_overwriting_input=True)
        self.page = pdflib.get_page(self.pno)

    def extract_mapped_chars(
        self, word: str, font_name: str | None
    ) -> list[dict[str, str]]:
        fonts = self.page.Resources.Font

        font = next(
            (
                font for font in fonts
                if str(fonts[font].DescendantFonts[0].BaseFont).lstrip("/") == font_name
            ), None
        )

        if not font:
            return

        font_stream = fonts[font].get("/ToUnicode")
        if not font_stream:
            return

        mapped_chars_dict = {}

        data = font_stream.read_bytes()
        cmap = data.decode()
        extracted = _Extractor(self.pdf, self.pno, fonts, font, cmap).extract(word)
        if extracted:
            mapped_chars_dict |= extracted

        multiple_chars = {}
        for char in mapped_chars_dict.keys():
            if len(char) > 1:
                start_idx = word.index(char)
                multiple_chars[start_idx] = char

        idx = 0
        word_list = list(word)
        mapped_chars_list = []
        while idx < len(word):
            chars = multiple_chars.get(idx)

            if chars:
                to_idx = idx + len(chars)
                char = word[idx:to_idx]
                idx = to_idx
            else:
                char = word_list[idx]
                idx += 1

            info = mapped_chars_dict[char]
            mapped_chars_list.append(
                { "char": char, "glyph_id": info["glyph_id"], "font": info["font"] }
            )

        return mapped_chars_list

    def remap(self, remap_chars: dict[str, str], font_name: str) -> None:
        fonts = self.page.Resources.Font

        font = next(
            (
                font for font in fonts
                if str(fonts[font].DescendantFonts[0].BaseFont).lstrip("/") == font_name
            ), None
        )

        font_stream = fonts[font].get("/ToUnicode")
        data = font_stream.read_bytes()
        cmap = data.decode()

        _Remapper(self.pdf, self.pno, fonts, font, cmap).remap(remap_chars)


class _Cmapper():
    def __init__(
        self, pdf: Pdf, pno: int, fonts: Object, font: str, cmap: str
    ) -> None:
        self.pdf = pdf
        self.pno = pno
        self.fonts = fonts
        self.font = font
        self.cmap = cmap

    def update_cmap(self, lines: list) -> None:
        self.cmap = "\n".join(lines)
        data = self.cmap.encode()
        stream = self.pdf.make_stream(data)
        self.fonts[self.font].ToUnicode = stream
        self.pdf.save(self.pdf.filename, linearize=False)


class _Remapper(_Cmapper):
    def remap(self, remap_chars: dict[str, str]):
        lines = self.cmap.splitlines()

        for idx, line in enumerate(lines):
            if not line.startswith("<"):
                continue

            glyph_id = line.split(" ")[0].strip("<>")

            new_char = remap_chars.get(glyph_id)
            if new_char:
                new_map = f"<{glyph_id}> <{"".join([to_unicode(char) for char in new_char])}>"
                lines.pop(idx)
                lines.insert(idx, new_map)

        self.update_cmap(lines)


class _Extractor(_Cmapper):
    SINGLE_UNICODE_LENGTH = 4
    IGNORE_CHARS = ["."]

    def extract(self, word: str) -> dict[str, str] | None:
        baselines = self.cmap.splitlines()
        mappings = re.findall(r"<\w{4}> <\w{4,}>", self.cmap)

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

            # Use Glyph IDs because some chars appear multiple times
            decoded_mappings[glyph_id] = char

        glyph_ids = [
            glyph_id for glyph_id, char in decoded_mappings.items()
            if char in word
        ]

        potential_corresponding_mappings = {}
        for glyph_id in glyph_ids:
            char = decoded_mappings[glyph_id]

            if char in self.IGNORE_CHARS:
                continue

            potential_corresponding_mappings[glyph_id] = { "char": char }

        mappings_cmap_format = []
        for glyph_id, info in potential_corresponding_mappings.items():
            char = info["char"]
            charcodes = [to_unicode(char) for char in char]
            mapping = f"<{glyph_id}> <{"".join(charcodes)}>"
            mappings_cmap_format.append(mapping)

        with open(self.pdf.filename, "rb") as pdf:
            pdf_stream = pdf.read()

        found = []
        corresponding_mappings = []
        max_workers = os.cpu_count()
        size = max_workers * 2
        chunks = [
            (
                mappings_cmap_format[i::size], _ExtractorPickle(self, pdf_stream, word)
            ) for i in range(size)
        ]
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    pickle.find_corresponding_mappings, baselines, mappings, found
                ) for mappings, pickle in chunks
            ]
            for future in futures:
                corresponding_mappings.extend(future.result())

        result = {}
        for mapping in corresponding_mappings:
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


class _ExtractorPickle:
    def __init__(self, extractor: _Extractor, pdf_stream: bytes, word: str):
        pdflib: PikepdfLib = PdfLibFactory(PdfLib.PIKEPDF)
        pdf = pdflib.open(io.BytesIO(pdf_stream))
        buf = io.BytesIO()
        pdf.save(buf)

        self.pdf_stream = buf.getvalue()
        self.pno = extractor.pno
        self.font = extractor.font
        self.word = word

    def find_corresponding_mappings(
        self, lines: list[str], mappings: list[str], found: list
    ) -> list[str]:
        if len(mappings) == 1:
            found.append(mappings[0])
            return found

        half = math.ceil(len(mappings)/2)
        first_half = mappings[:half]
        second_half = mappings[half:]

        in_first_half = self.check_half(lines, first_half)
        in_second_half = self.check_half(lines, second_half)

        if in_first_half:
            found.extend(self.find_corresponding_mappings(lines, first_half, found))

        if in_second_half:
            found.extend(self.find_corresponding_mappings(lines, second_half, found))

        return found

    def check_half(self, lines: list[str], subtract: list[str]) -> bool:
        subtracted = [line for line in lines if line not in set(subtract)]
        text = self.get_updated_page_text(subtracted)

        return self.word not in text

    def get_updated_page_text(self, lines: list[str]) -> str:
        pdflib: PikepdfLib = PdfLibFactory(PdfLib.PIKEPDF)
        pdf = pdflib.open(io.BytesIO(self.pdf_stream))
        cmap = "\n".join(lines)
        data = cmap.encode()
        stream = pdf.make_stream(data)
        page = pdflib.get_page(self.pno)
        fonts = page.Resources.Font
        fonts[self.font].ToUnicode = stream
        buf = io.BytesIO()
        pdf.save(buf, linearize=False)
        updated_pdf_stream = buf.getvalue()

        return get_page_text(updated_pdf_stream, self.pno)
