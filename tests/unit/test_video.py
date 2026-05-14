from __future__ import annotations

from pathlib import Path

import pytest

from alvaro.video._types import CompositorError, VideoMetadata


def _make_meta(**kwargs: object) -> VideoMetadata:
    defaults: dict[str, object] = {
        "file_path": Path("/tmp/v.mp4"),  # noqa: S108
        "duration_s": 48.0,
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "codec_video": "h264",
        "codec_audio": "aac",
        "size_bytes": 5_000_000,
        "r2_key": "videos/job_001.mp4",
    }
    defaults.update(kwargs)
    return VideoMetadata(**defaults)  # type: ignore[arg-type]


class TestVideoMetadata:
    def test_frozen_raises_on_assign(self) -> None:
        meta = _make_meta()
        with pytest.raises((AttributeError, TypeError)):
            meta.width = 720  # type: ignore[misc]

    def test_fields(self) -> None:
        meta = _make_meta()
        assert meta.width == 1080
        assert meta.height == 1920
        assert meta.fps == 30
        assert meta.codec_video == "h264"
        assert meta.codec_audio == "aac"
        assert meta.r2_key == "videos/job_001.mp4"

    def test_r2_key_field(self) -> None:
        meta = _make_meta(r2_key="videos/my_job.mp4")
        assert meta.r2_key == "videos/my_job.mp4"


class TestCompositorError:
    def test_is_exception(self) -> None:
        err = CompositorError("ffmpeg exited 1")
        assert isinstance(err, Exception)
        assert "ffmpeg" in str(err)
