from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from alvaro.config.loader import (
    IdeationNicheConfig,
    NichePromptConfig,
    PromptsConfig,
    ScriptingNicheConfig,
    VoiceConfig,
)
from alvaro.ideation.models import IdeaCandidate
from alvaro.scripting.generator import ScriptGenerationError, generate_script
from alvaro.scripting.models import Script, ValidationResult
from alvaro.scripting.validator import _hook_is_valid, validate_script


def _make_voice(
    voice_id: str = "alvaro_es",
    language: str = "es-ES",
) -> VoiceConfig:
    return VoiceConfig(
        id=voice_id,
        engine="edge-tts",
        voice="es-ES-AlvaroNeural",
        language=language,
        rate="+5%",
        pitch="+0Hz",
        niches=["science"],
    )


def _make_idea(niche_id: str = "science") -> IdeaCandidate:
    return IdeaCandidate(title="Titulo", hook="Por que el cielo es azul?", score=8, niche_id=niche_id)  # noqa: E501


_DEFAULT_TMPL = "Escribe {title} con hook {hook} voz {voice_id}."


def _make_prompts(template: str = _DEFAULT_TMPL) -> PromptsConfig:
    scripting = ScriptingNicheConfig(template=template, few_shots=[])
    ideation = IdeationNicheConfig(template="", few_shots=[])
    return PromptsConfig(
        system_base="Eres guionista.",
        niches={"science": NichePromptConfig(ideation=ideation, scripting=scripting)},
    )


def _make_script_json(voice_id: str = "alvaro_es", hook: str = "Por que?") -> str:
    return json.dumps(
        {
            "title": "Titulo",
            "hook": hook,
            "body": "palabra " * 100,
            "voice_id": voice_id,
            "duration_estimate_s": 46,
            "tags": ["tag1"],
            "description": "desc",
        }
    )


class TestHookIsValid:
    def test_ends_with_question_mark_valid(self) -> None:
        assert _hook_is_valid("Por que el cielo es azul?", "es-ES") is True

    def test_es_trigger_word_valid(self) -> None:
        assert _hook_is_valid("Sabias que los peces duermen?", "es-ES") is True

    def test_es_trigger_nunca(self) -> None:
        assert _hook_is_valid("Nunca viste esto en este juego", "es-ES") is True

    def test_en_trigger_did(self) -> None:
        assert _hook_is_valid("Did you know this fact?", "en-US") is True

    def test_en_trigger_what(self) -> None:
        assert _hook_is_valid("What happens when you sleep", "en-US") is True

    def test_unknown_first_word_invalid(self) -> None:
        assert _hook_is_valid("Hoy te contamos algo", "es-ES") is False

    def test_en_trigger_not_valid_for_es(self) -> None:
        assert _hook_is_valid("Did you know", "es-ES") is False

    def test_empty_hook_invalid(self) -> None:
        assert _hook_is_valid("", "es-ES") is False


class TestValidateScript:
    def test_valid_script_ok(self) -> None:
        voice = _make_voice()
        script = Script(
            title="T",
            hook="Por que existe el universo?",
            body="palabra " * 80,
            voice_id="alvaro_es",
            duration_estimate_s=37,
            tags=[],
            description="",
        )
        result = validate_script(script, voice, max_duration_s=55)
        assert result.ok is True
        assert result.errors == []

    def test_invalid_hook_reported(self) -> None:
        voice = _make_voice()
        script = Script(
            title="T",
            hook="Hola amigos bienvenidos",
            body="palabra " * 80,
            voice_id="alvaro_es",
            duration_estimate_s=37,
            tags=[],
            description="",
        )
        result = validate_script(script, voice, max_duration_s=55)
        assert result.ok is False
        assert any("hook" in e for e in result.errors)

    def test_duration_exceeded_reported(self) -> None:
        voice = _make_voice()
        script = Script(
            title="T",
            hook="Por que?",
            body="palabra " * 300,
            voice_id="alvaro_es",
            duration_estimate_s=200,
            tags=[],
            description="",
        )
        result = validate_script(script, voice, max_duration_s=55)
        assert result.ok is False
        assert any("duration" in e for e in result.errors)

    def test_voice_id_mismatch_reported(self) -> None:
        voice = _make_voice(voice_id="alvaro_es")
        script = Script(
            title="T",
            hook="Por que?",
            body="palabra " * 80,
            voice_id="wrong_voice",
            duration_estimate_s=37,
            tags=[],
            description="",
        )
        result = validate_script(script, voice, max_duration_s=55)
        assert result.ok is False
        assert any("voice_id" in e for e in result.errors)

    def test_en_voice_uses_higher_wpm(self) -> None:
        voice = _make_voice(voice_id="en_voice", language="en-US")
        body_words = 120
        script = Script(
            title="T",
            hook="What is quantum?",
            body="word " * body_words,
            voice_id="en_voice",
            duration_estimate_s=48,
            tags=[],
            description="",
        )
        result = validate_script(script, voice, max_duration_s=55)
        assert result.ok is True

    def test_validation_result_dataclass(self) -> None:
        r = ValidationResult(ok=True, errors=[])
        assert r.ok is True


class TestGenerateScript:
    async def test_returns_script_on_first_valid_attempt(self) -> None:
        client = AsyncMock()
        client.complete.return_value = _make_script_json()
        script = await generate_script(client, _make_idea(), _make_voice(), _make_prompts(), 55)
        assert isinstance(script, Script)
        assert script.voice_id == "alvaro_es"

    async def test_retries_on_validation_failure(self) -> None:
        client = AsyncMock()
        bad_json = _make_script_json(voice_id="wrong_voice")
        good_json = _make_script_json(voice_id="alvaro_es")
        client.complete.side_effect = [bad_json, good_json]
        script = await generate_script(client, _make_idea(), _make_voice(), _make_prompts(), 55)
        assert script.voice_id == "alvaro_es"
        assert client.complete.call_count == 2

    async def test_raises_after_all_attempts_fail(self) -> None:
        client = AsyncMock()
        client.complete.return_value = _make_script_json(voice_id="wrong_voice")
        with pytest.raises(ScriptGenerationError):
            await generate_script(client, _make_idea(), _make_voice(), _make_prompts(), 55)
        assert client.complete.call_count == 3

    async def test_escalates_temperature(self) -> None:
        client = AsyncMock()
        client.complete.return_value = _make_script_json()
        await generate_script(client, _make_idea(), _make_voice(), _make_prompts(), 55)
        temp = client.complete.call_args[1]["temperature"]
        assert temp == 0.7
