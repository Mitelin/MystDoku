from django.test import SimpleTestCase
from django.urls import reverse, resolve
from score import views, api

class ScoreURLTests(SimpleTestCase):
    # Test that the scoreboard URL resolves to the correct view function
    def test_scoreboard_url(self):
        url = reverse("scoreboard")
        self.assertEqual(resolve(url).func, views.scoreboard)

    # Test that the API URL for the scoreboard resolves to the correct API view
    def test_api_scoreboard_url(self):
        url = reverse("api_scoreboard")
        self.assertEqual(resolve(url).func, api.api_scoreboard)

    # Test that the API documentation URL resolves to the correct view
    def test_api_docs_url(self):
        url = reverse("api_docs")
        self.assertEqual(resolve(url).func, views.api_docs)
