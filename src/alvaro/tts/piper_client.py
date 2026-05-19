from __future__ import annotations

import os
import subprocess
from pathlib import Path

import httpx

from alvaro.config.loader import VoicesConfig
from alvaro.tts._types import TTSError, TTSNetworkError

_HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
_DEFAULT_MODEL = "es_ES-davefx-medium"
_MODEL_PATH_TMPL = "{lang}/{lang_full}/{name}/{quality}/{name}.onnx"
_CONFIG_PATH_TMPL = "{lang}/{lang_full}/{name}/{quality}/{name}.onnx.json"

_MODEL_SPECS: dict[str, dict[str, str]] = {
    "es_ES-davefx-medium": {
        "lang": "es",
        "lang_full": "es_ES",
        "name": "es_ES-davefx",
        "quality": "medium",
    },
}


def _models_dir() -> Path:
    return Path(os.environ.get("PIPER_MODELS_DIR", "/tmp/piper_models"))  # noqa: S108


def _ensure_model(model_name: str) -> Path:
    spec = _MODEL_SPECS.get(model_name)
    if spec is None:
        raise TTSError(f"unknown piper model '{model_name}'")
    models_dir = _models_dir()
    models_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = models_dir / f"{model_name}.onnx"
    config_path = models_dir / f"{model_name}.onnx.json"
    if onnx_path.exists() and config_path.exists():
        return onnx_path
    onnx_url = f"{_HF_BASE}/{_MODEL_PATH_TMPL.format(**spec)}"
    config_url = f"{_HF_BASE}/{_CONFIG_PATH_TMPL.format(**spec)}"
    try:
        with httpx.Client(follow_redirects=True, timeout=120) as http:
            for url, dest in [(config_url, config_path), (onnx_url, onnx_path)]:
                resp = http.get(url)
                resp.raise_for_status()
                dest.write_bytes(resp.content)
    except httpx.HTTPError as exc:
        raise TTSNetworkError(f"piper model download failed: {exc}") from exc
    return onnx_path


class PiperClient:
    # TODO(fase-11): mapear voice_id de edge-tts a modelo piper equivalente mas cercano
    # para consistencia de voz entre primary y fallback. Por ahora todos los voice_id
    # de edge mapean al mismo modelo es_ES-davefx-medium.

    def __init__(self, voices: VoicesConfig, timeout_s: int = 120) -> None:
        self._voices = voices
        self._timeout_s = timeout_s

    def _resolve_binary(self) -> str:
        return self._voices.fallback.binary

    def _resolve_model(self) -> str:
        return self._voices.fallback.model

    async def synthesize(self, text: str, voice_id: str, output_path: Path) -> Path:
        model_name = self._resolve_model()
        onnx_path = _ensure_model(model_name)
        binary = self._resolve_binary()
        cmd = [
            binary,
            "--model",
            str(onnx_path),
            "--output_file",
            str(output_path),
        ]
        try:
            proc = subprocess.run(  # noqa: S603
                cmd,
                input=text.encode(),
                capture_output=True,
                timeout=self._timeout_s,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise TTSNetworkError(f"piper subprocess error: {exc}") from exc
        if proc.returncode != 0:
            stderr = proc.stderr.decode(errors="replace")
            raise TTSError(f"piper exited {proc.returncode}: {stderr[:200]}")
        return output_path
