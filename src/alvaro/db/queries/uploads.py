from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from alvaro.db.client import DbClient

_SEL = (
    "SELECT id, video_id, youtube_video_id, status, privacy, "
    "scheduled_for, uploaded_at, quota_units_used, error FROM uploads"
)


@dataclass
class Upload:
    id: str
    video_id: str
    youtube_video_id: str | None
    status: str
    privacy: str
    scheduled_for: int | None
    uploaded_at: int | None
    quota_units_used: int
    error: str | None


def _row(r: Any) -> Upload:
    return Upload(
        id=str(r[0]),
        video_id=str(r[1]),
        youtube_video_id=str(r[2]) if r[2] is not None else None,
        status=str(r[3]),
        privacy=str(r[4]),
        scheduled_for=int(r[5]) if r[5] is not None else None,
        uploaded_at=int(r[6]) if r[6] is not None else None,
        quota_units_used=int(r[7]),
        error=str(r[8]) if r[8] is not None else None,
    )


async def insert_upload(
    client: DbClient,
    *,
    video_id: str,
    privacy: str = "public",
    scheduled_for: int | None = None,
) -> Upload:
    up_id = str(uuid.uuid4())
    await client.execute(
        "INSERT INTO uploads (id, video_id, status, privacy, scheduled_for) "
        "VALUES (?, ?, 'pending', ?, ?)",
        [up_id, video_id, privacy, scheduled_for],
    )
    result = await client.execute(f"{_SEL} WHERE id = ?", [up_id])
    return _row(result.rows[0])


async def mark_uploading(client: DbClient, upload_id: str) -> None:
    await client.execute("UPDATE uploads SET status = 'uploading' WHERE id = ?", [upload_id])


async def mark_done(
    client: DbClient, upload_id: str, youtube_video_id: str, quota_units: int
) -> None:
    await client.execute(
        "UPDATE uploads SET status = 'done', youtube_video_id = ?, "
        "uploaded_at = ?, quota_units_used = ? WHERE id = ?",
        [youtube_video_id, int(time.time()), quota_units, upload_id],
    )


async def mark_failed(client: DbClient, upload_id: str, error: str) -> None:
    await client.execute(
        "UPDATE uploads SET status = 'failed', error = ? WHERE id = ?",
        [error, upload_id],
    )


async def get_pending(client: DbClient) -> list[Upload]:
    result = await client.execute(f"{_SEL} WHERE status = 'pending' ORDER BY id ASC")
    return [_row(r) for r in result.rows]


async def get_by_video_id(client: DbClient, video_id: str) -> Upload | None:
    result = await client.execute(f"{_SEL} WHERE video_id = ?", [video_id])
    return _row(result.rows[0]) if result.rows else None


async def get_recent_done(client: DbClient, since: int) -> list[Upload]:
    result = await client.execute(
        f"{_SEL} WHERE status = 'done' AND youtube_video_id IS NOT NULL "
        "AND uploaded_at >= ? ORDER BY uploaded_at ASC",
        [since],
    )
    return [_row(r) for r in result.rows]
