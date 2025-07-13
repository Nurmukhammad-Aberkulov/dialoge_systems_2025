EXAMPLE_OUTPUT = """
Here is an example of the JSON you must return:

```json
{
  "evaluated_at": "2025-07-10T16:42:00Z",
  "target_role": "Software Engineer",
  "scores": {
    "content": 4,
    "clarity": 3,
    "structure": 4,
    "visual": 3,
    "ats": 5,
    "language": 5,
    "overall": 82
  },
  "rationales": {
    "content": "Good keyword match but missing backend metrics …",
    "clarity": "Some passive voice …",
    "structure": "Education above experience …",
    "visual": "Font size 9 pt on page 2 …",
    "ats": "Single column, parsable contact info …",
    "language": "Minor tense inconsistency …"
  },
  "highlights": [
    { "page": 1, "text": "Reduced API latency by 40 %", "note": "Strong quantified result" },
    { "page": 2, "text": "Personal interests section", "note": "Irrelevant; could trim" }
  ]
}

"""
SYSTEM_PROMPT = (
    "You are an HR résumé assessor evaluating CVs for the tech industry. "
    "Using the rubric provided, assign **integer** scores 1-5 for each dimension, "
    "then compute an overall weighted score 0-100. "
    "Respond **only** with a JSON object matching the output schema."
)
