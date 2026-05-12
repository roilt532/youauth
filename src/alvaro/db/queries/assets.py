from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from alvaro.db.client import DbClient

_SEL = (
    "SELECT id, r2_key, asset_type, niche_id, size_bytes, etag, verified_at, created_at FROM assets"
)


@dataclass
class Asset:
    id: str
    r2_key: str
    asset_type: str
    niche_id: str | None
    size_bytes: int
    etag: str
    verified_at: int | None
    created_at: int


def _row(r: Any) -> Asset:
    return Asset(
        id=str(r[0]),
        r2_key=str(r[1]),
        asset_type=str(r[2]),
        niche_id=str(r[3]) if r[3] is not None else None,
        size_bytes=int(r[4]),
        etag=str(r[5]),
        verified_at=int(r[6]) if r[6] is not None else None,
        created_at=int(r[7]),
    )


async def upsert_asset(
    client: DbClient,
    *,
    r2_key: str,
    asset_type: str,
    size_bytes: int,
    etag: str,
    niche_id: str | None = None,
) -> Asset:
    now = int(time.time())
    asset_id = str(uuid.uuid4())
    await client.execute(
        "INSERT INTO assets (id, r2_key, asset_type, niche_id, size_bytes, etag, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(r2_key) DO UPDATE SET "
        "size_bytes = excluded.size_bytes, etag = excluded.etag",
        [asset_id, r2_key, asset_type, niche_id, size_bytes, etag, now],
    )
    result = await client.execute(f"{_SEL} WHERE r2_key = ?", [r2_key])
    return _row(result.rows[0])


async def list_backgrounds(client: DbClient, niche_id: str | None = None) -> list[Asset]:
    if niche_id:
        result = await client.execute(
            f"{_SEL} WHERE asset_type = 'background' AND (niche_id = ? OR niche_id IS NULL) "
            "ORDER BY created_at DESC",
            [niche_id],
        )
    else:
        result = await client.execute(
            f"{_SEL} WHERE asset_type = 'background' ORDER BY created_at DESC"
        )
    return [_row(r) for r in result.rows]


async def mark_verified(client: DbClient, r2_key: str) -> None:
    await client.execute(
        "UPDATE assets SET verified_at = ? WHERE r2_key = ?",
        [int(time.time()), r2_key],
    )
