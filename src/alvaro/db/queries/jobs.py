from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from alvaro.db.client import DbClient

_SEL = (
    "SELECT id, idempotency_key, niche_id, status, run_id, "
    "created_at, started_at, finished_at, error FROM jobs"
)


@dataclass
class Job:
    id: str
    idempotency_key: str
    niche_id: str
    status: str
    run_id: str | None
    created_at: int
    started_at: int | None
    finished_at: int | None
    error: str | None


def _row(r: Any) -> Job:
    return Job(
        id=str(r[0]),
        idempotency_key=str(r[1]),
        niche_id=str(r[2]),
        status=str(r[3]),
        run_id=str(r[4]) if r[4] is not None else None,
        created_at=int(r[5]),
        started_at=int(r[6]) if r[6] is not None else None,
        finished_at=int(r[7]) if r[7] is not None else None,
        error=str(r[8]) if r[8] is not None else None,
    )


async def upsert_job(
    client: DbClient,
    *,
    idempotency_key: str,
    niche_id: str,
    run_id: str | None = None,
) -> Job:
    now = int(time.time())
    await client.execute(
        "INSERT OR IGNORE INTO jobs "
        "(id, idempotency_key, niche_id, status, run_id, created_at) "
        "VALUES (?, ?, ?, 'pending', ?, ?)",
        [str(uuid.uuid4()), idempotency_key, niche_id, run_id, now],
    )
    result = await client.execute(f"{_SEL} WHERE idempotency_key = ?", [idempotency_key])
    return _row(result.rows[0])


async def mark_running(client: DbClient, job_id: str) -> None:
    await client.execute(
        "UPDATE jobs SET status = 'running', started_at = ? WHERE id = ?",
        [int(time.time()), job_id],
    )


async def mark_done(client: DbClient, job_id: str) -> None:
    await client.execute(
        "UPDATE jobs SET status = 'done', finished_at = ? WHERE id = ?",
        [int(time.time()), job_id],
    )


async def mark_failed(client: DbClient, job_id: str, error: str) -> None:
    await client.execute(
        "UPDATE jobs SET status = 'failed', finished_at = ?, error = ? WHERE id = ?",
        [int(time.time()), error, job_id],
    )


async def get_pending(client: DbClient) -> list[Job]:
    result = await client.execute(f"{_SEL} WHERE status = 'pending' ORDER BY created_at ASC")
    return [_row(r) for r in result.rows]
