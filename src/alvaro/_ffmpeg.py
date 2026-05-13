from __future__ import annotations

import subprocess
from pathlib import Path


def probe_duration(path: Path) -> float:
    result = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        check=False,
        timeout=30,
    )
    return float(result.stdout.decode().strip())
