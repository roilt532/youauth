from __future__ import annotations

from pathlib import Path

from loguru import logger

from alvaro._ffmpeg import probe_duration
from alvaro.config.loader import load_voices
from alvaro.scripting.models import Script
from alvaro.subtitles._types import SubtitleTrack, WordTiming
from alvaro.subtitles.ass_renderer import render_ass
from alvaro.subtitles.styler import apply_keywords
from alvaro.subtitles.transcriber import transcribe

_WORDCOUNT_TOLERANCE = 0.15
_DURATION_TOLERANCE_S = 1.0


def _resolve_language(voice_id: str) -> str:
    voices = load_voices()
    for vc in voices.voices:
        if vc.id == voice_id:
            return vc.language[:2].lower()
    return "es"


def _script_wordcount(script: Script) -> int:
    all_text = " ".join([script.hook_text] + script.body_lines + [script.payoff_text])
    return len(all_text.split())


async def build_subtitles(
    audio_path: Path,
    script: Script,
    output_path: Path,
) -> SubtitleTrack:
    language = _resolve_language(script.suggested_voice_id)

    raw_words: list[WordTiming] = await transcribe(audio_path, language)

    script_wc = _script_wordcount(script)
    trans_wc = len(raw_words)
    if script_wc > 0:
        ratio = trans_wc / script_wc
        if not (1 - _WORDCOUNT_TOLERANCE) <= ratio <= (1 + _WORDCOUNT_TOLERANCE):
            logger.warning(
                "wordcount delta {:.0%}: transcribed={} script={}",
                ratio,
                trans_wc,
                script_wc,
            )

    words = apply_keywords(raw_words, script, language)

    render_ass(words, output_path)

    total_duration_s = words[-1].end_s if words else 0.0
    audio_duration = probe_duration(audio_path)
    if abs(total_duration_s - audio_duration) > _DURATION_TOLERANCE_S:
        logger.warning(
            "subtitle duration {:.2f}s vs audio {:.2f}s",
            total_duration_s,
            audio_duration,
        )

    keyword_count = sum(1 for w in words if w.is_keyword)
    return SubtitleTrack(
        ass_file_path=output_path,
        words=words,
        total_duration_s=total_duration_s,
        keyword_count=keyword_count,
    )
