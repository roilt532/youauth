from __future__ import annotations

from loguru import logger

from alvaro.llm._types import LLMClient, LLMTransientError


class RouterClient:
    _FAILURE_THRESHOLD: int = 2

    def __init__(self, primary: LLMClient, fallback: LLMClient) -> None:
        self._primary = primary
        self._fallback = fallback
        self._consecutive_failures: int = 0
        self._primary_unavailable: bool = False

    async def complete(self, system: str, user: str, temperature: float = 0.7) -> str:
        if not self._primary_unavailable:
            try:
                result = await self._primary.complete(system, user, temperature)
                self._consecutive_failures = 0
                return result
            except LLMTransientError as exc:
                self._consecutive_failures += 1
                logger.warning(
                    "primary llm failed consecutive={} err={}",
                    self._consecutive_failures,
                    exc,
                )
                if self._consecutive_failures >= self._FAILURE_THRESHOLD:
                    self._primary_unavailable = True
                    logger.warning("primary llm circuit open, switching to fallback")
        return await self._fallback.complete(system, user, temperature)
