from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

from pdf.forms.upload.form import UploadPdfForm
from pdf.helpers import clear_user_pdf


def index(request: HttpRequest) -> HttpResponse:
    request.session.flush()
    clear_user_pdf()

    ctx = {
        "upload_pdf_form": UploadPdfForm()
    }
    return render(request, "core/index.html", ctx)
