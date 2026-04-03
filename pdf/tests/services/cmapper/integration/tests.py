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

        text_inputs = soup.find_all("input", attrs={"type":"text"})
        self.assertEqual(len(text_inputs), len(word_list))

        for char in word_list:
            char_inputs = soup.find_all("input", attrs={"name": char})
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

        text_inputs = soup.find_all("input", attrs={"type":"text"})
        self.assertEqual(len(text_inputs), len(word_list))

        for char in word_list:
            char_inputs = soup.find_all("input", attrs={"name": char})
            char_spans = soup.find_all("span", text=char)
            count = word_list.count(char)
            self.assertEqual(len(char_inputs), count)
            self.assertEqual(len(char_spans), count)
