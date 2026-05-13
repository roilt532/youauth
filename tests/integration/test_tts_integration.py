from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_TTS_INTEGRATION"),
    reason="RUN_TTS_INTEGRATION not set - skipping TTS integration test",
)


async def test_edge_tts_synthesize_creates_mp3(tmp_path: Path) -> None:
    from alvaro.config.loader import load_voices
    from alvaro.tts.edge_client import EdgeTTSClient

    voices = load_voices()
    client = EdgeTTSClient(voices, timeout_s=30)
    output = tmp_path / "test_edge.mp3"
    result = await client.synthesize(
        "Esto es una prueba de sintesis de voz.",
        "alvaro_es",
        output,
    )
    assert result.exists()
    assert result.stat().st_size > 1000


async def test_loudnorm_produces_48khz_mp3(tmp_path: Path) -> None:
    from alvaro.config.loader import load_voices
    from alvaro.tts.edge_client import EdgeTTSClient
    from alvaro.tts.normalizer import loudnorm

    voices = load_voices()
    edge = EdgeTTSClient(voices, timeout_s=30)
    raw_path = tmp_path / "raw.mp3"
    await edge.synthesize("Prueba de normalizacion de audio.", "alvaro_es", raw_path)

    out_path = tmp_path / "normalized.mp3"
    lufs = loudnorm(raw_path, out_path)

    assert out_path.exists()
    assert out_path.stat().st_size > 1000
    assert -17.0 <= lufs <= -15.0


async def test_synthesize_script_full_pipeline(tmp_path: Path) -> None:
    from alvaro.config.loader import load_voices
    from alvaro.scripting.models import Script
    from alvaro.tts.synthesizer import synthesize_script

    voices = load_voices()
    script = Script(
        hook_text="Por que el cielo es azul?",
        body_lines=[
            "La luz del sol contiene todos los colores del espectro.",
            "Cuando entra en la atmosfera, choca con moleculas de aire.",
            "La luz azul se dispersa mas que los otros colores.",
            "Por eso vemos el cielo de color azul durante el dia.",
            "En el atardecer, la luz viaja mas distancia y vemos naranja.",
            "Este fenomeno se llama dispersion de Rayleigh.",
        ],
        payoff_text="Asi que el azul del cielo es pura fisica de la luz.",
        total_duration_estimate_s=52,
        suggested_voice_id="alvaro_es",
        suggested_background_niche="minecraft_parkour",
        niche_id="science",
    )
    output = tmp_path / "smoke.mp3"
    meta = await synthesize_script(script, "alvaro_es", voices, output)

    assert output.exists()
    assert meta.format == "mp3"
    assert meta.sample_rate == 48000
    assert meta.channels == 1
    assert -17.5 <= meta.lufs_integrated <= -14.5
    assert meta.duration_s >= 30.0
    assert output.stat().st_size > 50_000
