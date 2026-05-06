import tempfile

from bs4 import BeautifulSoup
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files import File

from pdf.helpers import uploaded_pdf_path
from pdf.constants import DEFAULT_PNO, TEXT_FORMAT_DICT
from pdf.models import Pdf
from pdf.tests.helpers import remove_tmpdir, PDF_SAMPLE_JIBBERISH_ON_READ, get_test_user, upload_pdf, create_pdf, write_pdf, stub_request_user
from pdf.services import Cmapper


class CmapperIntegrationTestCase(TestCase):
    fixtures = ["users.json"]

    def setUp(self):
        # This font corresponds to /C0_4 font in '  -on-read.pdf', page 1
        self.font = "Fd3376094"
        self.client = Client()
        file = File(open(PDF_SAMPLE_JIBBERISH_ON_READ, "rb"))
        pdf = Pdf.objects.create(file=file)
        self.user = get_test_user()
        self.user.pdf = pdf
        self.user.save()
        filename = uploaded_pdf_path(pdf.file.name)
        cmapper = Cmapper(filename, DEFAULT_PNO)
        cmapper.create_fonts(pdf.id)

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

    def test_single_unicode_codepoints(self):
        word = "ошворени"
        url = reverse("pdf:word", kwargs={"pno": DEFAULT_PNO, "word": word})
        url = f"{url}?font={self.font}"

        with stub_request_user(self.user):
            response = self.client.get(url)

        soup = BeautifulSoup(response.text, "html.parser")
        word_list = list(word)
        mapped_chars = [
            {'char': 'о', 'glyph_id': '0EC4', 'font': '/C0_4'}, {'char': 'ш', 'glyph_id': '10D1', 'font': '/C0_4'}, {'char': 'в', 'glyph_id': '0BE4', 'font': '/C0_4'}, {'char': 'о', 'glyph_id': '0EC4', 'font': '/C0_4'}, {'char': 'р', 'glyph_id': '0F2D', 'font': '/C0_4'}, {'char': 'е', 'glyph_id': '0C21', 'font': '/C0_4'}, {'char': 'н', 'glyph_id': '0E6A', 'font': '/C0_4'}, {'char': 'и', 'glyph_id': '0CF4', 'font': '/C0_4'}
        ]

        text_inputs = soup.find_all("input", attrs={"type":"text"})
        self.assertEqual(len(text_inputs), len(word_list))

        for mapped in mapped_chars:
            char = mapped["char"]
            char_inputs = soup.find_all("input", attrs={"name": mapped["glyph_id"]})
            char_spans = soup.find_all("span", text=char)
            count = word_list.count(char)
            self.assertEqual(len(char_inputs), count)
            self.assertEqual(len(char_spans), count)

    def test_multiple_unicode_codepoints(self):
        word = "ca.мof.nacHUK"
        url = reverse("pdf:word", kwargs={"pno": DEFAULT_PNO, "word": word})
        url = f"{url}?font={self.font}"

        with stub_request_user(self.user):
            response = self.client.get(url)

        soup = BeautifulSoup(response.text, "html.parser")
        word_list = ["c", "a.м", "o", "f.n", "a", 'c', 'H', 'U', 'K']

        mapped_chars = [
            {'char': 'c', 'glyph_id': '058D', 'font': '/C0_4'}, {'char': 'a.м', 'glyph_id': '056F', 'font': '/C0_4'}, {'char': 'o', 'glyph_id': '07D2', 'font': '/C0_4'}, {'char': 'f.n', 'glyph_id': '05F1', 'font': '/C0_4'}, {'char': 'a', 'glyph_id': '0549', 'font': '/C0_4'}, {'char': 'c', 'glyph_id': '058D', 'font': '/C0_4'}, {'char': 'H', 'glyph_id': '046A', 'font': '/C0_4'}, {'char': 'U', 'glyph_id': '04E9', 'font': '/C0_4'}, {'char': 'K', 'glyph_id': '04A4', 'font': '/C0_4'}
        ]

        text_inputs = soup.find_all("input", attrs={"type":"text"})
        self.assertEqual(len(text_inputs), len(mapped_chars))

        for mapped in mapped_chars:
            char = mapped["char"]
            char_inputs = soup.find_all("input", attrs={"name": mapped["glyph_id"]})
            char_spans = soup.find_all("span", text=char)
            count = word_list.count(char)
            self.assertEqual(len(char_inputs), count)
            self.assertEqual(len(char_spans), count)

    def test_remap_word(self):
        session = self.client.session
        session["word_font"] = self.font
        session.save()

        # Word appears twice
        count = 2
        invalid = "ca.мof.nacHUK"
        valid = "самогласник"

        url = reverse("pdf:page", kwargs={"pno": DEFAULT_PNO})

        with stub_request_user(self.user):
            response = self.client.get(url)

            self.assertEqual(response.text.count(invalid), count)
            self.assertEqual(response.text.count(valid), 0)

            remapped = {
                '058D': 'с', '056F': 'ам', '07D2': 'о', '05F1': 'гл', '0549': 'а', '046A': 'н', '04E9': 'и', '04A4': 'к'
            }
            url = reverse("pdf:remap", kwargs={"pno": DEFAULT_PNO, "word": invalid})
            response = self.client.post(url, remapped, follow=True)
            self.assertEqual(response.text.count(valid), count)
            self.assertEqual(response.text.count(invalid), 0)
