from django.test import TestCase
from gameplay.models import Room, Item, Game, Cell, Intro, Memory, DifficultyTransition, PlayerStoryProgress,SequenceFrame
from django.contrib.auth.models import User
import uuid

class RoomModelTest(TestCase):

    def test_room_str_returns_name(self):
        """__str__ method should return the room name"""
        room = Room.objects.create(name="Kitchen")
        self.assertEqual(str(room), "Kitchen")

    def test_room_name_unique(self):
        """Room name should be unique"""
        Room.objects.create(name="Library")
        with self.assertRaises(Exception):
            Room.objects.create(name="Library")


class ItemModelTest(TestCase):

    def setUp(self):
        self.room = Room.objects.create(name="Bathroom")

    def test_item_str_returns_correct_format(self):
        """__str__ method should return item name, number, and room"""
        item = Item.objects.create(name="Soap", number=3, room=self.room, group_id="soap")
        self.assertEqual(str(item), "Soap (3) in Bathroom")

    def test_item_unique_together_constraint(self):
        """Should raise IntegrityError if name, number, and room are duplicated"""
        Item.objects.create(name="Towel", number=1, room=self.room, group_id="towel")
        with self.assertRaises(Exception):
            Item.objects.create(name="Towel", number=1, room=self.room, group_id="duplicate")

    def test_item_allows_same_name_in_different_room(self):
        """Same item name and number should be allowed in different rooms"""
        other_room = Room.objects.create(name="Spa")
        Item.objects.create(name="Shampoo", number=2, room=self.room, group_id="shampoo")
        try:
            Item.objects.create(name="Shampoo", number=2, room=other_room, group_id="shampoo")
        except Exception:
            self.fail("Item with same name/number in different room should be allowed")

class GameModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='test123')

    def test_game_str_returns_readable_string(self):
        """__str__ should return formatted game info with username and status"""
        game = Game.objects.create(player=self.user)
        expected = f"Game {game.id} - User: tester - In progress"
        self.assertEqual(str(game), expected)

    def test_game_defaults(self):
        """Game should be created with correct default values"""
        game = Game.objects.create(player=self.user)
        self.assertIsInstance(game.id, uuid.UUID)
        self.assertFalse(game.completed)
        self.assertEqual(game.difficulty, 'easy')
        self.assertEqual(game.block_rooms, [])
        self.assertEqual(game.block_items, {})

    def test_game_can_be_marked_completed(self):
        """Completed field should reflect game completion"""
        game = Game.objects.create(player=self.user, completed=True)
        self.assertTrue(game.completed)


class GameCompletionTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='test123')
        self.room = Room.objects.create(name="TestRoom")
        self.item = Item.objects.create(name="Key", number=1, room=self.room, group_id="key")
        self.game = Game.objects.create(player=self.user)

    def test_is_completed_returns_true_if_all_cells_correct(self):
        """Game is completed when all cells are filled and correct"""
        for i in range(3):
            cell = Cell.objects.create(game=self.game, row=i, column=i,
                                       correct_item=self.item, selected_item=self.item)
            cell.is_correct = lambda: True  # simulate correctness
            cell.save()
        self.assertTrue(self.game.is_completed())

    def test_is_completed_returns_false_if_any_cell_missing_item(self):
        """Game is not completed if any cell has no selected_item"""
        Cell.objects.create(game=self.game, row=0, column=0,
                            correct_item=self.item, selected_item=None)
        self.assertFalse(self.game.is_completed())

    def test_is_completed_returns_false_if_any_cell_incorrect(self):
        """Game is not completed if any cell is incorrect"""
        wrong_item = Item.objects.create(name="Wrong", number=9, room=self.room, group_id="wrong")
        Cell.objects.create(game=self.game, row=0, column=0,
                            correct_item=self.item, selected_item=wrong_item)
        self.assertFalse(self.game.is_completed())

class CellModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='test123')
        self.room = Room.objects.create(name="TestRoom")
        self.correct_item = Item.objects.create(name="Statue", number=5, room=self.room, group_id="statue")
        self.wrong_item = Item.objects.create(name="Vase", number=9, room=self.room, group_id="vase")
        self.game = Game.objects.create(player=self.user)

    def test_cell_str_returns_coordinates(self):
        """__str__ should return (row, column) of the cell"""
        cell = Cell.objects.create(game=self.game, row=2, column=7,
                                   correct_item=self.correct_item)
        self.assertEqual(str(cell), "Cell (2, 7)")

    def test_is_correct_returns_true_for_matching_items(self):
        """is_correct returns True when selected_item and correct_item have the same number"""
        cell = Cell.objects.create(game=self.game, row=1, column=1,
                                   correct_item=self.correct_item,
                                   selected_item=self.correct_item)
        self.assertTrue(cell.is_correct())

    def test_is_correct_returns_false_for_different_items(self):
        """is_correct returns False when selected_item and correct_item differ in number"""
        cell = Cell.objects.create(game=self.game, row=3, column=3,
                                   correct_item=self.correct_item,
                                   selected_item=self.wrong_item)
        self.assertFalse(cell.is_correct())

    def test_is_correct_returns_false_when_selected_item_is_none(self):
        """is_correct returns False when selected_item is None"""
        cell = Cell.objects.create(game=self.game, row=0, column=0,
                                   correct_item=self.correct_item,
                                   selected_item=None)
        self.assertFalse(cell.is_correct())

