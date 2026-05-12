from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from alvaro.db.client import DbClient

QUOTA_DAILY_LIMIT = 9000
UNITS_UPLOAD = 1600
UNITS_LIST = 1
UNITS_UPDATE = 50

_SEL = "SELECT day, units_consumed, uploads_count, last_reset_at FROM youtube_quota_usage"


@dataclass
class QuotaUsage:
    day: str
    units_consumed: int
    uploads_count: int
    last_reset_at: int


def _row(r: Any) -> QuotaUsage:
    return QuotaUsage(
        day=str(r[0]),
        units_consumed=int(r[1]),
        uploads_count=int(r[2]),
        last_reset_at=int(r[3]),
    )


async def get_or_create(client: DbClient, day: str) -> QuotaUsage:
    now = int(time.time())
    await client.execute(
        "INSERT OR IGNORE INTO youtube_quota_usage "
        "(day, units_consumed, uploads_count, last_reset_at) VALUES (?, 0, 0, ?)",
        [day, now],
    )
    result = await client.execute(f"{_SEL} WHERE day = ?", [day])
    return _row(result.rows[0])


async def add_units(
    client: DbClient, day: str, units: int, *, is_upload: bool = False
) -> QuotaUsage:
    upload_inc = 1 if is_upload else 0
    await client.execute(
        "INSERT INTO youtube_quota_usage (day, units_consumed, uploads_count, last_reset_at) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(day) DO UPDATE SET "
        "units_consumed = units_consumed + excluded.units_consumed, "
        "uploads_count = uploads_count + excluded.uploads_count",
        [day, units, upload_inc, int(time.time())],
    )
    result = await client.execute(f"{_SEL} WHERE day = ?", [day])
    return _row(result.rows[0])


async def can_upload(client: DbClient, day: str) -> bool:
    result = await client.execute(
        "SELECT units_consumed FROM youtube_quota_usage WHERE day = ?", [day]
    )
    if not result.rows:
        return True
    consumed = int(result.rows[0][0])
    return consumed + UNITS_UPLOAD <= QUOTA_DAILY_LIMIT
