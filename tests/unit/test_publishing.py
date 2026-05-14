from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from alvaro.publishing._types import PublishingError, QuotaExceededError, UploadResult


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
