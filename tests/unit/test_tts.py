from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from alvaro.config.loader import FallbackVoiceConfig, VoiceConfig, VoicesConfig
from alvaro.scripting.models import Script
from alvaro.tts._types import AudioMetadata, TTSError, TTSNetworkError
from alvaro.tts.edge_client import EdgeTTSClient
from alvaro.tts.ssml import build_ssml


def _make_voices(
    voice_id: str = "alvaro_es",
    voice_name: str = "es-ES-AlvaroNeural",
    rate: str = "+5%",
    pitch: str = "+0Hz",
) -> VoicesConfig:
    vc = VoiceConfig(
        id=voice_id,
        engine="edge-tts",
        voice=voice_name,
        language="es-ES",
        rate=rate,
        pitch=pitch,
        niches=["science"],
    )
    fb = FallbackVoiceConfig(engine="piper", model="es_ES", binary="piper", niches=["*"])
    return VoicesConfig(voices=[vc], fallback=fb, niche_voice_map={"science": [voice_id]})


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


class TestEdgeTTSClient:
    async def test_synthesize_calls_communicate_save(self, tmp_path: Path) -> None:
        voices = _make_voices()
        client = EdgeTTSClient(voices)
        output = tmp_path / "out.mp3"
        mock_communicate = AsyncMock()
        mock_communicate.save = AsyncMock()
        with patch("alvaro.tts.edge_client.edge_tts.Communicate", return_value=mock_communicate):
            result = await client.synthesize("hola mundo", "alvaro_es", output)
        mock_communicate.save.assert_called_once_with(str(output))
        assert result == output

    async def test_synthesize_passes_rate_pitch_for_plain_text(self, tmp_path: Path) -> None:
        voices = _make_voices(rate="+10%", pitch="-2Hz")
        client = EdgeTTSClient(voices)
        output = tmp_path / "out.mp3"
        mock_communicate = AsyncMock()
        with patch(
            "alvaro.tts.edge_client.edge_tts.Communicate", return_value=mock_communicate
        ) as mock_cls:
            await client.synthesize("plain text", "alvaro_es", output)
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["rate"] == "+10%"
        assert call_kwargs["pitch"] == "-2Hz"

    async def test_synthesize_ssml_no_rate_pitch(self, tmp_path: Path) -> None:
        voices = _make_voices(rate="+10%", pitch="-2Hz")
        client = EdgeTTSClient(voices)
        output = tmp_path / "out.mp3"
        mock_communicate = AsyncMock()
        with patch(
            "alvaro.tts.edge_client.edge_tts.Communicate", return_value=mock_communicate
        ) as mock_cls:
            await client.synthesize("<speak><prosody>hi</prosody></speak>", "alvaro_es", output)
        call_kwargs = mock_cls.call_args[1]
        assert "rate" not in call_kwargs
        assert "pitch" not in call_kwargs

    async def test_unknown_voice_id_raises(self, tmp_path: Path) -> None:
        voices = _make_voices()
        client = EdgeTTSClient(voices)
        import pytest
        with pytest.raises(ValueError, match="not found"):
            await client.synthesize("text", "unknown_voice", tmp_path / "out.mp3")

    async def test_os_error_becomes_network_error(self, tmp_path: Path) -> None:
        voices = _make_voices()
        client = EdgeTTSClient(voices)
        output = tmp_path / "out.mp3"
        mock_communicate = MagicMock()
        mock_communicate.save = AsyncMock(side_effect=OSError("connection reset"))
        import pytest
        with patch("alvaro.tts.edge_client.edge_tts.Communicate", return_value=mock_communicate):
            with pytest.raises(TTSNetworkError):
                await client.synthesize("text", "alvaro_es", output)
