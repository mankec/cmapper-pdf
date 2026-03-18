from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.urls import reverse
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

from pdf.forms.upload.form import UploadPdfForm
from pdf.services import Cmapper
from pdf.helpers import save_pdf_to_storage


def upload(request: HttpRequest) -> HttpResponseRedirect:
    form = UploadPdfForm(request.POST, request.FILES)

    if form.is_valid():
        session = request.session
        file = request.FILES["file"]
        path = save_pdf_to_storage(file)
        session["uploaded_pdf_path"] = path
        url = reverse("pdf:page", kwargs={"pno": Cmapper.DEFAULT_PNO})
        return redirect(url)
    return redirect("/")


def page(request: HttpRequest, pno: int = Cmapper.DEFAULT_PNO) -> HttpResponse:
    session = request.session
    uploaded_pdf_path = session.get("uploaded_pdf_path")
    if not uploaded_pdf_path:
        return redirect("/")
    current_pno = session.get("current_pno")
    text = session.get("page_text")
    if pno != current_pno:
        file = default_storage.open(uploaded_pdf_path)
        blocks = Cmapper(file, pno).read()
        session["page_text"] = text
        session["current_pno"] = pno
    ctx = {
        "pno": pno,
        "blocks": blocks,
    }
    return render(request, "pdf/page.html", ctx)
