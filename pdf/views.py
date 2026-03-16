from pathlib import Path

from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.urls import reverse
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

from pdf.forms.upload.form import UploadPdfForm
from core.utils import upload_pdf_path, clear_user_pdf


def index(request: HttpRequest) -> HttpResponse:
    request.session.flush()
    clear_user_pdf()

    ctx = {
        "upload_pdf_form": UploadPdfForm()
    }
    return render(request, "pdf/index.html", ctx)


def upload(request: HttpRequest) -> HttpResponseRedirect:
    form = UploadPdfForm(request.POST, request.FILES)

    if form.is_valid():
        session = request.session
        file = request.FILES["file"]
        data = bytearray()
        for chunk in file.chunks():
            data += chunk
        path = default_storage.save(
            upload_pdf_path(file.name), ContentFile(bytes(data))
        )
        session["uploaded_pdf_path"] = path
        url = reverse("pdf:preview")
        return redirect(url)
    return redirect("/")


def preview(request: HttpRequest) -> HttpResponse:
    uploaded_pdf_path = request.session.get("uploaded_pdf_path")
    if not uploaded_pdf_path:
        return redirect("/")
    ctx = {}
    return render(request, "pdf/preview.html", ctx)
