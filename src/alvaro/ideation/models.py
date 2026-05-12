from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IdeaCandidate:
    hook: str
    topic: str
    angle: str
    estimated_engagement_score: int
    niche_id: str
