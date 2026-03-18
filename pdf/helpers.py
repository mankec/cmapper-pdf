from pathlib import Path

from django.core.files.base import File, ContentFile
from django.core.files.storage import default_storage

from project.settings import MEDIA_ROOT


def clear_user_pdf() -> None:
    fd = Path(f"{MEDIA_ROOT}/user/pdf")
    for file in fd.iterdir():
        if file.name == ".gitkeep":
            continue
        file.unlink()


def upload_pdf_path(name: str) -> str:
    basename = name.split('/')[-1]
    return f"user/pdf/{basename}"


def uploaded_pdf_path(name: str) -> str:
    basename = name.split('/')[-1]
    return f"{MEDIA_ROOT}/user/pdf/{basename}"


def save_pdf_to_storage(file: File) -> str:
    content_file = ContentFile(b"")

    for chunk in file.chunks():
        content_file.write(chunk)
    return default_storage.save(
        upload_pdf_path(file.name), content_file
    )
