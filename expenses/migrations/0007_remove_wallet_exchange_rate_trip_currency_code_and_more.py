# Generated by Django 4.2.20 on 2025-06-03 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0006_wallet_exchange_rate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='wallet',
            name='exchange_rate',
        ),
        migrations.AddField(
            model_name='trip',
            name='currency_code',
            field=models.CharField(default='KRW', max_length=5, verbose_name='기본 통화'),
        ),
        migrations.AddField(
            model_name='trip',
            name='exchange_rate_to_krw',
            field=models.DecimalField(decimal_places=4, default=1.0, max_digits=15, verbose_name='KRW 환율'),
        ),
    ]
