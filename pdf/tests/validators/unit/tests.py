import tempfile

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files import File

from pdf.validators import validate_pdf, INVALID_PDF_MESSAGE
from pdf.constants import PDF_EXT
from pdf.tests.helpers import create_pdf


class PdfValidatorsUnitTestCase(TestCase):
    def test_pdf_is_valid(self):
        with tempfile.NamedTemporaryFile(suffix=f".{PDF_EXT}") as tmpfile:
            create_pdf(tmpfile.name)

            with open(tmpfile.name, "rb") as f:
                pdf = File(f)
                validate_pdf(pdf)

    def test_pdf_is_invalid(self):
        with tempfile.NamedTemporaryFile(suffix=f".txt") as tmpfile:
            tmpfile.write(b"Hello!")
            tmpfile.seek(0)

            with open(tmpfile.name, "rb") as f:
                pdf = File(f)

                with self.assertRaises(ValidationError, msg=INVALID_PDF_MESSAGE):
                    validate_pdf(pdf)
