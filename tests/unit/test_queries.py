from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path

import pytest

from alvaro.db.client import DbClient
from alvaro.db.migrations import run_migrations
from alvaro.db.queries import assets, jobs, metrics, niches, quota, uploads, videos


@pytest.fixture
async def db(tmp_path: Path) -> DbClient:
    client = DbClient(url=f"file:{tmp_path / 'q.db'}")
    await client.connect()
    await run_migrations(client)
    yield client
    await client.close()


@pytest.fixture
async def niche(db: DbClient) -> str:
    await niches.get_or_create(db, "science")
    return "science"


@pytest.fixture
async def job(db: DbClient, niche: str) -> jobs.Job:
    return await jobs.upsert_job(db, idempotency_key="science_2026-01-01_08", niche_id=niche)


@pytest.fixture
async def video(db: DbClient, job: jobs.Job) -> videos.Video:
    return await videos.insert_video(
        db,
        job_id=job.id,
        niche_id=job.niche_id,
        title="Test title",
        script_hash=hashlib.sha256(b"script").hexdigest(),
        duration_s=45,
    )


class TestJobs:
    async def test_upsert_creates_pending(self, db: DbClient, niche: str) -> None:
        j = await jobs.upsert_job(db, idempotency_key="k1", niche_id=niche)
        assert j.status == "pending"
        assert j.idempotency_key == "k1"

    async def test_upsert_idempotent(self, db: DbClient, niche: str) -> None:
        j1 = await jobs.upsert_job(db, idempotency_key="k2", niche_id=niche)
        j2 = await jobs.upsert_job(db, idempotency_key="k2", niche_id=niche)
        assert j1.id == j2.id

    async def test_mark_running(self, db: DbClient, job: jobs.Job) -> None:
        await jobs.mark_running(db, job.id)
        result = await db.execute("SELECT status, started_at FROM jobs WHERE id = ?", [job.id])
        assert result.rows[0][0] == "running"
        assert result.rows[0][1] is not None

    async def test_mark_done(self, db: DbClient, job: jobs.Job) -> None:
        await jobs.mark_done(db, job.id)
        result = await db.execute("SELECT status FROM jobs WHERE id = ?", [job.id])
        assert result.rows[0][0] == "done"

    async def test_mark_failed_stores_error(self, db: DbClient, job: jobs.Job) -> None:
        await jobs.mark_failed(db, job.id, "timeout")
        result = await db.execute("SELECT status, error FROM jobs WHERE id = ?", [job.id])
        assert result.rows[0][0] == "failed"
        assert result.rows[0][1] == "timeout"

    async def test_get_pending(self, db: DbClient, niche: str) -> None:
        await jobs.upsert_job(db, idempotency_key="p1", niche_id=niche)
        pending = await jobs.get_pending(db)
        assert any(j.idempotency_key == "p1" for j in pending)


