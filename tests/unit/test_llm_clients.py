from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from alvaro.llm._types import LLMClient, LLMTransientError, _strip_fences
from alvaro.llm.gemini_client import GeminiClient
from alvaro.llm.groq_client import GroqClient


def test_strip_fences_removes_json_block() -> None:
    raw = "```json\n{\"key\": \"value\"}\n```"
    assert _strip_fences(raw) == '{"key": "value"}'


def test_strip_fences_removes_plain_block() -> None:
    raw = "```\n{\"key\": 1}\n```"
    assert _strip_fences(raw) == '{"key": 1}'


def test_strip_fences_passthrough_clean() -> None:
    raw = '{"key": "value"}'
    assert _strip_fences(raw) == raw


def test_llmclient_protocol_structural() -> None:
    class _Fake:
        async def complete(self, system: str, user: str, temperature: float = 0.7) -> str:
            return ""

    assert isinstance(_Fake(), LLMClient)


@pytest.fixture
def mock_groq_async() -> MagicMock:
    mock = MagicMock()
    mock.chat.completions.create = AsyncMock()
    choice = MagicMock()
    choice.message.content = "hello"
    mock.chat.completions.create.return_value.choices = [choice]
    return mock


async def test_groq_complete_returns_content(
    mock_groq_async: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    with patch("alvaro.llm.groq_client.groq.AsyncGroq", return_value=mock_groq_async):
        client = GroqClient()
        result = await client.complete("sys", "user")
    assert result == "hello"


async def test_groq_complete_wraps_api_error(
    mock_groq_async: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    import groq

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    mock_groq_async.chat.completions.create.side_effect = groq.APIConnectionError(
        request=MagicMock()
    )
    with patch("alvaro.llm.groq_client.groq.AsyncGroq", return_value=mock_groq_async):
        client = GroqClient()
        with pytest.raises(LLMTransientError):
            await client.complete("sys", "user")


async def test_groq_complete_empty_content(
    mock_groq_async: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    mock_groq_async.chat.completions.create.return_value.choices[0].message.content = None
    with patch("alvaro.llm.groq_client.groq.AsyncGroq", return_value=mock_groq_async):
        client = GroqClient()
        result = await client.complete("sys", "user")
    assert result == ""


@pytest.fixture
def mock_genai() -> MagicMock:
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=MagicMock(text="gemini-reply"))
    return mock_client


async def test_gemini_complete_returns_text(
    mock_genai: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    with patch("alvaro.llm.gemini_client.genai.Client", return_value=mock_genai):
        client = GeminiClient()
        result = await client.complete("sys", "user")
    assert result == "gemini-reply"


async def test_gemini_complete_wraps_exception(
    mock_genai: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_genai.aio.models.generate_content.side_effect = RuntimeError("boom")
    with patch("alvaro.llm.gemini_client.genai.Client", return_value=mock_genai):
        client = GeminiClient()
        with pytest.raises(LLMTransientError):
            await client.complete("sys", "user")


async def test_gemini_complete_empty_text(
    mock_genai: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_genai.aio.models.generate_content.return_value.text = None
    with patch("alvaro.llm.gemini_client.genai.Client", return_value=mock_genai):
        client = GeminiClient()
        result = await client.complete("sys", "user")
    assert result == ""
