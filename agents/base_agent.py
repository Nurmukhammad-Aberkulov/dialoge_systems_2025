from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
import json, os, time
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt

load_dotenv()                       # once per process

class BaseAgent(ABC):
    """
    Light agent interface: every concrete agent
    implements .build_messages() and .postprocess().
    """

    def __init__(self, model_provider: str | None = None):
        self.provider = (model_provider or
                         os.getenv("MODEL_PROVIDER", "openai")).lower()
        self.client, self.model_name = self._make_client()

    # ---- public API ------------------------------------------------------
    def __call__(self, **inputs):
        messages = self.build_messages(**inputs)
        raw = self._chat(messages)
        return self.postprocess(raw, **inputs)

    # ---- to be implemented by subclass ----------------------------------
    @abstractmethod
    def build_messages(self, **inputs): ...

    @abstractmethod
    def postprocess(self, raw_response: str, **inputs): ...

    # ---- common LLM plumbing --------------------------------------------
    def _make_client(self):
        if self.provider == "openai":
            from openai import OpenAI
            return OpenAI(api_key=os.environ["OPENAI_API_KEY"]), "gpt-4o-mini"
        elif self.provider == "google":
            import google.generativeai as genai
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            return genai, "gemini-1.5-flash"
        else:
            raise ValueError("Unknown provider")

    @retry(wait=wait_exponential(), stop=stop_after_attempt(3))
    def _chat(self, messages):
        if self.provider == "openai":
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        else:  # google
            model = self.client.GenerativeModel(self.model_name)
            resp = model.generate_content(messages)
            return resp.text.strip()
