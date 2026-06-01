"""Daily horoscope service.

Provides a *deterministic* daily horoscope for each of the 12 zodiac signs.
The free tier reading is assembled from curated phrase pools, seeded by a
SHA-256 hash of (date | sign) so that:
  - every sign gets a different reading on the same day,
  - the same sign gets the same reading all day long (stable),
  - the reading changes naturally from one day to the next.

The premium tier uses these structured cues as the seed for an AI-written,
longer, more personal horoscope (see views.interpret).
"""
from __future__ import annotations

import datetime
import hashlib
from typing import Optional

# --- Zodiac signs -----------------------------------------------------------

# Each sign: slug, names, glyph, element, ruling planet, date span (month, day).
SIGNS: list[dict] = [
    {"slug": "aries", "name_ru": "Овен", "name_en": "Aries", "symbol": "♈",
     "element": "fire", "planet_ru": "Марс", "planet_en": "Mars",
     "start": (3, 21), "end": (4, 19)},
    {"slug": "taurus", "name_ru": "Телец", "name_en": "Taurus", "symbol": "♉",
     "element": "earth", "planet_ru": "Венера", "planet_en": "Venus",
     "start": (4, 20), "end": (5, 20)},
    {"slug": "gemini", "name_ru": "Близнецы", "name_en": "Gemini", "symbol": "♊",
     "element": "air", "planet_ru": "Меркурий", "planet_en": "Mercury",
     "start": (5, 21), "end": (6, 20)},
    {"slug": "cancer", "name_ru": "Рак", "name_en": "Cancer", "symbol": "♋",
     "element": "water", "planet_ru": "Луна", "planet_en": "Moon",
     "start": (6, 21), "end": (7, 22)},
    {"slug": "leo", "name_ru": "Лев", "name_en": "Leo", "symbol": "♌",
     "element": "fire", "planet_ru": "Солнце", "planet_en": "Sun",
     "start": (7, 23), "end": (8, 22)},
    {"slug": "virgo", "name_ru": "Дева", "name_en": "Virgo", "symbol": "♍",
     "element": "earth", "planet_ru": "Меркурий", "planet_en": "Mercury",
     "start": (8, 23), "end": (9, 22)},
    {"slug": "libra", "name_ru": "Весы", "name_en": "Libra", "symbol": "♎",
     "element": "air", "planet_ru": "Венера", "planet_en": "Venus",
     "start": (9, 23), "end": (10, 22)},
    {"slug": "scorpio", "name_ru": "Скорпион", "name_en": "Scorpio", "symbol": "♏",
     "element": "water", "planet_ru": "Плутон", "planet_en": "Pluto",
     "start": (10, 23), "end": (11, 21)},
    {"slug": "sagittarius", "name_ru": "Стрелец", "name_en": "Sagittarius", "symbol": "♐",
     "element": "fire", "planet_ru": "Юпитер", "planet_en": "Jupiter",
     "start": (11, 22), "end": (12, 21)},
    {"slug": "capricorn", "name_ru": "Козерог", "name_en": "Capricorn", "symbol": "♑",
     "element": "earth", "planet_ru": "Сатурн", "planet_en": "Saturn",
     "start": (12, 22), "end": (1, 19)},
    {"slug": "aquarius", "name_ru": "Водолей", "name_en": "Aquarius", "symbol": "♒",
     "element": "air", "planet_ru": "Уран", "planet_en": "Uranus",
     "start": (1, 20), "end": (2, 18)},
    {"slug": "pisces", "name_ru": "Рыбы", "name_en": "Pisces", "symbol": "♓",
     "element": "water", "planet_ru": "Нептун", "planet_en": "Neptune",
     "start": (2, 19), "end": (3, 20)},
]

SIGN_BY_SLUG: dict[str, dict] = {s["slug"]: s for s in SIGNS}
VALID_SLUGS = set(SIGN_BY_SLUG.keys())

