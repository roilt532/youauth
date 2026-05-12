from __future__ import annotations

import os
from typing import Any

import libsql_client
from loguru import logger


class DbClient:
    def __init__(self, url: str, auth_token: str | None = None) -> None:
        self._url = url
        self._auth_token = auth_token
        self._client: Any = None

    async def connect(self) -> None:
        self._client = libsql_client.create_client(
            url=self._url,
            auth_token=self._auth_token,
        )
        logger.debug("db connected host={}", self._url.split("@")[-1].split("?")[0])

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def __aenter__(self) -> DbClient:
        await self.connect()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    def _ensure_connected(self) -> Any:
        if self._client is None:
            raise RuntimeError("DbClient not connected")
        return self._client

    async def execute(self, sql: str, args: list[Any] | None = None) -> Any:
        client = self._ensure_connected()
        return await client.execute(libsql_client.Statement(sql, args or []))

    async def batch(self, statements: list[tuple[str, list[Any]]]) -> Any:
        client = self._ensure_connected()
        stmts = [libsql_client.Statement(sql, args) for sql, args in statements]
        return await client.batch(stmts)


def _normalize_turso_url(url: str) -> str:
    if url.startswith("libsql://"):
        return "https://" + url[len("libsql://"):]
    return url


def build_db_client() -> DbClient:
    url = _normalize_turso_url(os.environ["TURSO_DATABASE_URL"])
    token = os.environ.get("TURSO_AUTH_TOKEN")
    return DbClient(url=url, auth_token=token)
