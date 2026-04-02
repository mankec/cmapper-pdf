from enum import StrEnum

from pdf.libs import BasePdfLib, PymupdfLib, PikepdfLib


class PdfLib(StrEnum):
    PYMUPDF = "pymupdf"
    PIKEPDF = "pikepdf"


class PdfLibFactory:
    def __new__(cls, lib: str) -> BasePdfLib:
        match lib:
            case PdfLib.PYMUPDF:
                return PymupdfLib()
            case PdfLib.PIKEPDF:
                return PikepdfLib()
            case _:
                raise ValueError("Unknown PDF library")
