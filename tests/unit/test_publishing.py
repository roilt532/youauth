from __future__ import annotations

import datetime
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from alvaro.publishing._types import PublishingError, QuotaExceededError, UploadResult
from alvaro.scripting.models import Script


def _make_script(**kwargs: object) -> Script:
    defaults: dict[str, object] = {
        "hook_text": "Por que el cielo es azul?",
        "body_lines": [
            "La luz solar contiene todos los colores del espectro.",
            "La luz azul se dispersa mas que otros colores.",
        ],
        "payoff_text": "Este fenomeno se llama dispersion de Rayleigh.",
        "total_duration_estimate_s": 35,
        "suggested_voice_id": "alvaro_es",
        "suggested_background_niche": "minecraft_parkour",
        "niche_id": "science",
    }
    defaults.update(kwargs)
    return Script(**defaults)  # type: ignore[arg-type]


def _make_result(**kwargs: object) -> UploadResult:
    defaults: dict[str, object] = {
        "video_id": "dQw4w9WgXcQ",
        "video_url": "https://youtube.com/shorts/dQw4w9WgXcQ",
        "title": "Por que el cielo es azul?",
        "description": "La luz solar...",
        "privacy_status": "private",
        "upload_timestamp": datetime.datetime(2026, 5, 14, 10, 0, 0, tzinfo=datetime.UTC),
        "quota_units_consumed": 1600,
    }
    defaults.update(kwargs)
    return UploadResult(**defaults)  # type: ignore[arg-type]


class TestUploadResult:
    def test_fields_frozen(self) -> None:
        r = _make_result()
        with pytest.raises((AttributeError, TypeError)):
            r.video_id = "other"  # type: ignore[misc]

    def test_video_url_field(self) -> None:
        r = _make_result()
        assert r.video_url == "https://youtube.com/shorts/dQw4w9WgXcQ"
        assert r.quota_units_consumed == 1600

    def test_quota_exceeded_is_publishing_error(self) -> None:
        exc = QuotaExceededError("limit reached")
        assert isinstance(exc, PublishingError)
        assert isinstance(exc, Exception)

    def test_publishing_error_is_exception(self) -> None:
        exc = PublishingError("upload failed")
        assert isinstance(exc, Exception)
        assert "upload failed" in str(exc)


