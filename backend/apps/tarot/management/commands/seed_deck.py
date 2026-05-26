"""
Management command: seed_deck

Upserts Card and SpreadType records from the JSON data files.
Safe to run multiple times (idempotent).

Usage:
    python manage.py seed_deck
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.tarot.models import Card, SpreadType

# Absolute path to the data directory (two levels up from backend/)
DATA_DIR = Path(__file__).resolve().parents[5] / "data" / "deck"
CARDS_FILE = DATA_DIR / "rider-waite.json"
SPREADS_FILE = DATA_DIR / "spread-positions.json"


class Command(BaseCommand):
    help = "Seed the database with cards and spread types from JSON data files."

    def handle(self, *args, **options) -> None:
        cards_seeded = self._seed_cards()
        spreads_seeded = self._seed_spreads()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {cards_seeded} cards, {spreads_seeded} spread types."
            )
        )

    def _seed_cards(self) -> int:
        if not CARDS_FILE.exists():
            raise CommandError(f"Cards file not found: {CARDS_FILE}")

        with CARDS_FILE.open(encoding="utf-8") as fh:
            data = json.load(fh)

        cards = data.get("cards", [])
        count = 0

        for card_data in cards:
            name_en = card_data.get("name_en", "").strip()
            if not name_en:
                # Skip stub cards with no English name
                continue

            slug = card_data["slug"]
            Card.objects.update_or_create(
                slug=slug,
                defaults={
                    "suit": card_data["suit"],
                    "number": card_data["number"],
                    "name_ru": card_data.get("name_ru", ""),
                    "name_en": name_en,
                    "upright_meaning_ru": card_data.get("upright_meaning_ru", ""),
                    "upright_meaning_en": card_data.get("upright_meaning_en", ""),
                    "reversed_meaning_ru": card_data.get("reversed_meaning_ru", ""),
                    "reversed_meaning_en": card_data.get("reversed_meaning_en", ""),
                    "keywords_ru": card_data.get("keywords_ru", []),
                    "keywords_en": card_data.get("keywords_en", []),
                    "image_url": card_data.get("image_url", ""),
                },
            )
            count += 1

        return count

    def _seed_spreads(self) -> int:
        if not SPREADS_FILE.exists():
            raise CommandError(f"Spreads file not found: {SPREADS_FILE}")

        with SPREADS_FILE.open(encoding="utf-8") as fh:
            data = json.load(fh)

        spreads = data.get("spreads", [])
        count = 0

        for spread_data in spreads:
            slug = spread_data["slug"]
            SpreadType.objects.update_or_create(
                slug=slug,
                defaults={
                    "name_ru": spread_data.get("name_ru", ""),
                    "name_en": spread_data.get("name_en", ""),
                    "positions_count": spread_data["positions_count"],
                    "positions": spread_data.get("positions", []),
                },
            )
            count += 1

        return count
