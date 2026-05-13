from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_CONFIGS_DIR = Path(__file__).parent.parent.parent.parent / "configs"


@dataclass(frozen=True)
class NicheConfig:
    id: str
    label: str
    schedule_utc: list[str]
    keywords: list[str]
    tone: str
    hook_style: str
    max_duration_s: int
    target_audience: str


@dataclass(frozen=True)
class VoiceConfig:
    id: str
    engine: str
    voice: str
    language: str
    rate: str
    pitch: str
    niches: list[str]
    gender: str = "neutral"
    style: str = "conversational"
    wpm_hint: int = 150


@dataclass(frozen=True)
class FallbackVoiceConfig:
    engine: str
    model: str
    binary: str
    niches: list[str]
    hf_repo: str = "rhasspy/piper-voices"
    languages: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class VoicesConfig:
    voices: list[VoiceConfig]
    fallback: FallbackVoiceConfig
    niche_voice_map: dict[str, list[str]]


@dataclass(frozen=True)
class FewShot:
    topic: str
    output: str


@dataclass(frozen=True)
class IdeationNicheConfig:
    template: str
    few_shots: list[FewShot]


@dataclass(frozen=True)
class ScriptingNicheConfig:
    template: str
    few_shots: list[FewShot]


@dataclass(frozen=True)
class NichePromptConfig:
    ideation: IdeationNicheConfig
    scripting: ScriptingNicheConfig


@dataclass(frozen=True)
class PromptsConfig:
    system_base: str
    niches: dict[str, NichePromptConfig]


@lru_cache(maxsize=1)
def load_niches(configs_dir: Path = _CONFIGS_DIR) -> list[NicheConfig]:
    raw: Any = yaml.safe_load((configs_dir / "niches.yaml").read_text())
    return [
        NicheConfig(
            id=n["id"],
            label=n["label"],
            schedule_utc=list(n["schedule_utc"]),
            keywords=list(n["keywords"]),
            tone=n["tone"],
            hook_style=n["hook_style"],
            max_duration_s=int(n["max_duration_s"]),
            target_audience=n["target_audience"],
        )
        for n in raw["niches"]
    ]


@lru_cache(maxsize=1)
def load_voices(configs_dir: Path = _CONFIGS_DIR) -> VoicesConfig:
    raw: Any = yaml.safe_load((configs_dir / "voices.yaml").read_text())
    voices = [
        VoiceConfig(
            id=v["id"],
            engine=v["engine"],
            voice=v["voice"],
            language=v["language"],
            rate=v["rate"],
            pitch=v["pitch"],
            niches=list(v["niches"]),
            gender=v.get("gender", "neutral"),
            style=v.get("style", "conversational"),
            wpm_hint=int(v.get("wpm_hint", 150)),
        )
        for v in raw["voices"]
    ]
    fb = raw["fallback"]
    fallback = FallbackVoiceConfig(
        engine=fb["engine"],
        model=fb["model"],
        binary=fb["binary"],
        niches=list(fb["niches"]),
        hf_repo=fb.get("hf_repo", "rhasspy/piper-voices"),
        languages=list(fb.get("languages", [])),
    )
    return VoicesConfig(
        voices=voices,
        fallback=fallback,
        niche_voice_map={k: list(v) for k, v in raw["niche_voice_map"].items()},
    )


@lru_cache(maxsize=1)
def load_prompts(configs_dir: Path = _CONFIGS_DIR) -> PromptsConfig:
    raw: Any = yaml.safe_load((configs_dir / "prompts.yaml").read_text())
    niches: dict[str, NichePromptConfig] = {}
    for niche_id, niche_data in raw["niches"].items():
        id_raw = niche_data["ideation"]
        sc_raw = niche_data["scripting"]
        niches[niche_id] = NichePromptConfig(
            ideation=IdeationNicheConfig(
                template=id_raw["template"],
                few_shots=[
                    FewShot(topic=fs["topic"], output=fs["output"])
                    for fs in id_raw.get("few_shots", [])
                ],
            ),
            scripting=ScriptingNicheConfig(
                template=sc_raw["template"],
                few_shots=[
                    FewShot(topic=fs["topic"], output=fs["output"])
                    for fs in sc_raw.get("few_shots", [])
                ],
            ),
        )
    return PromptsConfig(system_base=raw["system_base"], niches=niches)
