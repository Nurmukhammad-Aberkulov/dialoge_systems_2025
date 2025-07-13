from __future__ import annotations
import json, yaml, time
from pathlib import Path
from agents.base_agent import BaseAgent

EXAMPLE_JSON = """```json
{
  "advice": {
    "critical": [
      "Add quantified metrics to at least two bullets in your Experience section.",
      "Move 'Skills' section above Education to increase ATS keyword density."
    ],
    "important": [
      "Compress the summary to 2 sentences.",
      "Increase font size of section headings for readability."
    ],
    "nice_to_have": [
      "Mention any open-source contributions.",
      "Include links to portfolio projects."
    ]
  },
  "rewrites": [
    {
      "before": "Responsible for migrating database.",
      "after": "Led migration from MySQL to PostgreSQL, reducing query latency by 35 %."
    }
  ]
}
```"""

class CoachAgent(BaseAgent):
    SYSTEM_PROMPT = (
        "You are a career-coach agent. Based on the evaluation report, "
        "produce targeted, actionable feedback grouped by priority. "
        "Return ONLY a JSON object exactly like the example given."
    )

    def __init__(self, keyword_path: str | Path, *args, **kw):
        super().__init__(*args, **kw)
        self.role_kw = yaml.safe_load(Path(keyword_path).read_text())

    # ---------- Agent interface -----------------------------------------
    def build_messages(self, target_role: str, evaluation_json: dict,
                       resume_structured: dict):
        role = target_role.lower().replace(" ", "_")
        kw = self.role_kw.get(role, {})
        context = (
            f"### Evaluation report\n```json\n"
            f"{json.dumps(evaluation_json, indent=2)}\n```\n\n"
            f"### Role keywords\n```yaml\n{yaml.dump(kw)}\n```\n\n"
            f"### Example output\n{EXAMPLE_JSON}\n\n"
            "Respond with ONLY the JSON."
        )
        return [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ]

    def postprocess(self, raw_response: str, **_):
        start = raw_response.find("{")
        end = raw_response.rfind("}") + 1
        data = json.loads(raw_response[start:end])
        # quick sanity
        assert "advice" in data
        return data


if __name__ == "__main__":  # manual test
    import argparse, os
    p = argparse.ArgumentParser()
    p.add_argument("eval_json")
    p.add_argument("--role", required=True)
    p.add_argument("--structured_json")
    args = p.parse_args()

    coach = CoachAgent(keyword_path=Path(__file__).parent/"role_keywords.yaml")
    data = coach(
        target_role=args.role,
        evaluation_json=json.loads(Path(args.eval_json).read_text()),
        resume_structured=(
            json.loads(Path(args.structured_json).read_text())
            if args.structured_json else {}
        ),
    )
    out = Path(args.eval_json).with_suffix(".feedback.json")
    out.write_text(json.dumps(data, indent=2))
    print("Saved", out)
