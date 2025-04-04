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

def load_fixture_story():
    """
    Loads story.json
    """
    import os, json
    fixture_path = os.path.join(settings.BASE_DIR, 'gameplay', 'fixtures', 'story.json')

    if not os.path.exists(fixture_path):
        return None

    try:
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def story_matches_fixture(fixture_story):
    """
    Will check if story json data matches fixture data.
    Returns true if matches, false otherwise.
    """
    from gameplay.models import Intro, Memory, DifficultyTransition

    intro_match = list(Intro.objects.order_by('order').values('order', 'text')) == \
        [{'order': i['order'], 'text': i['text']} for i in fixture_story['intro']]

    memory_match = list(Memory.objects.order_by('order').values('order', 'difficulty', 'text', 'transition')) == \
        [
            {
                'order': m['order'],
                'difficulty': m['difficulty'],
                'text': m['text'],
                'transition': m['transition']
            }
            for m in fixture_story['memories']
        ]

    transition_match = list(DifficultyTransition.objects.order_by('difficulty').values('difficulty', 'text')) == \
        [{'difficulty': dt['difficulty'], 'text': dt['text']} for dt in fixture_story['difficulty_transitions']]

    return intro_match and memory_match and transition_match


def reload_story(fixture_story):
    """
    Deletes old data and loads from story.json
    """
    from gameplay.models import Intro, Memory, DifficultyTransition

    Intro.objects.all().delete()
    Memory.objects.all().delete()
    DifficultyTransition.objects.all().delete()

    # Load data from fixture:
    Intro.objects.bulk_create([
        Intro(order=i['order'], text=i['text'])
        for i in fixture_story['intro']
    ])

    Memory.objects.bulk_create([
        Memory(
            difficulty=m['difficulty'],
            order=m['order'],
            text=m['text'],
            transition=m['transition']
        )
        for m in fixture_story['memories']
    ])

    DifficultyTransition.objects.bulk_create([
        DifficultyTransition(
            difficulty=dt['difficulty'],
            text=dt['text']
        )
        for dt in fixture_story['difficulty_transitions']
    ])