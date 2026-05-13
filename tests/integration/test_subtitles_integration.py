from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_SUBTITLES_INTEGRATION"),
    reason="RUN_SUBTITLES_INTEGRATION not set - skipping subtitles integration test",
)


async def test_faster_whisper_real_transcription(tmp_path: Path) -> None:
    from alvaro.config.loader import load_voices
    from alvaro.subtitles.transcriber import transcribe
    from alvaro.tts.edge_client import EdgeTTSClient

    voices = load_voices()
    audio_path = tmp_path / "short.mp3"
    edge = EdgeTTSClient(voices, timeout_s=30)
    await edge.synthesize(
        "La fotosintesis convierte la luz solar en energia quimica.",
        "alvaro_es",
        audio_path,
    )

    words = await transcribe(audio_path, "es")

    assert len(words) >= 3
    assert all(w.start_s < w.end_s for w in words)
    assert all(len(w.text) > 0 for w in words)
    assert words[0].start_s >= 0.0


async def test_build_subtitles_real_pipeline(tmp_path: Path) -> None:
    from alvaro.config.loader import load_voices
    from alvaro.scripting.models import Script
    from alvaro.subtitles.builder import build_subtitles
    from alvaro.tts.synthesizer import synthesize_script

    voices = load_voices()
    script = Script(
        hook_text="Por que el cielo es azul?",
        body_lines=[
            "La luz solar contiene todos los colores del espectro visible.",
            "Cuando la luz entra en la atmosfera choca con moleculas de aire.",
            "La luz azul se dispersa mas que los otros colores.",
            "Por eso vemos el cielo de color azul durante el dia.",
        ],
        payoff_text="Este fenomeno se llama dispersion de Rayleigh.",
        total_duration_estimate_s=35,
        suggested_voice_id="alvaro_es",
        suggested_background_niche="minecraft_parkour",
        niche_id="science",
    )

    audio_path = tmp_path / "audio.mp3"
    await synthesize_script(script, "alvaro_es", voices, audio_path)

    ass_path = tmp_path / "subs.ass"
    track = await build_subtitles(audio_path, script, ass_path)

    assert ass_path.exists()
    assert ass_path.stat().st_size > 500
    content = ass_path.read_text()
    assert "[Script Info]" in content
    assert "[V4+ Styles]" in content
    assert "[Events]" in content
    assert "Dialogue:" in content

    assert len(track.words) >= 5
    assert track.keyword_count >= 1
    assert track.total_duration_s > 5.0
    assert all(w.start_s < w.end_s for w in track.words)
