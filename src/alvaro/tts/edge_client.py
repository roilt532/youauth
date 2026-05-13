from __future__ import annotations

from pathlib import Path

import edge_tts

from alvaro.config.loader import VoicesConfig
from alvaro.tts._types import TTSNetworkError


class EdgeTTSClient:
    def __init__(self, voices: VoicesConfig, timeout_s: int = 60) -> None:
        self._voices = voices
        self._timeout_s = timeout_s

    def _resolve_voice(self, voice_id: str) -> tuple[str, str, str]:
        for vc in self._voices.voices:
            if vc.id == voice_id:
                return vc.voice, vc.rate, vc.pitch
        raise ValueError(f"voice_id '{voice_id}' not found in voices catalog")

    async def synthesize(self, text: str, voice_id: str, output_path: Path) -> Path:
        voice_name, rate, pitch = self._resolve_voice(voice_id)
        if text.startswith("<speak>"):
            communicate = edge_tts.Communicate(
                text,
                voice_name,
                connect_timeout=10,
                receive_timeout=self._timeout_s,
            )
        else:
            communicate = edge_tts.Communicate(
                text,
                voice_name,
                rate=rate,
                pitch=pitch,
                connect_timeout=10,
                receive_timeout=self._timeout_s,
            )
        try:
            await communicate.save(str(output_path))
        except (TimeoutError, OSError) as exc:
            raise TTSNetworkError(f"edge-tts network error: {exc}") from exc
        except Exception as exc:
            msg = str(exc).lower()
            if "network" in msg or "connection" in msg or "timeout" in msg:
                raise TTSNetworkError(f"edge-tts error: {exc}") from exc
            raise
        return output_path
