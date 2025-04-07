from django.db import models
from django.contrib.auth.models import User
from django.apps import apps

class PlayerScore(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    total_completed_games = models.IntegerField(default=0)
    total_completed_time = models.DateTimeField(null=True, blank=True)

    completed_easy = models.IntegerField(default=0)
    completed_easy_time = models.DateTimeField(null=True, blank=True)

    completed_medium = models.IntegerField(default=0)
    completed_medium_time = models.DateTimeField(null=True, blank=True)

    completed_hard = models.IntegerField(default=0)
    completed_hard_time = models.DateTimeField(null=True, blank=True)

    best_time_easy = models.FloatField(null=True, blank=True)
    best_time_medium = models.FloatField(null=True, blank=True)
    best_time_hard = models.FloatField(null=True, blank=True)

    unlocked_memories = models.IntegerField(default=0) # Počet všech odemčených vzpomínek

    def update_unlocked_memories(self):
        """
        Aktualizuje počet odemčených vzpomínek z PlayerStoryProgress
        """
        # Dynamický import modelu přes `apps.get_model`
        PlayerStoryProgress = apps.get_model('gameplay', 'PlayerStoryProgress')

        try:
            # Získáme PlayerStoryProgress pro aktuálního uživatele
            story_progress = PlayerStoryProgress.objects.get(player=self.user)

            # Spočítáme počet odemčených vzpomínek pro každou obtížnost
            unlocked_easy = len(story_progress.unlocked_easy)
            unlocked_medium = len(story_progress.unlocked_medium)
            unlocked_hard = len(story_progress.unlocked_hard)

            # Aktualizujeme počet vzpomínek
            self.unlocked_memories = unlocked_easy + unlocked_medium + unlocked_hard
            self.save()

        except PlayerStoryProgress.DoesNotExist:
            # Pokud PlayerStoryProgress neexistuje pro uživatele, nastavíme default hodnotu
            self.unlocked_memories = 0
            self.save()

    def __str__(self):
        return f"{self.user.username} - Score"