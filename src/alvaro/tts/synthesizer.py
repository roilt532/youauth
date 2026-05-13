from __future__ import annotations

import tempfile
from pathlib import Path

from loguru import logger

from alvaro._ffmpeg import probe_duration
from alvaro.config.loader import VoicesConfig
from alvaro.scripting.models import Script
from alvaro.tts._types import AudioMetadata, TTSNetworkError
from alvaro.tts.edge_client import EdgeTTSClient
from alvaro.tts.normalizer import _SAMPLE_RATE, loudnorm
from alvaro.tts.piper_client import PiperClient
from alvaro.tts.ssml import build_ssml

_LUFS_TARGET = -16.0
_DURATION_TOLERANCE_S = 3

_probe_duration = probe_duration


def _resolve_voice_params(voices: VoicesConfig, voice_id: str) -> tuple[str, str]:
    for vc in voices.voices:
        if vc.id == voice_id:
            return vc.rate, vc.pitch
    return "+0%", "+0Hz"


async def synthesize_script(
    script: Script,
    voice_id: str,
    voices: VoicesConfig,
    output_path: Path,
) -> AudioMetadata:
    rate, pitch = _resolve_voice_params(voices, voice_id)
    ssml = build_ssml(script, rate, pitch)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        raw_path = Path(tmp.name)

    try:
        edge_client = EdgeTTSClient(voices)
        await edge_client.synthesize(ssml, voice_id, raw_path)
    except TTSNetworkError as exc:
        logger.warning("edge-tts failed, falling back to piper: {}", exc)
        piper_client = PiperClient(voices)
        plain_text = "\n\n".join(
            [script.hook_text] + script.body_lines + [script.payoff_text]
        )
        await piper_client.synthesize(plain_text, voice_id, raw_path)

    lufs = loudnorm(raw_path, output_path)
    raw_path.unlink(missing_ok=True)

    duration_s = _probe_duration(output_path)
    delta = abs(duration_s - script.total_duration_estimate_s)
    if delta > _DURATION_TOLERANCE_S:
        logger.warning(
            "duration mismatch: real {:.1f}s vs estimate {}s (delta {:.1f}s)",
            duration_s,
            script.total_duration_estimate_s,
            delta,
        )

    return AudioMetadata(
        file_path=output_path,
        format="mp3",
        duration_s=duration_s,
        sample_rate=_SAMPLE_RATE,
        channels=1,
        lufs_integrated=lufs,
        lufs_target=_LUFS_TARGET,
    )
