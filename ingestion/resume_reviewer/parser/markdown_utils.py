from markdownify import markdownify as md

def to_markdown(text: str) -> str:
    return md(text, heading_style="ATX")