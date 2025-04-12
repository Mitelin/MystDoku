from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from gameplay.utils import create_game_for_player
from gameplay.views import get_neighbors, load_image_map
from django.apps import apps
from score.models import PlayerScore
from gameplay.models import Game, Cell, Item, Room, Intro, DifficultyTransition, SequenceFrame, Memory, PlayerStoryProgress

class StartNewGameViewTest(TestCase):

    def setUp(self):
        # Create and log in a test user
        self.user = User.objects.create_user(username="tester", password="test123")
        self.client.login(username="tester", password="test123")

        # Set up 9 valid rooms, each with 9 unique items (numbers 1–9 with distinct group_ids)
        for i in range(9):
            room = Room.objects.create(name=f"Room {i}")
            for n in range(9):
                Item.objects.create(
                    name=f"Item {i}-{n}",
                    number=n + 1,
                    room=room,
                    group_id=f"group_{n}"
                )

    # Test that sending a GET request with a difficulty parameter creates a new game and redirects
    def test_get_creates_new_game_and_redirects(self):
        response = self.client.get(reverse("start_new_game") + "?difficulty=medium")

        # Verify a game was created
        self.assertEqual(Game.objects.count(), 1)
        new_game = Game.objects.first()
        self.assertEqual(new_game.difficulty, "medium")

        # Verify the response is a redirect to the game view
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("game_view", args=[new_game.id]))

    # Test that if no difficulty is provided, the view defaults to "easy"
    def test_get_without_difficulty_defaults_to_easy(self):
        response = self.client.get(reverse("start_new_game"))

        # Verify a game was created with default difficulty
        self.assertEqual(Game.objects.count(), 1)
        game = Game.objects.first()
        self.assertEqual(game.difficulty, "easy")