ELEMENT_LABELS = {
    "fire": {"ru": "Огонь", "en": "Fire"},
    "earth": {"ru": "Земля", "en": "Earth"},
    "air": {"ru": "Воздух", "en": "Air"},
    "water": {"ru": "Вода", "en": "Water"},
}


def sign_for_date(month: int, day: int) -> Optional[dict]:
    """Return the zodiac sign dict for a given calendar month/day."""
    for s in SIGNS:
        sm, sd = s["start"]
        em, ed = s["end"]
        if sm <= em:  # span within a single year
            if (month, day) >= (sm, sd) and (month, day) <= (em, ed):
                return s
        else:  # Capricorn wraps across the new year
            if (month, day) >= (sm, sd) or (month, day) <= (em, ed):
                return s
    return None


# --- Curated phrase pools ---------------------------------------------------
# Indexed deterministically by the day seed. Kept warm, supportive, non-fatalistic.

_OVERALL_RU = [
    "День просит тебя замедлиться и прислушаться к внутреннему ритму — спешка сегодня только запутает узоры.",
    "Вселенная подбрасывает мягкий ветер перемен: то, что вчера казалось закрытой дверью, сегодня лишь приоткрыто.",
    "Сегодня твоя интуиция звучит особенно чисто. Доверься первому тихому ощущению, а не громким сомнениям.",
    "Это день собранности: маленький, но завершённый шаг даст больше, чем десять начатых и брошенных.",
    "Звёзды настраивают тебя на встречи и разговоры — кто-то скажет слово, которое ты будешь вспоминать.",
    "Энергия дня тёплая и созидательная. Позволь себе создавать, а не только реагировать.",
    "Сегодня хорошо отпускать лишнее — мысли, обиды, незаконченные списки. Освободи место для нового.",
    "День глубины: за обыденными делами прячется важный смысл, если ты захочешь его заметить.",
]
_OVERALL_EN = [
    "The day asks you to slow down and listen to your inner rhythm — rushing will only tangle the threads.",
    "The universe sends a soft wind of change: what felt like a closed door yesterday is merely ajar today.",
    "Your intuition rings especially clear today. Trust the first quiet feeling, not the loud doubts.",
    "This is a day of focus: one small but finished step will give you more than ten begun and abandoned.",
    "The stars tune you toward meetings and conversations — someone will say a word you'll remember.",
    "The day's energy is warm and creative. Allow yourself to make, not only to react.",
    "Today is good for letting go of excess — thoughts, grudges, unfinished lists. Make room for the new.",
    "A day of depth: an important meaning hides behind ordinary tasks, if you choose to notice it.",
]

_LOVE_RU = [
    "В отношениях сегодня важна нежность мелочей: взгляд, прикосновение, вовремя сказанное «я рядом».",
    "Сердце готово открыться чуть шире обычного. Не бойся быть искренним первым.",
    "Если есть недосказанность — день благоволит честному, но бережному разговору.",
    "Одиноким звёзды шепчут: ты привлекательнее, когда живёшь своей жизнью, а не ждёшь чужой.",
    "Любовь сегодня — про слушать, а не убеждать. Дай близкому человеку быть услышанным.",
    "Тёплая искра вспыхнёт там, где ты меньше всего её ждёшь. Останься открытым.",
]
_LOVE_EN = [
    "In relationships, the tenderness of small things matters today: a glance, a touch, a timely 'I'm here'.",
    "Your heart is ready to open a little wider than usual. Don't be afraid to be sincere first.",
    "If something's left unsaid, the day favours an honest but gentle conversation.",
    "To the single ones the stars whisper: you're most magnetic when living your own life, not waiting for another's.",
    "Love today is about listening, not convincing. Let the one close to you feel heard.",
    "A warm spark will flare where you least expect it. Stay open.",
]

