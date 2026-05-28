"""Natal chart computation: geocoding + PyEphem planet calculations.

Uses PyEphem (pre-built binary wheel, no C compiler required) for
astronomical calculations. If kerykeion + pyswisseph become available
in the deployment environment, the calculate_chart function can be
swapped without changing the API surface.

Planet list: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus,
Neptune, True Node (North Node — computed from known regression rate).

House system: Whole Sign Houses (ascendant sign = 1st house,
subsequent signs = subsequent houses). Houses are only computed when
birth_time is known.

Free tier: only Sun, Moon, and Ascendant are returned.
Premium tier: all planets + houses + aspects.

Aspect orbs (major aspects only):
  conjunction   0° ±8°
  sextile      60° ±6°
  square       90° ±7°
  trine        120° ±8°
  opposition   180° ±8°
"""
from __future__ import annotations

import copy
import datetime
import math
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_EMOJIS = [
    "♈", "♉", "♊", "♋",
    "♌", "♍", "♎", "♏",
    "♐", "♑", "♒", "♓",
]

PLANET_GLYPHS: dict[str, str] = {
    "Sun": "☉",
    "Moon": "☽",
    "Mercury": "☿",
    "Venus": "♀",
    "Mars": "♂",
    "Jupiter": "♃",
    "Saturn": "♄",
    "Uranus": "♅",
    "Neptune": "♆",
    "True_Node": "☊",
}

# (aspect_name, exact_angle, max_orb)
MAJOR_ASPECTS = [
    ("conjunction", 0, 8),
    ("sextile", 60, 6),
    ("square", 90, 7),
    ("trine", 120, 8),
    ("opposition", 180, 8),
]

FREE_PLANETS = {"Sun", "Moon"}

# North Node regresses ~0.05295 degrees/day from its J2000 position of 125.04°
_NODE_AT_J2000 = 125.04
_NODE_DAILY_MOTION = 0.05295
_EPHEM_EPOCH_OFFSET = 2415020.0  # ephem Dublin JD → real Julian Date


# ---------------------------------------------------------------------------
# Geocoding helpers
# ---------------------------------------------------------------------------

class GeocodingError(ValueError):
    """Raised when the city cannot be resolved to coordinates."""


def geocode_city(city: str) -> tuple[float, float, str]:
    """Return (lat, lng, tz_str) for a city name.

    Raises GeocodingError if the city cannot be found or timezone unavailable.
    """
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    from timezonefinder import TimezoneFinder

    geolocator = Nominatim(user_agent="tarot_natal/1.0", timeout=10)
    try:
        location = geolocator.geocode(city, exactly_one=True, language="en")
    except (GeocoderTimedOut, GeocoderServiceError) as exc:
        raise GeocodingError(f"Geocoding service error: {exc}") from exc

    if location is None:
        raise GeocodingError(f"City not found: {city!r}")

    lat = float(location.latitude)
    lng = float(location.longitude)

    tf = TimezoneFinder()
    tz = tf.timezone_at(lat=lat, lng=lng)
    if not tz:
        tz = "UTC"

    return lat, lng, tz


# ---------------------------------------------------------------------------
# Astronomical helpers (ephem-based)
# ---------------------------------------------------------------------------

def _ecliptic_lon(body, obs) -> float:
    """Return ecliptic longitude (0–360°) for an ephem body at the given observer."""
    import ephem

    body.compute(obs)
    ecl = ephem.Ecliptic(body, epoch=ephem.J2000)
    return math.degrees(float(ecl.lon)) % 360


def _north_node_lon(ephem_date: float) -> float:
    """Approximate Mean North Node ecliptic longitude from ephem Date value."""
    jd = float(ephem_date) + _EPHEM_EPOCH_OFFSET
    J2000_JD = 2451545.0
    days_from_j2000 = jd - J2000_JD
    lon = (_NODE_AT_J2000 - days_from_j2000 * _NODE_DAILY_MOTION) % 360
    return lon


def _is_retrograde(body_class, obs) -> bool:
    """Detect retrograde by comparing ecliptic longitude today vs tomorrow."""
    import ephem

    obs_next = copy.copy(obs)
    obs_next.date = ephem.Date(obs.date + 1)

    b_now = body_class()
    b_now.compute(obs)
    b_next = body_class()
    b_next.compute(obs_next)

    ecl_now = ephem.Ecliptic(b_now, epoch=ephem.J2000)
    ecl_next = ephem.Ecliptic(b_next, epoch=ephem.J2000)
    lon_now = math.degrees(float(ecl_now.lon)) % 360
    lon_next = math.degrees(float(ecl_next.lon)) % 360

    diff = lon_next - lon_now
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360
    return diff < 0


def _obliquity(year: int) -> float:
    """Mean obliquity of the ecliptic (degrees) for a given year."""
    T = (year - 2000) / 100.0
    return 23.4392911 - 0.013004167 * T


