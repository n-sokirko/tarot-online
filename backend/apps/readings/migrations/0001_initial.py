import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tarot", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Reading",
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
                ("question", models.TextField()),
                (
                    "locale",
                    models.CharField(
                        choices=[("ru", "Russian"), ("en", "English")],
                        default="ru",
                        max_length=2,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "spread_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="tarot.spreadtype",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="readings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ReadingCard",
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
                ("position_index", models.PositiveSmallIntegerField()),
                ("is_reversed", models.BooleanField(default=False)),
                (
                    "card",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="tarot.card",
                    ),
                ),
                (
                    "reading",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cards",
                        to="readings.reading",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Interpretation",
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
                ("body_md", models.TextField()),
                ("model_used", models.CharField(max_length=64)),
                ("prompt_version", models.CharField(max_length=32)),
                ("generated_at", models.DateTimeField(auto_now_add=True)),
                ("token_count", models.PositiveIntegerField(default=0)),
                (
                    "reading",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="interpretation",
                        to="readings.reading",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="reading",
            index=models.Index(
                fields=["-created_at"], name="readings_reading_created_at_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="reading",
            index=models.Index(
                fields=["user", "-created_at"], name="readings_reading_user_created_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="readingcard",
            unique_together={("reading", "position_index")},
        ),
    ]
