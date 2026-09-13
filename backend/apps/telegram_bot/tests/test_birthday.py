"""Unit tests for birth-date parsing used by the /birthday flow."""
import datetime

from apps.telegram_bot.dates import parse_birth_date as _parse_birth_date


class TestParseBirthDate:
    def test_dot_format(self):
        assert _parse_birth_date("14.03.1995") == datetime.date(1995, 3, 14)

    def test_slash_format(self):
        assert _parse_birth_date("14/03/1995") == datetime.date(1995, 3, 14)

    def test_dash_format(self):
        assert _parse_birth_date("14-03-1995") == datetime.date(1995, 3, 14)

    def test_iso_format(self):
        assert _parse_birth_date("1995-03-14") == datetime.date(1995, 3, 14)

    def test_space_format(self):
        assert _parse_birth_date("14 03 1995") == datetime.date(1995, 3, 14)

    def test_two_digit_year(self):
        assert _parse_birth_date("14.03.95") == datetime.date(1995, 3, 14)

    def test_surrounding_whitespace(self):
        assert _parse_birth_date("  14.03.1995  ") == datetime.date(1995, 3, 14)

    def test_future_date_rejected(self):
        future = datetime.date.today() + datetime.timedelta(days=1)
        assert _parse_birth_date(future.strftime("%d.%m.%Y")) is None

    def test_year_before_1900_rejected(self):
        assert _parse_birth_date("14.03.1899") is None

    def test_garbage_rejected(self):
        assert _parse_birth_date("hello") is None
        assert _parse_birth_date("") is None
        assert _parse_birth_date("32.13.2000") is None

    def test_empty_and_none(self):
        assert _parse_birth_date(None) is None
