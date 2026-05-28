"""Numerology computation service.

Implements the standard Pythagorean numerology system:
- Life Path Number: from birth date (sum of digits, reduced)
- Destiny / Expression: from full birth name (all letters)
- Soul Urge: from vowels of full name
- Personality: from consonants of full name
- Birthday Number: from day of birth

Master numbers (11, 22, 33) are NOT reduced.
"""
from __future__ import annotations

import datetime
import re
import unicodedata

# Pythagorean letter → number map (Latin alphabet).
LATIN_MAP: dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8, "I": 9,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 6, "P": 7, "Q": 8, "R": 9,
    "S": 1, "T": 2, "U": 3, "V": 4, "W": 5, "X": 6, "Y": 7, "Z": 8,
}

# Cyrillic letter → number map (Russian / Ukrainian / Belarusian alphabet).
# Based on the standard Russian numerology table.
CYRILLIC_MAP: dict[str, int] = {
    "А": 1, "Б": 2, "В": 3, "Г": 4, "Д": 5, "Е": 6, "Ё": 7, "Ж": 8, "З": 9,
    "И": 1, "Й": 2, "К": 3, "Л": 4, "М": 5, "Н": 6, "О": 7, "П": 8, "Р": 9,
    "С": 1, "Т": 2, "У": 3, "Ф": 4, "Х": 5, "Ц": 6, "Ч": 7, "Ш": 8, "Щ": 9,
    "Ъ": 1, "Ы": 2, "Ь": 3, "Э": 4, "Ю": 5, "Я": 6,
}

LATIN_VOWELS = set("AEIOUY")
CYRILLIC_VOWELS = set("АЕЁИОУЫЭЮЯ")

MASTER_NUMBERS = {11, 22, 33}


def _digit_sum(n: int) -> int:
    return sum(int(d) for d in str(n))


def reduce_number(n: int) -> int:
    """Reduce to a single digit, preserving master numbers (11, 22, 33)."""
    if n <= 0:
        return 0
    while n > 9 and n not in MASTER_NUMBERS:
        n = _digit_sum(n)
    return n


def _letter_value(ch: str) -> int:
    """Return numerology value for one character (0 if not a recognised letter)."""
    upper = ch.upper()
    if upper in LATIN_MAP:
        return LATIN_MAP[upper]
    if upper in CYRILLIC_MAP:
        return CYRILLIC_MAP[upper]
    return 0


def _is_vowel(ch: str) -> bool:
    upper = ch.upper()
    return upper in LATIN_VOWELS or upper in CYRILLIC_VOWELS


def _is_letter(ch: str) -> bool:
    return _letter_value(ch) > 0


def _clean_name(name: str) -> str:
    """Strip diacritics, punctuation, digits — leave letters and spaces."""
    nfkd = unicodedata.normalize("NFKD", name)
    no_diacritics = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-zА-Яа-яЁё ]", "", no_diacritics).strip()


def life_path(birth_date: datetime.date) -> int:
    """Life Path = reduced sum of (day + month + year) digits, masters preserved."""
    d = _digit_sum(birth_date.day)
    m = _digit_sum(birth_date.month)
    y = _digit_sum(birth_date.year)
    # Each component reduced separately so master numbers in each survive.
    d_red = reduce_number(d)
    m_red = reduce_number(m)
    y_red = reduce_number(y)
    return reduce_number(d_red + m_red + y_red)


def birthday_number(birth_date: datetime.date) -> int:
    """Just the day of the month, reduced (masters preserved)."""
    return reduce_number(birth_date.day)


def destiny_number(full_name: str) -> int:
    """Destiny / Expression — sum of all letter values, reduced."""
    cleaned = _clean_name(full_name)
    total = sum(_letter_value(ch) for ch in cleaned if _is_letter(ch))
    return reduce_number(total)


def soul_urge_number(full_name: str) -> int:
    """Soul Urge / Heart's Desire — sum of vowels."""
    cleaned = _clean_name(full_name)
    total = sum(_letter_value(ch) for ch in cleaned if _is_letter(ch) and _is_vowel(ch))
    return reduce_number(total)


def personality_number(full_name: str) -> int:
    """Personality — sum of consonants."""
    cleaned = _clean_name(full_name)
    total = sum(_letter_value(ch) for ch in cleaned if _is_letter(ch) and not _is_vowel(ch))
    return reduce_number(total)


def calculate_profile(full_name: str, birth_date: datetime.date) -> dict:
    """Return the complete numerology profile."""
    return {
        "life_path": life_path(birth_date),
        "destiny": destiny_number(full_name),
        "soul_urge": soul_urge_number(full_name),
        "personality": personality_number(full_name),
        "birthday": birthday_number(birth_date),
    }


# ---------------------------------------------------------------------------
# Static interpretations (no AI required — works for free tier)
# ---------------------------------------------------------------------------

