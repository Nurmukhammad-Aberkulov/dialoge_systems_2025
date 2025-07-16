# agents/evaluator/evaluator_agent.py

from __future__ import annotations
import json
from pathlib import Path
from agents.base_agent import BaseAgent
from agents.evaluator.rubric import RUBRIC, DIMENSIONS
from agents.evaluator.prompts import SYSTEM_PROMPT, EXAMPLE_OUTPUT
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from agents.tools.calculator import calculator
from langchain.tools import DuckDuckGoSearchRun
from langchain.agents import Tool
import streamlit as st
from pydantic import BaseModel, Field
import os



class EvaluatorAgent(BaseAgent):
    """Returns an evaluation_report JSON using LLM + tools like calculator."""

    def __init__(self):
        super().__init__(api_key=st.session_state.get("openai_api_key"))

        # Use API key from UI or .env

        api_key = st.session_state.get("openai_api_key") or os.getenv("OPENAI_API_KEY")

        # Set up LLM + tools
        self.tools = [calculator,
        ]
        self.llm = ChatOpenAI(temperature=0, openai_api_key=api_key, response_format={"type": "json_object"},)
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            prefix=SYSTEM_PROMPT,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
        )

    # Dummy method to satisfy BaseAgent ABC
    def build_messages(self, **inputs):
        raise NotImplementedError("build_messages is unused when using tool-powered agent.")

    def __call__(self, **inputs):
        prompt = self._build_user_prompt(**inputs)
        raw = self.agent.run(prompt)
        return self.postprocess(raw, **inputs)

    def _build_user_prompt(self, raw_text: str, structured_json: dict, role: str) -> str:
        rubric_md = "### Rubric\n| Dimension | Description | Weight |\n|---|---|---|\n"
        for dim, cfg in RUBRIC.items():
            rubric_md += f"| {dim} | {cfg['description']} | {cfg['weight']} |\n"

        return (
            f"{rubric_md}\n\n"
            f"### Target role\n{role}\n\n"
            "### Structured résumé JSON\n```json\n"
            f"{json.dumps(structured_json, indent=2)[:8000]}\n```\n"
            "### Extracted CV text (truncated)\n"
            f"```\n{raw_text}\n```\n"
            f"{EXAMPLE_OUTPUT}\n"
            "Respond only with the JSON object."
        )

    def postprocess(self, raw_response: str, **_):
        start = raw_response.find("{")
        end = raw_response.rfind("}") + 1
        report = json.loads(raw_response[start:end])

        missing = [k for k in DIMENSIONS if k not in report.get("scores", {})]
        if missing:
            raise ValueError(f"Missing dimension keys: {missing}")
        return report


# Optional CLI
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
