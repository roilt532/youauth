from __future__ import annotations

from pathlib import Path

from alvaro.scripting.models import Script
from alvaro.tts._types import AudioMetadata, TTSError, TTSNetworkError
from alvaro.tts.ssml import build_ssml


def _make_script(
    hook: str = "Por que existe el universo?",
    body: list[str] | None = None,
    payoff: str = "Y eso es todo.",
) -> Script:
    return Script(
        hook_text=hook,
        body_lines=body or ["linea uno", "linea dos", "linea tres"],
        payoff_text=payoff,
        total_duration_estimate_s=52,
        suggested_voice_id="alvaro_es",
        suggested_background_niche="minecraft_parkour",
        niche_id="science",
    )


class TestSSMLBuilder:
    def test_contains_hook(self) -> None:
        ssml = build_ssml(_make_script(), rate="+5%", pitch="+0Hz")
        assert "Por que existe el universo?" in ssml

    def test_contains_payoff(self) -> None:
        ssml = build_ssml(_make_script(), rate="+5%", pitch="+0Hz")
        assert "Y eso es todo." in ssml

    def test_contains_body_lines(self) -> None:
        ssml = build_ssml(_make_script(), rate="+5%", pitch="+0Hz")
        assert "linea uno" in ssml
        assert "linea dos" in ssml
        assert "linea tres" in ssml

    def test_has_breaks_between_sections(self) -> None:
        ssml = build_ssml(_make_script(), rate="+5%", pitch="+0Hz")
        assert ssml.count('<break time="500ms"/>') == 4

    def test_prosody_rate(self) -> None:
        ssml = build_ssml(_make_script(), rate="+10%", pitch="+0Hz")
        assert 'rate="+10%"' in ssml

    def test_prosody_pitch(self) -> None:
        ssml = build_ssml(_make_script(), rate="+5%", pitch="-5Hz")
        assert 'pitch="-5Hz"' in ssml

    def test_speak_root_element(self) -> None:
        ssml = build_ssml(_make_script(), rate="+5%", pitch="+0Hz")
        assert ssml.startswith("<speak>")
        assert ssml.endswith("</speak>")

    def test_special_chars_escaped(self) -> None:
        script = _make_script(hook="3 < 5 & 6 > 4?")
        ssml = build_ssml(script, rate="+5%", pitch="+0Hz")
        assert "&lt;" in ssml
        assert "&amp;" in ssml
        assert "&gt;" in ssml

    def test_break_count_varies_with_body_length(self) -> None:
        script = _make_script(body=["a", "b"])
        ssml = build_ssml(script, rate="+5%", pitch="+0Hz")
        assert ssml.count('<break time="500ms"/>') == 3

    def test_single_body_line(self) -> None:
        script = _make_script(body=["solo"])
        ssml = build_ssml(script, rate="+5%", pitch="+0Hz")
        assert "solo" in ssml
        assert ssml.count('<break time="500ms"/>') == 2


class TestAudioMetadata:
    def test_frozen(self) -> None:
        meta = AudioMetadata(
            file_path=Path("/tmp/a.mp3"),  # noqa: S108
            format="mp3",
            duration_s=52.3,
            sample_rate=48000,
            channels=1,
            lufs_integrated=-16.1,
            lufs_target=-16.0,
        )
        assert meta.sample_rate == 48000
        assert meta.channels == 1
        assert meta.lufs_target == -16.0


class TestTTSErrors:
    def test_network_error_is_tts_error(self) -> None:
        err = TTSNetworkError("connection refused")
        assert isinstance(err, TTSError)

    def test_tts_error_message(self) -> None:
        err = TTSError("synthesis failed")
        assert "synthesis failed" in str(err)
