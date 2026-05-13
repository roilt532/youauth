from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from alvaro.subtitles._types import SubtitleError, SubtitleTrack, WordTiming


def _word(text: str = "hola", start: float = 0.0, end: float = 0.5, kw: bool = False) -> WordTiming:
    return WordTiming(text=text, start_s=start, end_s=end, is_keyword=kw)


class TestWordTiming:
    def test_frozen_raises_on_assign(self) -> None:
        w = _word()
        with pytest.raises((AttributeError, TypeError)):
            w.text = "otro"  # type: ignore[misc]

    def test_replace_creates_new(self) -> None:
        w = _word()
        w2 = replace(w, is_keyword=True)
        assert w2.is_keyword is True
        assert w.is_keyword is False

    def test_fields(self) -> None:
        w = _word("cielo", 1.0, 2.0, True)
        assert w.text == "cielo"
        assert w.start_s == 1.0
        assert w.end_s == 2.0
        assert w.is_keyword is True


class TestSubtitleTrack:
    def test_keyword_count(self) -> None:
        words = [_word(kw=True), _word(kw=False), _word(kw=True)]
        track = SubtitleTrack(
            ass_file_path=Path("/tmp/x.ass"),  # noqa: S108
            words=words,
            total_duration_s=3.0,
            keyword_count=2,
        )
        assert track.keyword_count == 2

    def test_frozen_raises_on_assign(self) -> None:
        track = SubtitleTrack(
            ass_file_path=Path("/tmp/x.ass"),  # noqa: S108
            words=[],
            total_duration_s=0.0,
            keyword_count=0,
        )
        with pytest.raises((AttributeError, TypeError)):
            track.keyword_count = 5  # type: ignore[misc]


class TestSubtitleError:
    def test_is_exception(self) -> None:
        err = SubtitleError("fail")
        assert isinstance(err, Exception)
        assert "fail" in str(err)
