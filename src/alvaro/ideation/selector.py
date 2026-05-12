from __future__ import annotations

from alvaro.ideation.models import IdeaCandidate


def select_best(candidates: list[IdeaCandidate]) -> IdeaCandidate:
    if not candidates:
        raise ValueError("no candidates to select from")
    return max(candidates, key=lambda c: (c.score, c.title))
