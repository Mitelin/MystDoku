from django.db import models
from django.contrib.auth.models import User
from django.apps import apps

class PlayerScore(models.Model):
    """
    Stores performance statistics for each player,
    including game counts, best times, and unlocked memories.
    """
    # Link to the user – one score per player
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Total completed games and when the first one was finished
    total_completed_games = models.IntegerField(default=0)
    total_completed_time = models.DateTimeField(null=True, blank=True)

    # Easy mode stats
    completed_easy = models.IntegerField(default=0)
    completed_easy_time = models.DateTimeField(null=True, blank=True)

    # Medium mode stats
    completed_medium = models.IntegerField(default=0)
    completed_medium_time = models.DateTimeField(null=True, blank=True)

    # Hard mode stats
    completed_hard = models.IntegerField(default=0)
    completed_hard_time = models.DateTimeField(null=True, blank=True)

    # Best times for each difficulty (in seconds)
    best_time_easy = models.FloatField(null=True, blank=True)
    best_time_medium = models.FloatField(null=True, blank=True)
    best_time_hard = models.FloatField(null=True, blank=True)

    # Total number of unlocked memories (1–60)
    unlocked_memories = models.IntegerField(default=0)

    def update_unlocked_memories(self):
        """
        Updates the number of unlocked memories for this user
        by counting unlocked entries from PlayerStoryProgress.
        """
        # Dynamic import model from `apps.get_model`
        PlayerStoryProgress = apps.get_model('gameplay', 'PlayerStoryProgress')

        try:
            # Load memory progress for this user
            story_progress = PlayerStoryProgress.objects.get(player=self.user)

            # Count unlocked memories for all difficulties
            unlocked_easy = len(story_progress.unlocked_easy)
            unlocked_medium = len(story_progress.unlocked_medium)
            unlocked_hard = len(story_progress.unlocked_hard)

            # Save the total count
            self.unlocked_memories = unlocked_easy + unlocked_medium + unlocked_hard
            self.save()

        except PlayerStoryProgress.DoesNotExist:
            # If progress does not exist (new player), reset to 0
            self.unlocked_memories = 0
            self.save()

    def __str__(self):
        return f"{self.user.username} - Score"