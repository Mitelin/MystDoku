from django.urls import path
from .views import home_landing, play_redirect, game_selection

urlpatterns = [
    path('', home_landing, name='main_page'),
    path('play_redirect/', play_redirect, name='play_redirect'),
    path('game/', game_selection, name='game_selection'),
]