from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Script:
    title: str
    hook: str
    body: str
    voice_id: str
    duration_estimate_s: int
    tags: list[str]
    description: str


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]
