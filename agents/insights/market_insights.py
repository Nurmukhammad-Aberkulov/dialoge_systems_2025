# agents/insights/market_insights.py
from __future__ import annotations

import json
from typing import Dict, Any

from agents.base_agent import BaseAgent
import streamlit as st


class MarketInsightsAgent(BaseAgent):
    """
    Returns recruiter-market insights for <role, country>.
    The agent first asks the LLM to list 4–5 relevant job-ad URLs, then
    summarises the hottest tech/soft skills and a salary hint.
    """
    def __init__(self):
        super().__init__(api_key=st.session_state.get("openai_api_key"))

    SYSTEM_PROMPT = (
        "You are a labour-market analyst. Use the web links provided to "
        "extract the TOP technical keywords, the common soft skills, and a "
        "plausible salary range for the role in that country. "
        "Respond ONLY with a JSON object like the example."
    )

    EXAMPLE_JSON = """```json
{
  "top_keywords": ["kubernetes", "aws", "microservices"],
  "soft_skills": ["communication", "stakeholder management"],
  "salary_hint": "€55-70 k (mid-level, Berlin)",
  "sources": [
    {"title": "Backend Engineer – Indeed (Berlin)", "url": "https://…"},
    {"title": "Software Eng – Stack Overflow Jobs", "url": "https://…"}
  ]
}
```"""



    # ------------------------------------------------------------------ #
    # Helper 1: let the LLM fetch a few fresh links
    # ------------------------------------------------------------------ #
    def _grab_links(self, query: str) -> list[dict]:
        """
        Ask the same LLM for 4-5 current job-ad URLs & titles.
        Returns list[{'title': str, 'url': str}].
        """
        prompt = (
            f"List exactly 5 live job-ad URLs (with titles) for '{query}'. "
            "Return JSON list: [ {\"title\": \"…\", \"url\": \"…\"}, … ] "
            "No markdown, no explanation."
        )
        raw = self._chat([{"role": "user", "content": prompt}])
        try:
            return json.loads(raw)
        except Exception:
            return []

    # ------------------------------------------------------------------ #
    # BaseAgent interface
    # ------------------------------------------------------------------ #
    def build_messages(
        self, *, role: str, country: str, structured_json: Dict[str, Any]
    ) -> list[dict]:
        query = f"{role} {country} job description skills requirements"
        links = self._grab_links(query)

        link_block = "\n".join(f"- {l['title']} ({l['url']})" for l in links) or "none"

        user_msg = (
            f"### Role\n{role}\n\n"
            f"### Country\n{country}\n\n"
            f"### Extracted résumé skills\n"
            f"{json.dumps(structured_json['sections']['skills'], indent=2)[:400]}\n\n"
            f"### Web links\n{link_block}\n\n"
            f"{self.EXAMPLE_JSON}\nRespond only the JSON."
        )

        return [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]

    def postprocess(self, raw_response: str, **_) -> Dict[str, Any]:
        start, end = raw_response.find("{"), raw_response.rfind("}") + 1
        try:
            data = json.loads(raw_response[start:end])
        except Exception:
            data = {}

        # guarantee keys exist
        return {
            "top_keywords": data.get("top_keywords", []),
            "soft_skills":  data.get("soft_skills", []),
            "salary_hint":  data.get("salary_hint", ""),
            "sources":      data.get("sources", []),
        }

