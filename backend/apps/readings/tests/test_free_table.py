"""Free table: the person pulls cards from the deck and arranges them freely."""
import pytest
from rest_framework.test import APIClient

from apps.readings.models import Reading, ReadingCard
from apps.readings.views import ReadingViewSet, _format_user_message
from apps.tarot.models import Card, SpreadType

TABLE = '/api/v1/readings/table/'


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def deck(db):
    return [
        Card.objects.create(
            slug=f'ft-{i}', suit='major', number=i,
            name_ru=f'Карта {i}', name_en=f'Card {i}',
            upright_meaning_ru='прямое значение', upright_meaning_en='upright meaning',
            reversed_meaning_ru='перевёрнутое значение', reversed_meaning_en='reversed meaning',
            keywords_ru=['ключ'], keywords_en=['key'],
            image_url=f'/ft{i}.jpg',
        ) for i in range(15)
    ]


@pytest.fixture
def free_table(db):
    return SpreadType.objects.create(
        slug='free-table', name_ru='Свободный стол', name_en='Free table',
        positions_count=0, positions=[],
    )


@pytest.fixture
def three_card(db):
    return SpreadType.objects.create(
        slug='three-card', name_ru='Три карты', name_en='Three cards',
        positions_count=3,
        positions=[{'index': i, 'label_ru': f'П{i}', 'label_en': f'P{i}'} for i in range(3)],
    )


@pytest.mark.django_db
class TestOpenTable:
    def test_opens_empty(self, api_client, free_table, deck):
        resp = api_client.post(TABLE, {'locale': 'ru'}, format='json')
        assert resp.status_code == 201
        body = resp.json()
        assert body['spread_type']['slug'] == 'free-table'
        assert body['cards'] == []

    def test_rejects_bad_locale(self, api_client, free_table):
        assert api_client.post(TABLE, {'locale': 'xx'}, format='json').status_code == 400

    def test_reports_missing_spread_instead_of_500(self, api_client, deck):
        """Deploying before the seed ran should say so, not blow up."""
        resp = api_client.post(TABLE, {'locale': 'ru'}, format='json')
        assert resp.status_code == 503


@pytest.mark.django_db
class TestDraw:
    def _open(self, api_client):
        return api_client.post(TABLE, {'locale': 'ru'}, format='json').json()['id']

    def test_draw_places_a_card_where_asked(self, api_client, free_table, deck):
        rid = self._open(api_client)
        resp = api_client.post(f'/api/v1/readings/{rid}/draw/',
                               {'x': 0.2, 'y': 0.8}, format='json')
        assert resp.status_code == 201
        body = resp.json()
        assert body['position_index'] == 0
        assert body['x'] == pytest.approx(0.2)
        assert body['y'] == pytest.approx(0.8)
        assert body['card']['name_ru'].startswith('Карта')

    def test_position_index_counts_up(self, api_client, free_table, deck):
        rid = self._open(api_client)
        for expected in range(3):
            resp = api_client.post(f'/api/v1/readings/{rid}/draw/', {}, format='json')
            assert resp.json()['position_index'] == expected

    def test_never_draws_the_same_card_twice(self, api_client, free_table, deck):
        rid = self._open(api_client)
        seen = set()
        for _ in range(ReadingViewSet.MAX_TABLE_CARDS):
            seen.add(api_client.post(f'/api/v1/readings/{rid}/draw/', {}, format='json')
                     .json()['card']['slug'])
        assert len(seen) == ReadingViewSet.MAX_TABLE_CARDS

    def test_table_fills_up(self, api_client, free_table, deck):
        rid = self._open(api_client)
        for _ in range(ReadingViewSet.MAX_TABLE_CARDS):
            api_client.post(f'/api/v1/readings/{rid}/draw/', {}, format='json')
        resp = api_client.post(f'/api/v1/readings/{rid}/draw/', {}, format='json')
        assert resp.status_code == 409
        assert resp.json()['detail'] == 'table_full'

    def test_coordinates_are_clamped(self, api_client, free_table, deck):
        """A dragged card can overshoot the surface; it must not be stored outside it."""
        rid = self._open(api_client)
        body = api_client.post(f'/api/v1/readings/{rid}/draw/',
                               {'x': 5, 'y': -3}, format='json').json()
        assert body['x'] == 1.0
        assert body['y'] == 0.0

    def test_garbage_coordinates_fall_back_to_centre(self, api_client, free_table, deck):
        rid = self._open(api_client)
        body = api_client.post(f'/api/v1/readings/{rid}/draw/',
                               {'x': 'nope', 'y': None}, format='json').json()
        assert body['x'] == 0.5 and body['y'] == 0.5

    def test_fixed_spreads_cannot_be_drawn_onto(self, api_client, three_card, deck):
        reading = api_client.post('/api/v1/readings/',
                                  {'locale': 'ru', 'spread_slug': 'three-card', 'question': ''},
                                  format='json').json()
        resp = api_client.post(f"/api/v1/readings/{reading['id']}/draw/", {}, format='json')
        assert resp.status_code == 400
        assert resp.json()['detail'] == 'not_a_free_table'


