import pymupdf


def create_pdf(name: str) -> None:
    doc = pymupdf.open()
    doc.new_page()
    doc.save(name)
    doc.close()