class IntroModelTest(TestCase):

    def test_intro_str_returns_order(self):
        """__str__ should return 'Intro <order>'"""
        intro = Intro.objects.create(order=1, text="Welcome to the game.")
        self.assertEqual(str(intro), "Intro 1")

    def test_intro_ordering_is_correct(self):
        """Intros should be automatically ordered by 'order' field"""
        Intro.objects.create(order=2, text="Second")
        Intro.objects.create(order=1, text="First")
        intros = Intro.objects.all()
        self.assertEqual(intros[0].order, 1)
        self.assertEqual(intros[1].order, 2)

class MemoryModelTest(TestCase):

    def test_memory_str_returns_id_and_difficulty(self):
        """__str__ should return 'Memory <order> (<difficulty>)'"""
        memory = Memory.objects.create(
            difficulty='easy',
            order=1,
            text="This is a distant memory.",
            transition="Who am I?"
        )
        self.assertEqual(str(memory), "Memory 1 (easy)")

    def test_memory_difficulty_choices(self):
        """Memory should accept only valid difficulty choices"""
        memory = Memory(
            difficulty='ultra',
            order=99,
            text="Invalid difficulty",
            transition="..."
        )
        with self.assertRaises(Exception):
            memory.full_clean()

    def test_memory_unique_order(self):
        """Memory order should be unique"""
        Memory.objects.create(
            difficulty='medium',
            order=2,
            text="First one",
            transition="..."
        )
        with self.assertRaises(Exception):
            Memory.objects.create(
                difficulty='hard',
                order=2,
                text="Second one with same order",
                transition="..."
            )

class DifficultyTransitionModelTest(TestCase):

    def test_transition_str_returns_correct_format(self):
        """__str__ should return 'Transition (<difficulty>)'"""
        trans = DifficultyTransition.objects.create(
            difficulty="medium",
            text="Now it gets harder."
        )
        self.assertEqual(str(trans), "Transition (medium)")

    def test_difficulty_choices_validation(self):
        """Only valid difficulty choices should be allowed"""
        trans = DifficultyTransition(
            difficulty="unknown",
            text="Invalid"
        )
        with self.assertRaises(Exception):
            trans.full_clean()

    def test_difficulty_unique_constraint(self):
        """Each difficulty level can only have one transition"""
        DifficultyTransition.objects.create(
            difficulty="easy",
            text="Welcome."
        )
        with self.assertRaises(Exception):
            another = DifficultyTransition(
                difficulty="easy",
                text="Duplicate"
            )
            another.full_clean()

class PlayerStoryProgressModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="test123")

    def test_str_returns_correct_format(self):
        """__str__ should return '<username> memory progress'"""
        progress = PlayerStoryProgress.objects.create(player=self.user)
        self.assertEqual(str(progress), "tester memory progress")

    def test_unlocked_defaults_are_empty_lists(self):
        """Unlocked fields should default to empty lists"""
        progress = PlayerStoryProgress.objects.create(player=self.user)
        self.assertEqual(progress.unlocked_easy, [])
        self.assertEqual(progress.unlocked_medium, [])
        self.assertEqual(progress.unlocked_hard, [])

    def test_unlocked_can_store_list_of_ids(self):
        """Unlocked fields should accept list of integers"""
        progress = PlayerStoryProgress.objects.create(
            player=self.user,
            unlocked_easy=[1, 2, 3],
            unlocked_medium=[4],
            unlocked_hard=[]
        )
        self.assertEqual(progress.unlocked_easy, [1, 2, 3])
        self.assertEqual(progress.unlocked_medium, [4])
        self.assertEqual(progress.unlocked_hard, [])

class SequenceFrameModelTest(TestCase):

    def test_str_returns_correct_format(self):
        """__str__ should return 'Frame <index> of <sequence>'"""
        frame = SequenceFrame.objects.create(sequence="intro", index=0, image="start.png")
        self.assertEqual(str(frame), "Frame 0 of intro")

    def test_unique_sequence_index_constraint(self):
        """Should not allow duplicate (sequence, index) pairs"""
        SequenceFrame.objects.create(sequence="memory", index=1, image="mem1.png")
        duplicate = SequenceFrame(sequence="memory", index=1, image="mem1_dup.png")
        with self.assertRaises(Exception):
            duplicate.full_clean()

    def test_ordering_by_sequence_and_index(self):
        """Frames should be ordered by sequence and then by index"""
        SequenceFrame.objects.create(sequence="intro", index=1, image="b.png")
        SequenceFrame.objects.create(sequence="intro", index=0, image="a.png")
        SequenceFrame.objects.create(sequence="memory", index=0, image="c.png")

        frames = SequenceFrame.objects.all()
        self.assertEqual(frames[0].sequence, "intro")
        self.assertEqual(frames[0].index, 0)
        self.assertEqual(frames[1].sequence, "intro")
        self.assertEqual(frames[1].index, 1)
        self.assertEqual(frames[2].sequence, "memory")
        self.assertEqual(frames[2].index, 0)