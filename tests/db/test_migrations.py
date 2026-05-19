from __future__ import annotations

from pathlib import Path

import pytest

from alvaro.db.client import DbClient
from alvaro.db.migrations import run_migrations


@pytest.fixture
async def db(tmp_path: Path) -> DbClient:
    client = DbClient(url=f"file:{tmp_path / 'test.db'}")
    await client.connect()
    yield client
    await client.close()


async def test_niches_state_seeded_and_schema(db: DbClient) -> None:
    await run_migrations(db)

    rows = await db.execute("SELECT COUNT(*) FROM niches_state")
    assert int(rows.rows[0][0]) == 5

    pragma = await db.execute("PRAGMA table_info(niches_state)")
    paused = next(r for r in pragma.rows if r[1] == "paused")
    assert str(paused[2]).upper() == "INTEGER"
    assert int(paused[3]) == 1
