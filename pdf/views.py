from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

from pdf.forms.upload.form import UploadPdfForm
from pdf.services import Cmapper
from pdf.helpers import save_pdf_to_storage
from pdf.constants import DEFAULT_PNO
from pdf.utils import get_word_blocks


def upload(request: HttpRequest) -> HttpResponseRedirect:
    form = UploadPdfForm(request.POST, request.FILES)

    if form.is_valid():
        session = request.session
        file = request.FILES["file"]
        path = save_pdf_to_storage(file)
        session["uploaded_pdf_path"] = path
        url = reverse("pdf:page", kwargs={"pno": DEFAULT_PNO})
        return redirect(url)
    return redirect("/")


def page(request: HttpRequest, pno: int) -> HttpResponse:
    session = request.session

    session.pop("mapped_chars", None)

    uploaded_pdf_path = session.get("uploaded_pdf_path")
    if not uploaded_pdf_path:
        return redirect("/")
    current_pno = session.get("current_pno")
    word_blocks = session.get("word_blocks")
    if pno != current_pno:
        word_blocks = get_word_blocks(uploaded_pdf_path, pno)
        session["word_blocks"] = word_blocks
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
    session["word_font"] = font
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
    session = request.session
    uploaded_pdf_path = session.get("uploaded_pdf_path")
    if not uploaded_pdf_path:
        return redirect("/")
    font = session["word_font"]
    remap_chars = {
        k: v for k, v in request.POST.items()
        if k != "csrfmiddlewaretoken"
    }
    Cmapper(uploaded_pdf_path, pno).remap(remap_chars, font)
    session["word_blocks"] = get_word_blocks(uploaded_pdf_path, pno)
    pno = session["current_pno"]
    url = reverse("pdf:page", kwargs={"pno": pno})
    return redirect(url)
