from pathlib import Path

from project.settings import MEDIA_ROOT


def upload_pdf_path(name: str) -> str:
    basename = name.split('/')[-1]
    return f"user/pdf/{basename}"

def uploaded_pdf_path(name: str) -> str:
    basename = name.split('/')[-1]
    return f"{MEDIA_ROOT}/user/pdf/{basename}"

def clear_user_pdf() -> None:
    fd = Path(f"{MEDIA_ROOT}/user/pdf")
    for file in fd.iterdir():
        file.unlink()
