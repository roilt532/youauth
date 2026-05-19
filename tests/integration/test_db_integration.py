from __future__ import annotations

import os

import pytest

from alvaro.db.client import build_db_client
from alvaro.db.migrations import run_migrations
from alvaro.db.queries import jobs, niches

pytestmark = pytest.mark.skipif(
    not os.environ.get("TURSO_DATABASE_URL"),
    reason="TURSO_DATABASE_URL not set - skipping integration test",
)


@pytest.fixture
async def db() -> object:
    client = build_db_client()
    await client.connect()
    yield client
    await client.close()


async def test_migrations_apply_and_idempotent(db: object) -> None:
    from alvaro.db.client import DbClient

    assert isinstance(db, DbClient)
    first = await run_migrations(db)
    second = await run_migrations(db)
    assert first >= 0
    assert second == 0


async def test_niche_create_and_job_roundtrip(db: object) -> None:
    from alvaro.db.client import DbClient

    assert isinstance(db, DbClient)
    niche_id = "science"
    idem_key = f"integration_science_{os.getpid()}"

    await niches.get_or_create(db, niche_id)
    job = await jobs.upsert_job(db, idempotency_key=idem_key, niche_id=niche_id)
    assert job.status == "pending"

    job2 = await jobs.upsert_job(db, idempotency_key=idem_key, niche_id=niche_id)
    assert job.id == job2.id

    await jobs.mark_done(db, job.id)
    result = await db.execute("SELECT status FROM jobs WHERE id = ?", [job.id])
    assert result.rows[0][0] == "done"
