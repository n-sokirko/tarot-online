"""Personal tarologist: persona gating, memory, dossier and the hidden tail."""
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.billing.models import CreditWallet, Entitlement
from apps.readings import personalization
from apps.readings.models import Interpretation, Reading, TarotProfile
from services.ai.client import GenerationResult

TAIL = ('Скорее нет: Луна держит туман.\n\n'
        '<memo>Дима · Луна, 5 Кубков, Звезда → ждать не стоит</memo>\n'
        '<dossier>\n- Аня, Рыбы\n- Дима — бывший\n</dossier>')


def _result(body=TAIL):
    return GenerationResult(body=body, model='claude-sonnet-4-6', input_tokens=10, output_tokens=10)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(django_user_model, db):
    return django_user_model.objects.create_user(username='ann', email='ann@example.com', password='pw')


@pytest.fixture
def premium(user):
    Entitlement.objects.create(user=user, key='sonnet_ai')
    CreditWallet.objects.create(user=user, balance=20)
    return user


def _reading(client, question='Напишет ли Дима?'):
    res = client.post('/api/v1/readings/', {'question': question, 'locale': 'ru',
                                            'spread_slug': 'three-card'}, format='json')
    assert res.status_code == 201, res.content
    return res.data['id']


class TestTail:
    def test_parse_tail_strips_memo_and_dossier(self):
        body, memo, dossier = personalization.parse_tail(TAIL)
        assert body == 'Скорее нет: Луна держит туман.'
        assert memo.startswith('Дима')
        assert dossier == ['Аня, Рыбы', 'Дима — бывший']

    def test_parse_tail_without_tags(self):
        assert personalization.parse_tail('Просто текст') == ('Просто текст', '', None)

    def test_stream_filter_hides_tail_split_across_chunks(self):
        f = personalization.TailFilter()
        chunks = ['Скорее нет. 2 < 3, ', 'и всё.\n<me', 'mo>секрет</memo>\n<dossier>- x</dossier>']
        out = ''.join(f.feed(c) for c in chunks) + f.flush()
        assert out == 'Скорее нет. 2 < 3, и всё.\n'

    def test_clean_dossier_caps_and_dedupes(self):
        items = ['- a', 'a', '', 5, 'x' * 500] + [f'i{n}' for n in range(20)]
        out = personalization.clean_dossier(items)
        assert out[0] == 'a' and len(out[1]) == TarotProfile.DOSSIER_MAX_LEN
        assert len(out) == TarotProfile.DOSSIER_MAX_ITEMS


