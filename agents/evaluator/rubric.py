"""
Central rubric & weights (keep in one place so Evaluator and tests agree)
"""
RUBRIC = {
    "content": {
        "weight": 25,
        "description": "Alignment to role keywords; quantified impact"
    },
    "clarity": {
        "weight": 15,
        "description": "Active voice; ≤2 pages; concise"
    },
    "structure": {
        "weight": 15,
        "description": "Logical order; headings; date formats"
    },
    "visual": {
        "weight": 10,
        "description": "Readable fonts; balanced whitespace"
    },
    "ats": {
        "weight": 20,
        "description": "Single-column; parsable contact info; minimal tables"
    },
    "language": {
        "weight": 15,
        "description": "No grammar/spelling errors; English throughout"
    },
}
DIMENSIONS = list(RUBRIC.keys())
