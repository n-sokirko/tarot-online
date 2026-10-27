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


@pytest.mark.parametrize('locale', LOCALES)
def test_when_questions_always_get_a_timeframe(locale):
    """Haiku skipped the timing rule once ("the cards show no timeline"), so it is
    now mandatory and the dodge is named as forbidden."""
    text = _read('base_system', locale)
    if locale == 'ru':
        assert 'всегда называй срок-ориентир' in text
        assert 'сроков карты не показывают' in text and 'запрещены' in text
    else:
        assert 'always give a timeframe estimate' in text
        assert 'the cards show no timeline' in text and 'forbidden' in text


@pytest.mark.parametrize('locale', LOCALES)
def test_negation_patterns_are_listed_as_forbidden(locale):
    text = _read('base_system', locale)
    marker = 'Запрещённые обороты с отрицанием' if locale == 'ru' else 'Forbidden negation patterns'
    assert marker in text


@pytest.mark.parametrize('locale', LOCALES)
@pytest.mark.parametrize('name', ('spread_3_cards', 'runes_cast'))
def test_worked_examples_do_not_use_the_banned_patterns(name, locale):
    """The model copies the examples, so they must not show "not X, but Y"."""
    text = _read(name, locale)
    banned = (['а не потому, что', 'Лёд — это не плохо', 'Эта руна не говорит'] if locale == 'ru'
              else ['not because there are none', 'Ice is not bad', 'This rune does not say'])
    for phrase in banned:
        assert phrase not in text


@pytest.mark.parametrize('locale', LOCALES)
def test_checklist_is_the_last_thing_the_model_reads(locale):
    """Haiku weighs the end of the prompt most, so the answer-first checklist is
    appended to every spread and rune prompt."""
    from services.ai import prompts

    marker = 'Проверь себя перед ответом' if locale == 'ru' else 'Check yourself before answering'
    for text in (prompts.tarot_spread('three-card', locale),
                 prompts.tarot_spread('celtic-cross', locale),
                 prompts.tarot_spread('free-table', locale),
                 prompts.runes_cast(locale)):
        assert marker in text
        assert text.index(marker) > len(text) // 2  # near the end, after the structure and examples
