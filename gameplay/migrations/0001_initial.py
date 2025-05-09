# Generated by Django 5.1.7 on 2025-04-06 17:03

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DifficultyTransition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('difficulty', models.CharField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard'), ('end', 'End')], max_length=10, unique=True)),
                ('text', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Intro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(unique=True)),
                ('text', models.TextField()),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('number', models.IntegerField()),
                ('group_id', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Memory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('difficulty', models.CharField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], max_length=10)),
                ('order', models.PositiveIntegerField(unique=True)),
                ('text', models.TextField()),
                ('transition', models.TextField()),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed', models.BooleanField(default=False)),
                ('block_rooms', models.JSONField(default=list)),
                ('block_items', models.JSONField(default=dict)),
                ('difficulty', models.CharField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], default='easy', max_length=10)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Cell',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('row', models.IntegerField()),
                ('column', models.IntegerField()),
                ('prefilled', models.BooleanField(default=False)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gameplay.game')),
                ('correct_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='correct_cells', to='gameplay.item')),
                ('selected_item', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='selected_cells', to='gameplay.item')),
            ],
        ),
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
        migrations.AddField(
            model_name='item',
            name='room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='gameplay.room'),
        ),
        migrations.CreateModel(
            name='SequenceFrame',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sequence', models.CharField(max_length=50)),
                ('index', models.PositiveIntegerField()),
                ('image', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['sequence', 'index'],
                'unique_together': {('sequence', 'index')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='item',
            unique_together={('name', 'number', 'room')},
        ),
    ]
