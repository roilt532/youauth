from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from alvaro.db.client import DbClient, build_db_client


@pytest.fixture
def mock_libsql(mocker: MockerFixture) -> MagicMock:
    mock = mocker.patch("alvaro.db.client.libsql_client")
    inner = MagicMock()
    inner.close = AsyncMock()
    inner.execute = AsyncMock()
    inner.batch = AsyncMock()
    mock.create_client.return_value = inner
    return mock


@pytest.fixture
def client() -> DbClient:
    return DbClient(url="libsql://test.turso.io", auth_token="tok")


def test_not_connected_raises(client: DbClient) -> None:
    with pytest.raises(RuntimeError, match="not connected"):
        client._ensure_connected()


async def test_connect_calls_create_client(
    client: DbClient, mock_libsql: MagicMock
) -> None:
    await client.connect()
    mock_libsql.create_client.assert_called_once_with(
        url="libsql://test.turso.io", auth_token="tok"
    )


async def test_context_manager_connects_and_closes(mock_libsql: MagicMock) -> None:
    async with DbClient(url="file::memory:") as db:
        assert db._client is not None
    mock_libsql.create_client.return_value.close.assert_awaited_once()


async def test_execute_uses_statement(
    client: DbClient, mock_libsql: MagicMock
) -> None:
    await client.connect()
    await client.execute("SELECT 1", [42])
    mock_libsql.Statement.assert_called_with("SELECT 1", [42])
    mock_libsql.create_client.return_value.execute.assert_awaited_once()


async def test_close_is_idempotent(client: DbClient, mock_libsql: MagicMock) -> None:
    await client.connect()
    await client.close()
    await client.close()
    mock_libsql.create_client.return_value.close.assert_awaited_once()


def test_build_db_client_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://env.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "envtoken")
    db = build_db_client()
    assert db._url == "libsql://env.turso.io"
    assert db._auth_token == "envtoken"


def test_build_db_client_missing_url_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    with pytest.raises(KeyError):
        build_db_client()
