from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

from alvaro._ffmpeg import probe_duration
from alvaro.storage.r2 import R2Client
from alvaro.video._types import CompositorError, VideoMetadata

_WIDTH = 1080
_HEIGHT = 1920
_FPS = 30
_INTRO_DUR = 0.5
_INTRO_TEXT = "ALVARO"


def _build_filter_complex(
    bg_duration: float,
    content_duration: float,
    subs_path: Path,
) -> str:
    total_frames = max(1, round(bg_duration * _FPS))
    subs_escaped = str(subs_path).replace("\\", "\\\\").replace(":", "\\:")

    if bg_duration < content_duration:
        bg_video = (
            f"[0:v]loop=loop=-1:size={total_frames}:start=0,"
            f"trim=end={content_duration:.3f},setpts=PTS-STARTPTS[bg_loop]"
        )
    else:
        bg_video = f"[0:v]trim=end={content_duration:.3f},setpts=PTS-STARTPTS[bg_loop]"

    fade_start = f"{_INTRO_DUR - 0.1:.1f}"
    return (
        f"{bg_video};"
        f"[bg_loop]scale={_WIDTH}:{_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={_WIDTH}:{_HEIGHT},setsar=1[bg_scaled];"
        f"[bg_scaled]ass=filename={subs_escaped}[v_subs];"
        f"color=black:s={_WIDTH}x{_HEIGHT}:d={_INTRO_DUR},"
        f"drawtext=text={_INTRO_TEXT}:fontsize=80:fontcolor=white"
        f":x=(w-text_w)/2:y=(h-text_h)/2,"
        f"fade=type=out:start_time={fade_start}:duration=0.1,"
        f"setsar=1[v_intro];"
        f"[v_intro][v_subs]concat=n=2:v=1:a=0[v_out];"
        f"anullsrc=channel_layout=stereo:sample_rate=48000:d={_INTRO_DUR}[a_silence];"
        f"[a_silence][1:a]concat=n=2:v=0:a=1[a_out]"
    )


def _run_ffmpeg(cmd: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        check=False,
        timeout=600,
    )


async def compose_video(
    audio_path: Path,
    background_path: Path,
    subs_path: Path,
    output_path: Path,
    job_id: str,
    r2_client: R2Client,
) -> VideoMetadata:
    bg_duration = await asyncio.to_thread(probe_duration, background_path)
    audio_duration = await asyncio.to_thread(probe_duration, audio_path)

    filter_complex = _build_filter_complex(bg_duration, audio_duration, subs_path)

    cmd = [  # noqa: S607
        "ffmpeg",
        "-y",
        "-i",
        str(background_path),
        "-i",
        str(audio_path),
        "-filter_complex",
        filter_complex,
        "-map",
        "[v_out]",
        "-map",
        "[a_out]",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-r",
        str(_FPS),
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
        "-loglevel",
        "error",
    ]

    result = await asyncio.to_thread(_run_ffmpeg, cmd)
    if result.returncode != 0:
        raise CompositorError(result.stderr.decode())

    duration_s = await asyncio.to_thread(probe_duration, output_path)
    size_bytes = output_path.stat().st_size
    r2_key = f"videos/{job_id}.mp4"

    await asyncio.to_thread(
        r2_client.upload_asset,
        r2_key,
        output_path.read_bytes(),
        "video/mp4",
    )

    return VideoMetadata(
        file_path=output_path,
        duration_s=duration_s,
        width=_WIDTH,
        height=_HEIGHT,
        fps=_FPS,
        codec_video="h264",
        codec_audio="aac",
        size_bytes=size_bytes,
        r2_key=r2_key,
    )