@pytest.mark.django_db
class TestLayout:
    def test_moving_cards_is_persisted(self, api_client, free_table, deck):
        rid = api_client.post(TABLE, {'locale': 'ru'}, format='json').json()['id']
        api_client.post(f'/api/v1/readings/{rid}/draw/', {'x': 0.1, 'y': 0.1}, format='json')
        api_client.post(f'/api/v1/readings/{rid}/draw/', {'x': 0.2, 'y': 0.2}, format='json')

        resp = api_client.patch(
            f'/api/v1/readings/{rid}/layout/',
            {'cards': [{'position_index': 1, 'x': 0.9, 'y': 0.4, 'is_reversed': True}]},
            format='json',
        )
        assert resp.status_code == 200
        moved = ReadingCard.objects.get(reading_id=rid, position_index=1)
        assert (moved.x, moved.y, moved.is_reversed) == (0.9, 0.4, True)
        untouched = ReadingCard.objects.get(reading_id=rid, position_index=0)
        assert (untouched.x, untouched.y) == (0.1, 0.1)

    def test_unknown_positions_are_ignored(self, api_client, free_table, deck):
        rid = api_client.post(TABLE, {'locale': 'ru'}, format='json').json()['id']
        api_client.post(f'/api/v1/readings/{rid}/draw/', {}, format='json')
        resp = api_client.patch(
            f'/api/v1/readings/{rid}/layout/',
            {'cards': [{'position_index': 99, 'x': 0.1, 'y': 0.1}]},
            format='json',
        )
        assert resp.status_code == 200

    def test_cards_must_be_a_list(self, api_client, free_table, deck):
        rid = api_client.post(TABLE, {'locale': 'ru'}, format='json').json()['id']
        assert api_client.patch(f'/api/v1/readings/{rid}/layout/',
                                {'cards': 'nope'}, format='json').status_code == 400


@pytest.mark.django_db
class TestPrompt:
    def test_free_table_describes_the_arrangement(self, free_table, deck):
        reading = Reading.objects.create(spread_type=free_table, question='', locale='ru')
        ReadingCard.objects.create(reading=reading, card=deck[0], position_index=0,
                                   x=0.1, y=0.1)
        ReadingCard.objects.create(reading=reading, card=deck[1], position_index=1,
                                   x=0.9, y=0.9)
        msg = _format_user_message(reading)
        assert 'Позиций нет' in msg
        assert 'вверху, слева' in msg
        assert 'внизу, справа' in msg

    def test_reversed_card_sends_its_reversed_meaning(self, free_table, deck):
        """The person turned the card on purpose — sending the upright text would
        silently discard that choice."""
        reading = Reading.objects.create(spread_type=free_table, question='', locale='ru')
        ReadingCard.objects.create(reading=reading, card=deck[0], position_index=0,
                                   is_reversed=True)
        msg = _format_user_message(reading)
        assert 'перевёрнутое значение' in msg
        assert 'перевёрнута' in msg

    def test_fixed_spread_still_uses_its_position_labels(self, three_card, deck):
        reading = Reading.objects.create(spread_type=three_card, question='', locale='ru')
        for i in range(3):
            ReadingCard.objects.create(reading=reading, card=deck[i], position_index=i)
        msg = _format_user_message(reading)
        assert 'П0' in msg and 'Позиций нет' not in msg
