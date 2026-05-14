from __future__ import annotations

from typing import Any

from alvaro.config.loader import load_voices
from alvaro.scripting.models import Script
from alvaro.subtitles.styler import _extract_script_keywords

_MAX_TITLE_LEN = 100
_MAX_TAGS_COUNT = 10
_MAX_TAGS_CHARS = 500


def _truncate_title(text: str) -> str:
    if len(text) <= _MAX_TITLE_LEN:
        return text
    cutoff = text[:97]
    last_space = cutoff.rfind(" ")
    if last_space > 0:
        cutoff = cutoff[:last_space]
    return cutoff + "..."


def _resolve_language(voice_id: str) -> str:
    for v in load_voices().voices:
        if v.id == voice_id:
            return v.language[:2].lower()
    return "es"


def _build_tags(script: Script, language: str) -> list[str]:
    keywords = sorted(_extract_script_keywords(script, language))
    tags: list[str] = []
    total_chars = 0
    for kw in keywords[:_MAX_TAGS_COUNT]:
        if total_chars + len(kw) + 1 > _MAX_TAGS_CHARS:
            break
        tags.append(kw)
        total_chars += len(kw) + 1
    return tags


def build_video_metadata(
    script: Script,
    niche_id: str,
    privacy_status: str,
) -> dict[str, Any]:
    language = _resolve_language(script.suggested_voice_id)
    title = _truncate_title(script.hook_text)
    tags = _build_tags(script, language)
    hashtags = "#shorts #" + niche_id + " " + " ".join("#" + t for t in tags[:5])
    description = (
        script.hook_text
        + "\n\n"
        + "\n".join(script.body_lines)
        + "\n\n"
        + script.payoff_text
        + "\n\n"
        + hashtags
    )
    return {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22",
            "defaultLanguage": language,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
        },
    }
