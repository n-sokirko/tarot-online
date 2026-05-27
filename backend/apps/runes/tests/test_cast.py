"""Rune casts: create, retrieve, interpret with mocked Anthropic."""
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.runes.models import Rune, RuneInterpretation


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def runes(db):
    out = []
    for i in range(24):
        out.append(
            Rune.objects.create(
                slug=f'r-{i}', number=i + 1, aett=(i // 8) + 1, symbol='ᚠ',
                name_ru=f'Руна {i}', name_en=f'Rune {i}',
                meaning_ru='значение', meaning_en='meaning',
                keywords_ru=['k'], keywords_en=['k'],
            )
        )
    return out


def _mock_result():
    from services.ai.client import GenerationResult
    return GenerationResult(
        body='Руны говорят...', model='claude-haiku-4-5-20251001',
        input_tokens=100, output_tokens=80,
    )


@pytest.mark.django_db
class TestRuneCast:
    def test_create_single_cast(self, api_client, runes):
        res = api_client.post('/api/v1/runes/casts/', {
            'layout': 'single', 'locale': 'ru', 'question': '',
        }, format='json')
        assert res.status_code == 201, res.content
        assert res.data['layout'] == 'single'
        assert len(res.data['items']) == 1

    def test_create_three_cast_three_distinct_runes(self, api_client, runes):
        res = api_client.post('/api/v1/runes/casts/', {
            'layout': 'three', 'locale': 'ru',
        }, format='json')
        assert res.status_code == 201
        slugs = [it['rune']['slug'] for it in res.data['items']]
        assert len(slugs) == 3
        assert len(set(slugs)) == 3

    def test_create_five_cast(self, api_client, runes):
        res = api_client.post('/api/v1/runes/casts/', {
            'layout': 'five', 'locale': 'en', 'question': 'guidance',
        }, format='json')
        assert res.status_code == 201
        assert len(res.data['items']) == 5
        # positions metadata is included
        assert len(res.data['positions']) == 5

    def test_get_cast(self, api_client, runes):
        cid = api_client.post('/api/v1/runes/casts/', {'layout': 'three', 'locale': 'ru'},
                              format='json').data['id']
        res = api_client.get(f'/api/v1/runes/casts/{cid}/')
        assert res.status_code == 200
        assert res.data['id'] == cid

    def test_interpret_creates_record(self, api_client, runes):
        cid = api_client.post('/api/v1/runes/casts/', {'layout': 'three', 'locale': 'ru'},
                              format='json').data['id']
        with patch('apps.runes.views.ai_client.generate_interpretation',
                   return_value=_mock_result()) as mock_gen:
            res = api_client.post(
                f'/api/v1/runes/casts/{cid}/interpret/',
                {'question': 'Что ждёт меня завтра?'},
                format='json',
            )
        assert res.status_code == 201
        assert mock_gen.called
        assert RuneInterpretation.objects.filter(cast_id=cid).exists()

    def test_interpret_without_question_returns_400(self, api_client, runes):
        cid = api_client.post('/api/v1/runes/casts/', {'layout': 'single', 'locale': 'ru'},
                              format='json').data['id']
        res = api_client.post(f'/api/v1/runes/casts/{cid}/interpret/', {}, format='json')
        assert res.status_code == 400
        assert res.data['detail'] == 'question_required'

    def test_interpret_is_idempotent(self, api_client, runes):
        cid = api_client.post('/api/v1/runes/casts/', {'layout': 'three', 'locale': 'ru'},
                              format='json').data['id']
        with patch('apps.runes.views.ai_client.generate_interpretation',
                   return_value=_mock_result()) as mock_gen:
            api_client.post(
                f'/api/v1/runes/casts/{cid}/interpret/',
                {'question': 'Путешествие'},
                format='json',
            )
            api_client.post(
                f'/api/v1/runes/casts/{cid}/interpret/',
                {'question': 'Путешествие'},
                format='json',
            )
        assert mock_gen.call_count == 1
