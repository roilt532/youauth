from __future__ import annotations

import time
from collections.abc import Sequence

from pydantic import BaseModel

from alvaro.config.loader import FewShot, load_prompts
from alvaro.db.client import DbClient
from alvaro.ideation.models import IdeaCandidate
from alvaro.llm._types import LLMClient, _strip_fences

_RECENT_TOPICS_LIMIT = 20
_RECENT_DAYS = 30
_IDEAS_COUNT = 6


class _IdeaItem(BaseModel):
    hook: str
    topic: str
    angle: str
    estimated_engagement_score: int


class _IdeaListResponse(BaseModel):
    ideas: list[_IdeaItem]


def _build_few_shots_text(few_shots: Sequence[FewShot]) -> str:
    return "\n\n".join(f"Topico: {fs.topic}\n{fs.output}" for fs in few_shots)


async def _get_recent_topics(db: DbClient, niche_id: str) -> list[str]:
    cutoff_ts = int(time.time()) - _RECENT_DAYS * 24 * 3600
    result = await db.execute(
        "SELECT title FROM videos WHERE niche_id = ? AND created_at > ? "
        "ORDER BY created_at DESC LIMIT ?",
        [niche_id, cutoff_ts, _RECENT_TOPICS_LIMIT],
    )
    return [str(row[0]) for row in (result.rows or [])]


async def generate_ideas(
    niche_id: str,
    llm: LLMClient,
    db: DbClient,
    n: int = 5,
) -> list[IdeaCandidate]:
    prompts = load_prompts()
    recent_topics = await _get_recent_topics(db, niche_id)
    niche_prompt = prompts.niches[niche_id].ideation
    few_shots_text = _build_few_shots_text(niche_prompt.few_shots)
    user_msg = niche_prompt.template.format_map(
        {
            "used_topics": ", ".join(recent_topics) if recent_topics else "ninguno",
            "few_shots": few_shots_text,
        }
    )
    raw = await llm.complete(prompts.system_base, user_msg)
    data = _IdeaListResponse.model_validate_json(_strip_fences(raw))
    candidates = [
        IdeaCandidate(
            hook=item.hook,
            topic=item.topic,
            angle=item.angle,
            estimated_engagement_score=item.estimated_engagement_score,
            niche_id=niche_id,
        )
        for item in data.ideas
    ]
    return sorted(candidates, key=lambda c: c.estimated_engagement_score, reverse=True)[:n]
