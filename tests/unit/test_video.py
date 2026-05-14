from __future__ import annotations

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from alvaro.storage._types import BackgroundAsset
from alvaro.video._types import CompositorError, VideoMetadata
from alvaro.video.background import _key_hash, select_background


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


class TestSelectBackground:
    async def test_fallback_synthetic_when_empty(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        r2 = mocker.MagicMock()
        r2.list_backgrounds.return_value = []
        synthetic = tmp_path / "synthetic_black.mp4"
        mock_synth = mocker.patch(
            "alvaro.video.background._generate_synthetic_background",
            return_value=synthetic,
        )

        result = await select_background("minecraft", r2, cache_dir=tmp_path)

        r2.list_backgrounds.assert_called_once_with("minecraft")
        mock_synth.assert_called_once_with(tmp_path)
        assert result == synthetic

    async def test_caches_locally_when_file_exists(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        asset = BackgroundAsset(key="backgrounds/mc/clip.mp4", niche_id="mc", filename="clip.mp4")
        r2 = mocker.MagicMock()
        r2.list_backgrounds.return_value = [asset]
        cached = tmp_path / f"{_key_hash(asset.key)}.mp4"
        cached.write_bytes(b"cached_data")

        result = await select_background("mc", r2, cache_dir=tmp_path, job_id="job1")

        r2.download_asset.assert_not_called()
        assert result == cached

    async def test_downloads_and_caches(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        asset = BackgroundAsset(key="backgrounds/mc/clip.mp4", niche_id="mc", filename="clip.mp4")
        r2 = mocker.MagicMock()
        r2.list_backgrounds.return_value = [asset]
        r2.download_asset.return_value = b"video_bytes"

        result = await select_background("mc", r2, cache_dir=tmp_path, job_id="job1")

        r2.download_asset.assert_called_once_with(asset.key)
        assert result.exists()
        assert result.read_bytes() == b"video_bytes"
