"""AI interpretation endpoint — uses mocked Anthropic SDK to avoid network."""
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.billing.models import CreditWallet, Entitlement, UsageLedger
from apps.tarot.models import Card, SpreadType
from apps.readings.models import Interpretation, Reading


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(django_user_model, db):
    return django_user_model.objects.create_user(
        username='carol', email='carol@example.com', password='pw',
    )


@pytest.fixture
def deck(db):
    return [
        Card.objects.create(
            slug=f'c-{i}', suit='major', number=i,
            name_ru=f'К{i}', name_en=f'C{i}',
            upright_meaning_ru='значение', upright_meaning_en='meaning',
            reversed_meaning_ru='перев', reversed_meaning_en='rev',
            keywords_ru=['k'], keywords_en=['k'],
            image_url=f'/c{i}.jpg',
        ) for i in range(5)
    ]


@pytest.fixture
def three_card_spread(db):
    return SpreadType.objects.create(
        slug='three-card', name_ru='Три', name_en='Three',
        positions_count=3,
        positions=[
            {'index': 0, 'label_ru': 'Прошлое', 'label_en': 'Past'},
            {'index': 1, 'label_ru': 'Настоящее', 'label_en': 'Present'},
            {'index': 2, 'label_ru': 'Будущее', 'label_en': 'Future'},
        ],
    )


def _mock_result():
    from services.ai.client import GenerationResult
    return GenerationResult(
        body='Интерпретация: **Карта** говорит...',
        model='claude-haiku-4-5-20251001',
        input_tokens=120,
        output_tokens=80,
    )


@pytest.mark.django_db
class TestInterpret:
    def _new_reading(self, client, deck, spread):
        res = client.post('/api/v1/readings/', {
            'question': 'Что делать?',
            'locale': 'ru',
            'spread_slug': 'three-card',
        }, format='json')
        assert res.status_code == 201
        return res.data['id']

    def test_anonymous_free_tier_gets_interpretation(self, api_client, deck, three_card_spread):
        rid = self._new_reading(api_client, deck, three_card_spread)
        with patch('apps.readings.views.ai_client.generate_interpretation',
                   return_value=_mock_result()) as mock_gen:
            res = api_client.post(f'/api/v1/readings/{rid}/interpret/')

        assert res.status_code == 201, res.content
        assert 'body_md' in res.data
        assert mock_gen.called
        # Anonymous → free model
        kwargs = mock_gen.call_args.kwargs
        assert 'haiku' in kwargs['model'].lower()

    def test_premium_user_uses_sonnet(self, api_client, deck, three_card_spread, user):
        Entitlement.objects.create(user=user, key='sonnet_ai')
        CreditWallet.objects.create(user=user, balance=10)
        api_client.force_authenticate(user=user)

        rid = self._new_reading(api_client, deck, three_card_spread)
        with patch('apps.readings.views.ai_client.generate_interpretation',
                   return_value=_mock_result()) as mock_gen:
            res = api_client.post(f'/api/v1/readings/{rid}/interpret/')

        assert res.status_code == 201
        assert 'sonnet' in mock_gen.call_args.kwargs['model'].lower()
        # Credits debited.
        assert CreditWallet.objects.get(user=user).balance == 9
        assert UsageLedger.objects.filter(user=user, kind=UsageLedger.KIND_AI_TAROT).exists()

    def test_empty_question_returns_400(self, api_client, deck, three_card_spread):
        """Interpret without a question is rejected to save API tokens."""
        res = api_client.post('/api/v1/readings/', {
            'question': '',
            'locale': 'ru',
            'spread_slug': 'three-card',
        }, format='json')
        rid = res.data['id']
        res = api_client.post(f'/api/v1/readings/{rid}/interpret/', {}, format='json')
        assert res.status_code == 400
        assert res.data['detail'] == 'question_required'

    def test_question_passed_to_reading_before_interpret(self, api_client, deck, three_card_spread):
        """The interpret endpoint saves the user question before building the prompt."""
        rid = self._new_reading(api_client, deck, three_card_spread)
        with patch('apps.readings.views.ai_client.generate_interpretation',
                   return_value=_mock_result()) as mock_gen:
            res = api_client.post(
                f'/api/v1/readings/{rid}/interpret/',
                {'question': 'Меня бросила девушка, что мне делать?'},
                format='json',
            )
        assert res.status_code == 201
        reading = Reading.objects.get(pk=rid)
        assert 'бросила' in reading.question
        # The user message passed to AI should include the question.
        user_msg = mock_gen.call_args.kwargs['user_message']
        assert 'бросила' in user_msg

    def test_idempotent_returns_existing(self, api_client, deck, three_card_spread):
        rid = self._new_reading(api_client, deck, three_card_spread)
        with patch('apps.readings.views.ai_client.generate_interpretation',
                   return_value=_mock_result()) as mock_gen:
            api_client.post(f'/api/v1/readings/{rid}/interpret/')
            api_client.post(f'/api/v1/readings/{rid}/interpret/')
        assert mock_gen.call_count == 1
        assert Interpretation.objects.filter(reading_id=rid).count() == 1

    @pytest.mark.skip(reason='Django debug template renderer is incompatible with Python 3.14 (Context.__copy__).')
    def test_no_anthropic_key_returns_503(self, api_client, deck, three_card_spread):
        rid = self._new_reading(api_client, deck, three_card_spread)
        with patch('apps.readings.views.ai_client.generate_interpretation',
                   side_effect=RuntimeError('ANTHROPIC_API_KEY not set')):
            res = api_client.post(f'/api/v1/readings/{rid}/interpret/')
        assert res.status_code == 503
