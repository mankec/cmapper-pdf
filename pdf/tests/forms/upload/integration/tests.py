import tempfile
from pathlib import Path

from django.test import TestCase, Client
from django.urls import reverse

from pdf.constants import PDF_EXT
from pdf.tests.helpers import create_pdf
from core.utils import uploaded_pdf_path


class UploadPdfFormIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_upload_valid_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=f".{PDF_EXT}") as tmpfile:
            create_pdf(tmpfile.name)

            with open(tmpfile.name, "rb") as pdf:
                url = reverse("pdf:upload")
                redirect_url = reverse("pdf:preview")
                response = self.client.post(url, {"file": pdf})
                self.assertRedirects(response, redirect_url)

            Path(
                uploaded_pdf_path(tmpfile.name)
            ).unlink()

    def test_upload_invalid_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=f".{PDF_EXT}") as tmpfile:
            with open(tmpfile.name, "rb") as pdf:
                url = reverse("pdf:upload")
                response = self.client.post(url, {"file": pdf})
                self.assertRedirects(response, "/")
