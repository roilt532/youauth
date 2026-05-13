from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from alvaro.config.loader import FallbackVoiceConfig, VoiceConfig, VoicesConfig
from alvaro.scripting.models import Script
from alvaro.tts._types import AudioMetadata, TTSError, TTSNetworkError
from alvaro.tts.edge_client import EdgeTTSClient
from alvaro.tts.piper_client import PiperClient
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
        with pytest.raises(ValueError, match="not found"):
            await client.synthesize("text", "unknown_voice", tmp_path / "out.mp3")

    async def test_os_error_becomes_network_error(self, tmp_path: Path) -> None:
        voices = _make_voices()
        client = EdgeTTSClient(voices)
        output = tmp_path / "out.mp3"
        mock_communicate = MagicMock()
        mock_communicate.save = AsyncMock(side_effect=OSError("connection reset"))
        with patch("alvaro.tts.edge_client.edge_tts.Communicate", return_value=mock_communicate):
            with pytest.raises(TTSNetworkError):
                await client.synthesize("text", "alvaro_es", output)


class TestPiperClient:
    async def test_synthesize_calls_piper_subprocess(self, tmp_path: Path) -> None:
        voices = _make_voices()
        client = PiperClient(voices)
        output = tmp_path / "out.wav"
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        onnx = tmp_path / "model.onnx"
        onnx.touch()
        json_cfg = tmp_path / "model.onnx.json"
        json_cfg.touch()
        with (
            patch("alvaro.tts.piper_client._ensure_model", return_value=onnx),
            patch("alvaro.tts.piper_client.subprocess.run", return_value=mock_proc) as mock_run,  # noqa: E501
        ):
            result = await client.synthesize("hola", "alvaro_es", output)
        assert result == output
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "piper" in call_args[0][0]

    async def test_nonzero_exit_raises_tts_error(self, tmp_path: Path) -> None:
        voices = _make_voices()
        client = PiperClient(voices)
        output = tmp_path / "out.wav"
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stderr = b"model error"
        onnx = tmp_path / "model.onnx"
        with (
            patch("alvaro.tts.piper_client._ensure_model", return_value=onnx),
            patch("alvaro.tts.piper_client.subprocess.run", return_value=mock_proc),
        ):
            with pytest.raises(TTSError, match="piper exited"):
                await client.synthesize("hola", "alvaro_es", output)

    async def test_subprocess_timeout_raises_network_error(self, tmp_path: Path) -> None:
        voices = _make_voices()
        client = PiperClient(voices)
        output = tmp_path / "out.wav"
        onnx = tmp_path / "model.onnx"
        with (
            patch("alvaro.tts.piper_client._ensure_model", return_value=onnx),
            patch(
                "alvaro.tts.piper_client.subprocess.run",
                side_effect=subprocess.TimeoutExpired("piper", 120),
            ),
        ):
            with pytest.raises(TTSNetworkError):
                await client.synthesize("hola", "alvaro_es", output)

    def test_ensure_model_skips_download_if_exists(self, tmp_path: Path) -> None:
        from alvaro.tts.piper_client import _ensure_model

        model_name = "es_ES-davefx-medium"
        onnx = tmp_path / f"{model_name}.onnx"
        json_cfg = tmp_path / f"{model_name}.onnx.json"
        onnx.touch()
        json_cfg.touch()
        with patch("alvaro.tts.piper_client._models_dir", return_value=tmp_path):
            result = _ensure_model(model_name)
        assert result == onnx

    def test_ensure_model_downloads_if_missing(self, tmp_path: Path) -> None:
        from alvaro.tts.piper_client import _ensure_model

        model_name = "es_ES-davefx-medium"
        mock_resp = MagicMock()
        mock_resp.content = b"fake_data"
        mock_resp.raise_for_status = MagicMock()
        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.get = MagicMock(return_value=mock_resp)
        with (
            patch("alvaro.tts.piper_client._models_dir", return_value=tmp_path),
            patch("alvaro.tts.piper_client.httpx.Client", return_value=mock_http),
        ):
            result = _ensure_model(model_name)
        assert result == tmp_path / f"{model_name}.onnx"
        assert (tmp_path / f"{model_name}.onnx").read_bytes() == b"fake_data"


_PASS1_STDERR = """\
[Parsed_loudnorm_0 @ 0x...] {
    "input_i" : "-23.45",
    "input_tp" : "-3.12",
    "input_lra" : "8.30",
    "input_thresh" : "-33.50",
    "output_i" : "-16.00",
    "output_tp" : "-1.50",
    "output_lra" : "8.30",
    "output_thresh" : "-26.10",
    "normalization_type" : "dynamic",
    "target_offset" : "0.45"
}
"""

_PASS2_STDERR = """\
[Parsed_loudnorm_0 @ 0x...]
Input Integrated:    -23.5 LUFS
Output Integrated:   -16.0 LUFS
Input True Peak:      -3.1 dBTP
Output True Peak:     -1.5 dBTP
"""


