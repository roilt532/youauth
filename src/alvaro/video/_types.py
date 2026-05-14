from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class CompositorError(Exception):
    pass


@dataclass(frozen=True)
class VideoMetadata:
    file_path: Path
    duration_s: float
    width: int
    height: int
    fps: int
    codec_video: str
    codec_audio: str
    size_bytes: int
    r2_key: str
