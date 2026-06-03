from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0002_alter_telegramuser_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramuser',
            name='daily_push',
            field=models.BooleanField(default=False),
        ),
    ]