class GameViewTest(TestCase):

    def setUp(self):
        # Create two users: one for the current session, one to simulate unauthorized access
        self.user = User.objects.create_user(username="tester", password="test123")
        self.other_user = User.objects.create_user(username="enemy", password="test123")
        self.client.login(username="tester", password="test123")

        # Prepare valid data to allow a game to be created:
        # 9 rooms, each with 9 unique items (numbers 1–9)
        for i in range(9):
            room = Room.objects.create(name=f"Room {i}")
            for n in range(9):
                Item.objects.create(
                    name=f"Item {i}-{n}",
                    number=n + 1,
                    room=room,
                    group_id=f"group_{n}"
                )

        # Create a valid game for the current user using real creation logic
        self.game = create_game_for_player(self.user, difficulty="easy")

    # Test that the game view returns HTTP 200 OK when accessed by the game's owner
    def test_view_returns_200_for_valid_game(self):
        url = reverse("game_view", args=[self.game.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # Test that the correct template is used to render the game view
    def test_view_renders_correct_template(self):
        url = reverse("game_view", args=[self.game.id])
        response = self.client.get(url)
        self.assertTemplateUsed(response, "gameplay/game.html")

    # Test that the context passed to the template contains all expected keys and data
    def test_view_context_contains_expected_data(self):
        url = reverse("game_view", args=[self.game.id])
        response = self.client.get(url)

        # Confirm the presence of primary context variables
        self.assertIn("game", response.context)
        self.assertIn("cells", response.context)
        self.assertIn("block_index", response.context)

        # Also confirm nested context data inside context[0] (possibly from a context processor or for loop)
        self.assertIn("block_item_names", response.context[0])
        self.assertIn("room_name", response.context[0])
        self.assertIn("items", response.context[0])
        self.assertIn("selected_block", response.context[0])
        self.assertIn("group_id", response.context[0])

    # Test that trying to access another user's game results in a redirect (403-like protection)
    def test_accessing_foreign_game_returns_404(self):
        foreign_game = Game.objects.create(player=self.other_user)
        url = reverse("game_view", args=[foreign_game.id])
        response = self.client.get(url)

        # Access to a foreign game should be denied → redirect to home or 404
        self.assertEqual(response.status_code, 302)

    # Test that anonymous users are redirected to the login page when trying to access the game view
    def test_anonymous_user_redirected_to_login(self):
        self.client.logout()
        url = reverse("game_view", args=[self.game.id])
        response = self.client.get(url)

        # Check for redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)



class PlaceItemViewTest(TestCase):

    def setUp(self):
        # Create a user and log them in
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.login(username="testuser", password="password")

        # Create a game instance for the user
        self.game = Game.objects.create(player=self.user, completed=False)

        # Create a room and an item to be used as the correct item in a cell
        room = Room.objects.create(name="Test Room")
        self.item = Item.objects.create(name="Test Item", room=room, number=1)

        # Create a cell in the game with the correct item assigned
        self.cell = Cell.objects.create(
            game=self.game,
            row=0,
            column=0,
            correct_item=self.item
        )

        # Store the URL for the place_item view
        self.url = reverse("place_item", args=[self.cell.id])

    # Test that a valid item number can be placed into the cell (currently commented out)
    # def test_place_item_valid(self):
    #     response = self.client.post(self.url, {"number": 1})
    #     self.assertEqual(response.status_code, 200)
    #
    #     # Reload cell from database and check if the correct item was set
    #     self.cell.refresh_from_db()
    #     self.assertEqual(self.cell.selected_item.number, 1)

    # Test that posting an invalid item number (e.g., 999) returns a 400 Bad Request
    def test_place_item_invalid_input(self):
        response = self.client.post(self.url, {"number": 999})  # 999 assumed to not exist
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(self.cell.selected_item)

    # Test that a user who is not authenticated cannot place an item
    def test_place_item_unauthorized(self):
        self.client.logout()  # Log the user out
        response = self.client.post(self.url, {"number": 1})

        # Should not return 200 → user is not authorized
        self.assertNotEqual(response.status_code, 200)


class GetNeighborsTests(TestCase):

    # Test that block 0 (top-left corner) has neighbors to the right and below
    def test_neighbors_for_block_0(self):
        neighbors = get_neighbors(0)
        expected = {'down': 3, 'right': 1}
        self.assertEqual(neighbors, expected)

    # Test that block 1 (top-middle) has neighbors on all sides except up
    def test_neighbors_for_block_1(self):
        neighbors = get_neighbors(1)
        expected = {'down': 4, 'left': 0, 'right': 2}
        self.assertEqual(neighbors, expected)

    # Test that block 2 (top-right corner) has neighbors to the left and below
    def test_neighbors_for_block_2(self):
        neighbors = get_neighbors(2)
        expected = {'down': 5, 'left': 1}
        self.assertEqual(neighbors, expected)

    # Test that block 3 (middle-left) has neighbors above, below, and to the right
    def test_neighbors_for_block_3(self):
        neighbors = get_neighbors(3)
        expected = {'up': 0, 'down': 6, 'right': 4}
        self.assertEqual(neighbors, expected)

    # Test that block 4 (center block) has neighbors in all four directions
    def test_neighbors_for_block_4(self):
        neighbors = get_neighbors(4)
        expected = {'up': 1, 'down': 7, 'left': 3, 'right': 5}
        self.assertEqual(neighbors, expected)

    # Test that block 5 (middle-right) has neighbors above, below, and to the left
    def test_neighbors_for_block_5(self):
        neighbors = get_neighbors(5)
        expected = {'up': 2, 'down': 8, 'left': 4}
        self.assertEqual(neighbors, expected)

    # Test that block 6 (bottom-left corner) has neighbors above and to the right
    def test_neighbors_for_block_6(self):
        neighbors = get_neighbors(6)
        expected = {'up': 3, 'right': 7}
        self.assertEqual(neighbors, expected)

    # Test that block 7 (bottom-middle) has neighbors on all sides except down
    def test_neighbors_for_block_7(self):
        neighbors = get_neighbors(7)
        expected = {'up': 4, 'right': 8, 'left': 6}
        self.assertEqual(neighbors, expected)

    # Test that block 8 (bottom-right corner) has neighbors above and to the left
    def test_neighbors_for_block_8(self):
        neighbors = get_neighbors(8)
        expected = {'up': 5, 'left': 7}
        self.assertEqual(neighbors, expected)



class LoadImageMapTests(TestCase):
    """
    Tests for the `load_image_map` function in the gameplay views.
    """

    def setUp(self):
        """
        Setup test data for the SequenceFrame model.
        """
        # Create a valid sequence with frames
        self.sequence_name = "intro"
        SequenceFrame.objects.create(sequence=self.sequence_name, index=0, image="image0.jpg")
        SequenceFrame.objects.create(sequence=self.sequence_name, index=1, image="image1.jpg")
        SequenceFrame.objects.create(sequence=self.sequence_name, index=2, image="image2.jpg")

        # Create a different sequence with no frames
        self.empty_sequence_name = "memory"

    def test_load_image_map_valid_sequence(self):
        """
        Test for a valid sequence name with frames.
        """
        # Act
        result = load_image_map(self.sequence_name)

        # Expected output (mapping frame indexes to image filenames)
        expected_result = {
            0: "image0.jpg",
            1: "image1.jpg",
            2: "image2.jpg"
        }

        # Assert that the result matches the expected output
        self.assertEqual(result, expected_result)

    def test_load_image_map_empty_sequence(self):
        """
        Test for an empty sequence name (no frames in the sequence).
        """
        # Act
        result = load_image_map(self.empty_sequence_name)

        # Assert that the result is an empty dictionary since no frames exist
        self.assertEqual(result, {})

    def test_load_image_map_invalid_sequence(self):
        """
        Test for an invalid sequence name (non-existent sequence).
        """
        # Act
        result = load_image_map("non_existent_sequence")

        # Assert that the result is an empty dictionary for a non-existent sequence
        self.assertEqual(result, {})

    def tearDown(self):
        """
        Cleanup the database after each test.
        """
        SequenceFrame.objects.all().delete()


class StorySoFarTests(TestCase):
    """
    Tests for the story_so_far view function.
    """

    def setUp(self):
        # Create and log in a test user
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client.login(username="testuser", password="testpassword")

        # Create 20 memories per difficulty (easy, medium, hard)
        for i in range(1, 21):
            Memory.objects.create(difficulty="easy", order=i, text=f"Easy memory {i}")
            Memory.objects.create(difficulty="medium", order=i + 100, text=f"Medium memory {i}")
            Memory.objects.create(difficulty="hard", order=i + 200, text=f"Hard memory {i}")

        # Create one transition message per difficulty
        DifficultyTransition.objects.create(difficulty="easy", text="Easy transition")
        DifficultyTransition.objects.create(difficulty="medium", text="Medium transition")
        DifficultyTransition.objects.create(difficulty="hard", text="Hard transition")

        # Add placeholder images for all sequence types
        SequenceFrame.objects.create(sequence="intro", index=0, image="intro_0.jpg")
        SequenceFrame.objects.create(sequence="easy_end", index=0, image="easy_end_0.jpg")
        SequenceFrame.objects.create(sequence="medium_end", index=0, image="medium_end_0.jpg")
        SequenceFrame.objects.create(sequence="hard_end", index=0, image="hard_end_0.jpg")
        SequenceFrame.objects.create(sequence="memory", index=0, image="memory_0.jpg")

        # Create a blank story progress object for the user
        self.progress = PlayerStoryProgress.objects.create(player=self.user)

        # Create an extra hard memory used to simulate "just unlocked" behavior
        self.extra_hard_memory = Memory.objects.create(
            difficulty="hard", order=221, text="Hard memory 21"
        )

    # Test when no memories have been unlocked — no sequence should be played
    def test_story_so_far_no_unlocked_memories(self):
        response = self.client.get(reverse("story_so_far"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["sequence_frames"]), 0)
        self.assertIsNone(response.context["sequence_name"])

    # Test that unlocking a single memory shows the memory sequence
    def test_story_so_far_memory_unlocked(self):
        self.progress.unlocked_hard = [self.extra_hard_memory.order]
        self.progress.save()

        # Simulate that this memory was just unlocked
        session = self.client.session
        session["just_unlocked_order"] = self.extra_hard_memory.order
        session.save()

        response = self.client.get(reverse("story_so_far"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sequence_name"], "memory")
        self.assertIn("Hard memory 21", response.content.decode())

    # Test that unlocking all easy memories triggers the easy_end sequence
    def test_story_so_far_all_easy_memories_unlocked(self):
        self.progress.unlocked_easy = list(range(1, 21))
        self.progress.save()

        # Simulate the last unlocked memory was the final one in easy
        last_memory = Memory.objects.filter(difficulty="easy").order_by("order").last()
        session = self.client.session
        session["just_unlocked_order"] = last_memory.order
        session.save()

        response = self.client.get(reverse("story_so_far"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sequence_name"], "easy_end")

    # Test that unlocking all memories (easy + medium + hard) triggers the hard_end (final) sequence
    def test_story_so_far_all_memories_unlocked_and_final_transition(self):
        self.progress.unlocked_easy = list(range(1, 21))
        self.progress.unlocked_medium = list(range(101, 121))
        self.progress.unlocked_hard = list(range(201, 221))
        self.progress.save()

        # Simulate that the last hard memory was just unlocked
        last_hard = Memory.objects.filter(difficulty="hard").order_by("order").last()
        session = self.client.session
        session["just_unlocked_order"] = last_hard.order
        session.save()

        response = self.client.get(reverse("story_so_far"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sequence_name"], "hard_end")

    # Clean up all test data after each test
    def tearDown(self):
        Memory.objects.all().delete()
        PlayerStoryProgress.objects.all().delete()
        SequenceFrame.objects.all().delete()
        DifficultyTransition.objects.all().delete()
        User.objects.all().delete()


class AutoFillTests(TestCase):
    def setUp(self):
        # Create and log in a test user
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client.force_login(self.user)

        # Create a room before adding items (required by Item)
        self.room = Room.objects.create(name="Test Room")  # 💥 Must come first!

        # Create two items with distinct numbers and group IDs
        self.item1 = Item.objects.create(name="Item 1", group_id="a", number=1, room=self.room)
        self.item2 = Item.objects.create(name="Item 2", group_id="b", number=2, room=self.room)

        # Create a new game for the user
        self.game = Game.objects.create(player=self.user, difficulty="easy")

        # Create two cells in the game with correct items assigned (but not prefilled)
        self.cell1 = Cell.objects.create(
            game=self.game,
            row=0,
            column=0,
            prefilled=False,
            correct_item=self.item1,
        )
        self.cell2 = Cell.objects.create(
            game=self.game,
            row=0,
            column=1,
            prefilled=False,
            correct_item=self.item2,
        )

        # Editable test cell that should be autofilled
        self.editable_cell = Cell.objects.create(
            game=self.game,
            row=0,
            column=0,
            prefilled=False,
            correct_item=self.item1,
        )

    def test_autofill_sets_correct_items(self):
        """
        Test that all editable cells are filled with correct items after autofill.
        """
        url = reverse("auto_fill", args=[self.game.id])
        response = self.client.get(url)

        # Reload the cell to check if it has been updated
        self.editable_cell.refresh_from_db()
        self.assertEqual(self.editable_cell.selected_item, self.item1)

        # Confirm that the view redirected after autofill (status code 302)
        self.assertEqual(response.status_code, 302)

class ResetProgressTests(TestCase):
    def setUp(self):
        # Create and log in a test user
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client.force_login(self.user)

        # Create story progress with unlocked memories in all difficulty levels
        self.story_progress = PlayerStoryProgress.objects.create(
            player=self.user,
            unlocked_easy=[1, 2],
            unlocked_medium=[101],
            unlocked_hard=[201]
        )

        # Create a score record for the user with non-zero values
        self.score = PlayerScore.objects.create(
            user=self.user,
            unlocked_memories=3,
            completed_easy=3,
            completed_medium=2,
            completed_hard=1,
            total_completed_games=6,
            best_time_easy=123,
            best_time_medium=234,
            best_time_hard=345,
        )

    def test_reset_progress_deletes_story_progress_and_resets_score(self):
        # Call the reset_progress view
        response = self.client.get(reverse("reset_progress"))

        # Import models using apps registry to match the way it's done in the actual view
        StoryModel = apps.get_model("gameplay", "PlayerStoryProgress")
        ScoreModel = apps.get_model("score", "PlayerScore")

        # Check that the story progress was deleted
        self.assertFalse(StoryModel.objects.filter(player=self.user).exists())

        # Check that all fields in the score record were reset
        score = ScoreModel.objects.get(user=self.user)
        self.assertEqual(score.unlocked_memories, 0)
        self.assertEqual(score.completed_easy, 0)
        self.assertEqual(score.completed_medium, 0)
        self.assertEqual(score.completed_hard, 0)
        self.assertEqual(score.total_completed_games, 0)
        self.assertIsNone(score.best_time_easy)
        self.assertIsNone(score.best_time_medium)
        self.assertIsNone(score.best_time_hard)

        # Confirm the response redirected to the game selection screen
        self.assertRedirects(response, reverse("game_selection"))


class GameSelectionViewTests(TestCase):
    def setUp(self):
        # Create and log in a test user
        self.user = User.objects.create_user(username="tester", password="pass")
        self.client.force_login(self.user)

        # Intro text must exist or the view would fail when trying to show intro
        Intro.objects.create(order=0, text="Welcome to the game!")

    # Test that the intro is shown if the player has no active game and no unlocked memories
    def test_intro_shown_when_no_game_and_no_memories(self):
        """
        The intro sequence should be shown when the player has no ongoing game and no unlocked memories.
        """
        response = self.client.get(reverse("game_selection"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["play_intro"])

    # Test that the intro is NOT shown if the player has an ongoing game
    def test_intro_not_shown_if_active_game_exists(self):
        """
        The intro should be skipped if the player has an active game.
        """
        Game.objects.create(player=self.user, difficulty="easy", completed=False)
        response = self.client.get(reverse("game_selection"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["play_intro"])

    # Test that the intro is NOT shown if the player has any unlocked memory
    def test_intro_not_shown_if_any_memory_unlocked(self):
        """
        The intro should be skipped if the player has at least one unlocked memory.
        """
        progress, _ = PlayerStoryProgress.objects.get_or_create(player=self.user)
        progress.unlocked_easy = [1]  # Simulate memory unlocked
        progress.save()

        response = self.client.get(reverse("game_selection"))
        self.assertFalse(response.context["play_intro"])

class ManualViewTests(TestCase):
    # Test that the manual view loads successfully and uses the correct template
    def test_manual_page_renders_correctly(self):
        """
        Test that the manual page renders successfully using the correct template.
        """
        response = self.client.get(reverse("manual"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "gameplay/manual.html")

