from django.test import TestCase
from gameplay.utils import (generate_sudoku, assign_items_to_board, get_valid_item_groups, build_number_to_item_mapping,
                            create_game_for_player, select_valid_rooms, build_block_items, fill_cells, has_solution,
                            try_unlock_memory, get_sequence_for_trigger)
from unittest.mock import patch, MagicMock
from gameplay.models import Item, Room, Cell, User, Game, PlayerStoryProgress, Memory
from django.contrib.auth import get_user_model


class GenerateSudokuTests(TestCase):
    # Test that the generated Sudoku board has 9 rows, each with 9 values
    def test_returns_9x9_board(self):
        board = generate_sudoku()
        self.assertEqual(len(board), 9)
        for row in board:
            self.assertEqual(len(row), 9)

    # Test that all values in the board are between 1 and 9 (inclusive)
    def test_values_are_between_1_and_9(self):
        board = generate_sudoku()
        for row in board:
            for val in row:
                self.assertTrue(1 <= val <= 9)

    # Test that all values in each row are unique (no duplicates)
    def test_rows_have_unique_values(self):
        board = generate_sudoku()
        for row in board:
            self.assertEqual(len(set(row)), 9)

    # Test that all values in each column are unique (no duplicates)
    def test_columns_have_unique_values(self):
        board = generate_sudoku()
        for col_idx in range(9):
            column = [board[row_idx][col_idx] for row_idx in range(9)]
            self.assertEqual(len(set(column)), 9)

    # Test that all values in each 3x3 block are unique (no duplicates)
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
    # Test that the assign_items_to_board function correctly assigns item objects to a 9x9 Sudoku board
    def test_assigns_correct_items_to_board(self):
        # 1. Input: A static 9x9 Sudoku board filled with numbers 1 through 9 (repeated across rows)
        board = [[1, 2, 3, 4, 5, 6, 7, 8, 9]] * 9

        # 2. Create a mock valid_groups dictionary simulating 9 groups, each with 9 mock item instances
        mock_item = MagicMock(name="ItemMock")
        fake_valid_groups = {
            f"group_{i}": [mock_item] * 9 for i in range(9)
        }

        # 3. Create a fake number-to-item mapping (e.g., 1 → Item_1, 2 → Item_2, ..., 9 → Item_9)
        fake_number_to_item = {i: MagicMock(name=f"Item_{i}") for i in range(1, 10)}

        # 4. Patch the helper functions used inside assign_items_to_board to return our mock data
        with patch("gameplay.utils.get_valid_item_groups", return_value=fake_valid_groups), \
             patch("gameplay.utils.build_number_to_item_mapping", return_value=fake_number_to_item):

            # Call the function under test
            result = assign_items_to_board(board)

        # 5. Assertions:
        # - The result is a 9x9 board
        # - Every row has 9 items
        # - Every cell is one of the mocked item instances (from fake_number_to_item)
        self.assertEqual(len(result), 9)
        self.assertTrue(all(len(row) == 9 for row in result))
        self.assertTrue(all(cell in fake_number_to_item.values() for row in result for cell in row))


class GetValidItemGroupsTests(TestCase):

    def setUp(self):
        # Create a test room to associate items with
        self.room = Room.objects.create(name="Test Room")

        # Create 9 valid item groups, each containing exactly 9 items numbered 1 through 9
        for g in range(9):
            for num in range(1, 10):
                Item.objects.create(
                    name=f"Item {g}-{num}",
                    number=num,
                    group_id=f"group{g}",
                    room=self.room
                )

    # Test that get_valid_item_groups() returns exactly 9 groups,
    # each containing 9 unique items with numbers from 1 to 9
    def test_returns_9_valid_groups(self):
        groups = get_valid_item_groups()
        self.assertEqual(len(groups), 9)
        for group in groups.values():
            self.assertEqual(len(group), 9)
            self.assertSetEqual(set(i.number for i in group), set(range(1, 10)))

    # Test that if there are no valid groups, the function raises a ValueError
    def test_raises_error_if_not_enough_valid_groups(self):
        Item.objects.all().delete()  # Delete all items from the database
        with self.assertRaises(ValueError):
            get_valid_item_groups()

    # Test that item groups with invalid number distributions (e.g., duplicates) are ignored
    def test_ignores_invalid_number_groups(self):
        # Add an invalid group with 9 items, all with the same number (1), which is not valid
        for i in range(9):
            Item.objects.create(
                name=f"Duplicate Item {i}",
                number=1,  # Duplicate number in group
                group_id="invalid_group",
                room=self.room
            )

        groups = get_valid_item_groups()

        # The invalid group should not be included; we should still have only the 9 original valid groups
        self.assertEqual(len(groups), 9)
        self.assertNotIn("invalid_group", groups)

