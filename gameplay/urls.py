from django.urls import path
from .views import (start_new_game, game_view, place_item, auto_fill, reset_progress, debug_add_memory,
                    game_selection, manual_view)
from gameplay.views import story_so_far

urlpatterns = [
    path('start/', start_new_game, name='start_new_game'),
    path('<uuid:game_id>/', game_view, name='game_view'),  # UUID instead of int
    path('place/<int:cell_id>/', place_item, name='place_item'),
    path('<uuid:game_id>/block/<int:block_index>/', game_view, name='game_block'),  # URL pro block ID
    path("story/", story_so_far, name="story_so_far"),
    path("auto_fill/<uuid:game_id>/", auto_fill, name="auto_fill"),
    path("debug/reset_progress/", reset_progress, name="reset_progress"),
    path("debug/add_memory/<str:difficulty>/", debug_add_memory, name="debug_add_memory"),
    path('game/', game_selection, name='game_selection'),
    path("manual/", manual_view, name="manual"),
]
