from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from alvaro.publishing._types import QuotaExceededError
from alvaro.scripting.models import Script


def _make_script(**kwargs: object) -> Script:
    defaults: dict[str, object] = {
        "hook_text": "Por que el cielo es azul?",
        "body_lines": ["Linea uno.", "Linea dos."],
        "payoff_text": "Fin.",
        "total_duration_estimate_s": 40,
        "suggested_voice_id": "alvaro_es",
        "suggested_background_niche": "minecraft_parkour",
        "niche_id": "science",
    }
    defaults.update(kwargs)
    return Script(**defaults)  # type: ignore[arg-type]


def _make_job(**kwargs: object) -> MagicMock:
    job = MagicMock()
    job.id = "job-001"
    job.status = "pending"
    job.niche_id = "science"
    for k, v in kwargs.items():
        setattr(job, k, v)
    return job


def _make_video(**kwargs: object) -> MagicMock:
    vid = MagicMock()
    vid.id = "vid-001"
    vid.r2_key = "videos/job-001.mp4"
    for k, v in kwargs.items():
        setattr(vid, k, v)
    return vid


def _make_video_meta() -> MagicMock:
    meta = MagicMock()
    meta.duration_s = 42.0
    meta.r2_key = "videos/job-001.mp4"
    return meta


def _p(mocker: MockerFixture, target: str, **kw: object) -> MagicMock:
    return mocker.patch(f"alvaro.cli.generate.{target}", **kw)  # type: ignore[arg-type]


