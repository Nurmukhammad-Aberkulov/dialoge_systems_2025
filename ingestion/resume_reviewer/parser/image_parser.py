from PIL import Image
import pytesseract

def extract(path: str) -> str:
    return pytesseract.image_to_string(Image.open(path))