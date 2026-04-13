from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from environs import Env

from pdf.forms.upload.form import UploadPdfForm
from pdf.helpers import clear_user_pdf
from project.settings import IS_PRODUCTION

env = Env()


def index(request: HttpRequest) -> HttpResponse:
    request.session.pop("uploaded_pdf_path", None)
    if not IS_PRODUCTION:
        clear_user_pdf()

    ctx = {
        "upload_pdf_form": UploadPdfForm()
    }
    return render(request, "core/index.html", ctx)
