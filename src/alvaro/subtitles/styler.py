from __future__ import annotations

import re
from dataclasses import replace

from alvaro.scripting.models import Script
from alvaro.subtitles._types import WordTiming

_STOPWORDS_ES: frozenset[str] = frozenset(
    {
        "el",
        "la",
        "los",
        "las",
        "un",
        "una",
        "unos",
        "unas",
        "de",
        "del",
        "al",
        "en",
        "con",
        "por",
        "para",
        "que",
        "se",
        "es",
        "son",
        "era",
        "fue",
        "muy",
        "mas",
        "pero",
        "sino",
        "como",
        "cuando",
        "donde",
        "quien",
        "cual",
        "cuales",
        "ya",
        "si",
        "no",
        "ni",
        "o",
        "y",
        "e",
        "u",
        "su",
        "sus",
        "mi",
        "mis",
        "tu",
        "tus",
        "hay",
        "esto",
        "esta",
        "estos",
        "estas",
        "ese",
        "esa",
        "esos",
        "esas",
        "lo",
        "le",
        "les",
        "me",
        "te",
        "nos",
        "han",
        "sido",
        "tiene",
        "tienen",
        "hacer",
        "hace",
        "hecho",
        "ser",
        "estar",
        "tener",
        "puede",
        "pueden",
        "cada",
        "todo",
        "toda",
        "todos",
        "todas",
        "otro",
        "otra",
        "otros",
        "otras",
    }
)

_STOPWORDS_EN: frozenset[str] = frozenset(
    {
        "the",
        "a",
        "an",
        "of",
        "in",
        "to",
        "is",
        "it",
        "its",
        "and",
        "or",
        "but",
        "for",
        "with",
        "on",
        "at",
        "by",
        "this",
        "that",
        "these",
        "those",
        "what",
        "when",
        "where",
        "who",
        "how",
        "why",
        "can",
        "do",
        "did",
        "are",
        "was",
        "were",
        "be",
        "been",
        "has",
        "have",
        "had",
        "will",
        "would",
        "not",
        "no",
        "so",
        "if",
        "as",
        "from",
        "than",
        "then",
        "we",
        "you",
        "he",
        "she",
        "they",
        "our",
        "your",
        "their",
        "his",
        "her",
        "all",
        "each",
        "every",
        "some",
        "any",
        "just",
        "also",
        "more",
        "most",
        "other",
        "about",
        "after",
        "before",
        "while",
        "which",
        "into",
        "over",
        "such",
        "even",
    }
)

_MIN_KW_LEN = 4
_DENSITY_GAP = 3


def _clean(text: str) -> str:
    return re.sub(r"[^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]", "", text).lower()


def _extract_script_keywords(script: Script, language: str) -> frozenset[str]:
    stopwords = _STOPWORDS_EN if language.startswith("en") else _STOPWORDS_ES
    all_text = " ".join([script.hook_text] + script.body_lines + [script.payoff_text])
    tokens = re.findall(r"[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+", all_text)
    return frozenset(
        t.lower() for t in tokens if len(t) >= _MIN_KW_LEN and t.lower() not in stopwords
    )


def apply_keywords(
    words: list[WordTiming],
    script: Script,
    language: str = "es",
) -> list[WordTiming]:
    keywords = _extract_script_keywords(script, language)

    marked: list[WordTiming] = [replace(w, is_keyword=(_clean(w.text) in keywords)) for w in words]

    last_keyword_idx = -_DENSITY_GAP
    for i in range(len(marked)):
        if marked[i].is_keyword:
            if (i - last_keyword_idx) >= _DENSITY_GAP:
                last_keyword_idx = i
            else:
                marked[i] = replace(marked[i], is_keyword=False)

    return marked
