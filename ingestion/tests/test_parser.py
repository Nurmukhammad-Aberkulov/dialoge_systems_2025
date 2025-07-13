# tests/test_parser.py
import pathlib, pytest
from resume_reviewer.parser import parse_resume

SAMPLES = pathlib.Path(__file__).parent / "samples"

@pytest.mark.parametrize("fname,ftype", [
    ("sample.pdf",  "pdf"),
    ("sample.docx", "docx"),
    ("sample.jpg",  "jpg"),
])
def test_parse(fname, ftype):
    res = parse_resume(SAMPLES / fname)
    assert res.metadata["filetype"] == ftype
    assert len(res.text) > 100