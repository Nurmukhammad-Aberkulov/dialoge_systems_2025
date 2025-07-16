from __future__ import annotations
import json, yaml, time
from pathlib import Path
from agents.base_agent import BaseAgent
import streamlit as st
from langchain.agents import initialize_agent, AgentType
from agents.coach.prompts import EXAMPLE_JSON, SYSTEM_PROMPT
from langchain.chat_models import ChatOpenAI
from agents.tools.coaching_tools import (
    keyword_gap_tool,
    bullet_improver_tool,
    salary_lookup_tool,
    web_search_tool
)




class CoachAgent(BaseAgent):

    def __init__(self, keyword_path: str | Path, tools: list | None = None, *args, **kw):
        super().__init__(api_key=st.session_state.get("openai_api_key"), *args, **kw)
        self.role_kw = yaml.safe_load(Path(keyword_path).read_text())


        # Set up LLM + tools
       
        self.tools = []

        if self.tools:
            self.llm = ChatOpenAI(temperature=0, openai_api_key=self.api_key)
            self.agent = initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.OPENAI_FUNCTIONS,
                verbose=True,
            )
        else:
            self.agent = None  # fall back to vanilla _chat

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
            {"role": "system", "content": SYSTEM_PROMPT},
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