class BuildNumberToItemMappingTests(TestCase):
    def setUp(self):
        # Create a test room to associate items with
        self.room = Room.objects.create(name="Test Room")

        # Create 9 item groups labeled A–I, each with 9 items numbered 1–9
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

        # Store the list of selected group IDs for testing
        self.selected_ids = list(self.group_map.keys())

    # Test that the build_number_to_item_mapping function creates a valid mapping
    # where each number from 1 to 9 maps to an item with that number
    def test_creates_valid_mapping(self):
        mapping = build_number_to_item_mapping(self.selected_ids, self.group_map)
        self.assertEqual(len(mapping), 9)
        for num in range(1, 10):
            self.assertIn(num, mapping)
            self.assertEqual(mapping[num].number, num)

    # Test that the function raises an error if any selected group is missing a required number
    def test_raises_error_when_missing_number(self):
        # Remove item with number 5 from group "E" to simulate an invalid group
        self.group_map["E"] = [i for i in self.group_map["E"] if i.number != 5]

        with self.assertRaises(ValueError) as context:
            build_number_to_item_mapping(self.selected_ids, self.group_map)

        # Confirm that the error message specifically mentions the missing number
        self.assertIn("does not contain item number 5", str(context.exception))


class CreateGameTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="player", password="test")

        # For each room (9 total), create 9 unique items with group_ids and numbers 1–9
        # Important: Each group_id must be unique per item, even if item names repeat
        for r in range(9):
            room = Room.objects.create(name=f"Room {r}")
            for n in range(1, 10):
                Item.objects.create(
                    name=f"Item {r}-{n}",
                    number=n,
                    group_id=f"group{r}-{n}",  # 💥 unique group_id per item!
                    room=room
                )

    # Test that a game is successfully created for a player when Sudoku is solvable
    @patch("gameplay.utils.is_sudoku_solvable", return_value=True)
    def test_create_game_success(self, mock_solver):
        # Attempt to create a game for the test user with difficulty set to "medium"
        game = create_game_for_player(self.user, difficulty="medium")

        # Check that the game was created and properly linked to the user
        self.assertIsNotNone(game)
        self.assertEqual(game.player, self.user)
        self.assertEqual(game.difficulty, "medium")

        # Ensure that 9 block_rooms and 9 block_items were assigned (standard 9 blocks in Sudoku)
        self.assertEqual(len(game.block_rooms), 9)
        self.assertEqual(len(game.block_items), 9)

        # Confirm that 81 cells were created (standard 9x9 Sudoku grid)
        self.assertEqual(Cell.objects.filter(game=game).count(), 81)


class SelectValidRoomsTests(TestCase):
    def setUp(self):
        # Helper function to create a valid room with 9 items, each having a unique group_id
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

        # Create 9 valid rooms for initial setup
        for i in range(9):
            create_valid_room(f"Room{i+1}", i)

    # Test that select_valid_rooms() returns exactly 9 valid rooms
    def test_selects_9_valid_rooms(self):
        rooms = select_valid_rooms()
        self.assertEqual(len(rooms), 9)

    # Test that a ValueError is raised if fewer than 9 valid rooms are available
    def test_raises_if_not_enough_valid_rooms(self):
        Room.objects.all().delete()  # Clear all rooms and items

        # Recreate only 8 valid rooms (1 short of the required 9)
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

    # Test that a room with duplicate group_ids is ignored when selecting valid rooms
    def test_ignores_room_with_duplicate_group_ids(self):
        # Add a new room that has two items sharing the same group_id (invalid)
        room = Room.objects.create(name="BadRoom")
        for i in range(1, 10):
            group = "shared" if i <= 2 else f"unique_{i}"
            Item.objects.create(
                name=f"BadItem{i}",
                number=i,
                group_id=group,  # Two items share 'shared' → invalid
                room=room
            )

        rooms = select_valid_rooms()

        # The invalid room should be ignored, so the result should still include only the original 9 valid ones
        self.assertEqual(len(rooms), 9)


