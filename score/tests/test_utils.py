from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from gameplay.models import Game
from score.models import PlayerScore
from score.utils import update_score_for_game
import time


class UpdateScoreForGameTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")

    def test_easy_score_is_updated_correctly(self):
        game = Game.objects.create(player=self.user, difficulty="easy")
        game.created_at = timezone.now() - timezone.timedelta(seconds=100)
        game.save()

        update_score_for_game(game)

        score = PlayerScore.objects.get(user=self.user)
        self.assertEqual(score.total_completed_games, 1)
        self.assertEqual(score.completed_easy, 1)
        self.assertAlmostEqual(score.best_time_easy, 100, delta=1)

    def test_medium_score_is_updated_correctly(self):
        game = Game.objects.create(player=self.user, difficulty="medium")
        game.created_at = timezone.now() - timezone.timedelta(seconds=200)
        game.save()

        update_score_for_game(game)

        score = PlayerScore.objects.get(user=self.user)
        self.assertEqual(score.completed_medium, 1)
        self.assertAlmostEqual(score.best_time_medium, 200, delta=1)

    def test_hard_score_is_updated_correctly(self):
        game = Game.objects.create(player=self.user, difficulty="hard")
        game.created_at = timezone.now() - timezone.timedelta(seconds=300)
        game.save()

        update_score_for_game(game)

        score = PlayerScore.objects.get(user=self.user)
        self.assertEqual(score.completed_hard, 1)
        self.assertAlmostEqual(score.best_time_hard, 300, delta=1)

    def test_best_time_only_updates_if_better(self):
        # First run - 120s
        game1 = Game.objects.create(player=self.user, difficulty="easy")
        game1.created_at = timezone.now() - timezone.timedelta(seconds=120)
        game1.save()
        update_score_for_game(game1)

        # Second run - 150s (worse)
        game2 = Game.objects.create(player=self.user, difficulty="easy")
        game2.created_at = timezone.now() - timezone.timedelta(seconds=150)
        game2.save()
        update_score_for_game(game2)

        score = PlayerScore.objects.get(user=self.user)
        self.assertAlmostEqual(score.best_time_easy, 120, delta=1)

    def test_best_time_is_updated_if_better(self):
        # First run - 200s
        game1 = Game.objects.create(player=self.user, difficulty="medium")
        game1.created_at = timezone.now() - timezone.timedelta(seconds=200)
        game1.save()
        update_score_for_game(game1)

        # Second run - 100s (better)
        game2 = Game.objects.create(player=self.user, difficulty="medium")
        game2.created_at = timezone.now() - timezone.timedelta(seconds=100)
        game2.save()
        update_score_for_game(game2)

        score = PlayerScore.objects.get(user=self.user)
        self.assertAlmostEqual(score.best_time_medium, 100, delta=1)