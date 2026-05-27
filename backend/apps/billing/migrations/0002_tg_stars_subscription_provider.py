from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='tg_stars_price',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='subscription',
            name='provider',
            field=models.CharField(
                choices=[('paddle', 'Paddle'), ('telegram', 'Telegram Stars')],
                default='paddle',
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name='subscription',
            name='tg_payment_charge_id',
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='paddle_subscription_id',
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
    ]
