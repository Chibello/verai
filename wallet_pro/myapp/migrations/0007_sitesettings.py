# Generated by Django 5.1.7 on 2025-04-17 22:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_profile_whatsapp_number_alter_profile_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('moderation_enabled', models.BooleanField(default=False)),
            ],
        ),
    ]