_CAREER_RU = [
    "В делах хорош спокойный темп: проверь детали, и удача сама закрепит результат.",
    "Сегодня твои идеи звучат убедительно — не держи их в столе, поделись с тем, кто решает.",
    "День удачен для наведения порядка: разбери завалы, и пространство ответит ясностью.",
    "Не бойся попросить о помощи — союзник окажется ближе, чем казалось.",
    "Финансовые решения лучше принимать с холодной головой: отложи импульс до завтра.",
    "Твоя усидчивость сегодня — суперсила. Один сосредоточенный час сделает больше, чем весь вчерашний день.",
]
_CAREER_EN = [
    "In work a calm pace serves you best: check the details and fortune will lock in the result.",
    "Your ideas sound convincing today — don't keep them in a drawer, share them with whoever decides.",
    "A good day for tidying up: clear the clutter and the space will answer with clarity.",
    "Don't be afraid to ask for help — an ally is closer than you thought.",
    "Make financial decisions with a cool head: hold the impulse until tomorrow.",
    "Your persistence is a superpower today. One focused hour will do more than all of yesterday.",
]

_WELLBEING_RU = [
    "Тело просит воды, воздуха и короткой прогулки. Подари ему эту простую заботу.",
    "Сегодня важен сон: ляг чуть раньше, и завтрашнее «я» скажет спасибо.",
    "Сделай паузу для дыхания — пять медленных вдохов вернут тебе центр.",
    "Энергии много, но расходуй её мудро: чередуй движение и тишину.",
    "Хороший день, чтобы побаловать себя чем-то вкусным и тёплым без чувства вины.",
    "Прислушайся к телу — мелкое напряжение в плечах сегодня сигнал отдохнуть.",
]
_WELLBEING_EN = [
    "Your body asks for water, air and a short walk. Give it this simple care.",
    "Sleep matters today: go to bed a little earlier and tomorrow's self will thank you.",
    "Take a breathing pause — five slow breaths will bring you back to center.",
    "There's plenty of energy, but spend it wisely: alternate movement and stillness.",
    "A good day to treat yourself to something tasty and warm, without guilt.",
    "Listen to your body — small tension in the shoulders is today's signal to rest.",
]

_MOOD_RU = ["Вдохновение", "Спокойствие", "Ясность", "Тепло", "Решимость",
            "Лёгкость", "Глубина", "Нежность", "Сила", "Любопытство"]
_MOOD_EN = ["Inspiration", "Calm", "Clarity", "Warmth", "Resolve",
            "Lightness", "Depth", "Tenderness", "Strength", "Curiosity"]

_COLOR_RU = ["Глубокий синий", "Тёплое золото", "Изумрудный", "Лиловый",
             "Алый", "Серебристый", "Янтарный", "Бирюзовый"]
_COLOR_EN = ["Deep blue", "Warm gold", "Emerald", "Violet",
             "Scarlet", "Silver", "Amber", "Turquoise"]


def _seed_bytes(date: datetime.date, sign_slug: str) -> bytes:
    raw = f"{date.isoformat()}|{sign_slug}".encode("utf-8")
    return hashlib.sha256(raw).digest()


def _pick(pool: list, seed: bytes, offset: int):
    """Deterministically pick one item from a pool using a seed byte."""
    return pool[seed[offset % len(seed)] % len(pool)]


