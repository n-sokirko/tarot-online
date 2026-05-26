"""API tests for Stage 1 — deck, spreads, readings (no AI)."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.tarot.models import Card, SpreadType
from apps.readings.models import Reading, ReadingCard


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_cards(db):
    """Create a minimal deck of 5 cards (enough for a 3-card spread)."""
    cards = []
    for i in range(5):
        cards.append(
            Card.objects.create(
                slug=f'card-{i}',
                suit='major',
                number=i,
                name_ru=f'Карта {i}',
                name_en=f'Card {i}',
                upright_meaning_ru='прямое значение',
                upright_meaning_en='upright meaning',
                reversed_meaning_ru='перевёрнутое значение',
                reversed_meaning_en='reversed meaning',
                keywords_ru=['ключ'],
                keywords_en=['keyword'],
                image_url=f'/cards/card-{i}.jpg',
            )
        )
    return cards


@pytest.fixture
def three_card_spread(db):
    """Create the 'three-card' SpreadType."""
    return SpreadType.objects.create(
        slug='three-card',
        name_ru='Три карты',
        name_en='Three Card',
        positions_count=3,
        positions=[
            {'index': 0, 'label_ru': 'Прошлое', 'label_en': 'Past'},
            {'index': 1, 'label_ru': 'Настоящее', 'label_en': 'Present'},
            {'index': 2, 'label_ru': 'Будущее', 'label_en': 'Future'},
        ],
    )


@pytest.fixture
def nine_card_spread(db):
    """Create the 'nine-card' SpreadType."""
    return SpreadType.objects.create(
        slug='nine-card',
        name_ru='Расклад из 9 карт',
        name_en='Nine-Card Spread',
        positions_count=9,
        positions=[
            {'index': 0, 'label_ru': 'Корни прошлого', 'label_en': 'Roots of Past'},
            {'index': 1, 'label_ru': 'Прошлое', 'label_en': 'Past'},
            {'index': 2, 'label_ru': 'Уходящее', 'label_en': 'Fading'},
            {'index': 3, 'label_ru': 'Скрытое', 'label_en': 'Hidden'},
            {'index': 4, 'label_ru': 'Настоящее', 'label_en': 'Present'},
            {'index': 5, 'label_ru': 'Внешнее', 'label_en': 'External'},
            {'index': 6, 'label_ru': 'Приходящее', 'label_en': 'Arriving'},
            {'index': 7, 'label_ru': 'Будущее', 'label_en': 'Future'},
            {'index': 8, 'label_ru': 'Итог', 'label_en': 'Outcome'},
        ],
    )


@pytest.fixture
def large_deck(db):
    """Create 10 cards — enough for a 9-card spread."""
    cards = []
    for i in range(10):
        cards.append(
            Card.objects.create(
                slug=f'large-card-{i}',
                suit='major',
                number=i,
                name_ru=f'Карта {i}',
                name_en=f'Card {i}',
                upright_meaning_ru='прямое значение',
                upright_meaning_en='upright meaning',
                reversed_meaning_ru='перевёрнутое значение',
                reversed_meaning_en='reversed meaning',
                keywords_ru=['ключ'],
                keywords_en=['keyword'],
                image_url=f'/cards/large-card-{i}.jpg',
            )
        )
    return cards


# ---------------------------------------------------------------------------
# Card list tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCardList:
    def test_returns_200(self, api_client, sample_cards):
        response = api_client.get('/api/v1/cards/')
        assert response.status_code == 200

    def test_returns_all_cards(self, api_client, sample_cards):
        response = api_client.get('/api/v1/cards/')
        assert len(response.data['results']) == len(sample_cards)

    def test_filter_by_suit(self, api_client, sample_cards):
        # Add a non-major card
        Card.objects.create(
            slug='cups-1',
            suit='cups',
            number=1,
            name_ru='Туз Кубков',
            name_en='Ace of Cups',
            upright_meaning_ru='прямое',
            upright_meaning_en='upright',
            reversed_meaning_ru='перевёрнутое',
            reversed_meaning_en='reversed',
            keywords_ru=[],
            keywords_en=[],
            image_url='/cards/cups-1.jpg',
        )
        response = api_client.get('/api/v1/cards/?suit=cups')
        assert response.status_code == 200
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['suit'] == 'cups'

    def test_filter_invalid_suit_returns_400(self, api_client, sample_cards):
        response = api_client.get('/api/v1/cards/?suit=invalid')
        assert response.status_code == 400

    def test_card_fields_present(self, api_client, sample_cards):
        response = api_client.get('/api/v1/cards/')
        card = response.data['results'][0]
        expected_fields = {
            'slug', 'suit', 'number', 'name_ru', 'name_en',
            'keywords_ru', 'keywords_en', 'image_url',
            'upright_meaning_ru', 'upright_meaning_en',
            'reversed_meaning_ru', 'reversed_meaning_en',
        }
        assert expected_fields.issubset(card.keys())


# ---------------------------------------------------------------------------
# Spread detail tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSpreadDetail:
    def test_returns_200_for_three_card(self, api_client, three_card_spread):
        response = api_client.get('/api/v1/spreads/three-card/')
        assert response.status_code == 200

    def test_spread_fields(self, api_client, three_card_spread):
        response = api_client.get('/api/v1/spreads/three-card/')
        data = response.data
        assert data['slug'] == 'three-card'
        assert data['positions_count'] == 3
        assert len(data['positions']) == 3
        assert 'name_ru' in data
        assert 'name_en' in data

    def test_returns_404_for_unknown_slug(self, api_client):
        response = api_client.get('/api/v1/spreads/nonexistent/')
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Create reading tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCreateReading:
    def test_post_creates_reading(self, api_client, sample_cards, three_card_spread):
        payload = {
            'question': 'What does my future hold?',
            'locale': 'en',
            'spread_slug': 'three-card',
        }
        response = api_client.post('/api/v1/readings/', payload, format='json')
        assert response.status_code == 201

    def test_post_creates_correct_number_of_reading_cards(
        self, api_client, sample_cards, three_card_spread
    ):
        payload = {
            'question': 'Что меня ждёт?',
            'locale': 'ru',
            'spread_slug': 'three-card',
        }
        response = api_client.post('/api/v1/readings/', payload, format='json')
        assert response.status_code == 201
        data = response.data
        assert len(data['cards']) == three_card_spread.positions_count
        assert Reading.objects.count() == 1
        assert ReadingCard.objects.count() == three_card_spread.positions_count

    def test_cards_have_distinct_slugs(self, api_client, sample_cards, three_card_spread):
        payload = {'question': 'Q', 'locale': 'en', 'spread_slug': 'three-card'}
        response = api_client.post('/api/v1/readings/', payload, format='json')
        slugs = [c['card']['slug'] for c in response.data['cards']]
        assert len(slugs) == len(set(slugs)), "Each card should appear at most once"

    def test_response_includes_spread_and_cards(
        self, api_client, sample_cards, three_card_spread
    ):
        payload = {'question': 'Q', 'locale': 'en', 'spread_slug': 'three-card'}
        response = api_client.post('/api/v1/readings/', payload, format='json')
        data = response.data
        assert 'id' in data
        assert 'question' in data
        assert 'locale' in data
        assert 'created_at' in data
        assert data['spread_type']['slug'] == 'three-card'

    def test_empty_question_returns_400(self, api_client, three_card_spread):
        payload = {'question': '', 'locale': 'en', 'spread_slug': 'three-card'}
        response = api_client.post('/api/v1/readings/', payload, format='json')
        assert response.status_code == 400

    def test_invalid_locale_returns_400(self, api_client, sample_cards, three_card_spread):
        payload = {'question': 'Q', 'locale': 'de', 'spread_slug': 'three-card'}
        response = api_client.post('/api/v1/readings/', payload, format='json')
        assert response.status_code == 400

    def test_unknown_spread_slug_returns_400(self, api_client, sample_cards):
        payload = {'question': 'Q', 'locale': 'en', 'spread_slug': 'nonexistent'}
        response = api_client.post('/api/v1/readings/', payload, format='json')
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Get reading tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGetReading:
    def _create_reading(self, api_client, sample_cards, three_card_spread):
        payload = {'question': 'Test?', 'locale': 'en', 'spread_slug': 'three-card'}
        response = api_client.post('/api/v1/readings/', payload, format='json')
        assert response.status_code == 201
        return response.data['id']

    def test_get_reading_returns_200(self, api_client, sample_cards, three_card_spread):
        reading_id = self._create_reading(api_client, sample_cards, three_card_spread)
        response = api_client.get(f'/api/v1/readings/{reading_id}/')
        assert response.status_code == 200

    def test_get_reading_returns_full_data(
        self, api_client, sample_cards, three_card_spread
    ):
        reading_id = self._create_reading(api_client, sample_cards, three_card_spread)
        response = api_client.get(f'/api/v1/readings/{reading_id}/')
        data = response.data

        assert data['id'] == reading_id
        assert data['question'] == 'Test?'
        assert data['locale'] == 'en'
        assert data['spread_type']['slug'] == 'three-card'
        assert len(data['cards']) == 3

        card_entry = data['cards'][0]
        assert 'position_index' in card_entry
        assert 'is_reversed' in card_entry
        assert 'card' in card_entry
        assert 'slug' in card_entry['card']

    def test_get_nonexistent_reading_returns_404(self, api_client):
        response = api_client.get('/api/v1/readings/99999/')
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Nine-card spread tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestNineCardReading:
    def test_nine_card_spread_endpoint_returns_201(
        self, api_client, large_deck, nine_card_spread
    ):
        payload = {
            'question': 'What is the full picture?',
            'locale': 'en',
            'spread_slug': 'nine-card',
        }
        response = api_client.post('/api/v1/readings/', payload, format='json')
        assert response.status_code == 201

    def test_nine_card_reading_has_nine_cards(
        self, api_client, large_deck, nine_card_spread
    ):
        payload = {
            'question': 'Покажи полную картину',
            'locale': 'ru',
            'spread_slug': 'nine-card',
        }
        response = api_client.post('/api/v1/readings/', payload, format='json')
        assert response.status_code == 201
        data = response.data
        assert len(data['cards']) == 9
        assert Reading.objects.count() == 1
        assert ReadingCard.objects.count() == 9

    def test_nine_card_reading_spread_type_in_response(
        self, api_client, large_deck, nine_card_spread
    ):
        payload = {'question': 'Q', 'locale': 'en', 'spread_slug': 'nine-card'}
        response = api_client.post('/api/v1/readings/', payload, format='json')
        assert response.status_code == 201
        assert response.data['spread_type']['slug'] == 'nine-card'
        assert response.data['spread_type']['positions_count'] == 9

    def test_nine_card_reading_all_cards_distinct(
        self, api_client, large_deck, nine_card_spread
    ):
        payload = {'question': 'Q', 'locale': 'en', 'spread_slug': 'nine-card'}
        response = api_client.post('/api/v1/readings/', payload, format='json')
        slugs = [c['card']['slug'] for c in response.data['cards']]
        assert len(slugs) == len(set(slugs)), "All 9 cards must be distinct"

    def test_nine_card_reading_position_indices(
        self, api_client, large_deck, nine_card_spread
    ):
        payload = {'question': 'Q', 'locale': 'en', 'spread_slug': 'nine-card'}
        response = api_client.post('/api/v1/readings/', payload, format='json')
        indices = sorted(c['position_index'] for c in response.data['cards'])
        assert indices == list(range(9))

    def test_insufficient_cards_returns_400(
        self, api_client, sample_cards, nine_card_spread
    ):
        """5 cards are not enough for a 9-card spread."""
        payload = {'question': 'Q', 'locale': 'en', 'spread_slug': 'nine-card'}
        response = api_client.post('/api/v1/readings/', payload, format='json')
        assert response.status_code == 400
