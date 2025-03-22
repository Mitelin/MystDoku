import json
import os
from django.apps import AppConfig
from django.core.management import call_command
from django.conf import settings


class GameplayConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gameplay'

    def ready(self):
        from gameplay.models import Item, Game

        # Path to file items.json
        fixture_path = os.path.join(settings.BASE_DIR, 'gameplay', 'fixtures', 'items.json')

        if not os.path.exists(fixture_path):
            print("❌ File fixtures/items.json does not exist.")
            return

        # Load file items.json
        try:
            with open(fixture_path, 'r', encoding='utf-8') as f:
                fixture_items = json.load(f)
        except Exception as e:
            print(f"❌ Error whit loading file items.json: {e}")
            return

        # Validates the content of items.json
        if not isinstance(fixture_items, list) or len(fixture_items) < 9:
            print("❌ File items.json is not valid items.json require at least 9 items.")
            return

        # Loads item data from database
        db_items = list(Item.objects.values('number', 'name'))

        # Sort fixture list and database list for comparison
        fixture_sorted = sorted([{'number': i['fields']['number'], 'name': i['fields']['name']} for i in fixture_items],
                                key=lambda x: (x['number'], x['name']))
        db_sorted = sorted(db_items, key=lambda x: (x['number'], x['name']))

        if fixture_sorted != db_sorted:
            print("🔁 Difference between fixture items and database items resetting database.")
            # Deletes games and items.
            Game.objects.all().delete()
            Item.objects.all().delete()

            # Import fixtures
            try:
                call_command('loaddata', 'items.json', app_label='gameplay')
                print("✅ items.json loaded.")
            except Exception as e:
                print(f"❌ Unable to import items.json: {e}")
        else:
            print("✅ Fixtures and database is equal skipping checks.")