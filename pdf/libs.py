from pathlib import Path
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import pymupdf
import pikepdf
from pymupdf import Document as PymupdfDocument, Page as PymupdfPage
from pikepdf import Pdf as PikepdfDocument, Page as PikepdfPage

from pdf.helpers import uploaded_pdf_path


TDocument = TypeVar("TDocument")
TPage = TypeVar("TPage")


class BasePdfLib(Generic[TDocument, TPage], ABC):
    pdf: TDocument | None

    def __init__(self):
        self.pdf = None

    @abstractmethod
    def open(self, filename_or_stream: str | bytes) -> TDocument:
        ...

    @abstractmethod
    def get_page(self, pno: int | str) -> TPage:
        ...


class PymupdfLib(BasePdfLib[PymupdfDocument, PymupdfPage]):
    def open(self, filename_or_stream: str | bytes, *args, **kwargs) -> PymupdfDocument:
        if isinstance(filename_or_stream, str):
            filename = uploaded_pdf_path(filename_or_stream)
            pdf = pymupdf.open(filename, *args, **kwargs)
        else:
            pdf = pymupdf.open(stream=filename_or_stream)

        self.pdf = pdf
        return pdf

    def get_page(self, pno: str | int) -> PymupdfPage:
        if not self.pdf:
            raise AttributeError("You must open the PDF before getting the page")

        # Convert to proper number since first number is 1 instead of 0, because of UX
        pno = int(pno) - 1

        return self.pdf.load_page(pno)


class PikepdfLib(BasePdfLib[PikepdfDocument, PikepdfPage]):
    def open(self, filename_or_stream: str | bytes, *args, **kwargs) -> PikepdfDocument:
        if isinstance(filename_or_stream, str):
            filename = uploaded_pdf_path(filename_or_stream)
            pdf = pikepdf.open(filename, *args, **kwargs)
        else:
            stream = filename_or_stream
            pdf = pikepdf.open(stream, *args, **kwargs)

        self.pdf = pdf
        return pdf

    def get_page(self, pno: str | int) -> PikepdfPage:
        if not self.pdf:
            raise AttributeError("You must open the PDF before getting the page")

        # Convert to proper number since first number is 1 instead of 0, because of UX
        pno = int(pno) - 1

        return self.pdf.pages[pno]
