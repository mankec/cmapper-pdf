from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

from pdf.forms.upload.form import UploadPdfForm
from pdf.services import PdfPageReader, Cmapper
from pdf.helpers import save_pdf_to_storage


def upload(request: HttpRequest) -> HttpResponseRedirect:
    form = UploadPdfForm(request.POST, request.FILES)

    if form.is_valid():
        session = request.session
        file = request.FILES["file"]
        path = save_pdf_to_storage(file)
        session["uploaded_pdf_path"] = path
        url = reverse("pdf:page", kwargs={"pno": PdfPageReader.DEFAULT_PNO})
        return redirect(url)
    return redirect("/")


def page(request: HttpRequest, pno: int) -> HttpResponse:
    session = request.session

    session.delete("mapped_chars")

    uploaded_pdf_path = session.get("uploaded_pdf_path")
    if not uploaded_pdf_path:
        return redirect("/")
    current_pno = session.get("current_pno")
    blocks = session.get("page_blocks")
    if pno != current_pno:
        word_blocks = PdfPageReader(uploaded_pdf_path, pno).get_word_blocks()
        session["page_blocks"] = blocks
        session["current_pno"] = pno
    ctx = {
        "pno": pno,
        "word_blocks": word_blocks,
    }
    return render(request, "pdf/page.html", ctx)


def word(request: HttpRequest, pno: int, word: str) -> HttpResponse:
    session = request.session
    uploaded_pdf_path = session.get("uploaded_pdf_path")
    if not uploaded_pdf_path:
        return redirect("/")
    font = request.GET.get("font")
    mapped_chars = session.get("mapped_chars")
    if not mapped_chars:
        mapped_chars = Cmapper(uploaded_pdf_path, pno).extract_mapped_chars(word, font)
        session["mapped_chars"] = mapped_chars
    ctx = {
        "pno": pno,
        "word": word,
        "chars": [mapped["char"] for mapped in mapped_chars],
        "mapped_chars": mapped_chars,
    }
    return render(request, "pdf/word.html", ctx)


def remap(request: HttpRequest, pno: int, word: str) -> HttpResponseRedirect:
    pass
