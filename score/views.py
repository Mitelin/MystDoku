from django.core.paginator import Paginator
from django.shortcuts import render
from .models import PlayerScore

def scoreboard(request):
    sort_field = request.GET.get("sort", "total_completed_games")

    # Seřazení
    if sort_field == "user__username":
        all_scores = PlayerScore.objects.all().order_by("user__username")
    elif sort_field == "total_completed_games":
        all_scores = PlayerScore.objects.all().order_by("-total_completed_games", "total_completed_time")
    elif sort_field == "completed_easy":
        all_scores = PlayerScore.objects.all().order_by("-completed_easy", "completed_easy_time")
    elif sort_field == "completed_medium":
        all_scores = PlayerScore.objects.all().order_by("-completed_medium", "completed_medium_time")
    elif sort_field == "completed_hard":
        all_scores = PlayerScore.objects.all().order_by("-completed_hard", "completed_hard_time")
    elif sort_field == "unlocked_memories":
        all_scores = PlayerScore.objects.all().order_by("-unlocked_memories", "user__username")
    elif sort_field in ["best_time_easy", "best_time_medium", "best_time_hard"]:
        all_scores = PlayerScore.objects.all().order_by(sort_field)
    else:
        all_scores = PlayerScore.objects.all().order_by("-total_completed_games", "total_completed_time")

    # Přidáme pořadí (rank)
    scores_with_rank = []
    for idx, score in enumerate(all_scores, start=1):
        score.rank = idx
        score.unlocked_memories_percent = (score.unlocked_memories / 60) * 100  # 💡 dopočet
        scores_with_rank.append(score)

    # Stránkování
    paginator = Paginator(scores_with_rank, 100)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Hráč mimo stránku – přidáme jeho řádek navíc
    current_player_score = None
    if request.user.is_authenticated:
        try:
            user_score = next(s for s in scores_with_rank if s.user == request.user)
            if user_score not in page_obj:
                current_player_score = user_score
                current_player_score.unlocked_memories_percent = (current_player_score.unlocked_memories / 60) * 100  # 💡 přidat!
        except StopIteration:
            pass

    return render(request, "score/scoreboard.html", {
        "page_obj": page_obj,
        "sort": sort_field,
        "current_player_score": current_player_score,
    })
