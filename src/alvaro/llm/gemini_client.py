from __future__ import annotations

from google import genai
from google.genai import types

from alvaro.llm._types import LLMTransientError

_MODEL = "gemini-2.0-flash"
_TIMEOUT = 30.0


class GeminiClient:
    def __init__(self, api_key: str) -> None:
        self._client = genai.Client(api_key=api_key)

    async def complete(self, system: str, user: str, temperature: float = 0.7) -> str:
        prompt = f"{system}\n\n{user}"
        try:
            response = await self._client.aio.models.generate_content(
                model=_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    http_options=types.HttpOptions(timeout=int(_TIMEOUT * 1000)),
                ),
            )
            return response.text or ""
        except Exception as exc:
            raise LLMTransientError(str(exc)) from exc
