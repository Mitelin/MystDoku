import json
import os

from django.apps import AppConfig
from django.conf import settings
from django.db import connection

class GameplayConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gameplay'

    def ready(self):
        if 'makemigrations' in os.sys.argv or 'migrate' in os.sys.argv:
            return

        if 'gameplay_item' not in connection.introspection.table_names():
            return

        fixture_items = load_fixture_items()
        if fixture_items is None:
            return

        if not validate_group_numbers(fixture_items):
            return

        if items_match_fixture(fixture_items):
            return

        reload_items()


def load_fixture_items():
    """
    Load items.json and filter for gameplay.item models only.
    """
    import os, json

    fixture_path = os.path.join(settings.BASE_DIR, 'gameplay', 'fixtures', 'items.json')

    if not os.path.exists(fixture_path):
        return None

    try:
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return [
                i for i in json.load(f)
                if i['model'] == 'gameplay.item'
            ]
    except Exception:
        return None


def validate_group_numbers(fixture_items):
    """
    Check that every (room_id, group_id) pair contains exactly numbers 1–9.
    """
    room_items = {}

    for i in fixture_items:
        fields = i['fields']
        room_id = fields['room']
        group_id = fields.get('group_id')
        number = fields['number']

        if group_id is None:
            return False

        room_items.setdefault((room_id, group_id), []).append(number)

    for numbers in room_items.values():
        if sorted(numbers) != list(range(1, 10)):
            return False

    return True


def items_match_fixture(fixture_items):
    """
    Compare fixture items to the database.
    Return True if they match exactly by name, number, group_id and room.
    """
    from gameplay.models import Item
    db_items = Item.objects.all().values('name', 'number', 'group_id', 'room')
    if len(db_items) != len(fixture_items):
        return False

    db_set = {
        (i['name'], i['number'], i['group_id'], i['room'])
        for i in db_items
    }
    json_set = {
        (i['fields']['name'], i['fields']['number'], i['fields']['group_id'], i['fields']['room'])
        for i in fixture_items
    }

    return db_set == json_set


def reload_items():
    """
    Delete existing game data and reload items.json using loaddata.
    """
    from gameplay.models import Item, Game, Room
    from django.core.management import call_command
    Game.objects.all().delete()
    Item.objects.all().delete()
    Room.objects.all().delete()

    try:
        call_command('loaddata', 'items.json', app_label='gameplay')
    except Exception:
        pass

