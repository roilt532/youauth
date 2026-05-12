from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IdeaCandidate:
    title: str
    hook: str
    score: int
    niche_id: str
