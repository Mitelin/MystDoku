from django.http import JsonResponse
from score.models import PlayerScore

def api_scoreboard(request):
    limit = int(request.GET.get("limit", 100))
    offset = int(request.GET.get("offset", 0))

    scores = PlayerScore.objects.all().select_related("user")
    scores = scores[offset : offset + limit]

    data = [
        {
            "username": score.user.username,
            "total_completed_games": score.total_completed_games,
            "completed_easy": score.completed_easy,
            "completed_medium": score.completed_medium,
            "completed_hard": score.completed_hard,
            "best_time_easy": score.best_time_easy,
            "best_time_medium": score.best_time_medium,
            "best_time_hard": score.best_time_hard,
            "unlocked_memories": score.unlocked_memories,
        }
        for score in scores
    ]

    return JsonResponse(data, safe=False)