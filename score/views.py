from django.core.paginator import Paginator
from .models import PlayerScore
import markdown
from django.shortcuts import render
from pathlib import Path

def scoreboard(request):
    """
    View for displaying the scoreboard with sorting, ranking, and pagination.
    It supports sorting by different stats and highlights the current player's score.
    """
    # Get the sorting field from query parameters (?sort=...)
    sort_field = request.GET.get("sort", "total_completed_games")

    # Sort all player scores based on the selected field
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
        # Fallback sorting by total completed games
        all_scores = PlayerScore.objects.all().order_by("-total_completed_games", "total_completed_time")


    # Add ranking (position in the list) and percent of unlocked memories
    scores_with_rank = []
    for idx, score in enumerate(all_scores, start=1):
        score.rank = idx
        score.unlocked_memories_percent = (score.unlocked_memories / 60) * 100  # 💡 dopočet
        scores_with_rank.append(score)

    # Paginate the results (100 per page)
    paginator = Paginator(scores_with_rank, 100)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)


    # Add current player's score if it's not visible on the current page
    current_player_score = None
    if request.user.is_authenticated:
        try:
            user_score = next(s for s in scores_with_rank if s.user == request.user)
            if user_score not in page_obj:
                current_player_score = user_score
                current_player_score.unlocked_memories_percent = (current_player_score.unlocked_memories / 60) * 100  # 💡 přidat!
        except StopIteration:
            pass

    # Render the scoreboard page
    return render(request, "score/scoreboard.html", {
        "page_obj": page_obj,
        "sort": sort_field,
        "current_player_score": current_player_score,
    })

def api_docs(request):
    """
    Loads the API documentation (Markdown) and renders it as HTML.
    """

    # Load the Markdown file
    md_path = Path("docs/api.md")
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Convert Markdown content to HTML using Python-Markdown
    html_content = markdown.markdown(md_content, extensions=["extra", "tables"])


    # Render the API documentation page
    return render(request, "score/api_docs.html", {
        "html_content": html_content
    })