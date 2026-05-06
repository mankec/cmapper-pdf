import os

from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

from pdf.forms.upload.form import UploadPdfForm
from pdf.services import Cmapper
from pdf.constants import DEFAULT_PNO
from pdf.models import Pdf
from pdf.helpers import uploaded_pdf_path
from project.settings import MEDIA_ROOT


def upload(request: HttpRequest) -> HttpResponseRedirect:
    form = UploadPdfForm(request.POST, request.FILES)

    if form.is_valid():
        file = request.FILES["file"]
        user = request.user
        user.pdf = Pdf.objects.create(file=file)
        user.save(update_fields=["pdf"])
        url = reverse("pdf:page", kwargs={"pno": DEFAULT_PNO})
        return redirect(url)
    return redirect("/")


def page(request: HttpRequest, pno: int) -> HttpResponse:
    session = request.session
    pdf = request.user.pdf

    session.pop("mapped_chars", None)

    if not pdf:
        return redirect("/")

    current_pno = session.get("current_pno")
    word_blocks = session.get("word_blocks")
    if pno != current_pno:
        filename = os.path.join(MEDIA_ROOT, pdf.file.name)
        word_blocks = Cmapper(filename, pno).get_word_blocks()
        session["word_blocks"] = word_blocks
        session["current_pno"] = pno
    ctx = {
        "pno": pno,
        "word_blocks": word_blocks,
    }
    return render(request, "pdf/page.html", ctx)


def word(request: HttpRequest, pno: int, word: str) -> HttpResponse:
    session = request.session
    pdf = request.user.pdf
    if not pdf:
        return redirect("/")

    font = request.GET.get("font")
    session["word_font"] = font
    mapped_chars = session.get("mapped_chars")
    if not mapped_chars:
        mapped_chars = Cmapper(uploaded_pdf_path(request.user.pdf.file.name), pno).extract_mapped_chars(word, font)
        session["mapped_chars"] = mapped_chars
    ctx = {
        "pno": pno,
        "word": word,
        "chars": [mapped["char"] for mapped in mapped_chars],
        "mapped_chars": mapped_chars,
    }
    return render(request, "pdf/word.html", ctx)

# Word param isn't used but is necessary for URL structure
def remap(request: HttpRequest, pno: int, word: str) -> HttpResponseRedirect:
    session = request.session
    pdf = request.user.pdf
    if not pdf:
        return redirect("/")

    font = session["word_font"]
    remap_chars = {
        k: v for k, v in request.POST.items()
        if k != "csrfmiddlewaretoken"
    }
    filename = uploaded_pdf_path(pdf.file.name)
    cmapper = Cmapper(filename, pno)
    cmapper.remap(remap_chars, font)
    session["word_blocks"] = cmapper.get_word_blocks()
    pno = session["current_pno"]
    url = reverse("pdf:page", kwargs={"pno": pno})
    return redirect(url)
