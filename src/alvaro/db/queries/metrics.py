from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from alvaro.db.client import DbClient

_SEL = (
    "SELECT id, youtube_video_id, snapshot_at, views, likes, comments, "
    "watch_time_s, impressions, ctr_pct FROM metrics"
)


@dataclass
class MetricSnapshot:
    id: str
    youtube_video_id: str
    snapshot_at: int
    views: int
    likes: int
    comments: int
    watch_time_s: int | None
    impressions: int | None
    ctr_pct: float | None


def _row(r: Any) -> MetricSnapshot:
    return MetricSnapshot(
        id=str(r[0]),
        youtube_video_id=str(r[1]),
        snapshot_at=int(r[2]),
        views=int(r[3]),
        likes=int(r[4]),
        comments=int(r[5]),
        watch_time_s=int(r[6]) if r[6] is not None else None,
        impressions=int(r[7]) if r[7] is not None else None,
        ctr_pct=float(r[8]) if r[8] is not None else None,
    )


async def insert_snapshot(
    client: DbClient,
    *,
    youtube_video_id: str,
    snapshot_at: int,
    views: int,
    likes: int,
    comments: int,
    watch_time_s: int | None = None,
    impressions: int | None = None,
    ctr_pct: float | None = None,
) -> MetricSnapshot:
    snap_id = str(uuid.uuid4())
    await client.execute(
        "INSERT INTO metrics (id, youtube_video_id, snapshot_at, views, likes, "
        "comments, watch_time_s, impressions, ctr_pct) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [snap_id, youtube_video_id, snapshot_at, views, likes, comments,
         watch_time_s, impressions, ctr_pct],
    )
    result = await client.execute(f"{_SEL} WHERE id = ?", [snap_id])
    return _row(result.rows[0])


async def get_latest(client: DbClient, youtube_video_id: str) -> MetricSnapshot | None:
    result = await client.execute(
        f"{_SEL} WHERE youtube_video_id = ? ORDER BY snapshot_at DESC LIMIT 1",
        [youtube_video_id],
    )
    return _row(result.rows[0]) if result.rows else None
