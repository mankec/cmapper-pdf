from pathlib import Path

from django.core.files.base import File, ContentFile
from django.core.files.storage import default_storage

from project.settings import MEDIA_ROOT, IS_TEST, TMPDIR


def clear_user_pdf() -> None:
    fd = Path(f"{MEDIA_ROOT}/user/pdf")
    for file in fd.iterdir():
        if file.name == ".gitkeep":
            continue
        file.unlink()


def upload_pdf_path(name: str) -> str:
    basename = name.split('/')[-1]
    upload_path = f"user/pdf/{basename}"
    if IS_TEST:
        if not Path(TMPDIR).exists():
            Path.mkdir(TMPDIR)
        return "tmp/" + upload_path
    return upload_path


def uploaded_pdf_path(name: str) -> str:
    return MEDIA_ROOT + upload_pdf_path(name)


def save_pdf_to_storage(file: File) -> str:
    content_file = ContentFile(b"")

    for chunk in file.chunks():
        content_file.write(chunk)
    return default_storage.save(
        upload_pdf_path(file.name), content_file
    )
