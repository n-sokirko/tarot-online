"""Tests for the natal chart API.

Strategy:
- Mock geocoding (Nominatim) to avoid network calls
- Mock chart calculation (calculate_chart) to avoid ephem/pytz overhead
- Test tier gating: free vs premium planets
- Test interpret endpoint entitlement check
"""
from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.billing.models import Entitlement

User = get_user_model()

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_PLANETS_ALL = [
    {"name": "Sun", "sign": "Gemini", "sign_num": 2, "position": 10.0, "abs_pos": 70.0,
     "emoji": "♊", "retrograde": False, "glyph": "☉", "house": 3},
    {"name": "Moon", "sign": "Virgo", "sign_num": 5, "position": 5.0, "abs_pos": 155.0,
     "emoji": "♍", "retrograde": False, "glyph": "☽", "house": 6},
    {"name": "Mercury", "sign": "Gemini", "sign_num": 2, "position": 20.0, "abs_pos": 80.0,
     "emoji": "♊", "retrograde": False, "glyph": "☿", "house": 3},
    {"name": "Venus", "sign": "Cancer", "sign_num": 3, "position": 5.0, "abs_pos": 95.0,
     "emoji": "♋", "retrograde": False, "glyph": "♀", "house": 4},
    {"name": "Mars", "sign": "Aries", "sign_num": 0, "position": 1.0, "abs_pos": 1.0,
     "emoji": "♈", "retrograde": False, "glyph": "♂", "house": 1},
    {"name": "Jupiter", "sign": "Cancer", "sign_num": 3, "position": 28.0, "abs_pos": 118.0,
     "emoji": "♋", "retrograde": False, "glyph": "♃", "house": 4},
    {"name": "Saturn", "sign": "Capricorn", "sign_num": 9, "position": 12.0, "abs_pos": 282.0,
     "emoji": "♑", "retrograde": False, "glyph": "♄", "house": 10},
    {"name": "Uranus", "sign": "Capricorn", "sign_num": 9, "position": 6.0, "abs_pos": 276.0,
     "emoji": "♑", "retrograde": False, "glyph": "♅", "house": 10},
    {"name": "Neptune", "sign": "Capricorn", "sign_num": 9, "position": 14.0, "abs_pos": 284.0,
     "emoji": "♑", "retrograde": False, "glyph": "♆", "house": 10},
    {"name": "True_Node", "sign": "Aquarius", "sign_num": 10, "position": 3.0, "abs_pos": 303.0,
     "emoji": "♒", "retrograde": True, "glyph": "☊", "house": 11},
]

MOCK_HOUSES = [
    {"number": i + 1, "sign": "Aries", "sign_num": 0, "abs_pos": float(i * 30), "emoji": "♈"}
    for i in range(12)
]

MOCK_ASPECTS = [
    {"planet1": "Sun", "planet2": "Mercury", "aspect": "conjunction", "angle": 10.0, "orb": 0.0}
]

MOCK_CHART_RESULT_PREMIUM = {
    "planets": MOCK_PLANETS_ALL,
    "houses": MOCK_HOUSES,
    "aspects": MOCK_ASPECTS,
    "ascendant": 15.0,
}

MOCK_CHART_RESULT_FREE = {
    "planets": [p for p in MOCK_PLANETS_ALL if p["name"] in ("Sun", "Moon")],
    "houses": [],
    "aspects": [],
    "ascendant": None,
}

# geocode_city returns (lat, lng, tz_str)
MOCK_GEOCODE = (55.7558, 37.6176, "Europe/Moscow")


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def premium_user(db):
    user = User.objects.create_user(
        username="premium",
        email="premium@test.com",
        password="pass",
    )
    Entitlement.objects.create(user=user, key="natal_chart")
    Entitlement.objects.create(user=user, key="sonnet_ai")
    return user


@pytest.fixture
def free_user(db):
    return User.objects.create_user(
        username="freeuser",
        email="free@test.com",
        password="pass",
    )


@pytest.fixture
def auth_client_premium(client, premium_user):
    client.force_authenticate(user=premium_user)
    return client


@pytest.fixture
def auth_client_free(client, free_user):
    client.force_authenticate(user=free_user)
    return client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_geocode(city):
    """Side-effect for geocode_city mock."""
    return MOCK_GEOCODE


def _mock_calc_free(**kwargs):
    return MOCK_CHART_RESULT_FREE


def _mock_calc_premium(**kwargs):
    return MOCK_CHART_RESULT_PREMIUM


