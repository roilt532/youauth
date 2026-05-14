from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UploadResult:
    video_id: str
    video_url: str
    title: str
    description: str
    privacy_status: str
    upload_timestamp: datetime
    quota_units_consumed: int


class PublishingError(Exception):
    pass


class QuotaExceededError(PublishingError):
    pass
