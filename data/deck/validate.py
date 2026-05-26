"""Validate the seed deck JSON. Run before committing changes to rider-waite.json.

Usage:
    python data/deck/validate.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DECK_PATH = ROOT / 'rider-waite.json'

EXPECTED_SUITS = {'major', 'cups', 'wands', 'swords', 'pentacles'}
EXPECTED_MAJOR_COUNT = 22
EXPECTED_PER_MINOR_SUIT = 14
EXPECTED_TOTAL = 78


def main() -> int:
    data = json.loads(DECK_PATH.read_text(encoding='utf-8'))
    cards = data.get('cards', [])

    errors: list[str] = []

    if len(cards) != EXPECTED_TOTAL:
        errors.append(f'expected {EXPECTED_TOTAL} cards, got {len(cards)}')

    slugs = [c['slug'] for c in cards]
    if len(set(slugs)) != len(slugs):
        errors.append('duplicate slugs detected')

    counts: dict[str, int] = {}
    for card in cards:
        suit = card['suit']
        if suit not in EXPECTED_SUITS:
            errors.append(f'unknown suit: {suit} in {card["slug"]}')
        counts[suit] = counts.get(suit, 0) + 1

        for field in (
            'slug', 'suit', 'number',
            'name_ru', 'name_en',
            'upright_meaning_ru', 'upright_meaning_en',
            'reversed_meaning_ru', 'reversed_meaning_en',
            'keywords_ru', 'keywords_en', 'image_url',
        ):
            if field not in card:
                errors.append(f'{card.get("slug", "?")}: missing field {field}')

    if counts.get('major', 0) != EXPECTED_MAJOR_COUNT:
        errors.append(f'major arcana: expected {EXPECTED_MAJOR_COUNT}, got {counts.get("major", 0)}')
    for suit in ('cups', 'wands', 'swords', 'pentacles'):
        if counts.get(suit, 0) != EXPECTED_PER_MINOR_SUIT:
            errors.append(f'{suit}: expected {EXPECTED_PER_MINOR_SUIT}, got {counts.get(suit, 0)}')

    todo_cards = [
        c['slug'] for c in cards
        if c.get('upright_meaning_en', '').startswith('TODO')
    ]
    if todo_cards:
        print(f'⚠  {len(todo_cards)} cards still have TODO content (content-agent will fill these):')
        for slug in todo_cards[:5]:
            print(f'    - {slug}')
        if len(todo_cards) > 5:
            print(f'    ... and {len(todo_cards) - 5} more')

    if errors:
        print('❌ Validation failed:')
        for err in errors:
            print(f'  - {err}')
        return 1

    print(f'✅ Deck OK: {len(cards)} cards, {len(cards) - len(todo_cards)} fully written, {len(todo_cards)} pending content.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
