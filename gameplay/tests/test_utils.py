from django.test import TestCase
from gameplay.utils import (generate_sudoku, assign_items_to_board, get_valid_item_groups, build_number_to_item_mapping,
                            create_game_for_player, select_valid_rooms, build_block_items, fill_cells, has_solution,
                            try_unlock_memory, get_sequence_for_trigger)
from unittest.mock import patch, MagicMock
from gameplay.models import Item, Room, Cell, User, Game, PlayerStoryProgress, Memory
from django.contrib.auth import get_user_model
from collections import defaultdict
import random

class GenerateSudokuTests(TestCase):
    def test_returns_9x9_board(self):
        board = generate_sudoku()
        self.assertEqual(len(board), 9)
        for row in board:
            self.assertEqual(len(row), 9)

    def test_values_are_between_1_and_9(self):
        board = generate_sudoku()
        for row in board:
            for val in row:
                self.assertTrue(1 <= val <= 9)

    def test_rows_have_unique_values(self):
        board = generate_sudoku()
        for row in board:
            self.assertEqual(len(set(row)), 9)

    def test_columns_have_unique_values(self):
        board = generate_sudoku()
        for col_idx in range(9):
            column = [board[row_idx][col_idx] for row_idx in range(9)]
            self.assertEqual(len(set(column)), 9)

    def test_blocks_have_unique_values(self):
        board = generate_sudoku()
        for block_row in range(3):
            for block_col in range(3):
                nums = []
                for r in range(block_row * 3, (block_row + 1) * 3):
                    for c in range(block_col * 3, (block_col + 1) * 3):
                        nums.append(board[r][c])
                self.assertEqual(len(set(nums)), 9)

class AssignItemsToBoardTests(TestCase):
    def test_assigns_correct_items_to_board(self):
        # 1. Vstupní čísla (9x9 sudoku)
        board = [[1, 2, 3, 4, 5, 6, 7, 8, 9]] * 9

        # 2. Mock valid_groups
        mock_item = MagicMock(name="ItemMock")
        fake_valid_groups = {
            f"group_{i}": [mock_item] * 9 for i in range(9)
        }

        # 3. Mock number_to_item map
        fake_number_to_item = {i: MagicMock(name=f"Item_{i}") for i in range(1, 10)}

        with patch("gameplay.utils.get_valid_item_groups", return_value=fake_valid_groups), \
             patch("gameplay.utils.build_number_to_item_mapping", return_value=fake_number_to_item):

            # 4. Zavolání funkce
            result = assign_items_to_board(board)

        # 5. Ověříme výstup
        self.assertEqual(len(result), 9)
        self.assertTrue(all(len(row) == 9 for row in result))
        self.assertTrue(all(cell in fake_number_to_item.values() for row in result for cell in row))

class GetValidItemGroupsTests(TestCase):

    def setUp(self):
        self.room = Room.objects.create(name="Test Room")
        # Vytvoříme 9 validních skupin po 9 itemech (čísla 1–9)
        for g in range(9):
            for num in range(1, 10):
                Item.objects.create(
                    name=f"Item {g}-{num}",
                    number=num,
                    group_id=f"group{g}",
                    room=self.room
                )

    def test_returns_9_valid_groups(self):
        groups = get_valid_item_groups()
        self.assertEqual(len(groups), 9)
        for group in groups.values():
            self.assertEqual(len(group), 9)
            self.assertSetEqual(set(i.number for i in group), set(range(1, 10)))

    def test_raises_error_if_not_enough_valid_groups(self):
        Item.objects.all().delete()  # smažeme vše
        with self.assertRaises(ValueError):
            get_valid_item_groups()

    def test_ignores_invalid_number_groups(self):
        # Přidáme nevalidní skupinu s duplicitními čísly
        for i in range(9):
            Item.objects.create(
                name=f"Duplicate Item {i}",  # ← každý název jiný
                number=1,  # stejná hodnota (nevalidní)
                group_id="invalid_group",
                room=self.room
            )
        groups = get_valid_item_groups()
        self.assertEqual(len(groups), 9)  # Původních 9 validních, nepočítá se ta nevalidní
        self.assertNotIn("invalid_group", groups)

class BuildNumberToItemMappingTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(name="Test Room")

        # Vytvoříme 9 skupin (A–I), každá má 9 položek s čísly 1–9
        self.group_map = {}
        for i, gid in enumerate("ABCDEFGHI"):
            items = []
            for n in range(1, 10):
                item = Item.objects.create(
                    name=f"{gid}-{n}",
                    number=n,
                    group_id=gid,
                    room=self.room
                )
                items.append(item)
            self.group_map[gid] = items

        self.selected_ids = list(self.group_map.keys())

    def test_creates_valid_mapping(self):
        mapping = build_number_to_item_mapping(self.selected_ids, self.group_map)
        self.assertEqual(len(mapping), 9)
        for num in range(1, 10):
            self.assertIn(num, mapping)
            self.assertEqual(mapping[num].number, num)

    def test_raises_error_when_missing_number(self):
        # Odebereme item s číslem 5 z jedné skupiny
        self.group_map["E"] = [i for i in self.group_map["E"] if i.number != 5]

        with self.assertRaises(ValueError) as context:
            build_number_to_item_mapping(self.selected_ids, self.group_map)
        self.assertIn("does not contain item number 5", str(context.exception))

class CreateGameTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="player", password="test")

        # Každá místnost musí mít 9 různých group_id (i když jména itemů se mohou opakovat)
        for r in range(9):
            room = Room.objects.create(name=f"Room {r}")
            for n in range(1, 10):
                Item.objects.create(
                    name=f"Item {r}-{n}",
                    number=n,
                    group_id=f"group{r}-{n}",  # 💥 každé jinak!
                    room=room
                )

    @patch("gameplay.utils.is_sudoku_solvable", return_value=True)
    def test_create_game_success(self, mock_solver):
        game = create_game_for_player(self.user, difficulty="medium")

        self.assertIsNotNone(game)
        self.assertEqual(game.player, self.user)
        self.assertEqual(game.difficulty, "medium")
        self.assertEqual(len(game.block_rooms), 9)
        self.assertEqual(len(game.block_items), 9)
        self.assertEqual(Cell.objects.filter(game=game).count(), 81)

class SelectValidRoomsTests(TestCase):
    def setUp(self):
        # Pomocná funkce pro vytvoření místnosti s 9 unikátními group_id
        def create_valid_room(name, index):
            room = Room.objects.create(name=name)
            for i in range(1, 10):
                Item.objects.create(
                    name=f"Item {index}-{i}",
                    number=i,
                    group_id=f"{name}_group_{i}",
                    room=room
                )
            return room

        # Vytvoříme 9 validních místností
        for i in range(9):
            create_valid_room(f"Room{i+1}", i)

    def test_selects_9_valid_rooms(self):
        rooms = select_valid_rooms()
        self.assertEqual(len(rooms), 9)

    def test_raises_if_not_enough_valid_rooms(self):
        # Smažeme všechny místnosti
        Room.objects.all().delete()

        # Vytvoříme 8 validních (1 chybí)
        for i in range(8):
            room = Room.objects.create(name=f"InvalidRoom{i+1}")
            for j in range(1, 10):
                Item.objects.create(
                    name=f"Item {i}-{j}",
                    number=j,
                    group_id=f"g{i}_{j}",
                    room=room
                )

        with self.assertRaises(ValueError):
            select_valid_rooms()

    def test_ignores_room_with_duplicate_group_ids(self):
        # Místnost se 2 položkami se stejným group_id → nepočítá se
        room = Room.objects.create(name="BadRoom")
        for i in range(1, 10):
            group = "shared" if i <= 2 else f"unique_{i}"
            Item.objects.create(
                name=f"BadItem{i}",
                number=i,
                group_id=group,
                room=room
            )

        rooms = select_valid_rooms()
        # Mělo by zůstat přesně 9 validních (BadRoom se ignoruje)
        self.assertEqual(len(rooms), 9)

class BuildBlockItemsTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(name="Test Room")
        # Vytvoříme 9 položek s unikátními group_id a čísly 1–9
        for i in range(1, 10):
            Item.objects.create(
                name=f"Item{i}",
                number=i,
                group_id=f"group_{i}",
                room=self.room
            )

    def test_returns_mapping_for_valid_room(self):
        mapping = build_block_items(self.room)
        self.assertEqual(len(mapping), 9)
        self.assertSetEqual(set(mapping.keys()), set(range(1, 10)))

    def test_raises_if_not_enough_unique_group_ids(self):
        room = Room.objects.create(name="Duplicate Groups")
        # 2 položky mají stejný group_id = 'shared'
        for i in range(1, 10):
            group_id = "shared" if i <= 2 else f"group_{i}"
            Item.objects.create(
                name=f"Item{i}",
                number=i,
                group_id=group_id,
                room=room
            )

        with self.assertRaises(ValueError):
            build_block_items(room)

    def test_raises_if_missing_number(self):
        room = Room.objects.create(name="Missing Number")
        # Vytvoříme položky 1–8, chybí číslo 9
        for i in range(1, 9):
            Item.objects.create(
                name=f"Item{i}",
                number=i,
                group_id=f"group_{i}",
                room=room
            )
        # Devátá položka má duplicitu čísla
        Item.objects.create(
            name="Dup",
            number=8,
            group_id="group_9",
            room=room
        )

        with self.assertRaises(ValueError):
            build_block_items(room)

class FillCellsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="test")

        self.room = Room.objects.create(name="Room 1")
        self.items = []
        for i in range(1, 10):
            item = Item.objects.create(
                name=f"Item {i}",
                group_id=f"group_{i}",
                number=i,
                room=self.room
            )
            self.items.append(item)

        self.game = Game.objects.create(player=self.user, difficulty="easy")  # 🔧 opraveno

        self.board = [[(i * 3 + i // 3 + j) % 9 + 1 for j in range(9)] for i in range(9)]

        self.block_items = {
            str(i): {n: self.items[n - 1].id for n in range(1, 10)}
            for i in range(9)
        }


    def test_cells_are_created_correctly(self):
        fill_cells(self.game, self.board, self.block_items, difficulty='medium')

        cells = Cell.objects.filter(game=self.game)
        self.assertEqual(cells.count(), 81)

        for cell in cells:
            self.assertEqual(cell.correct_item.number, self.board[cell.row][cell.column])
            self.assertEqual(cell.correct_item.id, cell.correct_item.id)
            self.assertTrue(cell.prefilled or cell.selected_item is None)

        # Check approximate number of prefilled cells (should be 30 for medium)
        prefilled_count = cells.filter(prefilled=True).count()
        self.assertTrue(25 <= prefilled_count <= 35)  # tolerance na random výběr

class HasSolutionTests(TestCase):

    def test_valid_sudoku_returns_true(self):
        board = [
            [5, 3, 0, 0, 7, 0, 0, 0, 0],
            [6, 0, 0, 1, 9, 5, 0, 0, 0],
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9],
        ]
        self.assertTrue(has_solution(board))

    def test_invalid_sudoku_returns_false(self):
        board = [
            [5, 5, 0, 0, 7, 0, 0, 0, 0],  # ❌ dva 5 v řádku
            [6, 0, 0, 1, 9, 5, 0, 0, 0],
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9],
        ]
        self.assertFalse(has_solution(board))

# class IsSudokuSolvableTests(TestCase):
#     def setUp(self):
#         # Vytvoříme uživatele a místnost, protože Item potřebuje Room
#         self.user = User.objects.create_user(username="tester", password="pass")
#         self.room = Room.objects.create(name="Test Room")
#
#         # Item se používá jako selected_item i correct_item
#         self.item1 = Item.objects.create(name="One", group_id="A", number=1, room=self.room)
#         self.item2 = Item.objects.create(name="Two", group_id="B", number=2, room=self.room)
#
#         # Hra pro test
#         self.game = Game.objects.create(player=self.user, difficulty="easy")
#
#     def test_solvable_grid_returns_true(self):
#         """Vytvoříme částečně vyplněnou sudoku mřížku, která má řešení."""
#         # 1 v levém horním rohu
#         Cell.objects.create(
#             game=self.game, row=0, column=0,
#             correct_item=self.item1,
#             selected_item=self.item1,
#             prefilled=False
#         )
#
#         result = is_sudoku_solvable(self.game)
#         self.assertTrue(result)
#
#     def test_unsolvable_grid_returns_false(self):
#         """Vytvoříme konfliktní sudoku – dva stejné čísla v jednom řádku."""
#         # Dvě stejné čísla (1) v jednom řádku
#         Cell.objects.create(
#             game=self.game, row=0, column=0,
#             correct_item=self.item1,
#             selected_item=self.item1,
#             prefilled=False
#         )
#         Cell.objects.create(
#             game=self.game, row=0, column=1,
#             correct_item=self.item1,
#             selected_item=self.item1,
#             prefilled=False
#         )
#
#         result = is_sudoku_solvable(self.game)
#         self.assertFalse(result)

class TryUnlockMemoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")

    def test_unlocks_new_memory_if_available(self):
        Memory.objects.create(order=0, difficulty="easy")
        Memory.objects.create(order=1, difficulty="easy")
        PlayerStoryProgress.objects.create(player=self.user, unlocked_easy=[0])

        game = Game.objects.create(player=self.user, difficulty="easy")
        new_memory = try_unlock_memory(game)

        self.assertIsNotNone(new_memory)
        self.assertIn(new_memory.order, [1])

        progress = PlayerStoryProgress.objects.get(player=self.user)
        self.assertIn(1, progress.unlocked_easy)

    def test_returns_none_if_all_memories_unlocked(self):
        Memory.objects.create(order=0, difficulty="easy")
        Memory.objects.create(order=1, difficulty="easy")
        PlayerStoryProgress.objects.create(player=self.user, unlocked_easy=[0, 1])

        game = Game.objects.create(player=self.user, difficulty="easy")
        result = try_unlock_memory(game)

        self.assertIsNone(result)

    def test_creates_progress_if_not_exists(self):
        memory = Memory.objects.create(order=0, difficulty="easy")
        game = Game.objects.create(player=self.user, difficulty="easy")

        new_memory = try_unlock_memory(game)

        self.assertEqual(new_memory, memory)
        progress = PlayerStoryProgress.objects.get(player=self.user)
        self.assertIn(memory.order, progress.unlocked_easy)

class GetSequenceForTriggerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")

    def test_start_triggers_intro_when_no_memories(self):
        PlayerStoryProgress.objects.create(player=self.user)
        result = get_sequence_for_trigger("start", self.user)
        self.assertEqual(result, "intro")

    def test_start_returns_none_if_some_memories_exist(self):
        PlayerStoryProgress.objects.create(player=self.user, unlocked_easy=[0])
        result = get_sequence_for_trigger("start", self.user)
        self.assertIsNone(result)

    def test_complete_triggers_easy_end(self):
        PlayerStoryProgress.objects.create(player=self.user, unlocked_easy=list(range(20)))
        result = get_sequence_for_trigger("complete", self.user)
        self.assertEqual(result, "easy_end")

    def test_complete_triggers_medium_end(self):
        PlayerStoryProgress.objects.create(player=self.user, unlocked_medium=list(range(20)))
        result = get_sequence_for_trigger("complete", self.user)
        self.assertEqual(result, "medium_end")

    def test_complete_triggers_hard_end(self):
        PlayerStoryProgress.objects.create(player=self.user, unlocked_hard=list(range(20)))
        result = get_sequence_for_trigger("complete", self.user)
        self.assertEqual(result, "hard_end")

    def test_complete_triggers_memory_if_memory_passed(self):
        PlayerStoryProgress.objects.create(player=self.user, unlocked_easy=[0, 1])
        memory = Memory(order=2, difficulty="easy", text="Memory text")
        result = get_sequence_for_trigger("complete", self.user, memory=memory)
        self.assertEqual(result, "memory")

    def test_complete_returns_none_if_no_memory_and_not_final(self):
        PlayerStoryProgress.objects.create(player=self.user, unlocked_easy=[0, 1])
        result = get_sequence_for_trigger("complete", self.user)
        self.assertIsNone(result)