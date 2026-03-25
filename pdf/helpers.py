import os
from pathlib import Path

from django.core.files.base import File, ContentFile
from django.core.files.storage import default_storage

from project.settings import MEDIA_ROOT, IS_TEST, TMPDIR


def clear_user_pdf() -> None:
    joined = os.path.join(MEDIA_ROOT, "user", "pdf")
    fd = Path(joined)
    for file in fd.iterdir():
        if file.name == ".gitkeep":
            continue
        file.unlink()


def upload_pdf_path(name: str) -> str:
    basename = name.split('/')[-1]
    upload_path = os.path.join("user", "pdf", basename)
    if IS_TEST:
        if not Path(TMPDIR).exists():
            Path.mkdir(TMPDIR)
        return os.path.join("tmp", upload_path)
    return upload_path


def uploaded_pdf_path(name: str) -> str:
    return os.path.join(
        MEDIA_ROOT, upload_pdf_path(name)
    )


def save_pdf_to_storage(file: File) -> str:
    content_file = ContentFile(b"")

    for chunk in file.chunks():
        content_file.write(chunk)
    return default_storage.save(
        upload_pdf_path(file.name), content_file
    )


def to_char(hex_digits: str) -> str:
    return chr(int(hex_digits, 16))


def to_unicode(char: str) -> str:
    utf_8_encoding = hex(ord(char))
    return utf_8_encoding.replace("x", "").zfill(4).upper()


def chunked_list(text: str, chunk_size: int) -> list:
    # Use this only when you know exact length of text and you want equal or close to equal chunks
    chunked = []
    from_idx = 0
    to_idx = chunk_size

    while to_idx <= len(text):
        chunked.append(text[from_idx:to_idx])

        from_idx = to_idx
        to_idx += chunk_size

    return chunked
