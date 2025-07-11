import re

def strip_headers_footers(text: str) -> str:
    lines = text.splitlines()
    return "\n".join(
        ln for ln in lines
        if not re.match(r"^\s*(Page\s+\d+|Curriculum Vitae)", ln, re.I)
    )

def normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+$", "", text, flags=re.M)   # trim line-end spaces
    text = re.sub(r"\n{3,}", "\n\n", text)            # 3+ blank lines → 1
    return text.strip()