LIFE_PATH_TEXT_RU: dict[int, str] = {
    1: "Путь Первопроходца. Ты создан вести, начинать и преодолевать. Твоя сила — независимость и инициатива.",
    2: "Путь Дипломата. Твой дар — гармония, чуткость, умение слышать других. Ты строишь мосты.",
    3: "Путь Творца. Радость, выражение, искусство. Ты вдохновляешь словом и красотой.",
    4: "Путь Строителя. Дисциплина, основа, надёжность. Ты создаёшь то, что выдерживает время.",
    5: "Путь Свободы. Перемены, путешествия, опыт. Жизнь зовёт тебя пробовать всё.",
    6: "Путь Заботы. Ответственность, дом, любовь. Ты — целитель и опора для близких.",
    7: "Путь Мудреца. Глубина, поиск истины, тишина. Ты родился для внутренней работы.",
    8: "Путь Власти. Влияние, материальный успех, лидерство. Ты учишься обращаться с силой.",
    9: "Путь Сострадания. Гуманизм, отдача, завершение циклов. Ты несёшь свет другим.",
    11: "Мастер-число. Путь Вдохновения. Ты — канал интуиции и духовного огня. Сложно и величественно.",
    22: "Мастер-число. Путь Строителя великих дел. Тебе доверены проекты, меняющие мир.",
    33: "Мастер-число. Путь Учителя любви. Высшее служение через сострадание и мудрость.",
}

LIFE_PATH_TEXT_EN: dict[int, str] = {
    1: "The Path of the Pioneer. You were made to lead, initiate, and break new ground. Your strength: independence and drive.",
    2: "The Path of the Diplomat. Your gift is harmony, sensitivity, the ability to hear others. You build bridges.",
    3: "The Path of the Creator. Joy, expression, art. You inspire with words and beauty.",
    4: "The Path of the Builder. Discipline, foundation, reliability. You create what endures.",
    5: "The Path of Freedom. Change, travel, experience. Life calls you to taste everything.",
    6: "The Path of Care. Responsibility, home, love. You are a healer and an anchor for your people.",
    7: "The Path of the Sage. Depth, search for truth, silence. You were born for inner work.",
    8: "The Path of Power. Influence, material success, leadership. You learn how to wield strength.",
    9: "The Path of Compassion. Humanism, giving, closing cycles. You carry light to others.",
    11: "Master number. The Path of Inspiration. You are a channel for intuition and spiritual fire. Difficult and majestic.",
    22: "Master number. The Path of the Great Builder. You are entrusted with world-changing projects.",
    33: "Master number. The Path of the Teacher of Love. Highest service through compassion and wisdom.",
}

SHORT_TITLES_RU: dict[int, str] = {
    1: "Лидер", 2: "Миротворец", 3: "Творец", 4: "Строитель", 5: "Странник",
    6: "Хранитель", 7: "Мудрец", 8: "Властитель", 9: "Целитель",
    11: "Провидец", 22: "Архитектор", 33: "Учитель",
}

SHORT_TITLES_EN: dict[int, str] = {
    1: "Leader", 2: "Peacemaker", 3: "Creator", 4: "Builder", 5: "Wanderer",
    6: "Guardian", 7: "Sage", 8: "Sovereign", 9: "Healer",
    11: "Visionary", 22: "Architect", 33: "Teacher",
}


def enrich_profile(profile: dict, locale: str) -> dict:
    """Attach short titles and a life-path summary to the raw profile."""
    titles = SHORT_TITLES_RU if locale == "ru" else SHORT_TITLES_EN
    lp_text = LIFE_PATH_TEXT_RU if locale == "ru" else LIFE_PATH_TEXT_EN
    return {
        **profile,
        "titles": {
            "life_path": titles.get(profile["life_path"], "—"),
            "destiny": titles.get(profile["destiny"], "—"),
            "soul_urge": titles.get(profile["soul_urge"], "—"),
            "personality": titles.get(profile["personality"], "—"),
            "birthday": titles.get(profile["birthday"], "—"),
        },
        "life_path_summary": lp_text.get(profile["life_path"], ""),
    }


def format_profile_for_ai(profile: dict, full_name: str, birth_date: datetime.date, locale: str) -> str:
    """Build the user message for AI interpretation of a numerology profile."""
    if locale == "ru":
        lines = [
            f"Имя: {full_name}",
            f"Дата рождения: {birth_date.isoformat()}",
            "",
            "Нумерологический профиль:",
            f"  Число жизненного пути: {profile['life_path']}",
            f"  Число судьбы (выражения): {profile['destiny']}",
            f"  Число души: {profile['soul_urge']}",
            f"  Число личности: {profile['personality']}",
            f"  Число дня рождения: {profile['birthday']}",
            "",
            "Напиши глубокую, тёплую, эзотерическую интерпретацию по правилам системного промпта.",
        ]
    else:
        lines = [
            f"Name: {full_name}",
            f"Birth date: {birth_date.isoformat()}",
            "",
            "Numerology profile:",
            f"  Life Path Number: {profile['life_path']}",
            f"  Destiny (Expression) Number: {profile['destiny']}",
            f"  Soul Urge Number: {profile['soul_urge']}",
            f"  Personality Number: {profile['personality']}",
            f"  Birthday Number: {profile['birthday']}",
            "",
            "Write a deep, warm, esoteric interpretation following the rules of the system prompt.",
        ]
    return "\n".join(lines)
