"""The reading admin shows the AI's answer, so a prompt change can be judged on real text.

These tests stop short of rendering the admin templates: the local Python 3.14 is
newer than this Django supports and fails inside Django's own template-context
copy, while production runs 3.12. The view's context, the list columns and the
search are checked instead, which is where this code lives.
"""
import pytest
from django.contrib import admin as dj_admin
from django.test import RequestFactory

from apps.readings.admin import InterpretationInline, ReadingAdmin, ReadingCardInline
from apps.readings.models import Interpretation, Reading
from apps.tarot.models import SpreadType

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff(django_user_model):
    return django_user_model.objects.create_superuser(
        username='root', email='root@example.com', password='pw')


@pytest.fixture
def spread(db):
    return SpreadType.objects.create(slug='three-card', name_ru='Три карты',
                                     name_en='Three cards', positions_count=3)


@pytest.fixture
def reading(spread):
    r = Reading.objects.create(spread_type=spread, question='Когда мне напишет Миша?')
    Interpretation.objects.create(
        reading=r, body_md='**Карты говорят: в ближайшие дни.** Текст ответа.',
        model_used='claude-haiku-4-5-20251001', prompt_version='2026-10-27-v2', token_count=531)
    return r


@pytest.fixture
def model_admin():
    return ReadingAdmin(Reading, dj_admin.site)


def _request(user):
    request = RequestFactory().get('/')
    request.user = user
    return request


def test_the_detail_page_carries_the_answer_model_and_prompt_version(model_admin, staff, reading):
    response = model_admin.changeform_view(_request(staff), str(reading.pk))
    assert response.status_code == 200
    answers = [fs for fs in response.context_data['inline_admin_formsets']
               if isinstance(fs.opts, InterpretationInline)]
    assert len(answers) == 1
    saved = answers[0].formset.queryset.get()
    assert 'Карты говорят: в ближайшие дни.' in saved.body_md
    assert saved.model_used == 'claude-haiku-4-5-20251001'
    assert saved.prompt_version == '2026-10-27-v2'


def test_the_answer_is_read_only(staff):
    inline = InterpretationInline(Reading, dj_admin.site)
    request = _request(staff)
    assert set(inline.fields) <= set(inline.readonly_fields)       # nothing editable
    assert inline.has_add_permission(request) is False
    assert inline.can_delete is False
    assert ReadingCardInline(Reading, dj_admin.site).has_add_permission(request) is False


def test_the_list_shows_which_model_and_prompt_wrote_the_answer(model_admin, reading):
    assert model_admin.answer_model(reading) == 'claude-haiku-4-5-20251001'
    assert model_admin.prompt_version(reading) == '2026-10-27-v2'
    assert model_admin.interpreted(reading) is True


def test_a_reading_without_an_answer_shows_dashes_not_errors(model_admin, spread):
    r = Reading.objects.create(spread_type=spread, question='без ответа')
    assert model_admin.answer_model(r) == '—'
    assert model_admin.prompt_version(r) == '—'
    assert model_admin.interpreted(r) is False


def test_search_finds_a_reading_by_what_the_model_said(model_admin, staff, reading, spread):
    Reading.objects.create(spread_type=spread, question='другой вопрос')
    found, _ = model_admin.get_search_results(_request(staff), Reading.objects.all(), 'ближайшие дни')
    assert list(found) == [reading]


def test_the_change_list_and_filters_build(model_admin, staff, reading):
    """The model/prompt filters reference the reverse relation; a typo there would
    break the whole list page."""
    response = model_admin.changelist_view(_request(staff))
    assert response.status_code == 200
    assert response.context_data['cl'].result_count == 1
