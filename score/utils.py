from score.models import PlayerScore
from django.utils import timezone

def update_score_for_game(game):
    """
    Updates the player's score after completing a game.

    This function:
    - Increases counters for total games and per difficulty
    - Updates first-completion timestamps per difficulty
    - Stores best completion time per difficulty
    - Recalculates unlocked memories
    """
    player = game.player
    duration = (timezone.now() - game.created_at).total_seconds()
    difficulty = game.difficulty

    # Get or create the PlayerScore object for this user
    score, _ = PlayerScore.objects.get_or_create(user=player)

    # Increase total completed games
    score.total_completed_games += 1
    if not score.total_completed_time:
        score.total_completed_time = timezone.now()

    # Update stats based on difficulty
    if difficulty == "easy":
        score.completed_easy += 1
        # Store timestamp of first easy win
        if not score.completed_easy_time:
            score.completed_easy_time = timezone.now()
        # Update best time if it's the first run or better than previous
        if not score.best_time_easy or duration < score.best_time_easy:
            score.best_time_easy = duration

    elif difficulty == "medium":
        score.completed_medium += 1
        # Store timestamp of first medium win
        if not score.completed_medium_time:
            score.completed_medium_time = timezone.now()
        # Update best time if it's the first run or better than previous
        if not score.best_time_medium or duration < score.best_time_medium:
            score.best_time_medium = duration

    elif difficulty == "hard":
        score.completed_hard += 1
        # Store timestamp of first hard win
        if not score.completed_hard_time:
            score.completed_hard_time = timezone.now()
        # Update best time if it's the first run or better than previous
        if not score.best_time_hard or duration < score.best_time_hard:
            score.best_time_hard = duration

    # Save updated stats
    score.save()
    # Recalculate number of unlocked memories
    score.update_unlocked_memories()