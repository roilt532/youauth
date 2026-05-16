from __future__ import annotations

from pathlib import Path

import pytest

from alvaro.db.client import DbClient
from alvaro.db.migrations import _parse_version, _split, run_migrations


@pytest.fixture
async def db(tmp_path: Path) -> DbClient:
    client = DbClient(url=f"file:{tmp_path / 'test.db'}")
    await client.connect()
    yield client
    await client.close()


async def test_apply_real_migration(db: DbClient) -> None:
    count = await run_migrations(db)
    assert count >= 1


async def test_idempotent(db: DbClient) -> None:
    await run_migrations(db)
    second = await run_migrations(db)
    assert second == 0


async def test_schema_versions_row_inserted(db: DbClient) -> None:
    count = await run_migrations(db)
    result = await db.execute("SELECT version FROM schema_versions ORDER BY version ASC")
    assert len(result.rows) == count
    assert int(result.rows[0][0]) == 1


async def test_custom_migration_dir(db: DbClient, tmp_path: Path) -> None:
    mig_dir = tmp_path / "migs"
    mig_dir.mkdir()
    (mig_dir / "0001_create_foo.sql").write_text(
        "CREATE TABLE IF NOT EXISTS foo (id INTEGER PRIMARY KEY)"
    )
    count = await run_migrations(db, migrations_dir=mig_dir)
    assert count == 1
    result = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='foo'")
    assert len(result.rows) == 1


async def test_invalid_filename_skipped(db: DbClient, tmp_path: Path) -> None:
    mig_dir = tmp_path / "migs2"
    mig_dir.mkdir()
    (mig_dir / "not_a_migration.sql").write_text("CREATE TABLE IF NOT EXISTS bad (id INTEGER)")
    count = await run_migrations(db, migrations_dir=mig_dir)
    assert count == 0


def test_parse_version_valid() -> None:
    assert _parse_version("0001_initial.sql") == 1
    assert _parse_version("0042_add_index.sql") == 42


def test_parse_version_invalid() -> None:
    assert _parse_version("not_numeric.sql") is None
    assert _parse_version("") is None


def test_split_statements() -> None:
    sql = "CREATE TABLE a (id INT); CREATE TABLE b (id INT)"
    parts = _split(sql)
    assert len(parts) == 2
    assert "CREATE TABLE a" in parts[0]


def test_split_ignores_empty() -> None:
    parts = _split(";;; SELECT 1 ;  ;")
    assert parts == ["SELECT 1"]
