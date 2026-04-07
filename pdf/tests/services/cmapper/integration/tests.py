from bs4 import BeautifulSoup
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files import File

from pdf.helpers import save_pdf_to_storage
from pdf.tests.helpers import remove_tmpdir, PDF_SAMPLE_JIBBERISH_ON_READ
from pdf.constants import DEFAULT_PNO


class CmapperIntegrationTestCase(TestCase):
    def setUp(self):
        # This font corresponds to /C0_4 font in 'jibberish-on-read.pdf', page 1
        self.font = "Fd3376094"
        self.client = Client()
        session = self.client.session
        file = File(open(PDF_SAMPLE_JIBBERISH_ON_READ, "rb"))
        session["uploaded_pdf_path"] = save_pdf_to_storage(file)
        session.save()

    def tearDown(self):
        remove_tmpdir()

    def test_single_unicode_codepoints(self):
        word = "ошворени"
        url = reverse("pdf:word", kwargs={"pno": DEFAULT_PNO, "word": word})
        url = f"{url}?font={self.font}"
        response = self.client.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        word_list = list(word)
        mapped_chars = [
            {'char': 'о', 'glyph_id': '0EC4', 'font': '/C0_4'}, {'char': 'ш', 'glyph_id': '10D1', 'font': '/C0_4'}, {'char': 'в', 'glyph_id': '0BE4', 'font': '/C0_4'}, {'char': 'о', 'glyph_id': '0EC4', 'font': '/C0_4'}, {'char': 'р', 'glyph_id': '0F2D', 'font': '/C0_4'}, {'char': 'е', 'glyph_id': '0C21', 'font': '/C0_4'}, {'char': 'н', 'glyph_id': '0E6A', 'font': '/C0_4'}, {'char': 'и', 'glyph_id': '0CF4', 'font': '/C0_4'}
        ]


        text_inputs = soup.find_all("input", attrs={"type":"text"})
        self.assertEqual(len(text_inputs), len(word_list))

        for mapped in mapped_chars:
            glyph_id = mapped["glyph_id"]
            char = mapped["char"]
            char_inputs = soup.find_all("input", attrs={"name": glyph_id})
            char_spans = soup.find_all("span", text=char)
            count = word_list.count(char)
            self.assertEqual(len(char_inputs), count)
            self.assertEqual(len(char_spans), count)


    def test_multiple_unicode_codepoints(self):
        word = "ca.мof.nacHUK"
        url = reverse("pdf:word", kwargs={"pno": DEFAULT_PNO, "word": word})
        url = f"{url}?font={self.font}"
        response = self.client.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        word_list = ["c", "a.м", "o", "f.n", "a", 'c', 'H', 'U', 'K']

        mapped_chars = [
            {'char': 'c', 'glyph_id': '058D', 'font': '/C0_4'}, {'char': 'a.м', 'glyph_id': '056F', 'font': '/C0_4'}, {'char': 'o', 'glyph_id': '07D2', 'font': '/C0_4'}, {'char': 'f.n', 'glyph_id': '05F1', 'font': '/C0_4'}, {'char': 'a', 'glyph_id': '0549', 'font': '/C0_4'}, {'char': 'c', 'glyph_id': '058D', 'font': '/C0_4'}, {'char': 'H', 'glyph_id': '046A', 'font': '/C0_4'}, {'char': 'U', 'glyph_id': '04E9', 'font': '/C0_4'}, {'char': 'K', 'glyph_id': '04A4', 'font': '/C0_4'}
        ]

        text_inputs = soup.find_all("input", attrs={"type":"text"})
        self.assertEqual(len(text_inputs), len(mapped_chars))

        for mapped in mapped_chars:
            glyph_id = mapped["glyph_id"]
            char = mapped["char"]
            char_inputs = soup.find_all("input", attrs={"name": glyph_id})
            char_spans = soup.find_all("span", text=char)
            count = word_list.count(char)
            self.assertEqual(len(char_inputs), count)
            self.assertEqual(len(char_spans), count)

    def test_remap_word(self):
        session = self.client.session
        session["word_font"] = self.font
        session.save()

        count = 2
        invalid = "ca.мof.nacHUK"
        valid = "самогласник"

        url = reverse("pdf:page", kwargs={"pno": DEFAULT_PNO})
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