class BuildBlockItemsTests(TestCase):
    def setUp(self):
        # Create a valid test room with 9 items
        self.room = Room.objects.create(name="Test Room")
        # Each item has a unique group_id and number from 1 to 9
        for i in range(1, 10):
            Item.objects.create(
                name=f"Item{i}",
                number=i,
                group_id=f"group_{i}",
                room=self.room
            )

    # Test that build_block_items() returns a correct mapping for a valid room
    def test_returns_mapping_for_valid_room(self):
        mapping = build_block_items(self.room)
        # Should return exactly 9 entries
        self.assertEqual(len(mapping), 9)
        # Keys should be the numbers 1 through 9
        self.assertSetEqual(set(mapping.keys()), set(range(1, 10)))

    # Test that a ValueError is raised if the room has duplicate group_ids
    def test_raises_if_not_enough_unique_group_ids(self):
        room = Room.objects.create(name="Duplicate Groups")
        # Two items share the same group_id ('shared'), which makes the group invalid
        for i in range(1, 10):
            group_id = "shared" if i <= 2 else f"group_{i}"
            Item.objects.create(
                name=f"Item{i}",
                number=i,
                group_id=group_id,
                room=room
            )

        # Function should raise a ValueError due to group_id duplication
        with self.assertRaises(ValueError):
            build_block_items(room)

    # Test that a ValueError is raised if any number from 1–9 is missing
    def test_raises_if_missing_number(self):
        room = Room.objects.create(name="Missing Number")
        # Add items with numbers 1 through 8 only (number 9 is missing)
        for i in range(1, 9):
            Item.objects.create(
                name=f"Item{i}",
                number=i,
                group_id=f"group_{i}",
                room=room
            )
        # Add a 9th item that duplicates an existing number (8)
        Item.objects.create(
            name="Dup",
            number=8,
            group_id="group_9",
            room=room
        )

        # Function should raise a ValueError due to number 9 being missing
        with self.assertRaises(ValueError):
            build_block_items(room)


