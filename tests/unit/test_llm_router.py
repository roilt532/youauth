from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from alvaro.llm._types import LLMTransientError
from alvaro.llm.router import RouterClient


def _make_router(
    primary_result: str | Exception | None = "primary-ok",
    fallback_result: str = "fallback-ok",
) -> tuple[RouterClient, AsyncMock, AsyncMock]:
    primary = AsyncMock()
    fallback = AsyncMock()
    if isinstance(primary_result, Exception):
        primary.complete.side_effect = primary_result
    else:
        primary.complete.return_value = primary_result
    fallback.complete.return_value = fallback_result
    return RouterClient(primary=primary, fallback=fallback), primary, fallback


async def test_router_uses_primary_when_healthy() -> None:
    router, primary, fallback = _make_router()
    result = await router.complete("sys", "user")
    assert result == "primary-ok"
    primary.complete.assert_awaited_once()
    fallback.complete.assert_not_awaited()


async def test_router_falls_back_on_transient_error() -> None:
    router, primary, fallback = _make_router(primary_result=LLMTransientError("fail"))
    result = await router.complete("sys", "user")
    assert result == "fallback-ok"
    fallback.complete.assert_awaited_once()


async def test_router_resets_failures_on_success() -> None:
    router, primary, _ = _make_router()
    router._consecutive_failures = 1
    await router.complete("sys", "user")
    assert router._consecutive_failures == 0


async def test_router_circuit_breaker_opens_after_threshold() -> None:
    router, primary, fallback = _make_router(primary_result=LLMTransientError("fail"))
    for _ in range(RouterClient._FAILURE_THRESHOLD):
        await router.complete("sys", "user")
    assert router._primary_unavailable is True


async def test_router_skips_primary_when_circuit_open() -> None:
    router, primary, fallback = _make_router(primary_result=LLMTransientError("fail"))
    router._primary_unavailable = True
    result = await router.complete("sys", "user")
    assert result == "fallback-ok"
    primary.complete.assert_not_awaited()
    fallback.complete.assert_awaited_once()


async def test_router_circuit_breaker_exactly_at_threshold() -> None:
    router, primary, _ = _make_router(primary_result=LLMTransientError("fail"))
    for i in range(RouterClient._FAILURE_THRESHOLD - 1):
        await router.complete("sys", "user")
        assert router._primary_unavailable is False, f"should be closed after {i + 1} failures"
    await router.complete("sys", "user")
    assert router._primary_unavailable is True


async def test_router_fallback_error_propagates() -> None:
    router, _, fallback = _make_router(primary_result=LLMTransientError("fail"))
    fallback.complete.side_effect = LLMTransientError("fallback-fail")
    with pytest.raises(LLMTransientError, match="fallback-fail"):
        await router.complete("sys", "user")
