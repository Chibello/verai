# Generated by Django 5.2 on 2025-05-16 21:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0002_transaction_user_alter_transaction_amount_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='narration',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='reference',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