def _compute_ascendant(lst_deg: float, lat_deg: float, obliquity_deg: float) -> float:
    """Compute Ascendant ecliptic longitude (standard astrological formula)."""
    ramc = math.radians(lst_deg)
    lat = math.radians(lat_deg)
    obl = math.radians(obliquity_deg)

    x = -math.cos(ramc)
    y = math.sin(ramc) * math.cos(obl) + math.tan(lat) * math.sin(obl)
    asc = math.degrees(math.atan2(x, y))

    if math.sin(ramc) < 0:
        asc = (asc + 360) % 360
    else:
        asc = (asc + 180) % 360

    return asc % 360


def _whole_sign_houses(ascendant_deg: float) -> list[dict]:
    """Return 12 whole-sign house cusp dicts."""
    asc_sign_num = int(ascendant_deg / 30)
    houses = []
    for i in range(12):
        sign_num = (asc_sign_num + i) % 12
        houses.append({
            "number": i + 1,
            "sign": SIGNS[sign_num],
            "sign_num": sign_num,
            "abs_pos": float(sign_num * 30),
            "emoji": SIGN_EMOJIS[sign_num],
        })
    return houses


def _planet_house(planet_abs_pos: float, houses: list[dict]) -> int:
    """Return 1-indexed house number for a planet ecliptic longitude."""
    if not houses:
        return 0
    for i in range(len(houses) - 1, -1, -1):
        if planet_abs_pos >= houses[i]["abs_pos"]:
            return houses[i]["number"]
    return houses[-1]["number"]


def _compute_aspects(planets: list[dict]) -> list[dict]:
    """Compute major aspects between all planet pairs."""
    aspects = []
    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            planet_a = planets[i]
            planet_b = planets[j]
            diff = abs(planet_a["abs_pos"] - planet_b["abs_pos"])
            if diff > 180:
                diff = 360 - diff
            for asp_name, asp_angle, asp_orb in MAJOR_ASPECTS:
                if abs(diff - asp_angle) <= asp_orb:
                    aspects.append({
                        "planet1": planet_a["name"],
                        "planet2": planet_b["name"],
                        "aspect": asp_name,
                        "angle": round(diff, 2),
                        "orb": round(abs(diff - asp_angle), 2),
                    })
                    break
    return aspects


# ---------------------------------------------------------------------------
# Main chart calculator
# ---------------------------------------------------------------------------

_PLANET_BODIES = [
    ("Sun", "Sun"),
    ("Moon", "Moon"),
    ("Mercury", "Mercury"),
    ("Venus", "Venus"),
    ("Mars", "Mars"),
    ("Jupiter", "Jupiter"),
    ("Saturn", "Saturn"),
    ("Uranus", "Uranus"),
    ("Neptune", "Neptune"),
]


def calculate_chart(
    *,
    birth_date: datetime.date,
    birth_time: Optional[datetime.time],
    lat: float,
    lng: float,
    tz_str: str,
    name: str = "",
    is_premium: bool = False,
) -> dict:
    """Calculate natal chart using PyEphem.

    Returns dict with keys: planets, houses, aspects, ascendant.
    When is_premium is False, only Sun and Moon are included in planets;
    houses and aspects are empty lists.
    """
    import ephem
    from zoneinfo import ZoneInfo

    has_time = birth_time is not None

    # Convert local birth time to UTC using stdlib zoneinfo (Python 3.9+)
    if has_time:
        local_dt = datetime.datetime(
            birth_date.year, birth_date.month, birth_date.day,
            birth_time.hour, birth_time.minute,
            getattr(birth_time, "second", 0),
            tzinfo=ZoneInfo(tz_str),
        )
    else:
        local_dt = datetime.datetime(
            birth_date.year, birth_date.month, birth_date.day, 12, 0, 0,
            tzinfo=ZoneInfo(tz_str),
        )

    utc_dt = local_dt.astimezone(datetime.timezone.utc)
    ephem_date_str = utc_dt.strftime("%Y/%m/%d %H:%M:%S")

    obs = ephem.Observer()
    obs.lat = str(lat)
    obs.lon = str(lng)
    obs.elevation = 0
    obs.epoch = ephem.J2000
    obs.date = ephem_date_str
    obs.pressure = 0  # skip atmospheric refraction

    obliquity = _obliquity(birth_date.year)

    # --- Planets ---
    all_planets: list[dict] = []
    for planet_name, ephem_class_name in _PLANET_BODIES:
        body_class = getattr(ephem, ephem_class_name)
        body = body_class()
        body.compute(obs)
        ecl = ephem.Ecliptic(body, epoch=ephem.J2000)
        abs_pos = math.degrees(float(ecl.lon)) % 360
        sign_num = int(abs_pos / 30)
        position = abs_pos - sign_num * 30

        retro = _is_retrograde(body_class, obs) if planet_name not in ("Sun", "Moon") else False

        all_planets.append({
            "name": planet_name,
            "sign": SIGNS[sign_num],
            "sign_num": sign_num,
            "position": round(position, 4),
            "abs_pos": round(abs_pos, 4),
            "emoji": SIGN_EMOJIS[sign_num],
            "retrograde": retro,
            "glyph": PLANET_GLYPHS.get(planet_name, ""),
            "house": 0,
        })

    # North Node
    node_abs = _north_node_lon(float(obs.date))
    node_sign_num = int(node_abs / 30)
    all_planets.append({
        "name": "True_Node",
        "sign": SIGNS[node_sign_num],
        "sign_num": node_sign_num,
        "position": round(node_abs - node_sign_num * 30, 4),
        "abs_pos": round(node_abs, 4),
        "emoji": SIGN_EMOJIS[node_sign_num],
        "retrograde": True,
        "glyph": PLANET_GLYPHS["True_Node"],
        "house": 0,
    })

    # --- Ascendant & houses ---
    ascendant: Optional[float] = None
    houses: list[dict] = []

    if has_time:
        lst_deg = math.degrees(float(obs.sidereal_time())) % 360
        ascendant = round(_compute_ascendant(lst_deg, lat, obliquity), 4)
        if is_premium:
            houses = _whole_sign_houses(ascendant)
            for p in all_planets:
                p["house"] = _planet_house(p["abs_pos"], houses)

    # --- Filter planets by tier ---
    if is_premium:
        planets = all_planets
    else:
        # Free tier: Sun, Moon + Ascendant sign (no planets filtered here,
        # caller passes is_premium=False to get only the Big 3)
        planets = [p for p in all_planets if p["name"] in FREE_PLANETS]
        # Ascendant is always included when available (it's just a float, not a planet)

    # --- Aspects (premium only) ---
    aspects: list[dict] = []
    if is_premium:
        aspects = _compute_aspects(all_planets)

    return {
        "planets": planets,
        "houses": houses,
        "aspects": aspects,
        "ascendant": ascendant,
    }


