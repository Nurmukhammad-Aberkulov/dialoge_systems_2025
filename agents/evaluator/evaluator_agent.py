#!/usr/bin/env python3
"""
EvaluatorAgent – scores a CV with the rubric.
"""

from __future__ import annotations
import json, time
from pathlib import Path
from agents.base_agent import BaseAgent      # ← the common mix-in
from agents.evaluator.extract_text import pdf_to_text
from agents.evaluator.rubric import RUBRIC, DIMENSIONS
from agents.evaluator.prompts import SYSTEM_PROMPT, EXAMPLE_OUTPUT

class EvaluatorAgent(BaseAgent):
    """Returns the same evaluation_report JSON we generated before."""

    def build_messages(self, pdf_path: str, structured_json: dict, role: str):
        # --- build rubric markdown table exactly like before -------------
        rubric_md = "### Rubric\n| Dimension | Description | Weight |\n|---|---|---|\n"
        for dim, cfg in RUBRIC.items():
            rubric_md += f"| {dim} | {cfg['description']} | {cfg['weight']} |\n"

        # text extraction (reuse helper)
        pdf_text = pdf_to_text(pdf_path)

        user_block = (
            f"{rubric_md}\n\n"
            f"### Target role\n{role}\n\n"
            "### Structured résumé JSON\n```json\n"
            f"{json.dumps(structured_json, indent=2)[:8000]}\n```\n"
            "### Extracted CV text (truncated)\n"
            f"```\n{pdf_text[:8000]}\n```\n"
            f"{EXAMPLE_OUTPUT}\n"
            "Respond only with the JSON object."
        )
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_block},
        ]

    # ------------ post-processing identical to old parse_response -------
    def postprocess(self, raw_response: str, **_):
        start = raw_response.find("{")
        end   = raw_response.rfind("}") + 1
        report = json.loads(raw_response[start:end])

        missing = [k for k in DIMENSIONS if k not in report.get("scores", {})]
        if missing:
            raise ValueError(f"Missing dimension keys: {missing}")
        return report


# Optional CLI entry-point so you can still run it standalone -------------
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("pdf")
    p.add_argument("structured_json")
    p.add_argument("--role", required=True)
    args = p.parse_args()

    agent = EvaluatorAgent()
    report = agent(
        pdf_path=args.pdf,
        structured_json=json.loads(Path(args.structured_json).read_text()),
        role=args.role,
    )
    out = Path(args.structured_json).with_suffix(".evaluation.json")
    out.write_text(json.dumps(report, indent=2))
    print("Saved", out)
