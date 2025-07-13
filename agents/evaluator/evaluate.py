#!/usr/bin/env python3
"""
Command-line Evaluator prototype.

Usage:
    python evaluate.py path/to/cv.pdf path/to/structured.json --role "Software Engineer"
"""

from __future__ import annotations

import argparse, json, os, sys, time
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

from .extract_text import pdf_to_text
from rubric import RUBRIC, DIMENSIONS
# ---- LLM provider glue ---------------------------------------------------- #

# --- replace the existing LLMClient class with this -----------------------

class LLMClient:
    """
    Thin wrapper around either OpenAI (>=1.0) or Google Gemini SDKs.
    """

    def __init__(self, provider: str):
        self.provider = provider.lower()

        if self.provider == "openai":
            # New-style client object
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise EnvironmentError("OPENAI_API_KEY missing in environment")
            self._client = OpenAI(api_key=api_key)
            self._model = "gpt-4o-mini"

        elif self.provider == "google":
            import google.generativeai as genai

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise EnvironmentError("GEMINI_API_KEY missing in environment")
            genai.configure(api_key=api_key)
            self._client = genai
            self._model = "gemini-1.5-flash"

        else:
            raise ValueError("provider must be 'openai' or 'google'")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def chat(self, messages: list[dict]) -> str:
        """
        Send a chat completion request and return assistant content text.
        """

        if self.provider == "openai":
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.2,
                max_tokens=2048,
            )
            return response.choices[0].message.content.strip()

        # --- Gemini path unchanged ---
        model = self._client.GenerativeModel(self._model)
        response = model.generate_content(messages)
        return response.text.strip()

# ---- Prompt builder ------------------------------------------------------- #

# ---------- Add near the top (after SYSTEM_PROMPT) -------------------------

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

def build_messages(role: str, pdf_text: str, structured_json: Dict[str, Any]) -> list[dict]:
    # -- rubric table as before --
    rubric_md = "### Rubric\n| Dimension | Description | Weight |\n|---|---|---|\n"
    for dim, cfg in RUBRIC.items():
        rubric_md += f"| {dim} | {cfg['description']} | {cfg['weight']} |\n"

    context_parts = [
        rubric_md,
        f"### Target role\n{role}",
        "### Structured résumé JSON",
        "```json\n" + json.dumps(structured_json, indent=2)[:8000] + "\n```",
        "### Extracted CV text (truncated)",
        "```\n" + pdf_text[:8000] + "\n```",
        EXAMPLE_OUTPUT,         #  ← new exemplar block
        "Respond only with the JSON object."
    ]

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "\n\n".join(context_parts)},
    ]

# ---- Score helper --------------------------------------------------------- #

def parse_response(resp: str) -> Dict[str, Any]:
    """
    Attempts to locate the first JSON object in the LLM response.
    """
    try:
        # allow the model to wrap JSON in markdown fences
        start = resp.find("{")
        end = resp.rfind("}") + 1
        return json.loads(resp[start:end])
    except Exception as e:
        raise ValueError(f"Could not parse JSON from LLM response: {resp}") from e


# ---- Main ----------------------------------------------------------------- #

def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path")
    parser.add_argument("json_path")
    parser.add_argument("--role", required=True, help="Target job role string")
    args = parser.parse_args()

    provider = os.getenv("MODEL_PROVIDER", "openai")
    llm = LLMClient(provider)

    pdf_text = pdf_to_text(args.pdf_path)
    structured = json.loads(Path(args.json_path).read_text())

    messages = build_messages(args.role, pdf_text, structured)

    # --- LLM call & basic retry -------------------------------------------
    print("[*] Calling LLM ...", file=sys.stderr)
    start = time.perf_counter()
    resp_text = llm.chat(messages)
    duration = time.perf_counter() - start
    print(f"[*] LLM done in {duration:.1f}s", file=sys.stderr)

    try:
        report = parse_response(resp_text)
    except ValueError:
        # If parsing fails, ask the model to repeat only the JSON
        print("[!] First response malformed. Requesting retry …", file=sys.stderr)
        messages.append(
            {
                "role": "assistant",
                "content": resp_text[:2000],  # keep conversation context
            }
        )
        messages.append(
            {
                "role": "user",
                "content": "Your previous reply was not valid JSON or missed keys. "
                           "Please return ONLY the complete JSON object as in the example."
            }
        )
        resp_text = llm.chat(messages)
        report = parse_response(resp_text)

    # sanity check
    missing = [k for k in DIMENSIONS if k not in report.get("scores", {})]
    if missing:
        raise ValueError(f"Missing dimension keys in JSON: {missing}")


    out_path = Path(args.json_path).with_suffix(".evaluation.json")
    out_path.write_text(json.dumps(report, indent=2))
    print(f"[+] Saved evaluation to {out_path}")


if __name__ == "__main__":
    main()
