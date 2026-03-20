import tempfile

from bs4 import BeautifulSoup
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files import File

from pdf.helpers import save_pdf_to_storage
from pdf.tests.helpers import upload_pdf_without_form
from pdf.constants import PDF_EXT
from pdf.tests.helpers import create_pdf, write_pdf, remove_pdf
from pdf.services import Cmapper


class CmapperIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_show_pdf_page_in_blocks(self):
        session = self.client.session
        first_page_text = {
            "block_1": "Page one, first block's words",
            "block_2": "Page one, second block's words",
            "block_3": "Page one, third block's words",
        }
        second_page_text = {
            "block_1": "Page two, first block's words",
            "block_2": "Page two, second block's words",
            "block_3": "Page two, third block's words",
        }

        with tempfile.NamedTemporaryFile(suffix=f".{PDF_EXT}") as tmpfile:
            pdf = create_pdf(tmpfile.name)

        pdf.new_page()
        first_page = pdf[0]
        second_page= pdf[1]
        for n in range(1, 4):
            x = 10
            y = n * 20
            write_pdf(first_page, first_page_text[f"block_{n}"], x, y)
            write_pdf(second_page, second_page_text[f"block_{n}"], x, y)

        expected_blocks_len = 3
        self.assertEqual(
            expected_blocks_len, len(first_page.get_text(Cmapper.TEXT_FORMAT_BLOCKS))
        )
        self.assertEqual(
            expected_blocks_len, len(second_page.get_text(Cmapper.TEXT_FORMAT_BLOCKS))
        )

        pdf.saveIncr()
        pdf.close()

        file = File(open(pdf.name, "rb"))
        path = save_pdf_to_storage(file)
        session["uploaded_pdf_path"] = path
        session.save()

        url = reverse("pdf:page", kwargs={"pno": Cmapper.DEFAULT_PNO})
        response = self.client.get(url)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        for n in range(0, 3):
            result_set = soup.css.select(f"#page-1-block-{n}")
            self.assertInHTML(str(result_set[0]), html, 1)

            result_set = soup.css.select(f"#page-2-block-{n}")
            self.assertFalse(result_set)

        remove_pdf(pdf.name)

    def test_page_blocks_are_saved_in_session(self):
        page_blocks = [
            "First block's words",
            "Second block's words",
            "Third block's words",
        ]
        pdf = upload_pdf_without_form(self.client.session, page_blocks)

        url = reverse("pdf:page", kwargs={"pno": Cmapper.DEFAULT_PNO})
        response = self.client.get(url)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        for n in range(0, 3):
            result_set = soup.css.select(f"#page-1-block-{n}")
            self.assertInHTML(str(result_set[0]), html, 1)

        response = self.client.get(url)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        for n in range(0, 3):
            result_set = soup.css.select(f"#page-1-block-{n}")
            self.assertInHTML(str(result_set[0]), html, 1)

        url = reverse("pdf:page", kwargs={"pno": Cmapper.DEFAULT_PNO})
        response = self.client.get(url)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        for n in range(0, 3):
            result_set = soup.css.select(f"#page-1-block-{n}")
            self.assertInHTML(str(result_set[0]), html, 1)

        remove_pdf(pdf.name)
