from django.utils import timezone
from score.models import PlayerScore
from datetime import datetime

from django.utils import timezone

def update_score_for_game(game):
    player = game.player
    duration = (timezone.now() - game.created_at).total_seconds()
    difficulty = game.difficulty

    score, _ = PlayerScore.objects.get_or_create(user=player)

    # Celkový počet her
    score.total_completed_games += 1
    if not score.total_completed_time:
        score.total_completed_time = timezone.now()

    # Počet her podle obtížnosti
    if difficulty == "easy":
        score.completed_easy += 1
        if not score.completed_easy_time:
            score.completed_easy_time = timezone.now()
        if not score.best_time_easy or duration < score.best_time_easy:
            score.best_time_easy = duration

    elif difficulty == "medium":
        score.completed_medium += 1
        if not score.completed_medium_time:
            score.completed_medium_time = timezone.now()
        if not score.best_time_medium or duration < score.best_time_medium:
            score.best_time_medium = duration

    elif difficulty == "hard":
        score.completed_hard += 1
        if not score.completed_hard_time:
            score.completed_hard_time = timezone.now()
        if not score.best_time_hard or duration < score.best_time_hard:
            score.best_time_hard = duration

    score.save()
    score.update_unlocked_memories()