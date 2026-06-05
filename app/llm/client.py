from __future__ import annotations

import json
import os
from typing import Any, Callable, Protocol

from app.config import load_env_file


class LLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Return a JSON object parsed as a dict."""


class OpenAILLMClient:
    def __init__(self, model: str | None = None) -> None:
        from openai import OpenAI

        load_env_file()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY must be set to use --llm mode")
        self.client = OpenAI(api_key=api_key)

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("LLM response was not a JSON object")
        return parsed


class MockLLMClient:
    def __init__(self, responses: list[dict[str, Any] | str] | Callable[[str, str], dict[str, Any] | str]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str]] = []

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        self.calls.append((system_prompt, user_prompt))
        if callable(self.responses):
            value = self.responses(system_prompt, user_prompt)
        else:
            if not self.responses:
                raise ValueError("No mock LLM responses left")
            value = self.responses.pop(0)
        if isinstance(value, str):
            parsed = json.loads(value)
        else:
            parsed = value
        if not isinstance(parsed, dict):
            raise ValueError("Mock LLM response was not a JSON object")
        return parsed
