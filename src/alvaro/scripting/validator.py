from __future__ import annotations

from alvaro.config.loader import VoiceConfig
from alvaro.scripting.models import Script, ValidationResult

_ES_TRIGGERS: frozenset[str] = frozenset(
    ["sabias", "nunca", "esto", "por", "que", "cual", "como", "cuando", "donde", "quien"]
)
_EN_TRIGGERS: frozenset[str] = frozenset(
    ["did", "you", "what", "how", "why", "when", "where", "who", "can", "is"]
)

_WPM_EN = 150
_WPM_ES = 130


def _hook_is_valid(hook: str, language: str) -> bool:
    stripped = hook.strip()
    if stripped.endswith("?"):
        return True
    words = stripped.lower().split()
    first = words[0] if words else ""
    triggers = _EN_TRIGGERS if language.lower().startswith("en") else _ES_TRIGGERS
    return first in triggers


def validate_script(script: Script, voice: VoiceConfig, max_duration_s: int) -> ValidationResult:
    errors: list[str] = []

    if not _hook_is_valid(script.hook, voice.language):
        errors.append("hook must end with '?' or start with a recognized trigger word")

    wpm = _WPM_EN if voice.language.lower().startswith("en") else _WPM_ES
    word_count = len(script.body.split())
    estimated_s = int(word_count / wpm * 60)
    if estimated_s > max_duration_s:
        errors.append(
            f"estimated duration {estimated_s}s exceeds max {max_duration_s}s"
        )

    if script.voice_id != voice.id:
        errors.append(f"voice_id mismatch: script={script.voice_id} expected={voice.id}")

    return ValidationResult(ok=len(errors) == 0, errors=errors)
