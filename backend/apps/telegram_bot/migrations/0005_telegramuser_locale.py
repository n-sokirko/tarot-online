from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0004_broadcast'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramuser',
            name='locale',
            field=models.CharField(default='ru', max_length=8),
        ),
    ]
