from django.db import models

from pdf.helpers import upload_pdf_path


class Pdf(models.Model):
    file = models.FileField(upload_to=upload_pdf_path, editable=True)

    class Meta:
        db_table = "pdf"
