from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class TTSError(Exception):
    pass


class TTSNetworkError(TTSError):
    pass


@dataclass(frozen=True)
class AudioMetadata:
    file_path: Path
    format: str
    duration_s: float
    sample_rate: int
    channels: int
    lufs_integrated: float
    lufs_target: float


class TTSClient(Protocol):
    async def synthesize(self, text: str, voice_id: str, output_path: Path) -> Path: ...
