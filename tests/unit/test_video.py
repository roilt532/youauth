from __future__ import annotations

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from alvaro.storage._types import BackgroundAsset
from alvaro.video._types import CompositorError, VideoMetadata
from alvaro.video.background import _key_hash, select_background
from alvaro.video.compositor import _build_filter_complex, compose_video


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


class TestBuildFilterComplex:
    def test_loop_when_bg_shorter_than_content(self) -> None:
        fc = _build_filter_complex(
            bg_duration=10.0, content_duration=45.0, subs_path=Path("/tmp/s.ass")  # noqa: S108
        )
        assert "loop=loop=-1" in fc
        assert "trim=end=45.000" in fc

    def test_trim_when_bg_longer_than_content(self) -> None:
        fc = _build_filter_complex(
            bg_duration=120.0, content_duration=45.0, subs_path=Path("/tmp/s.ass")  # noqa: S108
        )
        assert "loop=loop=-1" not in fc
        assert "trim=end=45.000" in fc

    def test_ass_filename_in_filter(self) -> None:
        fc = _build_filter_complex(
            bg_duration=10.0, content_duration=45.0, subs_path=Path("/tmp/s.ass")  # noqa: S108
        )
        assert "ass=filename=" in fc
        assert "s.ass" in fc

    def test_audio_silence_for_intro(self) -> None:
        fc = _build_filter_complex(
            bg_duration=10.0, content_duration=45.0, subs_path=Path("/tmp/s.ass")  # noqa: S108
        )
        assert "anullsrc" in fc
        assert "[a_silence][1:a]concat" in fc
        assert "[a_out]" in fc


class TestComposeVideo:
    def _make_completed(self, returncode: int = 0) -> object:
        import subprocess
        result = subprocess.CompletedProcess(args=[], returncode=returncode)
        result.stdout = b""
        result.stderr = b"error detail" if returncode != 0 else b""
        return result

    async def test_raises_compositor_error_on_ffmpeg_failure(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        mocker.patch("alvaro.video.compositor.probe_duration", return_value=10.0)
        mocker.patch(
            "alvaro.video.compositor._run_ffmpeg",
            return_value=self._make_completed(returncode=1),
        )
        r2 = mocker.MagicMock()
        out = tmp_path / "out.mp4"

        with pytest.raises(CompositorError):
            await compose_video(
                audio_path=tmp_path / "a.mp3",
                background_path=tmp_path / "bg.mp4",
                subs_path=tmp_path / "s.ass",
                output_path=out,
                job_id="job1",
                r2_client=r2,
            )

    async def test_metadata_contains_r2_key(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        mocker.patch("alvaro.video.compositor.probe_duration", return_value=48.0)
        mocker.patch(
            "alvaro.video.compositor._run_ffmpeg",
            return_value=self._make_completed(),
        )
        out = tmp_path / "out.mp4"
        out.write_bytes(b"fake_video_data")
        r2 = mocker.MagicMock()

        meta = await compose_video(
            audio_path=tmp_path / "a.mp3",
            background_path=tmp_path / "bg.mp4",
            subs_path=tmp_path / "s.ass",
            output_path=out,
            job_id="job_abc",
            r2_client=r2,
        )

        assert meta.r2_key == "videos/job_abc.mp4"
        assert meta.width == 1080
        assert meta.height == 1920
        assert meta.fps == 30
        assert meta.codec_video == "h264"
        assert meta.codec_audio == "aac"

    async def test_uploads_to_r2(self, tmp_path: Path, mocker: MockerFixture) -> None:
        mocker.patch("alvaro.video.compositor.probe_duration", return_value=48.0)
        mocker.patch(
            "alvaro.video.compositor._run_ffmpeg",
            return_value=self._make_completed(),
        )
        out = tmp_path / "out.mp4"
        out.write_bytes(b"fake_video_data")
        r2 = mocker.MagicMock()

        await compose_video(
            audio_path=tmp_path / "a.mp3",
            background_path=tmp_path / "bg.mp4",
            subs_path=tmp_path / "s.ass",
            output_path=out,
            job_id="job_abc",
            r2_client=r2,
        )

        r2.upload_asset.assert_called_once_with(
            "videos/job_abc.mp4", b"fake_video_data", "video/mp4"
        )
