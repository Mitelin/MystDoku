from django.core.paginator import Paginator
from .models import PlayerScore
import markdown
from django.shortcuts import render
from pathlib import Path
from datetime import timedelta , datetime
from django.utils.timezone import make_aware

# Precomputed aware datetime for fallback sorting (avoids recomputing each time)
AWARE_MAX_DATETIME = make_aware(datetime.max.replace(microsecond=0))

# Helper function to safely handle None values when sorting
# If the value is None, it returns a large default to ensure proper sorting (last)
# is_time=True → use max datetime (for DateTimeFields)
# is_time=False → use float("inf") (for FloatFields)
def safe_value(val, is_time=True):
    if val is None:
        return AWARE_MAX_DATETIME if is_time else float("inf")
    return val

# Main view for the scoreboard page
def scoreboard(request):
    # Get sort criteria from query (?sort=...)
    sort_field = request.GET.get("sort", "total_completed_games")

    # Load all scores from the database
    all_scores = list(PlayerScore.objects.all())

    # Apply sorting based on the selected field
    if sort_field == "user__username":
        all_scores.sort(key=lambda s: s.user.username.lower())
    elif sort_field == "total_completed_games":
        all_scores.sort(key=lambda s: (-s.total_completed_games, safe_value(s.total_completed_time)))
    elif sort_field == "completed_easy":
        all_scores.sort(key=lambda s: (-s.completed_easy, safe_value(s.completed_easy_time)))
    elif sort_field == "completed_medium":
        all_scores.sort(key=lambda s: (-s.completed_medium, safe_value(s.completed_medium_time)))
    elif sort_field == "completed_hard":
        all_scores.sort(key=lambda s: (-s.completed_hard, safe_value(s.completed_hard_time)))
    elif sort_field == "unlocked_memories":
        all_scores.sort(key=lambda s: (-s.unlocked_memories, s.user.username.lower()))
    elif sort_field in ["best_time_easy", "best_time_medium", "best_time_hard"]:
        all_scores.sort(key=lambda s: safe_value(getattr(s, sort_field), is_time=False))
    else:
        # Fallback sort (by total completed games)
        all_scores.sort(key=lambda s: (-s.total_completed_games, safe_value(s.total_completed_time)))

    # Add ranking and memory percentage for each score
    scores_with_rank = []
    for idx, score in enumerate(all_scores, start=1):
        score.rank = idx
        score.unlocked_memories_percent = (score.unlocked_memories / 60) * 100
        scores_with_rank.append(score)

    # Paginate results (10 per page)
    paginator = Paginator(scores_with_rank, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # If the current user is not on the current page, highlight their score below
    current_player_score = None
    if request.user.is_authenticated:
        try:
            user_score = next(s for s in scores_with_rank if s.user == request.user)
            if user_score not in page_obj:
                current_player_score = user_score
        except StopIteration:
            pass  # User has no score yet

    # Render scoreboard template
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