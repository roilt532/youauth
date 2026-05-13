from __future__ import annotations

import asyncio
import os
from pathlib import Path

from faster_whisper import WhisperModel

from alvaro.subtitles._types import WordTiming

_WHISPER_MODEL_SIZE = "small"
_COMPUTE_TYPE = "int8"
_MODEL_CACHE: dict[str, WhisperModel] = {}


def _models_dir() -> str:
    return os.environ.get("WHISPER_MODELS_DIR", "/tmp/whisper_models")  # noqa: S108


def _get_model() -> WhisperModel:
    key = _WHISPER_MODEL_SIZE
    if key not in _MODEL_CACHE:
        _MODEL_CACHE[key] = WhisperModel(
            _WHISPER_MODEL_SIZE,
            device="cpu",
            compute_type=_COMPUTE_TYPE,
            download_root=_models_dir(),
        )
    return _MODEL_CACHE[key]


def _run_transcribe(model: WhisperModel, audio_path_str: str, language: str) -> list[WordTiming]:
    segments, _ = model.transcribe(
        audio_path_str,
        language=language,
        word_timestamps=True,
        vad_filter=True,
        beam_size=5,
    )
    words: list[WordTiming] = []
    for seg in segments:
        for w in seg.words or []:
            words.append(
                WordTiming(
                    text=w.word.strip(),
                    start_s=w.start,
                    end_s=w.end,
                    is_keyword=False,
                )
            )
    return words


async def transcribe(audio_path: Path, language: str) -> list[WordTiming]:
    model = _get_model()
    return await asyncio.to_thread(_run_transcribe, model, str(audio_path), language)
