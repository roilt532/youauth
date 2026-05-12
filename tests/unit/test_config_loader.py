from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from alvaro.config.loader import (
    FewShot,
    NicheConfig,
    PromptsConfig,
    VoicesConfig,
    load_niches,
    load_prompts,
    load_voices,
)

_NICHE_YAML: dict[str, object] = {
    "niches": [
        {
            "id": "science",
            "label": "Ciencia",
            "schedule_utc": ["08:00", "14:00"],
            "keywords": ["kw1", "kw2"],
            "tone": "divulgativo",
            "hook_style": "pregunta",
            "max_duration_s": 55,
            "target_audience": "adultos 18-35",
        }
    ]
}

_VOICES_YAML: dict[str, object] = {
    "voices": [
        {
            "id": "alvaro_es",
            "engine": "edge-tts",
            "voice": "es-ES-AlvaroNeural",
            "language": "es-ES",
            "rate": "+5%",
            "pitch": "+0Hz",
            "niches": ["science"],
        }
    ],
    "fallback": {
        "engine": "piper",
        "model": "es_ES-davefx-medium",
        "binary": "piper",
        "niches": ["*"],
    },
    "niche_voice_map": {"science": ["alvaro_es"]},
}

_PROMPTS_YAML: dict[str, object] = {
    "system_base": "Eres un guionista.",
    "niches": {
        "science": {
            "ideation": {
                "template": "Genera {used_topics}.",
                "few_shots": [{"topic": "cuantica", "output": '{"ideas": []}'}],
            },
            "scripting": {
                "template": "Escribe {title}.",
                "few_shots": [],
            },
        }
    },
}


@pytest.fixture(autouse=True)
def clear_caches() -> None:
    load_niches.cache_clear()
    load_voices.cache_clear()
    load_prompts.cache_clear()


def _write(path: Path, data: object) -> None:
    path.write_text(yaml.dump(data, allow_unicode=True))


def test_load_niches_parses_fields(tmp_path: Path) -> None:
    _write(tmp_path / "niches.yaml", _NICHE_YAML)
    result = load_niches(tmp_path)
    assert len(result) == 1
    n = result[0]
    assert isinstance(n, NicheConfig)
    assert n.id == "science"
    assert n.max_duration_s == 55
    assert n.keywords == ["kw1", "kw2"]
    assert n.schedule_utc == ["08:00", "14:00"]


def test_load_niches_caches(tmp_path: Path) -> None:
    _write(tmp_path / "niches.yaml", _NICHE_YAML)
    r1 = load_niches(tmp_path)
    r2 = load_niches(tmp_path)
    assert r1 is r2


def test_load_voices_parses_structure(tmp_path: Path) -> None:
    _write(tmp_path / "voices.yaml", _VOICES_YAML)
    cfg = load_voices(tmp_path)
    assert isinstance(cfg, VoicesConfig)
    assert len(cfg.voices) == 1
    assert cfg.voices[0].id == "alvaro_es"
    assert cfg.voices[0].language == "es-ES"
    assert cfg.fallback.engine == "piper"
    assert cfg.niche_voice_map["science"] == ["alvaro_es"]


def test_load_voices_caches(tmp_path: Path) -> None:
    _write(tmp_path / "voices.yaml", _VOICES_YAML)
    v1 = load_voices(tmp_path)
    v2 = load_voices(tmp_path)
    assert v1 is v2


def test_load_prompts_parses_structure(tmp_path: Path) -> None:
    _write(tmp_path / "prompts.yaml", _PROMPTS_YAML)
    cfg = load_prompts(tmp_path)
    assert isinstance(cfg, PromptsConfig)
    assert cfg.system_base == "Eres un guionista."
    assert "science" in cfg.niches
    nc = cfg.niches["science"]
    assert nc.ideation.template == "Genera {used_topics}."
    assert len(nc.ideation.few_shots) == 1
    assert isinstance(nc.ideation.few_shots[0], FewShot)
    assert nc.ideation.few_shots[0].topic == "cuantica"
    assert nc.scripting.few_shots == []


def test_load_prompts_caches(tmp_path: Path) -> None:
    _write(tmp_path / "prompts.yaml", _PROMPTS_YAML)
    p1 = load_prompts(tmp_path)
    p2 = load_prompts(tmp_path)
    assert p1 is p2


def test_load_niches_multiple_entries(tmp_path: Path) -> None:
    data: dict[str, object] = {
        "niches": [
            {**_NICHE_YAML["niches"][0], "id": "science"},  # type: ignore[index]
            {**_NICHE_YAML["niches"][0], "id": "history"},  # type: ignore[index]
        ]
    }
    _write(tmp_path / "niches.yaml", data)
    result = load_niches(tmp_path)
    assert len(result) == 2
    assert result[1].id == "history"
