import tempfile

from django.test import TestCase, Client
from django.urls import reverse

from pdf.constants import PDF_EXT
from pdf.tests.helpers import create_pdf, remove_tmpdir
from pdf.services import PdfPage


class UploadPdfFormIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def tearDown(self):
        remove_tmpdir()

    def test_upload_valid_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=f".{PDF_EXT}") as tmpfile:
            create_pdf(tmpfile.name)

            with open(tmpfile.name, "rb") as pdf:
                url = reverse("pdf:upload")
                redirect_url = reverse("pdf:page", kwargs={"pno": PdfPage.DEFAULT_PNO})
                response = self.client.post(url, {"file": pdf})
                self.assertRedirects(response, redirect_url)

    def test_upload_invalid_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=f".{PDF_EXT}") as tmpfile:
            with open(tmpfile.name, "rb") as pdf:
                url = reverse("pdf:upload")
                response = self.client.post(url, {"file": pdf})
                self.assertRedirects(response, "/")
