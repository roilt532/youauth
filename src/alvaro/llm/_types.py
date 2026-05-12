from __future__ import annotations

import re
from typing import Protocol, runtime_checkable


class LLMTransientError(Exception):
    pass


@runtime_checkable
class LLMClient(Protocol):
    async def complete(self, system: str, user: str, temperature: float = 0.7) -> str:
        ...


def _strip_fences(text: str) -> str:
    text = re.sub(r"^```[a-z]*\n?", "", text.strip())
    text = re.sub(r"\n?```$", "", text)
    return text.strip()
