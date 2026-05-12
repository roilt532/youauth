from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel

from alvaro.config.loader import FewShot, PromptsConfig
from alvaro.ideation.models import IdeaCandidate
from alvaro.llm._types import LLMClient, _strip_fences


class _IdeaItem(BaseModel):
    title: str
    hook: str
    score: int


class _IdeaListResponse(BaseModel):
    ideas: list[_IdeaItem]


def _build_few_shots_text(few_shots: Sequence[FewShot]) -> str:
    return "\n\n".join(f"Topico: {fs.topic}\n{fs.output}" for fs in few_shots)


async def generate_ideas(
    client: LLMClient,
    niche_id: str,
    used_topics: list[str],
    prompts: PromptsConfig,
) -> list[IdeaCandidate]:
    niche_prompt = prompts.niches[niche_id].ideation
    few_shots_text = _build_few_shots_text(niche_prompt.few_shots)
    user_msg = niche_prompt.template.format_map(
        {
            "used_topics": ", ".join(used_topics) if used_topics else "ninguno",
            "few_shots": few_shots_text,
        }
    )
    raw = await client.complete(prompts.system_base, user_msg)
    data = _IdeaListResponse.model_validate_json(_strip_fences(raw))
    return [
        IdeaCandidate(
            title=item.title,
            hook=item.hook,
            score=item.score,
            niche_id=niche_id,
        )
        for item in data.ideas
    ]
