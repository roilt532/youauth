from __future__ import annotations

from alvaro.scripting.models import _VALID_BACKGROUNDS, Script, ValidationResult

_ES_TRIGGERS: frozenset[str] = frozenset(
    ["sabias", "nunca", "esto", "por", "que", "cual", "como", "cuando", "donde", "quien"]
)
_EN_TRIGGERS: frozenset[str] = frozenset(
    ["did", "you", "what", "how", "why", "when", "where", "who", "can", "is"]
)


def _hook_is_valid(hook: str, language: str) -> bool:
    stripped = hook.strip()
    if stripped.endswith("?"):
        return True
    words = stripped.lower().split()
    first = words[0] if words else ""
    triggers = _EN_TRIGGERS if language.lower().startswith("en") else _ES_TRIGGERS
    return first in triggers


def validate_script(
    script: Script,
    niche_voice_ids: list[str],
    max_duration_s: int,
    language: str = "es-ES",
) -> ValidationResult:
    errors: list[str] = []

    if not _hook_is_valid(script.hook_text, language):
        errors.append("hook_text must end with '?' or start with a recognized trigger word")

    if script.total_duration_estimate_s > max_duration_s:
        errors.append(
            f"duration {script.total_duration_estimate_s}s exceeds max {max_duration_s}s"
        )

    if script.suggested_voice_id not in niche_voice_ids:
        errors.append(
            f"suggested_voice_id '{script.suggested_voice_id}' not in catalog {niche_voice_ids}"
        )

    if script.suggested_background_niche not in _VALID_BACKGROUNDS:
        errors.append(
            f"suggested_background_niche '{script.suggested_background_niche}' not valid"
        )

    return ValidationResult(ok=len(errors) == 0, errors=errors)
