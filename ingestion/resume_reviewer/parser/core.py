"""Public entry-point for the Parser module."""

from __future__ import annotations

import json
from collections import namedtuple
from pathlib import Path

from .detector import detect
from .pdf_parser import extract as pdf_extract
from .docx_parser import extract as docx_extract
from .image_parser import extract as img_extract
from .cleanup import strip_headers_footers, normalize_whitespace
from .markdown_utils import to_markdown
from .structure import to_schema
import pdfplumber

# --------------------------------------------------------------------------- #
class ParsedResume(namedtuple("ParsedResume", ["text", "metadata", "structured"])):
    """Immutable return object with JSON helpers."""
    __slots__ = ()

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "metadata": self.metadata,
            "structured": self.structured,
        }

    def to_json(self, **json_kwargs) -> str:
        default = {"ensure_ascii": False, "indent": 2}
        default.update(json_kwargs)
        return json.dumps(self.to_dict(), **default)
# --------------------------------------------------------------------------- #


def parse_resume(
    path: str | Path,
    *,
    convert_to_md: bool = True,
) -> ParsedResume:
    """
    Parse a résumé file and return cleaned text + metadata.

    Parameters
    ----------
    path : str | Path
        File to parse (PDF, DOCX, or image).
    convert_to_md : bool, default True
        Convert cleaned text to Markdown.

    Returns
    -------
    ParsedResume
    """
    path = Path(path).expanduser().resolve()
    filetype = detect(path)

    # ---------- extraction --------------------------------------------------
    if filetype == "pdf":
        raw_text = pdf_extract(path)
        # Get page count for PDFs
        with pdfplumber.open(path) as pdf:
            page_count = len(pdf.pages)
    elif filetype == "docx":
        raw_text = docx_extract(path)
        page_count = 1  # DOCX files are typically single-page documents
    elif filetype in {"jpg", "jpeg", "png", "tiff"}:
        raw_text = img_extract(path)
        page_count = 1  # Images are single-page
    else:
        raise ValueError(f"Unsupported file type: {filetype}")

    # ---------- cleanup -----------------------------------------------------
    cleaned = normalize_whitespace(strip_headers_footers(raw_text))
        # ---------- optional Markdown conversion -------------------------------
    if convert_to_md:
        cleaned = to_markdown(cleaned)

    structured = to_schema(cleaned, filepath=path)
    structured["meta"]["page_count"] = page_count

    return ParsedResume(
        text=cleaned,
        metadata={"filetype": filetype, "source": str(path)},
        structured=structured,
    )



