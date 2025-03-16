from django.urls import path
from .views import start_new_game, game_view, place_item, win_view

urlpatterns = [
    path('start/', start_new_game, name='start_new_game'),
    path('<int:game_id>/', game_view, name='game_view'),
    path('place/<int:cell_id>/', place_item, name='place_item'),
    path('win/', win_view, name='win_page'),
    path('game/<int:game_id>/block/<int:block_index>/', game_view, name='game_block'),  # URL pro block ID
]