class FillCellsTests(TestCase):
    def setUp(self):
        # Create a test user
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="test")

        # Create a test room and 9 unique items with numbers 1–9
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

        # Create a new game object assigned to the test user
        self.game = Game.objects.create(player=self.user, difficulty="easy")  # 🔧 corrected

        # Create a valid 9x9 Sudoku board using a known formula (ensures a correct puzzle)
        self.board = [[(i * 3 + i // 3 + j) % 9 + 1 for j in range(9)] for i in range(9)]

        # Prepare block_items: a mapping from block index (as string) to number → item ID
        # All 9 blocks use the same 9 items for simplicity
        self.block_items = {
            str(i): {n: self.items[n - 1].id for n in range(1, 10)}
            for i in range(9)
        }

    # Test that fill_cells() correctly creates all 81 cells with proper items and prefill logic
    def test_cells_are_created_correctly(self):
        # Fill the board for the given game
        fill_cells(self.game, self.board, self.block_items, difficulty='medium')

        # Fetch all cells for the game
        cells = Cell.objects.filter(game=self.game)

        # There should be exactly 81 cells in a 9x9 board
        self.assertEqual(cells.count(), 81)

        # Each cell's correct_item should match the board number at that row/column
        for cell in cells:
            self.assertEqual(cell.correct_item.number, self.board[cell.row][cell.column])
            self.assertEqual(cell.correct_item.id, cell.correct_item.id)  # sanity check
            # Either the cell is prefilled or not filled at all yet
            self.assertTrue(cell.prefilled or cell.selected_item is None)

        # Check that the number of prefilled cells is around 30 for 'medium' difficulty
        prefilled_count = cells.filter(prefilled=True).count()
        self.assertTrue(25 <= prefilled_count <= 35)  # Allowing for randomness
class HasSolutionTests(TestCase):

    # Test that a valid, solvable Sudoku board returns True
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
        # This is a known solvable puzzle → should return True
        self.assertTrue(has_solution(board))

    # Test that an invalid Sudoku board (duplicate in row) returns False
    def test_invalid_sudoku_returns_false(self):
        board = [
            [5, 5, 0, 0, 7, 0, 0, 0, 0],  # ❌ Invalid: two 5s in the same row
            [6, 0, 0, 1, 9, 5, 0, 0, 0],
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9],
        ]
        # This board is unsolvable due to an invalid duplicate → should return False
        self.assertFalse(has_solution(board))

# Test class for checking if the current state of a game board is solvable
# Uses Cell objects filled with selected items to simulate player input

# class IsSudokuSolvableTests(TestCase):
#     def setUp(self):
#         # Create a test user and a test room (required for creating Items)
#         self.user = User.objects.create_user(username="tester", password="pass")
#         self.room = Room.objects.create(name="Test Room")
#
#         # Create two items with distinct numbers, used in cells
#         self.item1 = Item.objects.create(name="One", group_id="A", number=1, room=self.room)
#         self.item2 = Item.objects.create(name="Two", group_id="B", number=2, room=self.room)
#
#         # Create a game object linked to the test user
#         self.game = Game.objects.create(player=self.user, difficulty="easy")
#
#     # Test that a partially filled, valid Sudoku board is recognized as solvable
#     def test_solvable_grid_returns_true(self):
#         """Create a partially filled Sudoku grid that is valid and solvable."""
#         # Place item1 (number 1) in the top-left cell
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
#     # Test that a Sudoku grid with a direct conflict is identified as unsolvable
#     def test_unsolvable_grid_returns_false(self):
#         """Create a grid with two identical numbers in the same row, which makes it invalid."""
#         # Two cells in the same row contain the same number → violates Sudoku rules
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
        # Create a test user
        self.user = User.objects.create_user(username="tester", password="pass")

    # Test that try_unlock_memory() unlocks a new memory if one is still available
    def test_unlocks_new_memory_if_available(self):
        # Create two easy difficulty memories
        Memory.objects.create(order=0, difficulty="easy")
        Memory.objects.create(order=1, difficulty="easy")

        # The user has already unlocked the first one (order 0)
        PlayerStoryProgress.objects.create(player=self.user, unlocked_easy=[0])

        # Simulate finishing a game on easy difficulty
        game = Game.objects.create(player=self.user, difficulty="easy")
        new_memory = try_unlock_memory(game)

        # A new memory should be unlocked
        self.assertIsNotNone(new_memory)
        self.assertIn(new_memory.order, [1])

        # Check that the new memory was added to the player's progress
        progress = PlayerStoryProgress.objects.get(player=self.user)
        self.assertIn(1, progress.unlocked_easy)

    # Test that if all memories are already unlocked, the function returns None
    def test_returns_none_if_all_memories_unlocked(self):
        # Create two memories and mark both as unlocked
        Memory.objects.create(order=0, difficulty="easy")
        Memory.objects.create(order=1, difficulty="easy")
        PlayerStoryProgress.objects.create(player=self.user, unlocked_easy=[0, 1])

        # Simulate a game — no new memory should be available
        game = Game.objects.create(player=self.user, difficulty="easy")
        result = try_unlock_memory(game)

        self.assertIsNone(result)

    # Test that the function automatically creates PlayerStoryProgress if it doesn't exist
    def test_creates_progress_if_not_exists(self):
        # Only one memory exists, no progress record yet
        memory = Memory.objects.create(order=0, difficulty="easy")
        game = Game.objects.create(player=self.user, difficulty="easy")

        # Run unlocking logic
        new_memory = try_unlock_memory(game)

        # The single memory should be returned
        self.assertEqual(new_memory, memory)

        # A PlayerStoryProgress should now exist and contain the unlocked memory
        progress = PlayerStoryProgress.objects.get(player=self.user)
        self.assertIn(memory.order, progress.unlocked_easy)


class GetSequenceForTriggerTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="tester", password="pass")

    # Test that the "start" trigger returns "intro" if the player has no unlocked memories
    def test_start_triggers_intro_when_no_memories(self):
        PlayerStoryProgress.objects.create(player=self.user)
        result = get_sequence_for_trigger("start", self.user)
        self.assertEqual(result, "intro")

    # Test that "start" trigger returns None if the player already has at least one unlocked memory
    def test_start_returns_none_if_some_memories_exist(self):
        PlayerStoryProgress.objects.create(player=self.user, unlocked_easy=[0])
        result = get_sequence_for_trigger("start", self.user)
        self.assertIsNone(result)

    # Test that completing easy difficulty after unlocking all 20 easy memories triggers "easy_end"
    def test_complete_triggers_easy_end(self):
        PlayerStoryProgress.objects.create(player=self.user, unlocked_easy=list(range(20)))
        result = get_sequence_for_trigger("complete", self.user)
        self.assertEqual(result, "easy_end")

    # Test that completing medium difficulty after unlocking all 20 medium memories triggers "medium_end"
    def test_complete_triggers_medium_end(self):
        PlayerStoryProgress.objects.create(player=self.user, unlocked_medium=list(range(20)))
        result = get_sequence_for_trigger("complete", self.user)
        self.assertEqual(result, "medium_end")

    # Test that completing hard difficulty after unlocking all 20 hard memories triggers "hard_end"
    def test_complete_triggers_hard_end(self):
        PlayerStoryProgress.objects.create(player=self.user, unlocked_hard=list(range(20)))
        result = get_sequence_for_trigger("complete", self.user)
        self.assertEqual(result, "hard_end")

    # Test that when a memory is passed to the function, the "memory" sequence is returned
    def test_complete_triggers_memory_if_memory_passed(self):
        PlayerStoryProgress.objects.create(player=self.user, unlocked_easy=[0, 1])
        memory = Memory(order=2, difficulty="easy", text="Memory text")
        result = get_sequence_for_trigger("complete", self.user, memory=memory)
        self.assertEqual(result, "memory")

    # Test that "complete" returns None if there's no final memory condition met and no memory passed
    def test_complete_returns_none_if_no_memory_and_not_final(self):
        PlayerStoryProgress.objects.create(player=self.user, unlocked_easy=[0, 1])
        result = get_sequence_for_trigger("complete", self.user)
        self.assertIsNone(result)
