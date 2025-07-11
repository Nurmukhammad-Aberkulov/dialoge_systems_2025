import pathlib, filetype

def detect(path: str) -> str:
    """Return 'pdf', 'docx', 'jpg', etc.; raise on unknown."""
    ext = pathlib.Path(path).suffix.lower().lstrip(".")
    if ext in {"pdf", "docx", "jpg", "jpeg", "png", "tiff"}:
        return ext
    kind = filetype.guess(path)
    if kind is None:
        raise ValueError(f"Unsupported file type: {path}")
    return kind.extension