class TestGenerate:
    def _patch_all(
        self, mocker: MockerFixture, *, job_status: str = "pending"
    ) -> dict[str, MagicMock]:
        job = _make_job(status=job_status)
        niche_state = MagicMock()
        niche_state.paused = False

        db_mock = MagicMock()
        db_mock.connect = AsyncMock()
        db_mock.close = AsyncMock()

        mocks: dict[str, MagicMock] = {}
        mocks["build_db"] = _p(mocker, "build_db_client", return_value=db_mock)
        mocks["run_migrations"] = _p(mocker, "run_migrations", new_callable=AsyncMock)
        mocks["upsert_job"] = _p(
            mocker, "jobs_q.upsert_job", new_callable=AsyncMock, return_value=job
        )
        mocks["mark_running"] = _p(
            mocker, "jobs_q.mark_running", new_callable=AsyncMock
        )
        mocks["mark_done"] = _p(mocker, "jobs_q.mark_done", new_callable=AsyncMock)
        mocks["mark_failed"] = _p(
            mocker, "jobs_q.mark_failed", new_callable=AsyncMock
        )
        mocks["get_or_create"] = _p(
            mocker, "niches_q.get_or_create",
            new_callable=AsyncMock, return_value=niche_state,
        )
        mocks["mark_run_started"] = _p(
            mocker, "niches_q.mark_run_started", new_callable=AsyncMock
        )
        mocks["mark_success"] = _p(
            mocker, "niches_q.mark_success", new_callable=AsyncMock
        )
        mocks["increment_failures"] = _p(
            mocker, "niches_q.increment_failures", new_callable=AsyncMock
        )
        mocks["insert_video"] = _p(
            mocker, "videos_q.insert_video",
            new_callable=AsyncMock, return_value=_make_video(),
        )
        mocks["set_file_sha256"] = _p(
            mocker, "videos_q.set_file_sha256", new_callable=AsyncMock
        )
        mocks["set_r2_location"] = _p(
            mocker, "videos_q.set_r2_location", new_callable=AsyncMock
        )
        mocks["set_script_json"] = _p(
            mocker, "videos_q.set_script_json", new_callable=AsyncMock
        )
        mocks["load_voices"] = _p(mocker, "load_voices", return_value=MagicMock())
        mocks["build_r2"] = _p(
            mocker, "build_r2_client", return_value=MagicMock(_bucket="bkt")
        )
        _p(mocker, "GroqClient", return_value=MagicMock())
        _p(mocker, "GeminiClient", return_value=MagicMock())
        _p(mocker, "RouterClient", return_value=MagicMock())
        _p(mocker, "generate_ideas", new_callable=AsyncMock, return_value=[MagicMock()])
        _p(mocker, "select_best", return_value=MagicMock())
        _p(
            mocker, "generate_script",
            new_callable=AsyncMock, return_value=_make_script(),
        )
        _p(mocker, "synthesize_script", new_callable=AsyncMock)
        _p(mocker, "build_subtitles", new_callable=AsyncMock)
        _p(
            mocker, "select_background",
            new_callable=AsyncMock, return_value=Path("/tmp/bg.mp4"),  # noqa: S108
        )
        _p(
            mocker, "compose_video",
            new_callable=AsyncMock, return_value=_make_video_meta(),
        )
        _p(mocker, "shutil.rmtree")
        _p(mocker, "hashlib.sha256", return_value=MagicMock(hexdigest=lambda: "a" * 64))
        mocker.patch("pathlib.Path.read_bytes", return_value=b"data")
        mocker.patch("pathlib.Path.exists", return_value=True)
        return mocks

    async def test_creates_job_with_correct_idempotency_key(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.cli.generate import _run

        mocks = self._patch_all(mocker)
        await _run("science", "noon")

        mocks["upsert_job"].assert_awaited_once()
        kw = mocks["upsert_job"].call_args.kwargs
        assert "science_" in kw["idempotency_key"]
        assert "_noon" in kw["idempotency_key"]
        assert kw["niche_id"] == "science"

    async def test_skips_if_job_already_done(self, mocker: MockerFixture) -> None:
        from alvaro.cli.generate import _run

        mocks = self._patch_all(mocker, job_status="done")
        await _run("science", "noon")

        mocks["mark_running"].assert_not_awaited()
        mocks["insert_video"].assert_not_awaited()

    async def test_skips_if_niche_paused(self, mocker: MockerFixture) -> None:
        from alvaro.cli.generate import _run

        mocks = self._patch_all(mocker)
        mocks["get_or_create"].return_value.paused = True
        await _run("science", "noon")

        mocks["mark_running"].assert_not_awaited()
        mocks["insert_video"].assert_not_awaited()

    async def test_marks_failed_on_error(self, mocker: MockerFixture) -> None:
        from alvaro.cli.generate import _run

        mocks = self._patch_all(mocker)
        _p(
            mocker, "generate_ideas",
            new_callable=AsyncMock, side_effect=RuntimeError("llm down"),
        )

        with pytest.raises(SystemExit):
            await _run("science", "noon")

        mocks["mark_failed"].assert_awaited_once()
        mocks["increment_failures"].assert_awaited_once()

    async def test_cleanup_does_not_mask_pipeline_error(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.cli.generate import _run

        self._patch_all(mocker)
        _p(
            mocker, "generate_ideas",
            new_callable=AsyncMock, side_effect=RuntimeError("boom"),
        )
        _p(mocker, "shutil.rmtree", side_effect=OSError("disk full"))

        with pytest.raises(SystemExit) as exc_info:
            await _run("science", "noon")

        assert exc_info.value.code == 1

    async def test_marks_done_on_success(self, mocker: MockerFixture) -> None:
        from alvaro.cli.generate import _run

        mocks = self._patch_all(mocker)
        await _run("science", "noon")

        mocks["mark_done"].assert_awaited_once()
        mocks["mark_success"].assert_awaited_once()

    async def test_script_json_stored_as_serialized_dict(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.cli.generate import _run

        mocks = self._patch_all(mocker)
        script = _make_script()
        _p(mocker, "generate_script", new_callable=AsyncMock, return_value=script)

        await _run("science", "noon")

        mocks["set_script_json"].assert_awaited_once()
        stored_json = mocks["set_script_json"].call_args.args[2]
        parsed = json.loads(stored_json)
        assert parsed["hook_text"] == script.hook_text
        assert parsed == dataclasses.asdict(script)


def _make_uploadable_video(**kwargs: object) -> MagicMock:
    vid = MagicMock()
    vid.id = "vid-001"
    vid.job_id = "job-001"
    vid.niche_id = "science"
    vid.r2_key = "videos/job-001.mp4"
    vid.script_json = json.dumps(dataclasses.asdict(_make_script()))
    for k, v in kwargs.items():
        setattr(vid, k, v)
    return vid


def _up(mocker: MockerFixture, target: str, **kw: object) -> MagicMock:
    return mocker.patch(f"alvaro.cli.upload.{target}", **kw)  # type: ignore[arg-type]


class TestUpload:
    def _patch_upload(
        self,
        mocker: MockerFixture,
        *,
        videos: list[MagicMock] | None = None,
        quota_used: int = 0,
    ) -> dict[str, MagicMock]:
        if videos is None:
            videos = [_make_uploadable_video()]

        db_mock = MagicMock()
        db_mock.connect = AsyncMock()
        db_mock.close = AsyncMock()

        mocks: dict[str, MagicMock] = {}
        mocks["build_db"] = _up(mocker, "build_db_client", return_value=db_mock)
        mocks["build_r2"] = _up(mocker, "build_r2_client", return_value=MagicMock())
        mocks["get_uploadable"] = _up(
            mocker, "videos_q.get_uploadable",
            new_callable=AsyncMock, return_value=videos,
        )
        mocks["get_quota"] = _up(
            mocker, "get_daily_quota_used",
            new_callable=AsyncMock, return_value=quota_used,
        )
        mocks["publish"] = _up(
            mocker, "publish_video",
            new_callable=AsyncMock, return_value=MagicMock(video_id="yt-001"),
        )
        mocks["increment_uploads"] = _up(
            mocker, "niches_q.increment_uploads", new_callable=AsyncMock
        )
        return mocks

    async def test_processes_max_videos(self, mocker: MockerFixture) -> None:
        from alvaro.cli.upload import _run

        vids = [_make_uploadable_video(id=f"v{i}") for i in range(3)]
        mocks = self._patch_upload(mocker, videos=vids)

        await _run(3)

        assert mocks["publish"].await_count == 3

    async def test_stops_when_quota_cap_reached(self, mocker: MockerFixture) -> None:
        from alvaro.cli.upload import _run

        vids = [_make_uploadable_video(id=f"v{i}") for i in range(3)]
        mocks = self._patch_upload(mocker, videos=vids, quota_used=7600)

        await _run(3)

        mocks["publish"].assert_not_awaited()

    async def test_continues_on_individual_failure(self, mocker: MockerFixture) -> None:
        from alvaro.cli.upload import _run

        vids = [_make_uploadable_video(id=f"v{i}") for i in range(3)]
        mocks = self._patch_upload(mocker, videos=vids)
        mocks["publish"].side_effect = [
            RuntimeError("network"),
            MagicMock(video_id="yt-002"),
            MagicMock(video_id="yt-003"),
        ]

        await _run(3)

        assert mocks["publish"].await_count == 3
        assert mocks["increment_uploads"].await_count == 2

    async def test_stops_on_quota_exceeded_mid_loop(self, mocker: MockerFixture) -> None:
        from alvaro.cli.upload import _run

        vids = [_make_uploadable_video(id=f"v{i}") for i in range(3)]
        mocks = self._patch_upload(mocker, videos=vids)
        mocks["publish"].side_effect = [
            QuotaExceededError("quota"),
            MagicMock(video_id="yt-002"),
        ]

        await _run(3)

        assert mocks["publish"].await_count == 1

    async def test_skips_video_without_script_json(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.cli.upload import _run

        vid = _make_uploadable_video(script_json=None)
        mocks = self._patch_upload(mocker, videos=[vid])

        await _run(1)

        mocks["publish"].assert_not_awaited()


def _an(mocker: MockerFixture, target: str, **kw: object) -> MagicMock:
    return mocker.patch(f"alvaro.cli.analytics.{target}", **kw)  # type: ignore[arg-type]


class TestAnalytics:
    def _make_upload(self, yt_id: str = "yt-abc") -> MagicMock:
        up = MagicMock()
        up.youtube_video_id = yt_id
        return up

    def _patch_analytics(
        self,
        mocker: MockerFixture,
        *,
        uploads: list[MagicMock] | None = None,
    ) -> dict[str, MagicMock]:
        if uploads is None:
            uploads = [self._make_upload()]

        db_mock = MagicMock()
        db_mock.connect = AsyncMock()
        db_mock.close = AsyncMock()

        mocks: dict[str, MagicMock] = {}
        mocks["build_db"] = _an(mocker, "build_db_client", return_value=db_mock)
        mocks["get_recent_done"] = _an(
            mocker, "uploads_q.get_recent_done",
            new_callable=AsyncMock, return_value=uploads,
        )
        yt_mock = MagicMock()
        yt_mock._service.videos.return_value.list.return_value.execute.return_value = {
            "items": [{"statistics": {"viewCount": "100", "likeCount": "5", "commentCount": "2"}}]
        }
        mocks["yt_cls"] = _an(mocker, "YouTubeClient", return_value=yt_mock)
        mocks["insert_snapshot"] = _an(
            mocker, "metrics_q.insert_snapshot", new_callable=AsyncMock
        )
        return mocks

    async def test_inserts_metric_snapshot_for_each_upload(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.cli.analytics import _run

        ups = [self._make_upload("yt-1"), self._make_upload("yt-2")]
        mocks = self._patch_analytics(mocker, uploads=ups)

        await _run(7)

        assert mocks["insert_snapshot"].await_count == 2

    async def test_skips_when_no_uploads_in_window(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.cli.analytics import _run

        mocks = self._patch_analytics(mocker, uploads=[])

        await _run(7)

        mocks["insert_snapshot"].assert_not_awaited()
        mocks["yt_cls"].assert_not_called()

    async def test_continues_on_individual_failure(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.cli.analytics import _run

        ups = [self._make_upload("yt-1"), self._make_upload("yt-2")]
        mocks = self._patch_analytics(mocker, uploads=ups)
        mocks["insert_snapshot"].side_effect = [
            RuntimeError("db error"),
            MagicMock(),
        ]

        await _run(7)

        assert mocks["insert_snapshot"].await_count == 2
