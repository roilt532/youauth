from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set - skipping integration test",
)


async def test_groq_complete_returns_text() -> None:
    from alvaro.llm.groq_client import GroqClient

    client = GroqClient(api_key=os.environ["GROQ_API_KEY"])
    result = await client.complete(
        system="Responde solo con la palabra ok.",
        user="Di ok.",
        temperature=0.0,
    )
    assert isinstance(result, str)
    assert len(result) > 0
    assert "ok" in result.lower()


async def test_gemini_complete_returns_text() -> None:
    if not os.environ.get("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set")
    from alvaro.llm.gemini_client import GeminiClient

    client = GeminiClient(api_key=os.environ["GEMINI_API_KEY"])
    result = await client.complete(
        system="Responde solo con la palabra ok.",
        user="Di ok.",
        temperature=0.0,
    )
    assert isinstance(result, str)
    assert len(result) > 0
    assert "ok" in result.lower()
