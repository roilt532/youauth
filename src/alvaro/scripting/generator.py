from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ValidationError

from alvaro.config.loader import FewShot, VoicesConfig, load_niches, load_prompts
from alvaro.ideation.models import IdeaCandidate
from alvaro.llm._types import LLMClient, _strip_fences
from alvaro.scripting.models import _VALID_BACKGROUNDS, Script
from alvaro.scripting.validator import validate_script

_RETRY_TEMPS = [0.7, 0.9, 1.1]
_BACKGROUNDS_STR = ", ".join(sorted(_VALID_BACKGROUNDS))
_DEFAULT_MAX_DURATION_S = 55


class ScriptGenerationError(Exception):
    pass


class _ScriptResponse(BaseModel):
    hook_text: str
    body_lines: list[str]
    payoff_text: str
    total_duration_estimate_s: int
    suggested_voice_id: str
    suggested_background_niche: str


def _build_few_shots_text(few_shots: Sequence[FewShot]) -> str:
    return "\n\n".join(f"Topico: {fs.topic}\n{fs.output}" for fs in few_shots)


def _parse_script(raw: str, niche_id: str) -> Script:
    data = _ScriptResponse.model_validate_json(_strip_fences(raw))
    return Script(
        hook_text=data.hook_text,
        body_lines=data.body_lines,
        payoff_text=data.payoff_text,
        total_duration_estimate_s=data.total_duration_estimate_s,
        suggested_voice_id=data.suggested_voice_id,
        suggested_background_niche=data.suggested_background_niche,
        niche_id=niche_id,
    )


async def generate_script(
    idea: IdeaCandidate,
    niche_id: str,
    llm: LLMClient,
    voices: VoicesConfig,
) -> Script:
    prompts = load_prompts()
    niches = load_niches()
    niche_cfg = next((n for n in niches if n.id == niche_id), None)
    max_duration_s = niche_cfg.max_duration_s if niche_cfg else _DEFAULT_MAX_DURATION_S

    niche_voice_ids = voices.niche_voice_map.get(niche_id, [])
    voice_map = {v.id: v for v in voices.voices}
    voice_catalog = ", ".join(niche_voice_ids)

    niche_prompt = prompts.niches[niche_id].scripting
    few_shots_text = _build_few_shots_text(niche_prompt.few_shots)

    for temp in _RETRY_TEMPS:
        user_msg = niche_prompt.template.format_map(
            {
                "hook": idea.hook,
                "topic": idea.topic,
                "angle": idea.angle,
                "niche_id": niche_id,
                "voice_catalog": voice_catalog,
                "background_options": _BACKGROUNDS_STR,
                "max_duration_s": max_duration_s,
                "few_shots": few_shots_text,
            }
        )
        raw = await llm.complete(prompts.system_base, user_msg, temperature=temp)
        try:
            script = _parse_script(raw, niche_id)
        except (ValidationError, ValueError):
            continue
        chosen_voice = voice_map.get(script.suggested_voice_id)
        language = chosen_voice.language if chosen_voice else "es-ES"
        result = validate_script(script, niche_voice_ids, max_duration_s, language)
        if result.ok:
            return script

    raise ScriptGenerationError(
        f"script validation failed after {len(_RETRY_TEMPS)} attempts for niche '{niche_id}'"
    )
