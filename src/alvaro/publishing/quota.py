from __future__ import annotations

import datetime

from alvaro.db.client import DbClient
from alvaro.db.queries import quota as quota_q
from alvaro.publishing._types import QuotaExceededError

# YouTube API quota resets at 00:00 Pacific Time (~07:00-08:00 UTC). Tracking uses UTC dates.


def _today_utc() -> str:
    return datetime.datetime.now(tz=datetime.UTC).strftime("%Y-%m-%d")


async def get_daily_quota_used(db: DbClient) -> int:
    usage = await quota_q.get_or_create(db, _today_utc())
    return usage.units_consumed


async def reserve_quota(db: DbClient, units: int) -> None:
    ok = await quota_q.can_upload(db, _today_utc())
    if not ok:
        raise QuotaExceededError(f"daily quota {quota_q.QUOTA_DAILY_LIMIT} would be exceeded")


async def record_quota_usage(db: DbClient, units: int, video_id: str) -> None:
    await quota_q.add_units(db, _today_utc(), units, is_upload=True)
