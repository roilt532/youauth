from __future__ import annotations

import html

from alvaro.scripting.models import Script

_BREAK = '<break time="500ms"/>'


def build_ssml(script: Script, rate: str, pitch: str) -> str:
    parts: list[str] = []
    parts.append(html.escape(script.hook_text))
    for line in script.body_lines:
        parts.append(html.escape(line))
    parts.append(html.escape(script.payoff_text))
    inner = f" {_BREAK} ".join(parts)
    return (
        f'<speak><prosody rate="{rate}" pitch="{pitch}">'
        f"{inner}"
        f"</prosody></speak>"
    )
