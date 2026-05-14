from __future__ import annotations

import datetime

import pytest

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
