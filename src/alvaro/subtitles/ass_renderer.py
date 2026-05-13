from __future__ import annotations

import subprocess
from pathlib import Path

from loguru import logger

from alvaro.subtitles._types import WordTiming

_FONT_PRIMARY = "Inter Black"
_FONT_FALLBACK = "Arial Black"
_FONT_SIZE = 90
_OUTLINE = 6
_SHADOW = 2
_MARGIN_V = 280
_PAD_S = 0.05


def _detect_font() -> str:
    try:
        result = subprocess.run(  # noqa: S603
            ["fc-list"],  # noqa: S607
            capture_output=True,
            check=False,
            timeout=5,
        )
        if _FONT_PRIMARY.lower() in result.stdout.decode(errors="replace").lower():
            return _FONT_PRIMARY
    except (OSError, subprocess.TimeoutExpired):
        pass
    logger.warning("Inter Black not available, falling back to Arial Black")
    return _FONT_FALLBACK


def _fmt_time(s: float) -> str:
    cs = int(round(max(s, 0.0) * 100))
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    sec, cs_part = divmod(rem, 100)
    return f"{h}:{m:02d}:{sec:02d}.{cs_part:02d}"


def _build_header(font: str) -> str:
    colour_white = "&H00FFFFFF"
    colour_yellow = "&H0000FFFF"
    colour_black = "&H00000000"
    style_fmt = (
        "Style: {name},{font},{size},{primary},{secondary},{outline},{back},"
        "-1,0,0,0,100,100,0,0,1,{ol},{sh},2,20,20,{mv},1"
    )
    default_style = style_fmt.format(
        name="Default", font=font, size=_FONT_SIZE,
        primary=colour_white, secondary=colour_yellow,
        outline=colour_black, back=colour_black,
        ol=_OUTLINE, sh=_SHADOW, mv=_MARGIN_V,
    )
    keyword_style = style_fmt.format(
        name="Keyword", font=font, size=_FONT_SIZE,
        primary=colour_yellow, secondary=colour_yellow,
        outline=colour_black, back=colour_black,
        ol=_OUTLINE, sh=_SHADOW, mv=_MARGIN_V,
    )
    return "\n".join([
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "WrapStyle: 0",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        default_style,
        keyword_style,
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ])


_ANIM = (
    r"{\fscx80\fscy80\alpha&HFF&"
    r"\t(0,80,\fscx110\fscy110\alpha&H00&)"
    r"\t(80,120,\fscx100\fscy100\alpha&H00&)}"
)


def _dialogue_line(word: WordTiming) -> str:
    start = _fmt_time(word.start_s - _PAD_S)
    end = _fmt_time(word.end_s + _PAD_S)
    style = "Keyword" if word.is_keyword else "Default"
    return f"Dialogue: 0,{start},{end},{style},,0,0,0,,{_ANIM}{word.text}"


def render_ass(words: list[WordTiming], output_path: Path, font: str | None = None) -> None:
    if font is None:
        font = _detect_font()
    header = _build_header(font)
    lines = [header] + [_dialogue_line(w) for w in words]
    output_path.write_text("\n".join(lines), encoding="utf-8")
