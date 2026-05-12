from __future__ import annotations

import os

import groq

from alvaro.llm._types import LLMTransientError

_MODEL = "llama-3.3-70b-versatile"
_TIMEOUT = 30.0


class GroqClient:
    def __init__(self) -> None:
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key is None:
            raise OSError("GROQ_API_KEY env var not set")
        self._client = groq.AsyncGroq(api_key=api_key)

    async def complete(self, system: str, user: str, temperature: float = 0.7) -> str:
        try:
            completion = await self._client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                timeout=_TIMEOUT,
            )
            return completion.choices[0].message.content or ""
        except groq.APIError as exc:
            raise LLMTransientError(str(exc)) from exc
