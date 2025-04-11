from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from score.models import PlayerScore
from pathlib import Path

class ScoreboardViewTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="alice", password="pass")
        self.user2 = User.objects.create_user(username="bob", password="pass")
        self.user3 = User.objects.create_user(username="carol", password="pass")

        PlayerScore.objects.create(user=self.user1, completed_easy=5, unlocked_memories=30, total_completed_games=10)
        PlayerScore.objects.create(user=self.user2, completed_easy=10, unlocked_memories=40, total_completed_games=12)
        PlayerScore.objects.create(user=self.user3, completed_easy=3, unlocked_memories=10, total_completed_games=5)

    def test_scoreboard_basic_renders(self):
        response = self.client.get(reverse("scoreboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "score/scoreboard.html")

    def test_sorting_by_completed_easy(self):
        response = self.client.get(reverse("scoreboard") + "?sort=completed_easy")
        scores = list(response.context["page_obj"])
        self.assertGreaterEqual(scores[0].completed_easy, scores[1].completed_easy)

    def test_unlocked_percent_computation(self):
        response = self.client.get(reverse("scoreboard"))
        scores = list(response.context["page_obj"])
        for score in scores:
            expected_percent = (score.unlocked_memories / 60) * 100
            self.assertAlmostEqual(score.unlocked_memories_percent, expected_percent)

    def test_current_user_score_highlighted(self):
        # Přidáme 110 dalších hráčů, aby byl uživatel mimo první stránku
        for i in range(110):
            u = User.objects.create_user(username=f"extra{i}")
            PlayerScore.objects.create(user=u, completed_easy=99, unlocked_memories=50, total_completed_games=100)

        self.client.login(username="alice", password="pass")
        response = self.client.get(reverse("scoreboard"))

        # ✅ alice není na první stránce, proto by měla být zvýrazněná mimo page_obj
        self.assertIsNotNone(response.context["current_player_score"])
        self.assertEqual(response.context["current_player_score"].user.username, "alice")

class ApiDocsViewTests(TestCase):
    def setUp(self):
        self.md_path = Path("docs/api.md")
        self.md_path.parent.mkdir(exist_ok=True)
        self.md_path.write_text("# API Docs\n\nThis is test content.", encoding="utf-8")

    def tearDown(self):
        self.md_path.unlink()  # smažeme testovací markdown

    def test_api_docs_renders_markdown(self):
        response = self.client.get(reverse("api_docs"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>API Docs</h1>")
        self.assertContains(response, "<p>This is test content.</p>")