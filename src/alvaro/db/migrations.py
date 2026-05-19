from __future__ import annotations

import time
from pathlib import Path

from loguru import logger

from alvaro.db.client import DbClient

MIGRATIONS_DIR = Path(__file__).parent.parent.parent.parent / "configs" / "migrations"

_BOOTSTRAP_SQL = """
CREATE TABLE IF NOT EXISTS schema_versions (
    version     INTEGER PRIMARY KEY,
    applied_at  INTEGER NOT NULL,
    description TEXT    NOT NULL
)
"""


async def run_migrations(
    client: DbClient,
    migrations_dir: Path = MIGRATIONS_DIR,
) -> int:
    await client.execute(_BOOTSTRAP_SQL)
    applied = await _applied_versions(client)
    sql_files = sorted(migrations_dir.glob("*.sql"))
    count = 0
    for path in sql_files:
        version = _parse_version(path.name)
        if version is None or version in applied:
            continue
        description = path.stem[5:]
        logger.info("migration v{} ({})", version, description)
        await _apply(client, path, version, description)
        count += 1
    logger.info("migrations done count={}", count)
    return count


async def _applied_versions(client: DbClient) -> set[int]:
    result = await client.execute("SELECT version FROM schema_versions")
    return {int(row[0]) for row in result.rows}


async def _apply(client: DbClient, path: Path, version: int, description: str) -> None:
    for stmt in _split(path.read_text()):
        await client.execute(stmt)
    await client.execute(
        "INSERT INTO schema_versions (version, applied_at, description) VALUES (?, ?, ?)",
        [version, int(time.time()), description],
    )


def _split(sql: str) -> list[str]:
    return [s.strip() for s in sql.split(";") if s.strip()]


def _parse_version(filename: str) -> int | None:
    try:
        return int(filename.split("_")[0])
    except (ValueError, IndexError):
        return None
