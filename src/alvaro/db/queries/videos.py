from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from alvaro.db.client import DbClient

_SEL = (
    "SELECT id, job_id, niche_id, title, script_hash, file_sha256, "
    "duration_s, r2_key, r2_bucket, created_at, status, script_json FROM videos"
)

_UPLOADABLE = (
    "SELECT v.id, v.job_id, v.niche_id, v.title, v.script_hash, v.file_sha256, "
    "v.duration_s, v.r2_key, v.r2_bucket, v.created_at, v.status, v.script_json "
    "FROM videos v LEFT JOIN uploads u ON u.video_id = v.id "
    "WHERE v.status = 'stored' AND (u.id IS NULL OR u.status IN ('failed', 'pending')) "
    "ORDER BY v.created_at ASC LIMIT ?"
)


@dataclass
class Video:
    id: str
    job_id: str
    niche_id: str
    title: str
    script_hash: str
    file_sha256: str | None
    duration_s: int
    r2_key: str | None
    r2_bucket: str | None
    created_at: int
    status: str
    script_json: str | None


def _row(r: Any) -> Video:
    return Video(
        id=str(r[0]),
        job_id=str(r[1]),
        niche_id=str(r[2]),
        title=str(r[3]),
        script_hash=str(r[4]),
        file_sha256=str(r[5]) if r[5] is not None else None,
        duration_s=int(r[6]),
        r2_key=str(r[7]) if r[7] is not None else None,
        r2_bucket=str(r[8]) if r[8] is not None else None,
        created_at=int(r[9]),
        status=str(r[10]),
        script_json=str(r[11]) if r[11] is not None else None,
    )


async def insert_video(
    client: DbClient,
    *,
    job_id: str,
    niche_id: str,
    title: str,
    script_hash: str,
    duration_s: int,
) -> Video:
    vid_id = str(uuid.uuid4())
    now = int(time.time())
    await client.execute(
        "INSERT INTO videos "
        "(id, job_id, niche_id, title, script_hash, duration_s, created_at, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 'generated')",
        [vid_id, job_id, niche_id, title, script_hash, duration_s, now],
    )
    result = await client.execute(f"{_SEL} WHERE id = ?", [vid_id])
    return _row(result.rows[0])


async def set_file_sha256(client: DbClient, video_id: str, sha256: str) -> None:
    await client.execute(
        "UPDATE videos SET file_sha256 = ? WHERE id = ?", [sha256, video_id]
    )


async def set_r2_location(
    client: DbClient, video_id: str, r2_key: str, r2_bucket: str
) -> None:
    await client.execute(
        "UPDATE videos SET r2_key = ?, r2_bucket = ?, status = 'stored' WHERE id = ?",
        [r2_key, r2_bucket, video_id],
    )


async def set_script_json(client: DbClient, video_id: str, script_json: str) -> None:
    await client.execute(
        "UPDATE videos SET script_json = ? WHERE id = ?", [script_json, video_id]
    )


async def get_by_job(client: DbClient, job_id: str) -> Video | None:
    result = await client.execute(f"{_SEL} WHERE job_id = ?", [job_id])
    return _row(result.rows[0]) if result.rows else None


async def get_uploadable(client: DbClient, limit: int) -> list[Video]:
    result = await client.execute(_UPLOADABLE, [limit])
    return [_row(r) for r in result.rows]
