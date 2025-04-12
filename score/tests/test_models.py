from django.test import TestCase
from django.contrib.auth.models import User
from score.models import PlayerScore

class PlayerScoreModelTest(TestCase):
    def setUp(self):
        # Create a user and associated PlayerScore instance
        self.user = User.objects.create_user(username="tester", password="test123")
        self.score = PlayerScore.objects.create(user=self.user)

    # Test that all default fields on PlayerScore are correctly initialized
    def test_str_fields_defaults_and_types(self):
        """Score fields should have correct defaults and types"""
        self.assertEqual(self.score.total_completed_games, 0)
        self.assertIsNone(self.score.total_completed_time)
        self.assertEqual(self.score.completed_easy, 0)
        self.assertIsNone(self.score.best_time_easy)
        self.assertEqual(self.score.unlocked_memories, 0)

    # Test that each PlayerScore is linked to a specific user
    def test_score_linked_to_user(self):
        """Each PlayerScore must be linked to one user"""
        self.assertEqual(self.score.user.username, "tester")

    # Test that update_unlocked_memories() computes correct total from story progress
    def test_update_unlocked_memories_counts_correctly(self):
        """
        update_unlocked_memories should calculate memory count from PlayerStoryProgress
        """
        # Manually create PlayerStoryProgress with 3 total unlocked memories
        from gameplay.models import PlayerStoryProgress
        PlayerStoryProgress.objects.create(
            player=self.user,
            unlocked_easy=[1, 2],
            unlocked_medium=[10],
            unlocked_hard=[]
        )

        # Call update method and check updated memory count
        self.score.update_unlocked_memories()
        self.score.refresh_from_db()
        self.assertEqual(self.score.unlocked_memories, 3)
