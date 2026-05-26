"""
Management command: seed_runes

Upserts Rune records from data/deck/runes.json. Idempotent.

Usage:
    python manage.py seed_runes
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.runes.models import Rune

DATA_FILE = Path(__file__).resolve().parents[5] / "data" / "deck" / "runes.json"


class Command(BaseCommand):
    help = "Seed Elder Futhark runes from data/deck/runes.json."

    def handle(self, *args, **options) -> None:
        if not DATA_FILE.exists():
            raise CommandError(f"Runes file not found: {DATA_FILE}")

        with DATA_FILE.open(encoding="utf-8") as fh:
            data = json.load(fh)

        runes = data.get("runes", [])
        count = 0
        for item in runes:
            Rune.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "number": item["number"],
                    "aett": item["aett"],
                    "symbol": item["symbol"],
                    "name_ru": item["name_ru"],
                    "name_en": item["name_en"],
                    "meaning_ru": item["meaning_ru"],
                    "meaning_en": item["meaning_en"],
                    "keywords_ru": item.get("keywords_ru", []),
                    "keywords_en": item.get("keywords_en", []),
                },
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {count} runes."))
