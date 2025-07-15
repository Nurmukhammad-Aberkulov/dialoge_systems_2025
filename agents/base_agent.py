from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
import json, os, time
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt

load_dotenv()

class BaseAgent(ABC):
    """
    BaseAgent with optional tool support (OpenAI only).
    Subclasses can define self.tools = [...] to use them.
    """

    def __init__(self, model_provider: str | None = None):
        self.provider = (model_provider or
                         os.getenv("MODEL_PROVIDER", "openai")).lower()
        self.client, self.model_name = self._make_client()
        self.tools = []  # Optional: subclasses can override

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

    # ---- LLM client init -------------------------------------------------
    def _make_client(self):
        if self.provider == "openai":
            from openai import OpenAI
            return OpenAI(api_key=os.environ["OPENAI_API_KEY"]), "gpt-4o"
        elif self.provider == "google":
            import google.generativeai as genai
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            return genai, "gemini-1.5-flash"
        else:
            raise ValueError("Unknown provider")

    # ---- LLM chat call with tool support (OpenAI) ------------------------
    @retry(wait=wait_exponential(), stop=stop_after_attempt(3))
    def _chat(self, messages):
        if self.provider == "openai":
            kwargs = dict(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
            )
            if self.tools:
                kwargs["tools"] = self.tools
                kwargs["tool_choice"] = "auto"

            resp = self.client.chat.completions.create(**kwargs)

            if hasattr(resp.choices[0].message, "tool_calls") and resp.choices[0].message.tool_calls:
                # Tool was invoked, handle tool call (synchronously)
                for call in resp.choices[0].message.tool_calls:
                    tool_name = call.function.name
                    args = json.loads(call.function.arguments)
                    for tool in self.tools:
                        if tool["function"]["name"] == tool_name:
                            result = tool["function"]["function"](**args)
                            return json.dumps({"tool_result": result})  # Could be more structured
                return "Tool was called, but not handled correctly."
            return resp.choices[0].message.content.strip()

        else:  # Gemini or fallback
            model = self.client.GenerativeModel(self.model_name)
            resp = model.generate_content(messages)
            return resp.text.strip()