# ---------------------------------------------------------------------------
# Test: geocoding is called with the city name
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_geocoding_called_with_city(client):
    """POST /natal/charts/ calls geocode_city with the city from the request body."""
    with patch("apps.natal.views.natal_svc.geocode_city", side_effect=_mock_geocode) as mock_geo, \
         patch("apps.natal.views.natal_svc.calculate_chart", return_value=MOCK_CHART_RESULT_FREE):
        resp = client.post("/api/v1/natal/charts/", {
            "birth_date": "1990-06-01",
            "birth_city": "Moscow",
            "locale": "en",
        }, format="json")

    assert resp.status_code == 201, resp.data
    mock_geo.assert_called_once_with("Moscow")


# ---------------------------------------------------------------------------
# Test: free tier returns only Sun and Moon
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_free_tier_returns_only_big_3(client):
    """Anonymous user: planets list should contain only Sun and Moon."""
    with patch("apps.natal.views.natal_svc.geocode_city", return_value=MOCK_GEOCODE), \
         patch("apps.natal.views.natal_svc.calculate_chart", return_value=MOCK_CHART_RESULT_FREE):
        resp = client.post("/api/v1/natal/charts/", {
            "birth_date": "1990-06-01",
            "birth_city": "Moscow",
            "locale": "en",
        }, format="json")

    assert resp.status_code == 201, resp.data
    planet_names = {p["name"] for p in resp.data["planets"]}
    assert planet_names == {"Sun", "Moon"}
    assert resp.data["houses"] == []
    assert resp.data["aspects"] == []


# ---------------------------------------------------------------------------
# Test: premium tier returns all planets
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_premium_tier_returns_all_planets(auth_client_premium):
    """Premium user (has natal_chart entitlement): all 10 planets returned."""
    with patch("apps.natal.views.natal_svc.geocode_city", return_value=MOCK_GEOCODE), \
         patch("apps.natal.views.natal_svc.calculate_chart", return_value=MOCK_CHART_RESULT_PREMIUM):
        resp = auth_client_premium.post("/api/v1/natal/charts/", {
            "birth_date": "1990-06-01",
            "birth_city": "Moscow",
            "locale": "en",
        }, format="json")

    assert resp.status_code == 201, resp.data
    planet_names = {p["name"] for p in resp.data["planets"]}
    assert "Mercury" in planet_names
    assert "Saturn" in planet_names
    assert "True_Node" in planet_names
    assert len(resp.data["houses"]) == 12
    assert len(resp.data["aspects"]) >= 1


# ---------------------------------------------------------------------------
# Test: retrieve saved chart (GET)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_retrieve_chart(client):
    """GET /natal/charts/{id}/ returns the saved chart."""
    with patch("apps.natal.views.natal_svc.geocode_city", return_value=MOCK_GEOCODE), \
         patch("apps.natal.views.natal_svc.calculate_chart", return_value=MOCK_CHART_RESULT_FREE):
        create_resp = client.post("/api/v1/natal/charts/", {
            "birth_date": "1990-06-01",
            "birth_city": "Moscow",
            "locale": "ru",
        }, format="json")

    chart_id = create_resp.data["id"]
    get_resp = client.get(f"/api/v1/natal/charts/{chart_id}/")
    assert get_resp.status_code == 200
    assert get_resp.data["id"] == chart_id
    assert get_resp.data["birth_city"] == "Moscow"


# ---------------------------------------------------------------------------
# Test: interpret requires natal_chart entitlement
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_interpret_requires_entitlement(auth_client_free, free_user):
    """Free user attempting to interpret a natal chart gets 403."""
    with patch("apps.natal.views.natal_svc.geocode_city", return_value=MOCK_GEOCODE), \
         patch("apps.natal.views.natal_svc.calculate_chart", return_value=MOCK_CHART_RESULT_FREE):
        create_resp = auth_client_free.post("/api/v1/natal/charts/", {
            "birth_date": "1990-06-01",
            "birth_city": "Moscow",
            "locale": "ru",
        }, format="json")

    chart_id = create_resp.data["id"]
    interp_resp = auth_client_free.post(f"/api/v1/natal/charts/{chart_id}/interpret/")
    assert interp_resp.status_code == 403
    assert interp_resp.data["required_entitlement"] == "natal_chart"


