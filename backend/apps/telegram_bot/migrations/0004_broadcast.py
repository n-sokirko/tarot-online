from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0003_telegramuser_daily_push'),
    ]

    operations = [
        migrations.CreateModel(
            name='Broadcast',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, help_text='Только для тебя, в сообщение не идёт.', max_length=120)),
                ('message', models.TextField(help_text='Текст рассылки. Поддерживает Markdown.')),
                ('target', models.CharField(choices=[('all', 'Все пользователи бота'), ('subscribers', 'Только подписчики (/subscribe)')], default='all', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('sent_count', models.PositiveIntegerField(default=0)),
                ('failed_count', models.PositiveIntegerField(default=0)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
