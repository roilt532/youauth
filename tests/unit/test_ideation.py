from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from alvaro.config.loader import (
    FewShot,
    IdeationNicheConfig,
    NichePromptConfig,
    PromptsConfig,
    ScriptingNicheConfig,
)
from alvaro.ideation.generator import generate_ideas
from alvaro.ideation.models import IdeaCandidate
from alvaro.ideation.selector import select_best


def _make_prompts(
    template: str = "Genera ideas. Usados: {used_topics}. {few_shots}",
) -> PromptsConfig:
    ideation = IdeationNicheConfig(template=template, few_shots=[])
    scripting = ScriptingNicheConfig(template="", few_shots=[])
    return PromptsConfig(
        system_base="Eres guionista.",
        niches={"science": NichePromptConfig(ideation=ideation, scripting=scripting)},
    )


def _make_db() -> AsyncMock:
    db = AsyncMock()
    db.execute.return_value = MagicMock(rows=[])
    return db


_VALID_JSON = (
    '{"ideas": [{"hook": "H1", "topic": "T1", "angle": "A1", "estimated_engagement_score": 8},'
    ' {"hook": "H2", "topic": "T2", "angle": "A2", "estimated_engagement_score": 6}]}'
)


async def test_generate_ideas_parses_json() -> None:
    client = AsyncMock()
    client.complete.return_value = _VALID_JSON
    with patch("alvaro.ideation.generator.load_prompts", return_value=_make_prompts()):
        result = await generate_ideas("science", client, _make_db())
    assert len(result) == 2
    assert result[0].hook == "H1"
    assert result[0].topic == "T1"
    assert result[0].estimated_engagement_score == 8
    assert result[0].niche_id == "science"


async def test_generate_ideas_strips_fences() -> None:
    client = AsyncMock()
    client.complete.return_value = f"```json\n{_VALID_JSON}\n```"
    with patch("alvaro.ideation.generator.load_prompts", return_value=_make_prompts()):
        result = await generate_ideas("science", client, _make_db())
    assert len(result) == 2


async def test_generate_ideas_passes_used_topics() -> None:
    client = AsyncMock()
    client.complete.return_value = _VALID_JSON
    db = AsyncMock()
    db.execute.return_value = MagicMock(rows=[("fisica",), ("quimica",)])
    with patch("alvaro.ideation.generator.load_prompts", return_value=_make_prompts()):
        await generate_ideas("science", client, db)
    call_args = client.complete.call_args
    assert "fisica" in call_args[0][1]
    assert "quimica" in call_args[0][1]


async def test_generate_ideas_empty_used_topics_uses_ninguno() -> None:
    client = AsyncMock()
    client.complete.return_value = _VALID_JSON
    with patch("alvaro.ideation.generator.load_prompts", return_value=_make_prompts()):
        await generate_ideas("science", client, _make_db())
    call_args = client.complete.call_args
    assert "ninguno" in call_args[0][1]


async def test_generate_ideas_includes_few_shots() -> None:
    client = AsyncMock()
    client.complete.return_value = _VALID_JSON
    ideation = IdeationNicheConfig(
        template="Ideas. Usados: {used_topics}. Ejemplos:\n{few_shots}",
        few_shots=[FewShot(topic="cuantica", output='{"ideas": []}')],
    )
    scripting = ScriptingNicheConfig(template="", few_shots=[])
    prompts = PromptsConfig(
        system_base="sys",
        niches={"science": NichePromptConfig(ideation=ideation, scripting=scripting)},
    )
    with patch("alvaro.ideation.generator.load_prompts", return_value=prompts):
        await generate_ideas("science", client, _make_db())
    call_args = client.complete.call_args
    assert "cuantica" in call_args[0][1]


def test_select_best_picks_highest_score() -> None:
    candidates = [
        IdeaCandidate(hook="h", topic="A", angle="a", estimated_engagement_score=5, niche_id="science"),  # noqa: E501
        IdeaCandidate(hook="h", topic="B", angle="a", estimated_engagement_score=9, niche_id="science"),  # noqa: E501
        IdeaCandidate(hook="h", topic="C", angle="a", estimated_engagement_score=7, niche_id="science"),  # noqa: E501
    ]
    best = select_best(candidates)
    assert best.estimated_engagement_score == 9


def test_select_best_tiebreak_by_hook() -> None:
    candidates = [
        IdeaCandidate(
            hook="Alfa", topic="t", angle="a", estimated_engagement_score=8, niche_id="science"
        ),
        IdeaCandidate(
            hook="Zeta", topic="t", angle="a", estimated_engagement_score=8, niche_id="science"
        ),
    ]
    best = select_best(candidates)
    assert best.hook == "Zeta"


def test_select_best_single_candidate() -> None:
    candidates = [
        IdeaCandidate(hook="H", topic="X", angle="a", estimated_engagement_score=7, niche_id="science")  # noqa: E501
    ]
    assert select_best(candidates).hook == "H"


def test_select_best_empty_raises() -> None:
    with pytest.raises(ValueError, match="no candidates"):
        select_best([])