class TestVideos:
    async def test_insert_returns_generated(self, video: videos.Video) -> None:
        assert video.status == "generated"
        assert video.file_sha256 is None

    async def test_set_file_sha256(self, db: DbClient, video: videos.Video) -> None:
        await videos.set_file_sha256(db, video.id, "abc123")
        result = await db.execute("SELECT file_sha256 FROM videos WHERE id = ?", [video.id])
        assert result.rows[0][0] == "abc123"

    async def test_set_r2_location(self, db: DbClient, video: videos.Video) -> None:
        await videos.set_r2_location(db, video.id, "videos/v.mp4", "bucket")
        v = await videos.get_by_job(db, video.job_id)
        assert v is not None
        assert v.status == "stored"
        assert v.r2_key == "videos/v.mp4"

    async def test_get_by_job_none_when_missing(self, db: DbClient) -> None:
        result = await videos.get_by_job(db, "nonexistent")
        assert result is None

    async def test_script_json_none_by_default(self, video: videos.Video) -> None:
        assert video.script_json is None

    async def test_set_script_json_stores_json(
        self, db: DbClient, video: videos.Video
    ) -> None:
        await videos.set_script_json(db, video.id, '{"hook_text": "test"}')
        v = await videos.get_by_job(db, video.job_id)
        assert v is not None
        assert v.script_json == '{"hook_text": "test"}'

    async def test_get_uploadable_returns_stored_without_upload(
        self, db: DbClient, video: videos.Video
    ) -> None:
        await videos.set_r2_location(db, video.id, "videos/v.mp4", "bucket")
        result = await videos.get_uploadable(db, 10)
        assert any(v.id == video.id for v in result)

    async def test_get_uploadable_excludes_done_uploads(
        self, db: DbClient, video: videos.Video
    ) -> None:
        await videos.set_r2_location(db, video.id, "videos/v.mp4", "bucket")
        u = await uploads.insert_upload(db, video_id=video.id)
        await uploads.mark_done(db, u.id, "yt_abc", 1600)
        result = await videos.get_uploadable(db, 10)
        assert not any(v.id == video.id for v in result)

    async def test_get_uploadable_includes_failed_upload(
        self, db: DbClient, video: videos.Video
    ) -> None:
        await videos.set_r2_location(db, video.id, "videos/v.mp4", "bucket")
        u = await uploads.insert_upload(db, video_id=video.id)
        await uploads.mark_failed(db, u.id, "network error")
        result = await videos.get_uploadable(db, 10)
        assert any(v.id == video.id for v in result)

    async def test_get_uploadable_respects_limit(
        self, db: DbClient, job: jobs.Job
    ) -> None:
        for i in range(3):
            j = await jobs.upsert_job(
                db, idempotency_key=f"limit_test_{i}", niche_id=job.niche_id
            )
            v = await videos.insert_video(
                db, job_id=j.id, niche_id=j.niche_id,
                title=f"T{i}", script_hash="h", duration_s=30,
            )
            await videos.set_r2_location(db, v.id, f"videos/{i}.mp4", "b")
        result = await videos.get_uploadable(db, 2)
        assert len(result) == 2


