import pymupdf
from django.core.exceptions import ValidationError
from django.core.files import File

from pdf.constants import PDF_EXT


INVALID_PDF_MESSAGE = "Uploaded PDF is invalid"


def validate_pdf(file: File) -> None:
    try:
        data = bytearray()
        for chunk in file.chunks():
            data += chunk

        pymupdf.open(stream=data, filetype=PDF_EXT)
    except RuntimeError:
        # Catch general error since it only matters if PDF is valid
        raise ValidationError(
            message=INVALID_PDF_MESSAGE,
            code="invalid_pdf",
        )
