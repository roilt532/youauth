from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class SubtitleError(Exception):
    pass


@dataclass(frozen=True)
class WordTiming:
    text: str
    start_s: float
    end_s: float
    is_keyword: bool


@dataclass(frozen=True)
class SubtitleTrack:
    ass_file_path: Path
    words: list[WordTiming]
    total_duration_s: float
    keyword_count: int
