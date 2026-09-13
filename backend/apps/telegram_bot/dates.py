"""Pure date helpers for the bot — no telegram/Django imports, so unit-testable
without the bot stack installed."""
import datetime

# Birth-date input formats accepted from users. Day-first first (RU/EU convention),
# ISO last. Two-digit year is a fallback after the 4-digit variants.
_BIRTH_FORMATS = ('%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y', '%d %m %Y', '%Y-%m-%d', '%d.%m.%y')


def parse_birth_date(text: str) -> datetime.date | None:
    """Parse a user-typed birth date. Returns None if unparseable or out of range
    (before 1900 or in the future)."""
    raw = ' '.join((text or '').split())
    if not raw:
        return None
    for fmt in _BIRTH_FORMATS:
        try:
            d = datetime.datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
        if d.year < 1900 or d > datetime.date.today():
            return None
        return d
    return None
