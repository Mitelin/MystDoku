from django.urls import path
from .views import start_new_game, game_view, place_item

urlpatterns = [
    path('start/', start_new_game, name='start_new_game'), # URL for game creation
    path('<int:game_id>/', game_view, name='game_view'),
    path('place/<int:cell_id>/<int:item_id>/', place_item, name='place_item'),# URL for game display
]