import json, yaml
from pathlib import Path
from agents.base_agent import BaseAgent


class GAIA_Agent(BaseAgent):
    # Prompt taken from the GAIA paper
    SYSTEM_PROMPT = """You are a general AI assistant. I will ask you a question. Report your thoughts, and
        finish your answer with the following template: FINAL ANSWER: [YOUR FINAL ANSWER].
        YOUR FINAL ANSWER should be a number OR as few words as possible OR a comma separated
        list of numbers and/or strings.
        If you are asked for a number, don’t use comma to write your number neither use units such as $ or
        percent sign unless specified otherwise.
        If you are asked for a string, don’t use articles, neither abbreviations (e.g. for cities), and write the
        digits in plain text unless specified otherwise.
        If you are asked for a comma separated list, apply the above rules depending of whether the element
        to be put in the list is a number or a string.
        """

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

    # ---------- Agent interface -----------------------------------------
    def build_messages(self, question: str):
        return [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]

    def postprocess(self, raw_response: str, **_):
        return str(raw_response).split("FINAL ANSWER: ")[1]
