import tempfile

from bs4 import BeautifulSoup
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files import File

from pdf.tests.helpers import stub_request_user, upload_pdf, create_pdf, write_pdf, remove_tmpdir, get_test_user
from pdf.constants import TEXT_FORMAT_DICT, DEFAULT_PNO
from pdf.models import Pdf


class PdfViewsTestCase(TestCase):
    fixtures = ["users.json"]

    def setUp(self):
        self.client = Client()
        self.user = get_test_user()

    def tearDown(self):
        remove_tmpdir()

    def test_show_pdf_page_in_word_blocks(self):
        helvetica = "Helvetica"
        first_page_blocks = [
            "Page one, first block's words",
            "Page one, second block's words",
            "Page one, third block's words",
        ]
        second_page_blocks = [
            "Page two, first block's words",
            "Page two, second block's words",
            "Page two, third block's words",
        ]

        with tempfile.NamedTemporaryFile(suffix=f".pdf") as tmpfile:
            doc = create_pdf(tmpfile.name)

        doc.new_page()
        first_page = doc[0]
        second_page= doc[1]
        for i in range(0, 3):
            x = 10
            y = (i + 1) * 20
            write_pdf(first_page, first_page_blocks[i], x, y)
            write_pdf(second_page, second_page_blocks[i], x, y)

        expected_blocks_len = 3
        self.assertEqual(
            expected_blocks_len, len(first_page.get_text(TEXT_FORMAT_DICT)["blocks"])
        )
        self.assertEqual(
            expected_blocks_len, len(second_page.get_text(TEXT_FORMAT_DICT)["blocks"])
        )

        doc.saveIncr()

        first_page_text = first_page.get_text()

        doc.close()

        file = File(open(doc.name, "rb"))
        pdf = Pdf.objects.create(file=file)
        self.user.pdf = pdf
        self.user.save()

        url = reverse("pdf:page", kwargs={"pno": DEFAULT_PNO})

        with stub_request_user(self.user):
            response = self.client.get(url)

        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        for i in range(0, 3):
            result_set = soup.css.select(f"#page-1-block-{i}")
            self.assertInHTML(str(result_set[0]), html, 1)

            result_set = soup.css.select(f"#page-2-block-{i}")
            self.assertFalse(result_set)

        for sentence in first_page_blocks:
            for word in sentence.split(" "):
                word_url = reverse("pdf:word", kwargs={"pno": DEFAULT_PNO, "word": word})
                word_url += f"?font={helvetica}"
                link = soup.find(href=word_url)
                self.assertInHTML(str(link), html, first_page_text.count(word))

    def test_page_blocks_are_saved_in_session(self):
        page_blocks = [
            "First block's words",
            "Second block's words",
            "Third block's words",
        ]
        upload_pdf(self.user, page_blocks)

        url = reverse("pdf:page", kwargs={"pno": DEFAULT_PNO})

        with stub_request_user(self.user):
            response = self.client.get(url)

            html = response.text
            soup = BeautifulSoup(html, "html.parser")
            for i in range(0, 3):
                result_set = soup.css.select(f"#page-1-block-{i}")
                self.assertInHTML(str(result_set[0]), html, 1)

            response = self.client.get(url)

            html = response.text
            soup = BeautifulSoup(html, "html.parser")
            for i in range(0, 3):
                result_set = soup.css.select(f"#page-1-block-{i}")
                self.assertInHTML(str(result_set[0]), html, 1)

            url = reverse("pdf:page", kwargs={"pno": DEFAULT_PNO})

            response = self.client.get(url)

            html = response.text
            soup = BeautifulSoup(html, "html.parser")
            for i in range(0, 3):
                result_set = soup.css.select(f"#page-1-block-{i}")
                self.assertInHTML(str(result_set[0]), html, 1)
