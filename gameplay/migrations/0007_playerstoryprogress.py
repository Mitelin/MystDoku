# Generated by Django 5.1.7 on 2025-04-05 17:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gameplay', '0006_difficultytransition_intro_memory'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlayerStoryProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unlocked_easy', models.JSONField(default=list)),
                ('unlocked_medium', models.JSONField(default=list)),
                ('unlocked_hard', models.JSONField(default=list)),
                ('player', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