class TestQuota:
    def _mock_db(self, mocker: MockerFixture, *, can_upload: bool = True) -> MagicMock:
        from alvaro.db.queries.quota import QuotaUsage
        db = MagicMock()
        db.execute = AsyncMock()
        mocker.patch(
            "alvaro.publishing.quota.quota_q.get_or_create",
            new_callable=AsyncMock,
            return_value=QuotaUsage(
                day="2026-05-14", units_consumed=400, uploads_count=0, last_reset_at=0
            ),
        )
        mocker.patch(
            "alvaro.publishing.quota.quota_q.can_upload",
            new_callable=AsyncMock,
            return_value=can_upload,
        )
        mocker.patch(
            "alvaro.publishing.quota.quota_q.add_units",
            new_callable=AsyncMock,
        )
        return db

    async def test_get_daily_quota_used_delegates_to_db(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.publishing.quota import get_daily_quota_used
        db = self._mock_db(mocker)
        result = await get_daily_quota_used(db)
        assert result == 400

    async def test_reserve_passes_when_under_limit(self, mocker: MockerFixture) -> None:
        from alvaro.publishing.quota import reserve_quota
        db = self._mock_db(mocker, can_upload=True)
        await reserve_quota(db, 1600)

    async def test_reserve_raises_when_at_limit(self, mocker: MockerFixture) -> None:
        from alvaro.publishing.quota import reserve_quota
        db = self._mock_db(mocker, can_upload=False)
        with pytest.raises(QuotaExceededError):
            await reserve_quota(db, 1600)

    async def test_record_usage_calls_add_units(self, mocker: MockerFixture) -> None:
        from alvaro.publishing.quota import record_quota_usage
        db = self._mock_db(mocker)
        mock_add = mocker.patch(
            "alvaro.publishing.quota.quota_q.add_units",
            new_callable=AsyncMock,
        )
        await record_quota_usage(db, 1600, "yt_abc123")
        mock_add.assert_awaited_once()


class TestMetadataBuilder:
    def _script(self, **kwargs: object) -> Script:
        return _make_script(**kwargs)

    def test_title_under_100_chars_unchanged(self, mocker: MockerFixture) -> None:
        from alvaro.publishing.metadata_builder import build_video_metadata
        mocker.patch(
            "alvaro.publishing.metadata_builder._resolve_language", return_value="es"
        )
        script = self._script(hook_text="Titulo corto")
        meta = build_video_metadata(script, "science", "private")
        assert meta["snippet"]["title"] == "Titulo corto"  # type: ignore[index]

    def test_title_truncated_at_word_boundary(self, mocker: MockerFixture) -> None:
        from alvaro.publishing.metadata_builder import build_video_metadata
        mocker.patch(
            "alvaro.publishing.metadata_builder._resolve_language", return_value="es"
        )
        long_title = "palabra " * 15
        script = self._script(hook_text=long_title.strip())
        meta = build_video_metadata(script, "science", "private")
        title = str(meta["snippet"]["title"])  # type: ignore[index]
        assert len(title) <= 100
        assert title.endswith("...")

    def test_description_includes_hook_body_payoff(self, mocker: MockerFixture) -> None:
        from alvaro.publishing.metadata_builder import build_video_metadata
        mocker.patch(
            "alvaro.publishing.metadata_builder._resolve_language", return_value="es"
        )
        script = self._script()
        meta = build_video_metadata(script, "science", "private")
        desc = str(meta["snippet"]["description"])  # type: ignore[index]
        assert script.hook_text in desc
        assert script.payoff_text in desc
        assert script.body_lines[0] in desc

    def test_tags_under_500_chars_total(self, mocker: MockerFixture) -> None:
        from alvaro.publishing.metadata_builder import build_video_metadata
        mocker.patch(
            "alvaro.publishing.metadata_builder._resolve_language", return_value="es"
        )
        script = self._script()
        meta = build_video_metadata(script, "science", "private")
        tags = meta["snippet"]["tags"]  # type: ignore[index]
        assert isinstance(tags, list)
        total = sum(len(t) for t in tags)
        assert total < 500

    def test_sets_synthetic_media_disclosure(self, mocker: MockerFixture) -> None:
        from alvaro.publishing.metadata_builder import build_video_metadata
        mocker.patch(
            "alvaro.publishing.metadata_builder._resolve_language", return_value="es"
        )
        script = self._script()
        meta = build_video_metadata(script, "science", "private")
        assert meta["status"]["containsSyntheticMedia"] is True  # type: ignore[index]
        assert meta["status"]["selfDeclaredMadeForKids"] is False  # type: ignore[index]

    def test_default_language_from_voice(self) -> None:
        from alvaro.publishing.metadata_builder import _resolve_language
        lang = _resolve_language("alvaro_es")
        assert lang == "es"

    def test_default_language_fallback_es(self) -> None:
        from alvaro.publishing.metadata_builder import _resolve_language
        lang = _resolve_language("unknown_voice_xyz")
        assert lang == "es"


class TestYouTubeClient:
    def test_builds_credentials_from_env(
        self, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("YT_REFRESH_TOKEN", "rt")  # noqa: S106
        monkeypatch.setenv("YT_CLIENT_ID", "cid")
        monkeypatch.setenv("YT_CLIENT_SECRET", "cs")  # noqa: S106
        mocker.patch("alvaro.publishing.youtube_client.build", return_value=MagicMock())
        from alvaro.publishing.youtube_client import YouTubeClient
        client = YouTubeClient()
        assert client._service is not None

    def test_raises_publishing_error_on_refresh_failure(
        self, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import google.auth.exceptions
        monkeypatch.setenv("YT_REFRESH_TOKEN", "bad")  # noqa: S106
        monkeypatch.setenv("YT_CLIENT_ID", "cid")
        monkeypatch.setenv("YT_CLIENT_SECRET", "cs")  # noqa: S106
        mock_build = mocker.patch("alvaro.publishing.youtube_client.build")
        mock_build.side_effect = google.auth.exceptions.RefreshError("bad token")
        from alvaro.publishing._types import PublishingError
        from alvaro.publishing.youtube_client import YouTubeClient
        with pytest.raises(PublishingError, match="OAuth refresh failed"):
            YouTubeClient()


class TestPublisher:
    def _setup(self, mocker: MockerFixture, *, existing: object = None) -> dict[str, MagicMock]:
        mocker.patch(
            "alvaro.publishing.publisher.uploads_q.get_by_video_id",
            new_callable=AsyncMock,
            return_value=existing,
        )
        mock_insert = mocker.patch(
            "alvaro.publishing.publisher.uploads_q.insert_upload",
            new_callable=AsyncMock,
            return_value=MagicMock(id="upload-001"),
        )
        mock_uploading = mocker.patch(
            "alvaro.publishing.publisher.uploads_q.mark_uploading",
            new_callable=AsyncMock,
        )
        mock_done = mocker.patch(
            "alvaro.publishing.publisher.uploads_q.mark_done",
            new_callable=AsyncMock,
        )
        mock_failed = mocker.patch(
            "alvaro.publishing.publisher.uploads_q.mark_failed",
            new_callable=AsyncMock,
        )
        mock_reserve = mocker.patch(
            "alvaro.publishing.publisher.reserve_quota",
            new_callable=AsyncMock,
        )
        mock_record = mocker.patch(
            "alvaro.publishing.publisher.record_quota_usage",
            new_callable=AsyncMock,
        )
        mock_yt_cls = mocker.patch("alvaro.publishing.publisher.YouTubeClient")
        mock_yt_cls.return_value.upload = AsyncMock(return_value="dQw4w9WgXcQ")
        return {
            "insert": mock_insert,
            "uploading": mock_uploading,
            "done": mock_done,
            "failed": mock_failed,
            "reserve": mock_reserve,
            "record": mock_record,
            "yt_cls": mock_yt_cls,
        }

    def _r2(self, mocker: MockerFixture) -> MagicMock:
        r2 = MagicMock()
        r2.download_asset.return_value = b"video_data"
        return r2

    async def test_skips_on_status_done(
        self, mocker: MockerFixture, tmp_path: pytest.TempPathFactory
    ) -> None:
        from alvaro.publishing.publisher import publish_video
        existing = MagicMock()
        existing.status = "done"
        existing.youtube_video_id = "dQw4w9WgXcQ"
        existing.privacy = "private"
        existing.uploaded_at = 1747000000
        mocks = self._setup(mocker, existing=existing)
        mocker.patch("alvaro.publishing.publisher.build_video_metadata", return_value={
            "snippet": {"title": "T", "description": "D"},
            "status": {"privacyStatus": "private"},
        })

        result = await publish_video(
            job_id="j1", r2_key="videos/j1.mp4", script=_make_script(),
            r2_client=self._r2(mocker), db=MagicMock(), video_db_id="vid-001",
        )

        mocks["yt_cls"].assert_not_called()
        mocks["reserve"].assert_not_awaited()
        assert result.video_id == "dQw4w9WgXcQ"
        assert result.quota_units_consumed == 0

    async def test_raises_on_status_uploading(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.publishing.publisher import publish_video
        existing = MagicMock()
        existing.status = "uploading"
        self._setup(mocker, existing=existing)

        with pytest.raises(PublishingError, match="inconsistent state"):
            await publish_video(
                job_id="j1", r2_key="videos/j1.mp4", script=_make_script(),
                r2_client=self._r2(mocker), db=MagicMock(), video_db_id="vid-001",
            )

    async def test_proceeds_on_status_failed_uses_existing_id(
        self, mocker: MockerFixture, tmp_path: pytest.TempPathFactory
    ) -> None:
        from alvaro.publishing.publisher import publish_video
        existing = MagicMock()
        existing.status = "failed"
        existing.id = "upload-existing"
        mocks = self._setup(mocker, existing=existing)

        await publish_video(
            job_id="j1", r2_key="videos/j1.mp4", script=_make_script(),
            r2_client=self._r2(mocker), db=MagicMock(), video_db_id="vid-001",
        )

        mocks["insert"].assert_not_awaited()
        mocks["uploading"].assert_awaited_once_with(ANY, "upload-existing")

    async def test_proceeds_on_status_pending_uses_existing_id(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.publishing.publisher import publish_video
        existing = MagicMock()
        existing.status = "pending"
        existing.id = "upload-pending"
        mocks = self._setup(mocker, existing=existing)

        await publish_video(
            job_id="j1", r2_key="videos/j1.mp4", script=_make_script(),
            r2_client=self._r2(mocker), db=MagicMock(), video_db_id="vid-001",
        )

        mocks["insert"].assert_not_awaited()
        mocks["uploading"].assert_awaited_once_with(ANY, "upload-pending")

    async def test_downloads_from_r2_before_upload(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.publishing.publisher import publish_video
        self._setup(mocker)
        r2 = self._r2(mocker)

        await publish_video(
            job_id="j1", r2_key="videos/j1.mp4", script=_make_script(),
            r2_client=r2, db=MagicMock(), video_db_id="vid-001",
        )

        r2.download_asset.assert_called_once_with("videos/j1.mp4")

    async def test_records_quota_after_upload(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.publishing.publisher import publish_video
        mocks = self._setup(mocker)

        await publish_video(
            job_id="j1", r2_key="videos/j1.mp4", script=_make_script(),
            r2_client=self._r2(mocker), db=MagicMock(), video_db_id="vid-001",
        )

        mocks["record"].assert_awaited_once()

    async def test_raises_quota_exceeded_on_403(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.publishing.publisher import publish_video
        mocks = self._setup(mocker)
        mocks["yt_cls"].return_value.upload = AsyncMock(
            side_effect=QuotaExceededError("quota")
        )

        with pytest.raises(QuotaExceededError):
            await publish_video(
                job_id="j1", r2_key="videos/j1.mp4", script=_make_script(),
                r2_client=self._r2(mocker), db=MagicMock(), video_db_id="vid-001",
            )

    async def test_does_not_create_row_on_quota_exceeded_before_upload(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.publishing.publisher import publish_video
        mocks = self._setup(mocker)
        mocks["reserve"].side_effect = QuotaExceededError("over limit")

        with pytest.raises(QuotaExceededError):
            await publish_video(
                job_id="j1", r2_key="videos/j1.mp4", script=_make_script(),
                r2_client=self._r2(mocker), db=MagicMock(), video_db_id="vid-001",
            )

        mocks["insert"].assert_not_awaited()

    async def test_marks_row_failed_on_upload_exception(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.publishing.publisher import publish_video
        mocks = self._setup(mocker)
        mocks["yt_cls"].return_value.upload = AsyncMock(
            side_effect=PublishingError("network")
        )

        with pytest.raises(PublishingError):
            await publish_video(
                job_id="j1", r2_key="videos/j1.mp4", script=_make_script(),
                r2_client=self._r2(mocker), db=MagicMock(), video_db_id="vid-001",
            )

        mocks["failed"].assert_awaited_once()

    async def test_cleanup_temp_file_on_success(
        self, mocker: MockerFixture, tmp_path: pytest.TempPathFactory
    ) -> None:
        from alvaro.publishing.publisher import publish_video
        self._setup(mocker)
        mock_unlink = mocker.patch("alvaro.publishing.publisher.Path.unlink")

        await publish_video(
            job_id="j1", r2_key="videos/j1.mp4", script=_make_script(),
            r2_client=self._r2(mocker), db=MagicMock(), video_db_id="vid-001",
        )

        mock_unlink.assert_called_once_with(missing_ok=True)

    async def test_cleanup_temp_file_on_failure(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.publishing.publisher import publish_video
        mocks = self._setup(mocker)
        mocks["yt_cls"].return_value.upload = AsyncMock(
            side_effect=PublishingError("fail")
        )
        mock_unlink = mocker.patch("alvaro.publishing.publisher.Path.unlink")

        with pytest.raises(PublishingError):
            await publish_video(
                job_id="j1", r2_key="videos/j1.mp4", script=_make_script(),
                r2_client=self._r2(mocker), db=MagicMock(), video_db_id="vid-001",
            )

        mock_unlink.assert_called_once_with(missing_ok=True)

    async def test_returns_upload_result_with_video_id(
        self, mocker: MockerFixture
    ) -> None:
        from alvaro.publishing.publisher import publish_video
        self._setup(mocker)

        result = await publish_video(
            job_id="j1", r2_key="videos/j1.mp4", script=_make_script(),
            r2_client=self._r2(mocker), db=MagicMock(), video_db_id="vid-001",
        )

        assert result.video_id == "dQw4w9WgXcQ"
        assert result.video_url == "https://youtube.com/shorts/dQw4w9WgXcQ"
        assert result.quota_units_consumed == 1600
