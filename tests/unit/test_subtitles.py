from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from alvaro.scripting.models import Script
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


def _make_whisper_word(word: str = " hola", start: float = 0.1, end: float = 0.5) -> MagicMock:
    w = MagicMock()
    w.word = word
    w.start = start
    w.end = end
    w.probability = 0.9
    return w


def _make_segment(words: list[MagicMock]) -> MagicMock:
    seg = MagicMock()
    seg.words = words
    return seg


class TestTranscriber:
    async def test_returns_word_timings(self, tmp_path: Path) -> None:
        from alvaro.subtitles.transcriber import transcribe

        audio = tmp_path / "audio.mp3"
        audio.touch()
        seg = _make_segment([_make_whisper_word(" hola", 0.1, 0.5)])
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (iter([seg]), MagicMock())
        with patch("alvaro.subtitles.transcriber._get_model", return_value=mock_model):
            words = await transcribe(audio, "es")
        assert len(words) == 1
        assert words[0].text == "hola"
        assert words[0].start_s == pytest.approx(0.1)
        assert words[0].end_s == pytest.approx(0.5)
        assert words[0].is_keyword is False

    async def test_forces_language_arg(self, tmp_path: Path) -> None:
        from alvaro.subtitles.transcriber import transcribe

        audio = tmp_path / "audio.mp3"
        audio.touch()
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (iter([]), MagicMock())
        with patch("alvaro.subtitles.transcriber._get_model", return_value=mock_model):
            await transcribe(audio, "en")
        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs["language"] == "en"

    async def test_word_timestamps_and_vad_enabled(self, tmp_path: Path) -> None:
        from alvaro.subtitles.transcriber import transcribe

        audio = tmp_path / "audio.mp3"
        audio.touch()
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (iter([]), MagicMock())
        with patch("alvaro.subtitles.transcriber._get_model", return_value=mock_model):
            await transcribe(audio, "es")
        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs["word_timestamps"] is True
        assert call_kwargs["vad_filter"] is True

    async def test_strips_leading_space_from_word(self, tmp_path: Path) -> None:
        from alvaro.subtitles.transcriber import transcribe

        audio = tmp_path / "audio.mp3"
        audio.touch()
        seg = _make_segment([_make_whisper_word(" mundo", 0.0, 0.3)])
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (iter([seg]), MagicMock())
        with patch("alvaro.subtitles.transcriber._get_model", return_value=mock_model):
            words = await transcribe(audio, "es")
        assert words[0].text == "mundo"


def _make_script(
    hook: str = "Por que el cielo es azul?",
    body: list[str] | None = None,
    payoff: str = "Y eso es todo.",
) -> Script:
    return Script(
        hook_text=hook,
        body_lines=body or ["La luz dispersa en moleculas de aire."],
        payoff_text=payoff,
        total_duration_estimate_s=52,
        suggested_voice_id="alvaro_es",
        suggested_background_niche="minecraft_parkour",
        niche_id="science",
    )


class TestStyler:
    def test_marks_keyword_from_script(self) -> None:
        from alvaro.subtitles.styler import apply_keywords

        script = _make_script(hook="Fotosintesis es clave para vida")
        words = [_word("fotosintesis"), _word("de"), _word("la")]
        result = apply_keywords(words, script, "es")
        assert result[0].is_keyword is True

    def test_removes_stopwords(self) -> None:
        from alvaro.subtitles.styler import apply_keywords

        script = _make_script(hook="de la que en el")
        words = [_word("de"), _word("la"), _word("que"), _word("el")]
        result = apply_keywords(words, script, "es")
        assert all(not w.is_keyword for w in result)

    def test_ignores_short_words(self) -> None:
        from alvaro.subtitles.styler import apply_keywords

        script = _make_script(hook="luz sol mar")
        words = [_word("luz"), _word("sol"), _word("mar")]
        result = apply_keywords(words, script, "es")
        assert all(not w.is_keyword for w in result)

    def test_density_cap_global_positions_0_3_6(self) -> None:
        from alvaro.subtitles.styler import apply_keywords

        script = _make_script(
            hook="alpha bravo charlie delta echo foxtrot gamma",
            body=[], payoff="",
        )
        words = [
            _word("alpha"), _word("bravo"), _word("charlie"),
            _word("delta"), _word("echo"), _word("foxtrot"),
            _word("gamma"),
        ]
        result = apply_keywords(words, script, "es")
        kw_indices = [i for i, w in enumerate(result) if w.is_keyword]
        assert kw_indices == [0, 3, 6]

    def test_density_cap_no_two_adjacent(self) -> None:
        from alvaro.subtitles.styler import apply_keywords

        script = _make_script(hook="alpha bravo charlie", body=[], payoff="")
        words = [_word("alpha"), _word("bravo"), _word("charlie")]
        result = apply_keywords(words, script, "es")
        kw_positions = [i for i, w in enumerate(result) if w.is_keyword]
        for i in range(len(kw_positions) - 1):
            assert kw_positions[i + 1] - kw_positions[i] >= 3

    def test_en_stopwords_not_marked(self) -> None:
        from alvaro.subtitles.styler import apply_keywords

        script = _make_script(hook="the and that what")
        words = [_word("the"), _word("and"), _word("that"), _word("what")]
        result = apply_keywords(words, script, "en")
        assert all(not w.is_keyword for w in result)

    def test_case_insensitive_match(self) -> None:
        from alvaro.subtitles.styler import apply_keywords

        script = _make_script(hook="Fotosintesis produce energia solar")
        words = [_word("FOTOSINTESIS")]
        result = apply_keywords(words, script, "es")
        assert result[0].is_keyword is True
