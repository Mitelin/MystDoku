from django.test import SimpleTestCase
from django.urls import reverse, resolve
from score import views, api


class ScoreURLTests(SimpleTestCase):
    def test_scoreboard_url(self):
        url = reverse("scoreboard")
        self.assertEqual(resolve(url).func, views.scoreboard)

    def test_api_scoreboard_url(self):
        url = reverse("api_scoreboard")
        self.assertEqual(resolve(url).func, api.api_scoreboard)

    def test_api_docs_url(self):
        url = reverse("api_docs")
        self.assertEqual(resolve(url).func, views.api_docs)