from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from alvaro.config.loader import (
    FallbackVoiceConfig,
    IdeationNicheConfig,
    NicheConfig,
    NichePromptConfig,
    PromptsConfig,
    ScriptingNicheConfig,
    VoiceConfig,
    VoicesConfig,
)
from alvaro.ideation.models import IdeaCandidate
from alvaro.scripting.generator import ScriptGenerationError, generate_script
from alvaro.scripting.models import Script, ValidationResult
from alvaro.scripting.validator import _hook_is_valid, validate_script

_DEFAULT_TMPL = (
    "Hook: {hook}. Tema: {topic}. Angulo: {angle}. Niche: {niche_id}. "
    "Voces: {voice_catalog}. Fondos: {background_options}. "
    "Duracion: {max_duration_s}s. {few_shots}"
)


def _make_voice(voice_id: str = "alvaro_es", language: str = "es-ES") -> VoiceConfig:
    return VoiceConfig(
        id=voice_id,
        engine="edge-tts",
        voice="es-ES-AlvaroNeural",
        language=language,
        rate="+5%",
        pitch="+0Hz",
        niches=["science"],
    )


def _make_voices(voice_id: str = "alvaro_es", language: str = "es-ES") -> VoicesConfig:
    voice = _make_voice(voice_id, language)
    fallback = FallbackVoiceConfig(
        engine="piper", model="es_ES", binary="piper", niches=["science"]
    )
    return VoicesConfig(
        voices=[voice],
        fallback=fallback,
        niche_voice_map={"science": [voice_id]},
    )


def _make_niches(max_duration_s: int = 55) -> list[NicheConfig]:
    return [
        NicheConfig(
            id="science",
            label="Science",
            schedule_utc=[],
            keywords=[],
            tone="educational",
            hook_style="question",
            max_duration_s=max_duration_s,
            target_audience="general",
        )
    ]


def _make_idea(niche_id: str = "science") -> IdeaCandidate:
    return IdeaCandidate(
        hook="Por que el cielo es azul?",
        topic="Fisica de la luz",
        angle="curiosidad",
        estimated_engagement_score=8,
        niche_id=niche_id,
    )


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
            "hook_text": hook,
            "body_lines": ["linea uno", "linea dos", "linea tres"],
            "payoff_text": "Y esto es todo.",
            "total_duration_estimate_s": 52,
            "suggested_voice_id": voice_id,
            "suggested_background_niche": "minecraft_parkour",
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
    def _make_script(
        self,
        hook_text: str = "Por que existe el universo?",
        voice_id: str = "alvaro_es",
        background: str = "minecraft_parkour",
        duration_s: int = 52,
    ) -> Script:
        return Script(
            hook_text=hook_text,
            body_lines=["linea uno", "linea dos"],
            payoff_text="Y asi es todo.",
            total_duration_estimate_s=duration_s,
            suggested_voice_id=voice_id,
            suggested_background_niche=background,
            niche_id="science",
        )

    def test_valid_script_ok(self) -> None:
        result = validate_script(self._make_script(), ["alvaro_es"], 55)
        assert result.ok is True
        assert result.errors == []

    def test_invalid_hook_reported(self) -> None:
        result = validate_script(self._make_script(hook_text="Hola amigos bienvenidos"), ["alvaro_es"], 55)  # noqa: E501
        assert result.ok is False
        assert any("hook" in e for e in result.errors)

    def test_duration_below_min_reported(self) -> None:
        result = validate_script(self._make_script(duration_s=45), ["alvaro_es"], 55)
        assert result.ok is False
        assert any("below minimum" in e for e in result.errors)

    def test_duration_exceeded_reported(self) -> None:
        result = validate_script(self._make_script(duration_s=200), ["alvaro_es"], 55)
        assert result.ok is False
        assert any("exceeds max" in e for e in result.errors)

    def test_voice_id_mismatch_reported(self) -> None:
        result = validate_script(self._make_script(voice_id="wrong_voice"), ["alvaro_es"], 55)
        assert result.ok is False
        assert any("voice_id" in e for e in result.errors)

    def test_invalid_background_reported(self) -> None:
        result = validate_script(self._make_script(background="invalid_bg"), ["alvaro_es"], 55)
        assert result.ok is False
        assert any("background" in e for e in result.errors)

    def test_validation_result_dataclass(self) -> None:
        r = ValidationResult(ok=True, errors=[])
        assert r.ok is True


class TestGenerateScript:
    async def test_returns_script_on_first_valid_attempt(self) -> None:
        client = AsyncMock()
        client.complete.return_value = _make_script_json()
        with (
            patch("alvaro.scripting.generator.load_prompts", return_value=_make_prompts()),
            patch("alvaro.scripting.generator.load_niches", return_value=_make_niches()),
        ):
            script = await generate_script(_make_idea(), "science", client, _make_voices())
        assert isinstance(script, Script)
        assert script.suggested_voice_id == "alvaro_es"

    async def test_retries_on_validation_failure(self) -> None:
        client = AsyncMock()
        bad_json = _make_script_json(voice_id="wrong_voice")
        good_json = _make_script_json(voice_id="alvaro_es")
        client.complete.side_effect = [bad_json, good_json]
        with (
            patch("alvaro.scripting.generator.load_prompts", return_value=_make_prompts()),
            patch("alvaro.scripting.generator.load_niches", return_value=_make_niches()),
        ):
            script = await generate_script(_make_idea(), "science", client, _make_voices())
        assert script.suggested_voice_id == "alvaro_es"
        assert client.complete.call_count == 2

    async def test_raises_after_all_attempts_fail(self) -> None:
        client = AsyncMock()
        client.complete.return_value = _make_script_json(voice_id="wrong_voice")
        with (
            patch("alvaro.scripting.generator.load_prompts", return_value=_make_prompts()),
            patch("alvaro.scripting.generator.load_niches", return_value=_make_niches()),
        ):
            with pytest.raises(ScriptGenerationError):
                await generate_script(_make_idea(), "science", client, _make_voices())
        assert client.complete.call_count == 3

    async def test_escalates_temperature(self) -> None:
        client = AsyncMock()
        client.complete.return_value = _make_script_json()
        with (
            patch("alvaro.scripting.generator.load_prompts", return_value=_make_prompts()),
            patch("alvaro.scripting.generator.load_niches", return_value=_make_niches()),
        ):
            await generate_script(_make_idea(), "science", client, _make_voices())
        temp = client.complete.call_args[1]["temperature"]
        assert temp == 0.7