@pytest.mark.django_db
class TestInterpretWithPersonalization:
    def test_free_user_gets_memo_but_no_dossier_or_persona(self, api_client, user, deck, three_card_spread):
        CreditWallet.objects.create(user=user, balance=5)
        api_client.force_authenticate(user=user)
        rid = _reading(api_client)
        with patch('apps.readings.views.ai_client.generate_interpretation', return_value=_result()) as gen:
            res = api_client.post(f'/api/v1/readings/{rid}/interpret/')
        assert res.status_code == 201, res.content
        kw = gen.call_args.kwargs
        assert '<memo>' in kw['extra_system_prompt'] and '<dossier>' not in kw['extra_system_prompt']
        assert 'haiku' in kw['model']
        assert res.data['body_md'] == 'Скорее нет: Луна держит туман.'
        assert Interpretation.objects.get(reading_id=rid).memo.startswith('Дима')
        assert TarotProfile.objects.get(user=user).dossier == []

    def test_premium_persona_uses_persona_model_and_saves_dossier(self, api_client, premium, deck,
                                                                  three_card_spread, settings):
        settings.ANTHROPIC_MODEL_PERSONA = 'claude-sonnet-4-6'
        TarotProfile.objects.create(user=premium, persona='val')
        api_client.force_authenticate(user=premium)
        rid = _reading(api_client)
        with patch('apps.readings.views.ai_client.generate_interpretation', return_value=_result()) as gen:
            api_client.post(f'/api/v1/readings/{rid}/interpret/')
        kw = gen.call_args.kwargs
        assert kw['model'] == 'claude-sonnet-4-6'
        assert 'Вэл' in kw['extra_system_prompt'] and 'ОТМЕНЯЕТ' in kw['extra_system_prompt']
        assert TarotProfile.objects.get(user=premium).dossier == ['Аня, Рыбы', 'Дима — бывший']

    def test_memory_and_dossier_reach_next_reading(self, api_client, premium, deck, three_card_spread):
        TarotProfile.objects.create(user=premium, dossier=['Аня, Рыбы'])
        api_client.force_authenticate(user=premium)
        first = _reading(api_client)
        with patch('apps.readings.views.ai_client.generate_interpretation', return_value=_result()):
            api_client.post(f'/api/v1/readings/{first}/interpret/')
        second = _reading(api_client, 'А работа?')
        with patch('apps.readings.views.ai_client.generate_interpretation', return_value=_result()) as gen:
            api_client.post(f'/api/v1/readings/{second}/interpret/')
        extra = gen.call_args.kwargs['extra_system_prompt']
        assert '«Напишет ли Дима?»' in extra and 'ждать не стоит' in extra
        assert '- Дима — бывший' in extra

    def test_deleted_readings_and_memory_off_are_respected(self, api_client, premium, deck, three_card_spread):
        api_client.force_authenticate(user=premium)
        first = _reading(api_client)
        with patch('apps.readings.views.ai_client.generate_interpretation', return_value=_result()):
            api_client.post(f'/api/v1/readings/{first}/interpret/')
        from django.utils import timezone
        Reading.objects.filter(pk=first).update(deleted_at=timezone.now())
        second = _reading(api_client)
        with patch('apps.readings.views.ai_client.generate_interpretation', return_value=_result()) as gen:
            api_client.post(f'/api/v1/readings/{second}/interpret/')
        assert 'ждать не стоит' not in gen.call_args.kwargs['extra_system_prompt']

        TarotProfile.objects.filter(user=premium).update(remember=False)
        third = _reading(api_client)
        with patch('apps.readings.views.ai_client.generate_interpretation', return_value=_result()) as gen:
            api_client.post(f'/api/v1/readings/{third}/interpret/')
        assert gen.call_args.kwargs['extra_system_prompt'] == ''
        assert Interpretation.objects.get(reading_id=third).memo == ''

    def test_stream_never_leaks_tail(self, api_client, premium, deck, three_card_spread):
        api_client.force_authenticate(user=premium)
        rid = _reading(api_client)

        def fake_stream(**kw):
            for ch in ['Скорее нет: Луна', ' держит туман.\n\n<mem', 'o>gist</memo>']:
                yield ('delta', ch)
            yield ('done', _result('Скорее нет: Луна держит туман.\n\n<memo>gist</memo>'))
        with patch('apps.readings.views.ai_client.stream_interpretation', side_effect=fake_stream):
            res = api_client.post(f'/api/v1/readings/{rid}/interpret-stream/')
            text = b''.join(res.streaming_content).decode()
        deltas = text.split('"type": "done"')[0]
        assert 'memo' not in deltas and 'gist' not in deltas
        assert Interpretation.objects.get(reading_id=rid).memo == 'gist'


@pytest.mark.django_db
class TestTarologistApi:
    def test_requires_auth(self, api_client):
        assert api_client.get('/api/v1/tarologist/').status_code in (401, 403)

    def test_free_user_cannot_pick_persona(self, api_client, user):
        api_client.force_authenticate(user=user)
        res = api_client.patch('/api/v1/tarologist/', {'persona': 'mira'}, format='json')
        assert res.status_code == 402
        res = api_client.patch('/api/v1/tarologist/', {'remember': False}, format='json')
        assert res.status_code == 200 and res.data['remember'] is False

    def test_val18_needs_adult_confirmation(self, api_client, premium):
        api_client.force_authenticate(user=premium)
        res = api_client.patch('/api/v1/tarologist/', {'persona': 'val18'}, format='json')
        assert res.data['detail'] == 'adult_confirmation_required'
        res = api_client.patch('/api/v1/tarologist/', {'persona': 'val18', 'adult_confirm': True},
                               format='json')
        assert res.status_code == 200
        assert res.data['effective_persona'] == 'val18' and res.data['adult_confirmed'] is True

    def test_val18_gates(self, premium):
        p = TarotProfile.objects.create(user=premium, persona='val18')
        assert personalization.effective_persona(p, premium=True) == 'val'
        assert personalization.effective_persona(p, premium=False) == 'classic'

    def test_edit_dossier_and_forget(self, api_client, premium, deck, three_card_spread):
        api_client.force_authenticate(user=premium)
        rid = _reading(api_client)
        with patch('apps.readings.views.ai_client.generate_interpretation', return_value=_result()):
            api_client.post(f'/api/v1/readings/{rid}/interpret/')
        res = api_client.patch('/api/v1/tarologist/', {'dossier': ['Аня, Рыбы']}, format='json')
        assert res.data['dossier'] == ['Аня, Рыбы']
        res = api_client.post('/api/v1/tarologist/forget/')
        assert res.data['dossier'] == []
        assert Interpretation.objects.get(reading_id=rid).memo == ''