class TestNormalizer:
    def test_loudnorm_returns_lufs(self, tmp_path: Path) -> None:
        from alvaro.tts.normalizer import loudnorm

        inp = tmp_path / "in.mp3"
        inp.touch()
        out = tmp_path / "out.mp3"
        with patch(
            "alvaro.tts.normalizer._run_ffmpeg",
            side_effect=[_PASS1_STDERR, _PASS2_STDERR],
        ):
            result = loudnorm(inp, out)
        assert result == pytest.approx(-16.0)

    def test_loudnorm_calls_ffmpeg_twice(self, tmp_path: Path) -> None:
        from alvaro.tts.normalizer import loudnorm

        inp = tmp_path / "in.mp3"
        inp.touch()
        out = tmp_path / "out.mp3"
        with patch(
            "alvaro.tts.normalizer._run_ffmpeg",
            side_effect=[_PASS1_STDERR, _PASS2_STDERR],
        ) as mock_ffmpeg:
            loudnorm(inp, out)
        assert mock_ffmpeg.call_count == 2

    def test_pass2_args_include_48khz(self, tmp_path: Path) -> None:
        from alvaro.tts.normalizer import loudnorm

        inp = tmp_path / "in.mp3"
        inp.touch()
        out = tmp_path / "out.mp3"
        with patch(
            "alvaro.tts.normalizer._run_ffmpeg",
            side_effect=[_PASS1_STDERR, _PASS2_STDERR],
        ) as mock_ffmpeg:
            loudnorm(inp, out)
        pass2_args = mock_ffmpeg.call_args_list[1][0][0]
        assert "48000" in pass2_args

    def test_malformed_pass1_raises(self, tmp_path: Path) -> None:
        from alvaro.tts.normalizer import loudnorm

        inp = tmp_path / "in.mp3"
        inp.touch()
        with patch("alvaro.tts.normalizer._run_ffmpeg", return_value="no json here"):
            with pytest.raises(TTSError, match="pass 1"):
                loudnorm(inp, tmp_path / "out.mp3")

    def test_malformed_pass2_raises(self, tmp_path: Path) -> None:
        from alvaro.tts.normalizer import loudnorm

        inp = tmp_path / "in.mp3"
        inp.touch()
        with patch(
            "alvaro.tts.normalizer._run_ffmpeg",
            side_effect=[_PASS1_STDERR, "no LUFS line here"],
        ):
            with pytest.raises(TTSError, match="pass 2"):
                loudnorm(inp, tmp_path / "out.mp3")


class TestSynthesizer:
    async def test_synthesize_script_returns_metadata(self, tmp_path: Path) -> None:
        from alvaro.tts.synthesizer import synthesize_script

        script = _make_script()
        voices = _make_voices()
        output = tmp_path / "out.mp3"
        with (
            patch("alvaro.tts.synthesizer.EdgeTTSClient") as mock_edge_cls,
            patch("alvaro.tts.synthesizer.loudnorm", return_value=-16.0),
            patch("alvaro.tts.synthesizer._probe_duration", return_value=52.5),
            patch("alvaro.tts.synthesizer.Path.unlink"),
        ):
            mock_edge = AsyncMock()
            mock_edge_cls.return_value = mock_edge
            result = await synthesize_script(script, "alvaro_es", voices, output)
        assert isinstance(result, AudioMetadata)
        assert result.lufs_integrated == pytest.approx(-16.0)
        assert result.duration_s == pytest.approx(52.5)
        assert result.sample_rate == 48000
        assert result.channels == 1
        assert result.format == "mp3"

    async def test_falls_back_to_piper_on_network_error(self, tmp_path: Path) -> None:
        from alvaro.tts.synthesizer import synthesize_script

        script = _make_script()
        voices = _make_voices()
        output = tmp_path / "out.mp3"
        with (
            patch("alvaro.tts.synthesizer.EdgeTTSClient") as mock_edge_cls,
            patch("alvaro.tts.synthesizer.PiperClient") as mock_piper_cls,
            patch("alvaro.tts.synthesizer.loudnorm", return_value=-16.0),
            patch("alvaro.tts.synthesizer._probe_duration", return_value=50.0),
            patch("alvaro.tts.synthesizer.Path.unlink"),
        ):
            mock_edge = AsyncMock()
            mock_edge.synthesize.side_effect = TTSNetworkError("timeout")
            mock_edge_cls.return_value = mock_edge
            mock_piper = AsyncMock()
            mock_piper_cls.return_value = mock_piper
            result = await synthesize_script(script, "alvaro_es", voices, output)
        mock_piper.synthesize.assert_called_once()
        assert result.duration_s == pytest.approx(50.0)

    async def test_ssml_passed_to_edge_client(self, tmp_path: Path) -> None:
        from alvaro.tts.synthesizer import synthesize_script

        script = _make_script()
        voices = _make_voices()
        output = tmp_path / "out.mp3"
        with (
            patch("alvaro.tts.synthesizer.EdgeTTSClient") as mock_edge_cls,
            patch("alvaro.tts.synthesizer.loudnorm", return_value=-16.0),
            patch("alvaro.tts.synthesizer._probe_duration", return_value=52.0),
            patch("alvaro.tts.synthesizer.Path.unlink"),
        ):
            mock_edge = AsyncMock()
            mock_edge_cls.return_value = mock_edge
            await synthesize_script(script, "alvaro_es", voices, output)
        call_args = mock_edge.synthesize.call_args
        text_arg = call_args[0][0]
        assert text_arg.startswith("<speak>")
        assert script.hook_text in text_arg