# ---------------------------------------------------------------------------
# AI prompt formatting
# ---------------------------------------------------------------------------

def format_chart_for_ai(chart, locale: str) -> str:
    """Build the user-message string for the AI interpretation prompt."""
    planets = chart.planets
    houses = chart.houses
    aspects = chart.aspects
    ascendant = chart.ascendant

    lines: list[str] = []

    if locale == "ru":
        lines.append(f"Натальная карта: {chart.birth_name or chart.birth_city}")
        lines.append(f"Дата рождения: {chart.birth_date}")
        if chart.birth_time:
            lines.append(f"Время рождения: {chart.birth_time}")
        lines.append(f"Место: {chart.birth_city}")
        if ascendant is not None:
            asc_sign_num = int(ascendant / 30)
            lines.append(f"Асцендент: {SIGNS[asc_sign_num]} {ascendant:.1f}°")
        lines.append("")
        lines.append("Планеты:")
        for p in planets:
            retro = " (ретро)" if p.get("retrograde") else ""
            house = f", дом {p['house']}" if p.get("house") else ""
            lines.append(f"  {p['glyph']} {p['name']}: {p['sign']} {p['position']:.1f}°{house}{retro}")
        if houses:
            lines.append("")
            lines.append("Дома:")
            for h in houses:
                lines.append(f"  Дом {h['number']}: {h['sign']} {h['abs_pos']:.1f}°")
        if aspects:
            lines.append("")
            lines.append("Аспекты:")
            for a in aspects:
                lines.append(f"  {a['planet1']} {a['aspect']} {a['planet2']} (орб {a['orb']:.1f}°)")
        lines.append("")
        lines.append("Напиши глубокую натальную интерпретацию по правилам системного промпта.")
    else:
        lines.append(f"Natal chart: {chart.birth_name or chart.birth_city}")
        lines.append(f"Birth date: {chart.birth_date}")
        if chart.birth_time:
            lines.append(f"Birth time: {chart.birth_time}")
        lines.append(f"Place: {chart.birth_city}")
        if ascendant is not None:
            asc_sign_num = int(ascendant / 30)
            lines.append(f"Ascendant: {SIGNS[asc_sign_num]} {ascendant:.1f}°")
        lines.append("")
        lines.append("Planets:")
        for p in planets:
            retro = " (retrograde)" if p.get("retrograde") else ""
            house = f", house {p['house']}" if p.get("house") else ""
            lines.append(f"  {p['glyph']} {p['name']}: {p['sign']} {p['position']:.1f}°{house}{retro}")
        if houses:
            lines.append("")
            lines.append("Houses:")
            for h in houses:
                lines.append(f"  House {h['number']}: {h['sign']} {h['abs_pos']:.1f}°")
        if aspects:
            lines.append("")
            lines.append("Aspects:")
            for a in aspects:
                lines.append(f"  {a['planet1']} {a['aspect']} {a['planet2']} (orb {a['orb']:.1f}°)")
        lines.append("")
        lines.append("Write a deep natal interpretation following the rules of the system prompt.")

    return "\n".join(lines)