class TestUploads:
    async def test_insert_pending(self, db: DbClient, video: videos.Video) -> None:
        u = await uploads.insert_upload(db, video_id=video.id)
        assert u.status == "pending"
        assert u.privacy == "public"

    async def test_mark_done(self, db: DbClient, video: videos.Video) -> None:
        u = await uploads.insert_upload(db, video_id=video.id)
        await uploads.mark_done(db, u.id, "yt_abc123", 1600)
        result = await db.execute(
            "SELECT youtube_video_id, quota_units_used FROM uploads WHERE id = ?", [u.id]
        )
        assert result.rows[0][0] == "yt_abc123"
        assert int(result.rows[0][1]) == 1600

    async def test_mark_failed(self, db: DbClient, video: videos.Video) -> None:
        u = await uploads.insert_upload(db, video_id=video.id)
        await uploads.mark_failed(db, u.id, "quota exceeded")
        result = await db.execute("SELECT status, error FROM uploads WHERE id = ?", [u.id])
        assert result.rows[0][0] == "failed"

    async def test_get_recent_done_returns_within_window(
        self, db: DbClient, video: videos.Video
    ) -> None:
        u = await uploads.insert_upload(db, video_id=video.id)
        await uploads.mark_done(db, u.id, "yt_xyz", 1600)
        since = int(time.time()) - 60
        result = await uploads.get_recent_done(db, since)
        assert any(up.youtube_video_id == "yt_xyz" for up in result)

    async def test_get_recent_done_excludes_outside_window(
        self, db: DbClient, video: videos.Video
    ) -> None:
        u = await uploads.insert_upload(db, video_id=video.id)
        await uploads.mark_done(db, u.id, "yt_old", 1600)
        since = int(time.time()) + 60
        result = await uploads.get_recent_done(db, since)
        assert not any(up.youtube_video_id == "yt_old" for up in result)

    def test_sqlite_enforces_fk_with_pragma_on(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fk.db"))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("CREATE TABLE videos (id TEXT PRIMARY KEY)")
        conn.execute(
            "CREATE TABLE uploads "
            "(id TEXT PRIMARY KEY, video_id TEXT NOT NULL REFERENCES videos(id))"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO uploads VALUES ('u1', 'nonexistent')")
        conn.close()


class TestAssets:
    async def test_upsert_creates(self, db: DbClient) -> None:
        a = await assets.upsert_asset(
            db, r2_key="backgrounds/science/a.mp4", asset_type="background",
            size_bytes=1024, etag="etag1", niche_id="science",
        )
        assert a.r2_key == "backgrounds/science/a.mp4"

    async def test_upsert_updates_etag(self, db: DbClient) -> None:
        await assets.upsert_asset(
            db, r2_key="backgrounds/h.mp4", asset_type="background",
            size_bytes=500, etag="old",
        )
        a = await assets.upsert_asset(
            db, r2_key="backgrounds/h.mp4", asset_type="background",
            size_bytes=600, etag="new",
        )
        assert a.etag == "new"

    async def test_list_backgrounds_by_niche(self, db: DbClient) -> None:
        await assets.upsert_asset(
            db, r2_key="backgrounds/science/x.mp4", asset_type="background",
            size_bytes=100, etag="e1", niche_id="science",
        )
        result = await assets.list_backgrounds(db, niche_id="science")
        assert any(a.r2_key == "backgrounds/science/x.mp4" for a in result)


class TestNiches:
    async def test_get_or_create_defaults(self, db: DbClient) -> None:
        n = await niches.get_or_create(db, "history")
        assert n.consecutive_failures == 0
        assert n.paused is False

    async def test_increment_failures(self, db: DbClient) -> None:
        await niches.get_or_create(db, "mystery")
        await niches.increment_failures(db, "mystery")
        await niches.increment_failures(db, "mystery")
        n = await niches.get_or_create(db, "mystery")
        assert n.consecutive_failures == 2

    async def test_mark_success_resets_failures(self, db: DbClient) -> None:
        await niches.get_or_create(db, "gaming_culture")
        await niches.increment_failures(db, "gaming_culture")
        await niches.mark_success(db, "gaming_culture")
        n = await niches.get_or_create(db, "gaming_culture")
        assert n.consecutive_failures == 0
        assert n.total_videos_generated == 1

    async def test_set_paused(self, db: DbClient) -> None:
        await niches.get_or_create(db, "gaming_secrets")
        await niches.set_paused(db, "gaming_secrets", paused=True)
        n = await niches.get_or_create(db, "gaming_secrets")
        assert n.paused is True


class TestMetrics:
    async def test_insert_snapshot(self, db: DbClient) -> None:
        snap = await metrics.insert_snapshot(
            db, youtube_video_id="yt1", snapshot_at=int(time.time()),
            views=100, likes=10, comments=5,
        )
        assert snap.views == 100
        assert snap.ctr_pct is None

    async def test_get_latest(self, db: DbClient) -> None:
        t = int(time.time())
        await metrics.insert_snapshot(
            db, youtube_video_id="yt2", snapshot_at=t - 100,
            views=50, likes=5, comments=1,
        )
        await metrics.insert_snapshot(
            db, youtube_video_id="yt2", snapshot_at=t,
            views=200, likes=20, comments=10,
        )
        latest = await metrics.get_latest(db, "yt2")
        assert latest is not None
        assert latest.views == 200

    async def test_get_latest_none_when_missing(self, db: DbClient) -> None:
        result = await metrics.get_latest(db, "nonexistent")
        assert result is None


class TestQuota:
    async def test_can_upload_when_no_row(self, db: DbClient) -> None:
        assert await quota.can_upload(db, "2026-01-01") is True

    async def test_add_units_creates_row(self, db: DbClient) -> None:
        q = await quota.add_units(db, "2026-01-02", 1600, is_upload=True)
        assert q.units_consumed == 1600
        assert q.uploads_count == 1

    async def test_add_units_accumulates(self, db: DbClient) -> None:
        await quota.add_units(db, "2026-01-03", 1600, is_upload=True)
        q = await quota.add_units(db, "2026-01-03", 1600, is_upload=True)
        assert q.units_consumed == 3200

    async def test_can_upload_false_near_limit(self, db: DbClient) -> None:
        await quota.add_units(db, "2026-01-04", 8000)
        assert await quota.can_upload(db, "2026-01-04") is False
