from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from alvaro.db.client import DbClient

_SEL = (
    "SELECT niche_id, last_run_at, last_success_at, consecutive_failures, "
    "total_videos_generated, total_uploads, paused FROM niches_state"
)


@dataclass
class NicheState:
    niche_id: str
    last_run_at: int | None
    last_success_at: int | None
    consecutive_failures: int
    total_videos_generated: int
    total_uploads: int
    paused: bool


def _row(r: Any) -> NicheState:
    return NicheState(
        niche_id=str(r[0]),
        last_run_at=int(r[1]) if r[1] is not None else None,
        last_success_at=int(r[2]) if r[2] is not None else None,
        consecutive_failures=int(r[3]),
        total_videos_generated=int(r[4]),
        total_uploads=int(r[5]),
        paused=bool(int(r[6])),
    )


async def get_or_create(client: DbClient, niche_id: str) -> NicheState:
    await client.execute(
        "INSERT OR IGNORE INTO niches_state (niche_id) VALUES (?)", [niche_id]
    )
    result = await client.execute(f"{_SEL} WHERE niche_id = ?", [niche_id])
    return _row(result.rows[0])


async def mark_run_started(client: DbClient, niche_id: str) -> None:
    await client.execute(
        "UPDATE niches_state SET last_run_at = ? WHERE niche_id = ?",
        [int(time.time()), niche_id],
    )


async def mark_success(client: DbClient, niche_id: str) -> None:
    await client.execute(
        "UPDATE niches_state SET last_success_at = ?, consecutive_failures = 0, "
        "total_videos_generated = total_videos_generated + 1 WHERE niche_id = ?",
        [int(time.time()), niche_id],
    )


async def increment_uploads(client: DbClient, niche_id: str) -> None:
    await client.execute(
        "UPDATE niches_state SET total_uploads = total_uploads + 1 WHERE niche_id = ?",
        [niche_id],
    )


async def increment_failures(client: DbClient, niche_id: str) -> None:
    await client.execute(
        "UPDATE niches_state SET consecutive_failures = consecutive_failures + 1 "
        "WHERE niche_id = ?",
        [niche_id],
    )


async def set_paused(client: DbClient, niche_id: str, *, paused: bool) -> None:
    await client.execute(
        "UPDATE niches_state SET paused = ? WHERE niche_id = ?",
        [1 if paused else 0, niche_id],
    )