def daily_horoscope(sign_slug: str, date: datetime.date, locale: str = "ru") -> dict:
    """Build a deterministic daily horoscope for a sign + date."""
    locale = "ru" if locale not in ("ru", "en") else locale
    sign = SIGN_BY_SLUG[sign_slug]
    seed = _seed_bytes(date, sign_slug)

    if locale == "ru":
        overall = _pick(_OVERALL_RU, seed, 0)
        love = _pick(_LOVE_RU, seed, 1)
        career = _pick(_CAREER_RU, seed, 2)
        wellbeing = _pick(_WELLBEING_RU, seed, 3)
        mood = _pick(_MOOD_RU, seed, 4)
        color = _pick(_COLOR_RU, seed, 5)
    else:
        overall = _pick(_OVERALL_EN, seed, 0)
        love = _pick(_LOVE_EN, seed, 1)
        career = _pick(_CAREER_EN, seed, 2)
        wellbeing = _pick(_WELLBEING_EN, seed, 3)
        mood = _pick(_MOOD_EN, seed, 4)
        color = _pick(_COLOR_EN, seed, 5)

    lucky_number = (seed[6] % 9) + 1
    # 1..5 "energy" rating from another seed byte.
    energy = (seed[7] % 5) + 1

    return {
        "sign": sign_slug,
        "name_ru": sign["name_ru"],
        "name_en": sign["name_en"],
        "symbol": sign["symbol"],
        "element": sign["element"],
        "element_ru": ELEMENT_LABELS[sign["element"]]["ru"],
        "element_en": ELEMENT_LABELS[sign["element"]]["en"],
        "planet_ru": sign["planet_ru"],
        "planet_en": sign["planet_en"],
        "date": date.isoformat(),
        "locale": locale,
        "overall": overall,
        "love": love,
        "career": career,
        "wellbeing": wellbeing,
        "mood": mood,
        "lucky_color": color,
        "lucky_number": lucky_number,
        "energy": energy,
    }


def list_signs(locale: str = "ru") -> list[dict]:
    locale = "ru" if locale not in ("ru", "en") else locale
    out = []
    for s in SIGNS:
        out.append({
            "slug": s["slug"],
            "name": s["name_ru"] if locale == "ru" else s["name_en"],
            "name_ru": s["name_ru"],
            "name_en": s["name_en"],
            "symbol": s["symbol"],
            "element": s["element"],
            "element_label": ELEMENT_LABELS[s["element"]][locale],
            "planet": s["planet_ru"] if locale == "ru" else s["planet_en"],
            "date_range": _date_range_label(s, locale),
        })
    return out


_MONTHS_RU = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]
_MONTHS_EN = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _date_range_label(sign: dict, locale: str) -> str:
    sm, sd = sign["start"]
    em, ed = sign["end"]
    if locale == "ru":
        return f"{sd} {_MONTHS_RU[sm]} – {ed} {_MONTHS_RU[em]}"
    return f"{_MONTHS_EN[sm]} {sd} – {_MONTHS_EN[em]} {ed}"


def format_horoscope_for_ai(horo: dict, locale: str = "ru") -> str:
    """Turn the structured daily cues into a user message for the AI deep reading."""
    if locale == "ru":
        return (
            f"Знак зодиака: {horo['name_ru']} {horo['symbol']} "
            f"(стихия: {horo['element_ru']}, управитель: {horo['planet_ru']}).\n"
            f"Дата: {horo['date']}.\n"
            f"Настрой дня: {horo['mood']}.\n"
            f"Ключевые мотивы дня (используй как опорные образы, перепиши живо и развёрнуто):\n"
            f"- Общее: {horo['overall']}\n"
            f"- Любовь: {horo['love']}\n"
            f"- Дела и финансы: {horo['career']}\n"
            f"- Самочувствие: {horo['wellbeing']}\n"
            f"Счастливое число: {horo['lucky_number']}, цвет дня: {horo['lucky_color']}.\n\n"
            f"Напиши тёплый, образный гороскоп на день для этого знака."
        )
    return (
        f"Zodiac sign: {horo['name_en']} {horo['symbol']} "
        f"(element: {horo['element_en']}, ruler: {horo['planet_en']}).\n"
        f"Date: {horo['date']}.\n"
        f"Mood of the day: {horo['mood']}.\n"
        f"Key motifs of the day (use them as anchor images, rewrite vividly and at length):\n"
        f"- Overall: {horo['overall']}\n"
        f"- Love: {horo['love']}\n"
        f"- Work & money: {horo['career']}\n"
        f"- Wellbeing: {horo['wellbeing']}\n"
        f"Lucky number: {horo['lucky_number']}, colour of the day: {horo['lucky_color']}.\n\n"
        f"Write a warm, vivid daily horoscope for this sign."
    )
