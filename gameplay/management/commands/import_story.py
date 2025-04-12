import json
from django.core.management.base import BaseCommand
from gameplay.models import Intro, Memory, DifficultyTransition


class Command(BaseCommand):
    help = "Imports story data from the storyzaloha.json file"

    def handle(self, *args, **options):
        path = "gameplay/fixtures/story.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Delete all existing data in the models
        Intro.objects.all().delete()
        Memory.objects.all().delete()
        DifficultyTransition.objects.all().delete()

        # Create new Intro objects from the data
        for intro in data.get("intro", []):
            Intro.objects.create(
                order=intro["order"],
                text=intro["text"]
            )

        # Create new Memory objects from the data
        for memory in data.get("memories", []):
            Memory.objects.create(
                order=memory["order"],
                difficulty=memory["difficulty"],
                text=memory["text"],
                transition=memory.get("transition", "")
            )

        # Create new DifficultyTransition objects from the data
        for trans in data.get("difficulty_transitions", []):
            DifficultyTransition.objects.create(
                difficulty=trans["difficulty"],
                text=trans["text"]
            )

        self.stdout.write(self.style.SUCCESS("✅ Story data has been successfully imported."))