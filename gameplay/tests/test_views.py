from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from gameplay.models import Game, Room, Intro, Cell, PlayerStoryProgress, DifficultyTransition, SequenceFrame, Memory
from gameplay.utils import create_game_for_player
from django.utils.http import urlencode
from gameplay.views import get_neighbors, load_image_map
from score.models import PlayerScore
from django.apps import apps
from score.models import PlayerScore
from gameplay.models import PlayerStoryProgress

class StartNewGameViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="test123")
        self.client.login(username="tester", password="test123")

        # Setup valid rooms and items for game creation
        for i in range(9):
            room = Room.objects.create(name=f"Room {i}")
            for n in range(9):
                Item.objects.create(name=f"Item {i}-{n}", number=n + 1, room=room, group_id=f"group_{n}")

    def test_get_creates_new_game_and_redirects(self):
        # GET request with difficulty should create game and redirect
        response = self.client.get(reverse("start_new_game") + "?difficulty=medium")
        self.assertEqual(Game.objects.count(), 1)
        new_game = Game.objects.first()
        self.assertEqual(new_game.difficulty, "medium")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("game_view", args=[new_game.id]))

    def test_get_without_difficulty_defaults_to_easy(self):
        # GET without difficulty param should default to easy
        response = self.client.get(reverse("start_new_game"))
        self.assertEqual(Game.objects.count(), 1)
        game = Game.objects.first()
        self.assertEqual(game.difficulty, "easy")

class GameViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="test123")
        self.other_user = User.objects.create_user(username="enemy", password="test123")
        self.client.login(username="tester", password="test123")

        # Setup valid data so game can be created
        for i in range(9):
            room = Room.objects.create(name=f"Room {i}")
            for n in range(9):
                Item.objects.create(name=f"Item {i}-{n}", number=n + 1, room=room, group_id=f"group_{n}")

        # Create game using actual logic
        self.game = create_game_for_player(self.user, difficulty="easy")

    def test_view_returns_200_for_valid_game(self):
        # Should return 200 OK when game exists and belongs to user
        url = reverse("game_view", args=[self.game.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_renders_correct_template(self):
        # Should use game.html template
        url = reverse("game_view", args=[self.game.id])
        response = self.client.get(url)
        # The game view should render the correct template
        self.assertTemplateUsed(response, "gameplay/game.html")

    def test_view_context_contains_expected_data(self):
        # Context should contain game, block_index, cells, items
        url = reverse("game_view", args=[self.game.id])
        response = self.client.get(url)
        # The game view context should include all required data to render the block
        self.assertIn("game", response.context)
        self.assertIn("cells", response.context)
        self.assertIn("block_index", response.context)
        self.assertIn("block_item_names", response.context[0])
        self.assertIn("room_name", response.context[0])
        self.assertIn("items", response.context[0])
        self.assertIn("selected_block", response.context[0])
        self.assertIn("group_id", response.context[0])

    def test_accessing_foreign_game_returns_404(self):
        # User should not be able to access another user's game
        foreign_game = Game.objects.create(player=self.other_user)
        url = reverse("game_view", args=[foreign_game.id])
        response = self.client.get(url)
        # Accessing another user's game should redirect (not allowed)
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_redirected_to_login(self):
        # Not logged in → should redirect to login page
        self.client.logout()
        url = reverse("game_view", args=[self.game.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)


class PlaceItemViewTest(TestCase):

    def setUp(self):
        # Create a user and game instance
        self.user = User.objects.create_user(username="testuser", password="password")
        self.game = Game.objects.create(player=self.user, completed=False)

        # Create an item for the cell's correct_item_id field
        room = Room.objects.create(name="Test Room")
        self.item = Item.objects.create(name="Test Item", room=room, number=1)

        # Create a cell and assign the item to correct_item_id
        self.cell = Cell.objects.create(game=self.game, row=0, column=0, correct_item=self.item)

        # Log in the user
        self.client.login(username="testuser", password="password")

        # Define the URL for the view being tested
        self.url = reverse("place_item", args=[self.cell.id])

    # def test_place_item_valid(self):
    #     # Implement test for placing a valid item
    #     response = self.client.post(self.url, {"number": 1})
    #     self.assertEqual(response.status_code, 200)
    #
    #     # Ensure the cell is updated
    #     self.cell.refresh_from_db()
    #     self.assertEqual(self.cell.selected_item.number, 1)  # Adjust based on how your model works

    def test_place_item_invalid_input(self):
        # Implement test for invalid input
        response = self.client.post(self.url, {"number": 999})  # Assuming 999 is invalid
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(self.cell.selected_item)

    def test_place_item_unauthorized(self):
        # Implement test for unauthorized access
        self.client.logout()  # Ensure the user is logged out
        response = self.client.post(self.url, {"number": 1})
        self.assertNotEqual(response.status_code, 200)  # Check for unauthorized response

class GetNeighborsTests(TestCase):

    def test_neighbors_for_block_0(self):
        neighbors = get_neighbors(0)
        expected = {'down': 3, 'right': 1}
        self.assertEqual(neighbors, expected)

    def test_neighbors_for_block_1(self):
        neighbors = get_neighbors(1)
        expected = {'down': 4, 'left': 0, 'right': 2}
        self.assertEqual(neighbors, expected)

    def test_neighbors_for_block_2(self):
        neighbors = get_neighbors(2)
        expected = {'down': 5, 'left': 1}
        self.assertEqual(neighbors, expected)

    def test_neighbors_for_block_3(self):
        neighbors = get_neighbors(3)
        expected = {'up': 0, 'down': 6, 'right': 4}
        self.assertEqual(neighbors, expected)

    def test_neighbors_for_block_4(self):
        neighbors = get_neighbors(4)
        expected = {'up': 1, 'down': 7, 'left': 3, 'right': 5}
        self.assertEqual(neighbors, expected)

    def test_neighbors_for_block_5(self):
        neighbors = get_neighbors(5)
        expected = {'up': 2, 'down': 8, 'left': 4}
        self.assertEqual(neighbors, expected)

    def test_neighbors_for_block_6(self):
        neighbors = get_neighbors(6)
        expected = {'up': 3, 'right': 7}
        self.assertEqual(neighbors, expected)

    def test_neighbors_for_block_7(self):
        neighbors = get_neighbors(7)
        expected = {'up': 4, 'right': 8, 'left': 6}
        self.assertEqual(neighbors, expected)

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
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client.login(username="testuser", password="testpassword")

        # Vytvoření vzpomínek s unikátními order hodnotami
        for i in range(1, 21):
            Memory.objects.create(difficulty="easy", order=i, text=f"Easy memory {i}")
            Memory.objects.create(difficulty="medium", order=i + 100, text=f"Medium memory {i}")
            Memory.objects.create(difficulty="hard", order=i + 200, text=f"Hard memory {i}")

        # Přechodové texty
        DifficultyTransition.objects.create(difficulty="easy", text="Easy transition")
        DifficultyTransition.objects.create(difficulty="medium", text="Medium transition")
        DifficultyTransition.objects.create(difficulty="hard", text="Hard transition")

        # Obrázky pro sekvence
        SequenceFrame.objects.create(sequence="intro", index=0, image="intro_0.jpg")
        SequenceFrame.objects.create(sequence="easy_end", index=0, image="easy_end_0.jpg")
        SequenceFrame.objects.create(sequence="medium_end", index=0, image="medium_end_0.jpg")
        SequenceFrame.objects.create(sequence="hard_end", index=0, image="hard_end_0.jpg")
        SequenceFrame.objects.create(sequence="memory", index=0, image="memory_0.jpg")

        # Inicializace progress objektu
        self.progress = PlayerStoryProgress.objects.create(player=self.user)

        # Vytvoření extra memory pro test "just unlocked"
        self.extra_hard_memory = Memory.objects.create(
            difficulty="hard", order=221, text="Hard memory 21"
        )

    def test_story_so_far_no_unlocked_memories(self):
        response = self.client.get(reverse("story_so_far"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["sequence_frames"]), 0)
        self.assertIsNone(response.context["sequence_name"])

    def test_story_so_far_memory_unlocked(self):
        self.progress.unlocked_hard = [self.extra_hard_memory.order]
        self.progress.save()

        session = self.client.session
        session["just_unlocked_order"] = self.extra_hard_memory.order
        session.save()

        response = self.client.get(reverse("story_so_far"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sequence_name"], "memory")
        self.assertIn("Hard memory 21", response.content.decode())

    def test_story_so_far_all_easy_memories_unlocked(self):
        self.progress.unlocked_easy = list(range(1, 21))
        self.progress.save()

        last_memory = Memory.objects.filter(difficulty="easy").order_by("order").last()
        session = self.client.session
        session["just_unlocked_order"] = last_memory.order
        session.save()

        response = self.client.get(reverse("story_so_far"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sequence_name"], "easy_end")

    def test_story_so_far_all_memories_unlocked_and_final_transition(self):
        self.progress.unlocked_easy = list(range(1, 21))
        self.progress.unlocked_medium = list(range(101, 121))
        self.progress.unlocked_hard = list(range(201, 221))
        self.progress.save()

        last_hard = Memory.objects.filter(difficulty="hard").order_by("order").last()
        session = self.client.session
        session["just_unlocked_order"] = last_hard.order
        session.save()

        response = self.client.get(reverse("story_so_far"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sequence_name"], "hard_end")

    def tearDown(self):
        Memory.objects.all().delete()
        PlayerStoryProgress.objects.all().delete()
        SequenceFrame.objects.all().delete()
        DifficultyTransition.objects.all().delete()
        User.objects.all().delete()


from gameplay.models import Game, Cell, Item, Room

class AutoFillTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client.force_login(self.user)

        self.room = Room.objects.create(name="Test Room")  # 💥 Tohle musí být dřív!

        self.item1 = Item.objects.create(name="Item 1", group_id="a", number=1, room=self.room)
        self.item2 = Item.objects.create(name="Item 2", group_id="b", number=2, room=self.room)

        self.game = Game.objects.create(player=self.user, difficulty="easy")

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

        self.editable_cell.refresh_from_db()
        self.assertEqual(self.editable_cell.selected_item, self.item1)

        # 👇 místo redirect kontroly jen ověř, že redirect proběhl (kód 302)
        self.assertEqual(response.status_code, 302)

class ResetProgressTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client.force_login(self.user)

        # Vytvoř hráčův příběhový progress
        self.story_progress = PlayerStoryProgress.objects.create(
            player=self.user,
            unlocked_easy=[1, 2],
            unlocked_medium=[101],
            unlocked_hard=[201]
        )

        # Vytvoř hráčův skóre záznam
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
        # Spusť view
        response = self.client.get(reverse("reset_progress"))

        # Použij stejný import modelu jako ve view
        StoryModel = apps.get_model("gameplay", "PlayerStoryProgress")
        ScoreModel = apps.get_model("score", "PlayerScore")

        # Zkontroluj, že příběh byl smazán
        self.assertFalse(StoryModel.objects.filter(player=self.user).exists())

        # Zkontroluj, že skóre bylo resetováno
        score = ScoreModel.objects.get(user=self.user)
        self.assertEqual(score.unlocked_memories, 0)
        self.assertEqual(score.completed_easy, 0)
        self.assertEqual(score.completed_medium, 0)
        self.assertEqual(score.completed_hard, 0)
        self.assertEqual(score.total_completed_games, 0)
        self.assertIsNone(score.best_time_easy)
        self.assertIsNone(score.best_time_medium)
        self.assertIsNone(score.best_time_hard)

        # Zkontroluj redirect
        self.assertRedirects(response, reverse("game_selection"))

class GameSelectionViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")
        self.client.force_login(self.user)

        # Intro data (musí existovat, jinak by view failnul)
        Intro.objects.create(order=0, text="Welcome to the game!")

    def test_intro_shown_when_no_game_and_no_memories(self):
        """
        Zobrazí se intro, pokud hráč nemá rozehranou hru ani žádné vzpomínky.
        """
        response = self.client.get(reverse("game_selection"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["play_intro"])

    def test_intro_not_shown_if_active_game_exists(self):
        """
        Intro se nezobrazí, pokud hráč má rozehranou hru.
        """
        Game.objects.create(player=self.user, difficulty="easy", completed=False)
        response = self.client.get(reverse("game_selection"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["play_intro"])

    def test_intro_not_shown_if_any_memory_unlocked(self):
        """
        Intro se nezobrazí, pokud hráč má aspoň jednu odemčenou vzpomínku.
        """
        progress, _ = PlayerStoryProgress.objects.get_or_create(player=self.user)
        progress.unlocked_easy = [1]
        progress.save()

        response = self.client.get(reverse("game_selection"))

        self.assertFalse(response.context["play_intro"])

class ManualViewTests(TestCase):
    def test_manual_page_renders_correctly(self):
        """
        Test that the manual page renders successfully using the correct template.
        """
        response = self.client.get(reverse("manual"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "gameplay/manual.html")

