from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Card",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("slug", models.SlugField(unique=True, max_length=64)),
                (
                    "suit",
                    models.CharField(
                        max_length=16,
                        choices=[
                            ("major", "Major Arcana"),
                            ("cups", "Cups"),
                            ("wands", "Wands"),
                            ("swords", "Swords"),
                            ("pentacles", "Pentacles"),
                        ],
                    ),
                ),
                ("number", models.PositiveSmallIntegerField()),
                ("name_ru", models.CharField(max_length=128)),
                ("name_en", models.CharField(max_length=128)),
                ("upright_meaning_ru", models.TextField()),
                ("upright_meaning_en", models.TextField()),
                ("reversed_meaning_ru", models.TextField()),
                ("reversed_meaning_en", models.TextField()),
                ("keywords_ru", models.JSONField(default=list)),
                ("keywords_en", models.JSONField(default=list)),
                ("image_url", models.CharField(max_length=255)),
            ],
            options={
                "ordering": ["suit", "number"],
            },
        ),
        migrations.CreateModel(
            name="SpreadType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("slug", models.SlugField(unique=True, max_length=64)),
                ("name_ru", models.CharField(max_length=128)),
                ("name_en", models.CharField(max_length=128)),
                ("positions_count", models.PositiveSmallIntegerField()),
                ("positions", models.JSONField(default=list)),
            ],
        ),
        migrations.AddIndex(
            model_name="card",
            index=models.Index(fields=["suit", "number"], name="tarot_card_suit_number_idx"),
        ),
    ]
