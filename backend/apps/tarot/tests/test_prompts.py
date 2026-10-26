"""The reading prompts must tell the model to answer, and must not teach it to dodge.

An earlier version told the model "never give instructions" and showed it a
model answer that said "the cards do not answer quit-or-continue". The model
copied that, and people who asked "should I quit?" got no answer. These tests
keep the prompts from sliding back.
"""
from pathlib import Path

import pytest

PROMPTS = Path(__file__).resolve().parents[1] / 'prompts'
LOCALES = ('ru', 'en')
SPREADS = ('spread_3_cards', 'spread_celtic-cross', 'spread_free-table', 'runes_cast')

# Phrases that, inside a prompt or its worked example, teach the model to refuse.
DODGES = {
    'ru': ['Карты не говорят «продолжай»', 'Карты не отвечают «бросать',
           'Руны не отвечают «езжай»', 'Никогда не давай инструкций',
           'не пророчество', 'не приговор. Используй сослагательные'],
    'en': ['The cards do not say "continue"', 'The cards do not answer "quit',
           'The runes do not answer "go"', 'Never give instructions',
           'not prophecy', 'not a verdict. Use conditional'],
}
ANSWER_MARKER = {'ru': 'Прямой ответ', 'en': 'Direct answer'}


def _read(name: str, locale: str) -> str:
    return (PROMPTS / f'{name}_{locale}.md').read_text(encoding='utf-8')


@pytest.mark.parametrize('locale', LOCALES)
def test_base_prompt_requires_a_direct_answer_first(locale):
    text = _read('base_system', locale)
    assert 'Прямота' in text or 'Directness' in text
    assert 'The first sentence' in text or 'Первое предложение' in text


@pytest.mark.parametrize('locale', LOCALES)
@pytest.mark.parametrize('name', SPREADS)
def test_every_structure_starts_with_a_direct_answer(name, locale):
    assert ANSWER_MARKER[locale] in _read(name, locale)


@pytest.mark.parametrize('locale', LOCALES)
@pytest.mark.parametrize('name', ('base_system',) + SPREADS)
def test_prompts_do_not_teach_dodging(name, locale):
    text = _read(name, locale)
    for phrase in DODGES[locale]:
        assert phrase not in text, f'{name}_{locale}.md still contains: {phrase!r}'


@pytest.mark.parametrize('locale', LOCALES)
def test_worked_examples_open_with_an_answer(locale):
    """The few-shot answers are what the model imitates most closely."""
    lead = {'ru': ('Карты говорят', 'Руны говорят'), 'en': ('The cards say', 'The runes say')}[locale]
    for name in ('spread_3_cards', 'runes_cast'):
        assert any(f'**{l}' in _read(name, locale) for l in lead), name


@pytest.mark.parametrize('locale', LOCALES)
def test_ethics_floor_is_kept(locale):
    """Being direct does not mean predicting illness, death or divorce."""
    text = _read('base_system', locale)
    assert ('болезнь, смерть, развод' in text) or ('illness, death, divorce' in text)
    assert ('специалисту' in text) or ('professional' in text)
