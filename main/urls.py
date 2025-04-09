from django.urls import path
from .views import home_landing, play_redirect, fallback_redirect

urlpatterns = [
    path('', home_landing, name='main_page'),
    path('play_redirect/', play_redirect, name='play_redirect'),
    path('<path:unused_path>', fallback_redirect),
]

