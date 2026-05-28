"""Prompt loader. Reads system prompts from apps/tarot/prompts/ and composes them.

Prompts are split into:
- base_system_{locale}.md  — common tone, ethics, format
- spread_{slug}_{locale}.md — per-spread structure + few-shot examples
- runes_cast_{locale}.md    — for the rune cast

We compose two distinct content blocks so the base part is eligible for
prompt caching by Anthropic, while the spread-specific part can change
between requests without invalidating the cache.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "apps" / "tarot" / "prompts"
PROMPT_VERSION = "2026-05-26-v1"


@lru_cache(maxsize=16)
def _read(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def base_system(locale: str) -> str:
    locale = "ru" if locale not in ("ru", "en") else locale
    return _read(f"base_system_{locale}.md")


def tarot_spread(spread_slug: str, locale: str) -> str:
    """Return spread-specific structure prompt. Falls back to 3-card."""
    locale = "ru" if locale not in ("ru", "en") else locale
    candidates = [
        f"spread_{spread_slug}_{locale}.md",
        f"spread_3_cards_{locale}.md",
    ]
    for name in candidates:
        try:
            return _read(name)
        except FileNotFoundError:
            continue
    raise FileNotFoundError(f"No spread prompt for {spread_slug}/{locale}")


def runes_cast(locale: str) -> str:
    locale = "ru" if locale not in ("ru", "en") else locale
    return _read(f"runes_cast_{locale}.md")


def natal_chart(locale: str) -> str:
    locale = "ru" if locale not in ("ru", "en") else locale
    return _read(f"natal_chart_{locale}.md")


def numerology(locale: str) -> str:
    locale = "ru" if locale not in ("ru", "en") else locale
    return _read(f"numerology_{locale}.md")
