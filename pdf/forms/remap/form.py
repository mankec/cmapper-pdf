from django import forms
from django.core.validators import FileExtensionValidator

from pdf.validators import validate_pdf
from pdf.constants import PDF_EXT


class RemapWordForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                "accept": "application/pdf",
                "onchange": "form.submit()",
                "class": "file-input file-input-xl",
            }
        ),
        validators=[
            FileExtensionValidator(allowed_extensions=[PDF_EXT]),
            validate_pdf
        ]
    )
