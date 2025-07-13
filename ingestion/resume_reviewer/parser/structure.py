# resume_reviewer/parser/structure.py
from __future__ import annotations
import hashlib, re, datetime as dt, unicodedata, yaml
from pathlib import Path
from collections import defaultdict
from dateutil import parser as date_parse

SECTION_RE = re.compile(r"^(experience|work history|education|skills?)[:\s]*$", re.I)
DATE_RANGE_RE = re.compile(r"(\w+\s+\d{4})\s*[-–]\s*(present|\w+\s+\d{4})", re.I)
EMAIL_RE = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.I)
PHONE_RE = re.compile(r"\+?\d[\d ()-]{7,}")

def _normalize(s: str) -> str:
    return unicodedata.normalize("NFKC", s)

def _checksum(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return f"sha256:{h.hexdigest()}"

# -------------------------------------------------
def to_schema(text: str, *, filepath: Path, parser_version="0.4.0") -> dict:
    lines = [_normalize(l).strip() for l in text.splitlines() if l.strip()]
    sections = defaultdict(list)

    current = "misc"
    for ln in lines:
        m = SECTION_RE.match(ln)
        if m:
            current = m.group(1).lower()
            continue
        sections[current].append(ln)

    # --- candidate block ---------------------------------------------------
    contact_block = "\n".join(sections["misc"][:15])  # heuristic: first lines
    email = EMAIL_RE.search(contact_block)
    phone = PHONE_RE.search(contact_block)
    full_name = lines[0] if len(lines[0].split()) <= 5 else ""
    candidate = {
        "full_name": full_name,
        "contact": {
            "email": email.group(0) if email else "",
            "phone": phone.group(0) if phone else "",
            "location": "",
            "linkedin": "",
            "github": "",
        },
        "summary": "",
    }

    # --- experience (very naive) ------------------------------------------
    exp_entries = []
    chunks = "\n".join(sections["experience"]).split("\n\n")
    for blk in chunks:
        if not blk.strip(): continue
        start, end = None, None
        dmatch = DATE_RANGE_RE.search(blk)
        if dmatch:
            start = _date_norm(dmatch.group(1))
            end   = _date_norm(dmatch.group(2))
        bullets = [l.lstrip("-• ") for l in blk.splitlines() if l.startswith(("-", "•"))]
        exp_entries.append({
            "title": "",
            "employer": "",
            "location": "",
            "start_date": start or "",
            "end_date": end or "",
            "bullets": bullets,
        })

    # --- skills ------------------------------------------------------------
    skills = {"hard": [], "soft": []}
    skills_txt = " ".join(sections["skills"])
    for token in re.split(r"[,/;]", skills_txt):
        token = token.strip()
        if token:
            skills["hard"].append(token)   # todo: classify later

    # --- compose schema ----------------------------------------------------
    schema = {
        "meta": {
            "checksum": _checksum(filepath),
            "parsed_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "file_name": filepath.name,
            "page_count": 0,  # filled outside if pdfplumber already open
            "parser_version": parser_version,
        },
        "candidate": candidate,
        "sections": {
            "experience": exp_entries,
            "education": [],        # TODO: parse
            "skills": skills,
            "certifications": [],
            "languages": [],
            "awards": [],
        },
        "parser_notes": [],
        "media_refs": [],
        "target_role": None,
    }
    return schema

def _date_norm(raw: str) -> str:
    if not raw or raw.lower() == "present":
        return "present"
    try:
        return date_parse.parse(raw).strftime("%Y-%m")
    except ValueError:
        return ""
