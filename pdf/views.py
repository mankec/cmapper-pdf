from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

from pdf.forms.upload.form import UploadPdfForm
from pdf.services import PdfPage
from pdf.helpers import save_pdf_to_storage


def upload(request: HttpRequest) -> HttpResponseRedirect:
    form = UploadPdfForm(request.POST, request.FILES)

    if form.is_valid():
        session = request.session
        file = request.FILES["file"]
        path = save_pdf_to_storage(file)
        session["uploaded_pdf_path"] = path
        url = reverse("pdf:page", kwargs={"pno": PdfPage.DEFAULT_PNO})
        return redirect(url)
    return redirect("/")


def page(request: HttpRequest, pno: int) -> HttpResponse:
    session = request.session
    uploaded_pdf_path = session.get("uploaded_pdf_path")
    if not uploaded_pdf_path:
        return redirect("/")
    current_pno = session.get("current_pno")
    word_blocks = session.get("word_blocks")
    if pno != current_pno:
        word_blocks = PdfPage(uploaded_pdf_path, pno).get_word_blocks()
        session["word_blocks"] = word_blocks
        session["current_pno"] = pno
    ctx = {
        "pno": pno,
        "word_blocks": word_blocks,
    }
    return render(request, "pdf/page.html", ctx)


def word(request: HttpRequest, pno: int, word: str) -> HttpResponse:
    pass