# ---------------------------------------------------------------------------
# Test: interpret with valid entitlement calls AI and returns body
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_interpret_with_entitlement(auth_client_premium, premium_user):
    """Premium user (natal_chart entitlement) can get AI interpretation."""
    from dataclasses import dataclass

    @dataclass
    class FakeResult:
        body: str = "The stars speak of great potential..."
        model: str = "claude-haiku-test"
        input_tokens: int = 100
        output_tokens: int = 200

    with patch("apps.natal.views.natal_svc.geocode_city", return_value=MOCK_GEOCODE), \
         patch("apps.natal.views.natal_svc.calculate_chart", return_value=MOCK_CHART_RESULT_PREMIUM):
        create_resp = auth_client_premium.post("/api/v1/natal/charts/", {
            "birth_date": "1990-06-01",
            "birth_city": "Moscow",
            "locale": "en",
        }, format="json")

    chart_id = create_resp.data["id"]

    with patch("apps.natal.views.ai_client.generate_interpretation", return_value=FakeResult()), \
         patch("apps.natal.views.ai_prompts.base_system", return_value="base"), \
         patch("apps.natal.views.ai_prompts.natal_chart", return_value="natal"), \
         patch("apps.natal.views.billing.charge_credits", return_value=(True, 47)):
        interp_resp = auth_client_premium.post(f"/api/v1/natal/charts/{chart_id}/interpret/")

    assert interp_resp.status_code == 201, interp_resp.data
    assert "body_md" in interp_resp.data
    assert "The stars speak" in interp_resp.data["body_md"]


# ---------------------------------------------------------------------------
# Test: interpret is idempotent
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_interpret_idempotent(auth_client_premium):
    """Calling interpret twice returns the same interpretation without re-generating."""
    from dataclasses import dataclass

    @dataclass
    class FakeResult:
        body: str = "Second call would be a waste."
        model: str = "claude-haiku-test"
        input_tokens: int = 10
        output_tokens: int = 20

    with patch("apps.natal.views.natal_svc.geocode_city", return_value=MOCK_GEOCODE), \
         patch("apps.natal.views.natal_svc.calculate_chart", return_value=MOCK_CHART_RESULT_PREMIUM):
        create_resp = auth_client_premium.post("/api/v1/natal/charts/", {
            "birth_date": "1990-06-01",
            "birth_city": "Moscow",
            "locale": "en",
        }, format="json")

    chart_id = create_resp.data["id"]

    mock_gen = MagicMock(return_value=FakeResult())

    with patch("apps.natal.views.ai_client.generate_interpretation", mock_gen), \
         patch("apps.natal.views.ai_prompts.base_system", return_value="base"), \
         patch("apps.natal.views.ai_prompts.natal_chart", return_value="natal"), \
         patch("apps.natal.views.billing.charge_credits", return_value=(True, 47)):
        r1 = auth_client_premium.post(f"/api/v1/natal/charts/{chart_id}/interpret/")
        r2 = auth_client_premium.post(f"/api/v1/natal/charts/{chart_id}/interpret/")

    assert r1.status_code == 201
    assert r2.status_code == 200  # already exists → 200
    # AI was only called once
    assert mock_gen.call_count == 1
    assert r1.data["body_md"] == r2.data["body_md"]


# ---------------------------------------------------------------------------
# Test: city not found returns 400
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_city_not_found(client):
    """If geocoding fails, the view returns 400 with city_not_found detail."""
    from apps.natal.services import GeocodingError

    with patch("apps.natal.views.natal_svc.geocode_city", side_effect=GeocodingError("not found")):
        resp = client.post("/api/v1/natal/charts/", {
            "birth_date": "1990-06-01",
            "birth_city": "XxNonexistentCityXx",
            "locale": "en",
        }, format="json")

    assert resp.status_code == 400
    assert resp.data["detail"] == "city_not_found"


# ---------------------------------------------------------------------------
# Test: services.geocode_city returns correct 3-tuple structure
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_geocode_city_returns_tuple():
    """Unit test: geocode_city returns correct (lat, lng, tz) 3-tuple structure.

    Nominatim and TimezoneFinder are lazy-imported inside geocode_city, so we
    patch them in their source modules.
    """
    with patch("geopy.geocoders.Nominatim") as MockNom, \
         patch("timezonefinder.TimezoneFinder") as MockTF:
        # Configure Nominatim mock
        mock_loc = MagicMock()
        mock_loc.latitude = 55.7558
        mock_loc.longitude = 37.6176
        MockNom.return_value.geocode.return_value = mock_loc

        # Configure TimezoneFinder mock
        MockTF.return_value.timezone_at.return_value = "Europe/Moscow"

        from apps.natal.services import geocode_city
        lat, lng, tz = geocode_city("Moscow")

    assert abs(lat - 55.7558) < 0.01
    assert abs(lng - 37.6176) < 0.01
    assert tz == "Europe/Moscow"
