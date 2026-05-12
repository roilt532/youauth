from __future__ import annotations

from dataclasses import dataclass

_VALID_BACKGROUNDS: frozenset[str] = frozenset(
    ["minecraft_parkour", "subway_surfers", "roblox_obby", "gameplay_generic"]
)


@dataclass
class Script:
    hook_text: str
    body_lines: list[str]
    payoff_text: str
    total_duration_estimate_s: int
    suggested_voice_id: str
    suggested_background_niche: str
    niche_id: str


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]
