from __future__ import annotations

import asyncio
import hashlib
import random
import subprocess
from pathlib import Path

from alvaro.storage.r2 import R2Client

# TODO(fase-11): si distribucion de uso de clips sale sesgada con pocos clips disponibles,
# considerar round-robin via tabla niches_state.last_background_idx


def _key_hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def _generate_synthetic_background(cache_dir: Path) -> Path:
    out = cache_dir / "synthetic_black.mp4"
    if out.exists():
        return out
    cache_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(  # noqa: S603
        [  # noqa: S607
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=black:s=1920x1080:d=60:r=30",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "30",
            str(out),
            "-loglevel",
            "error",
        ],
        check=True,
        timeout=30,
    )
    return out


async def select_background(
    niche_background: str,
    r2_client: R2Client,
    cache_dir: Path = Path("/tmp/alvaro_backgrounds"),  # noqa: S108
    job_id: str = "",
) -> Path:
    assets = r2_client.list_backgrounds(niche_background)
    if not assets:
        return _generate_synthetic_background(cache_dir)

    rng = random.Random(job_id or niche_background)  # noqa: S311
    asset = rng.choice(assets)

    local_path = cache_dir / f"{_key_hash(asset.key)}.mp4"
    if local_path.exists():
        return local_path

    cache_dir.mkdir(parents=True, exist_ok=True)
    data = await asyncio.to_thread(r2_client.download_asset, asset.key)
    local_path.write_bytes(data)
    return local_path
