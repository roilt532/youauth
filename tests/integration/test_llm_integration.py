# DEUDA TECNICA CONOCIDA:
# El proyecto Google Cloud "alvaro-shorts" tiene quota=0 en free tier de gemini-2.0-flash.
# No resoluble desde el dashboard de Google Cloud (quota allocator asigno 0).
# La key GEMINI_API_KEY es valida y la API esta habilitada.
# El wrapper GeminiClient esta validado funcionalmente en unit tests:
#   - mock 429 -> LLMTransientError (test_gemini_complete_wraps_exception)
#   - RouterClient fallback Groq->Gemini validado con mocks (test_router_falls_back_on_transient_error)
# Retomar con cuenta Google secundaria antes de merge final a main.
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


@pytest.mark.skip(
    reason=(
        "Gemini free tier quota=0 en proyecto alvaro-shorts. "
        "Wrapper validado en unit tests (mock 429 -> LLMTransientError). "
        "Retomar con cuenta Google secundaria antes de merge final a main."
    )
)
async def test_gemini_complete_returns_text() -> None:
    from alvaro.llm.gemini_client import GeminiClient

    client = GeminiClient(api_key=os.environ.get("GEMINI_API_KEY", ""))
    result = await client.complete(
        system="Responde solo con la palabra ok.",
        user="Di ok.",
        temperature=0.0,
    )
    assert isinstance(result, str)
    assert len(result) > 0
    assert "ok" in result.lower()
