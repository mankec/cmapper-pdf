from http import HTTPStatus

from bs4 import BeautifulSoup
from django.test import TestCase, Client
from django.urls import reverse

from pdf.tests.helpers import remove_tmpdir, upload_pdf_without_form
from pdf.services import Cmapper

class PdfPageViewIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def tearDown(self):
        remove_tmpdir()

    def test_word_in_url_is_same_as_one_in_text(self):
        page_blocks = [
            "First block's words",
            "Second block's words",
            "Third block's words",
        ]
        word = "words"
        pdf = upload_pdf_without_form(self.client.session, page_blocks)
        url = reverse("pdf:page", kwargs={"pno": Cmapper.DEFAULT_PNO})
        response = self.client.get(url)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        remap_url = reverse("pdf:remap", kwargs={"pno": Cmapper.DEFAULT_PNO, "word": word})
        result_set = soup.find_all(href=remap_url)
        self.assertEqual(3, len(result_set))

        response = self.client.get(remap_url)
        self.assertEqual(HTTPStatus.OK.value, response.status_code)
