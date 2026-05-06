from django.db import models

from pdf.helpers import upload_pdf_path
from pdf.constants import MAX_VARCHAR_LENGTH


class Pdf(models.Model):
    file = models.FileField(upload_to=upload_pdf_path, editable=True)

    class Meta:
        db_table = "pdf"


class Font(models.Model):
    name = models.CharField(max_length=MAX_VARCHAR_LENGTH)
    cmap = models.TextField()
    cmap_name = models.CharField(blank=True, max_length=MAX_VARCHAR_LENGTH)

    pdf = models.ForeignKey(Pdf, on_delete=models.CASCADE, related_name="fonts")

    @classmethod
    def get_cmap_name(cls, cmap):
        return cmap.splitlines()[9].split(" ")[1]

    class Meta:
        db_table = "font"
