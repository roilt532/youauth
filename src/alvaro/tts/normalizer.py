from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from alvaro.tts._types import TTSError

_TARGET_I = -16.0
_TARGET_LRA = 11.0
_TARGET_TP = -1.5
_SAMPLE_RATE = 48000


def _run_ffmpeg(args: list[str], timeout_s: int = 60) -> str:
    result = subprocess.run(  # noqa: S603
        ["ffmpeg", "-y", *args],  # noqa: S607
        capture_output=True,
        timeout=timeout_s,
        check=False,
    )
    return result.stderr.decode(errors="replace")


def _parse_pass1_json(stderr: str) -> dict[str, str]:
    match = re.search(r"\{[^{}]+\}", stderr, re.DOTALL)
    if not match:
        raise TTSError(f"loudnorm pass 1: no JSON in ffmpeg output\n{stderr[:500]}")
    try:
        data: dict[str, str] = json.loads(match.group())
    except json.JSONDecodeError as exc:
        raise TTSError(f"loudnorm pass 1: invalid JSON: {exc}") from exc
    required = {"input_i", "input_tp", "input_lra", "input_thresh", "target_offset"}
    missing = required - data.keys()
    if missing:
        raise TTSError(f"loudnorm pass 1: missing keys {missing}")
    return data


def _parse_output_lufs(stderr: str) -> float:
    match = re.search(r"Output Integrated:\s*([-\d.]+)\s*LUFS", stderr)
    if not match:
        raise TTSError(f"loudnorm pass 2: could not parse Output Integrated\n{stderr[:500]}")
    return float(match.group(1))


def loudnorm(input_path: Path, output_path: Path, timeout_s: int = 60) -> float:
    filter1 = f"loudnorm=I={_TARGET_I}:LRA={_TARGET_LRA}:TP={_TARGET_TP}:print_format=json"
    stderr1 = _run_ffmpeg(
        ["-i", str(input_path), "-af", filter1, "-f", "null", "-"],
        timeout_s=timeout_s,
    )
    stats = _parse_pass1_json(stderr1)

    filter2 = (
        f"loudnorm=I={_TARGET_I}:LRA={_TARGET_LRA}:TP={_TARGET_TP}"
        f":measured_I={stats['input_i']}"
        f":measured_TP={stats['input_tp']}"
        f":measured_LRA={stats['input_lra']}"
        f":measured_thresh={stats['input_thresh']}"
        f":offset={stats['target_offset']}"
        f":linear=true:print_format=summary"
    )
    stderr2 = _run_ffmpeg(
        [
            "-i",
            str(input_path),
            "-af",
            filter2,
            "-ar",
            str(_SAMPLE_RATE),
            "-ac",
            "1",
            "-b:a",
            "128k",
            str(output_path),
        ],
        timeout_s=timeout_s,
    )
    return _parse_output_lufs(stderr2)
