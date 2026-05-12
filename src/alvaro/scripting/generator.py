from __future__ import annotations

from pydantic import BaseModel

from alvaro.config.loader import PromptsConfig, VoiceConfig
from alvaro.ideation.models import IdeaCandidate
from alvaro.llm._types import LLMClient, _strip_fences
from alvaro.scripting.models import Script
from alvaro.scripting.validator import validate_script

_RETRY_TEMPS = [0.7, 0.9, 1.1]


class ScriptGenerationError(Exception):
    pass


class _ScriptResponse(BaseModel):
    title: str
    hook: str
    body: str
    voice_id: str
    duration_estimate_s: int
    tags: list[str]
    description: str


def _parse_script(raw: str) -> Script:
    data = _ScriptResponse.model_validate_json(_strip_fences(raw))
    return Script(
        title=data.title,
        hook=data.hook,
        body=data.body,
        voice_id=data.voice_id,
        duration_estimate_s=data.duration_estimate_s,
        tags=data.tags,
        description=data.description,
    )


async def generate_script(
    client: LLMClient,
    idea: IdeaCandidate,
    voice: VoiceConfig,
    prompts: PromptsConfig,
    max_duration_s: int,
) -> Script:
    niche_prompt = prompts.niches[idea.niche_id].scripting
    for temp in _RETRY_TEMPS:
        user_msg = niche_prompt.template.format_map(
            {
                "title": idea.title,
                "hook": idea.hook,
                "voice_id": voice.id,
                "max_duration_s": max_duration_s,
            }
        )
        raw = await client.complete(prompts.system_base, user_msg, temperature=temp)
        script = _parse_script(raw)
        result = validate_script(script, voice, max_duration_s)
        if result.ok:
            return script
    raise ScriptGenerationError(
        f"script validation failed after {len(_RETRY_TEMPS)} attempts"
    )
