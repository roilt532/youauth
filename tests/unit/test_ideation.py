from __future__ import annotations

from unittest.mock import AsyncMock

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


def _make_prompts(template: str = "Genera ideas. Usados: {used_topics}.") -> PromptsConfig:
    ideation = IdeationNicheConfig(template=template, few_shots=[])
    scripting = ScriptingNicheConfig(template="", few_shots=[])
    return PromptsConfig(
        system_base="Eres guionista.",
        niches={"science": NichePromptConfig(ideation=ideation, scripting=scripting)},
    )


_VALID_JSON = (
    '{"ideas": [{"title": "T1", "hook": "H1", "score": 8},'
    ' {"title": "T2", "hook": "H2", "score": 6}]}'
)


async def test_generate_ideas_parses_json() -> None:
    client = AsyncMock()
    client.complete.return_value = _VALID_JSON
    result = await generate_ideas(client, "science", [], _make_prompts())
    assert len(result) == 2
    assert result[0].title == "T1"
    assert result[0].score == 8
    assert result[0].niche_id == "science"


async def test_generate_ideas_strips_fences() -> None:
    client = AsyncMock()
    client.complete.return_value = f"```json\n{_VALID_JSON}\n```"
    result = await generate_ideas(client, "science", [], _make_prompts())
    assert len(result) == 2


async def test_generate_ideas_passes_used_topics() -> None:
    client = AsyncMock()
    client.complete.return_value = _VALID_JSON
    await generate_ideas(client, "science", ["fisica", "quimica"], _make_prompts())
    call_args = client.complete.call_args
    assert "fisica" in call_args[0][1]
    assert "quimica" in call_args[0][1]


async def test_generate_ideas_empty_used_topics_uses_ninguno() -> None:
    client = AsyncMock()
    client.complete.return_value = _VALID_JSON
    await generate_ideas(client, "science", [], _make_prompts())
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
    await generate_ideas(client, "science", [], prompts)
    call_args = client.complete.call_args
    assert "cuantica" in call_args[0][1]


def test_select_best_picks_highest_score() -> None:
    candidates = [
        IdeaCandidate(title="A", hook="h", score=5, niche_id="science"),
        IdeaCandidate(title="B", hook="h", score=9, niche_id="science"),
        IdeaCandidate(title="C", hook="h", score=7, niche_id="science"),
    ]
    best = select_best(candidates)
    assert best.title == "B"
    assert best.score == 9


def test_select_best_tiebreak_by_title() -> None:
    candidates = [
        IdeaCandidate(title="Alfa", hook="h", score=8, niche_id="science"),
        IdeaCandidate(title="Zeta", hook="h", score=8, niche_id="science"),
    ]
    best = select_best(candidates)
    assert best.title == "Zeta"


def test_select_best_single_candidate() -> None:
    candidates = [IdeaCandidate(title="X", hook="h", score=7, niche_id="science")]
    assert select_best(candidates).title == "X"


def test_select_best_empty_raises() -> None:
    with pytest.raises(ValueError, match="no candidates"):
        select_best([])
