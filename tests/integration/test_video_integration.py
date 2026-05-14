from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_VIDEO_INTEGRATION"),
    reason="RUN_VIDEO_INTEGRATION not set - skipping video integration test",
)


async def test_compose_video_real_pipeline(tmp_path: Path) -> None:
    from alvaro.config.loader import load_voices
    from alvaro.scripting.models import Script
    from alvaro.storage.r2 import build_r2_client
    from alvaro.subtitles.builder import build_subtitles
    from alvaro.tts.synthesizer import synthesize_script
    from alvaro.video.background import select_background
    from alvaro.video.compositor import compose_video

    voices = load_voices()
    script = Script(
        hook_text="Por que el cielo es azul?",
        body_lines=[
            "La luz solar contiene todos los colores del espectro visible.",
            "Cuando la luz entra en la atmosfera choca con moleculas de aire.",
            "La luz azul se dispersa mas que los otros colores.",
        ],
        payoff_text="Este fenomeno se llama dispersion de Rayleigh.",
        total_duration_estimate_s=30,
        suggested_voice_id="alvaro_es",
        suggested_background_niche="minecraft_parkour",
        niche_id="science",
    )

    job_id = "integration_test_job"
    audio_path = tmp_path / "audio.mp3"
    await synthesize_script(script, "alvaro_es", voices, audio_path)
    assert audio_path.exists()

    ass_path = tmp_path / "subs.ass"
    await build_subtitles(audio_path, script, ass_path)
    assert ass_path.exists()

    r2 = build_r2_client()
    bg_path = await select_background(
        script.suggested_background_niche, r2, cache_dir=tmp_path / "bg_cache"
    )
    assert bg_path.exists()

    out_path = tmp_path / "final.mp4"
    meta = await compose_video(
        audio_path=audio_path,
        background_path=bg_path,
        subs_path=ass_path,
        output_path=out_path,
        job_id=job_id,
        r2_client=r2,
    )

    assert out_path.exists()
    assert meta.width == 1080
    assert meta.height == 1920
    assert meta.fps == 30
    assert meta.codec_video == "h264"
    assert meta.codec_audio == "aac"
    assert meta.duration_s > 5.0
    assert meta.size_bytes > 0
    assert meta.r2_key == f"videos/{job_id}.mp4"
    assert meta.file_path == out_path
