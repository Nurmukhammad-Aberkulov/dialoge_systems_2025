import pdfplumber
from pathlib import Path

def pdf_to_text(pdf_path: str, max_chars: int = 15000) -> str:
    """
    Extracts text from first N characters of a PDF using pdfplumber.
    Stops once max_chars is reached to control token costs.
    """
    pdf_path = Path(pdf_path)
    assert pdf_path.exists(), f"{pdf_path} not found"

    collected = []
    chars = 0

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if not page_text:
                continue
            if chars + len(page_text) > max_chars:
                page_text = page_text[: max_chars - chars]
            collected.append(page_text)
            chars += len(page_text)
            if chars >= max_chars:
                break

    return "\n\n".join(collected)
