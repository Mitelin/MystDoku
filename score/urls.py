from django.urls import path
from . import views
from . import api
from .views import api_docs

urlpatterns = [
    path("", views.scoreboard, name="scoreboard"),
    path("api/scoreboard/", api.api_scoreboard, name="api_scoreboard"),
    path("api/docs/", api_docs, name="api_docs"),
]