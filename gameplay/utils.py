import random
from .models import Game, Cell, Item, Room, PlayerStoryProgress, Memory
from collections import defaultdict

def generate_sudoku():
    """
    Generates a fully valid, randomized 9x9 Sudoku board as a nested list.

    The generation is based on a base pattern formula to ensure a valid Sudoku,
    then it applies randomized shuffling of rows, columns, and digits to create variability
    while maintaining the structure.

    Returns:
        A 9x9 list of integers (1–9) representing a completed Sudoku board.
    """
    base = 3
    side = base * base


    def pattern(r, c):
        """
        Calculates the value index at position (r, c) based on a fixed pattern.
        This ensures the basic Sudoku structure (each digit 1–9 appears once per row, column, block).
        """
        return (base * (r % base) + r // base + c) % side


    def shuffle(s):
        """
        Shuffles a sequence randomly and returns a new shuffled list.
        Used for randomizing rows, columns, and digits.
        """
        return random.sample(s, len(s))

    # Randomly shuffle the groups and their internal order (rows and columns by block)
    rows = [g * base + r for g in shuffle(range(base)) for r in shuffle(range(base))]
    cols = [g * base + c for g in shuffle(range(base)) for c in shuffle(range(base))]

    # Randomly assign digits 1-9 to the board positions
    nums = shuffle(range(1, side + 1))

    # Create the final Sudoku board by applying the shuffled indices and number mapping
    board = [[nums[pattern(r, c)] for c in cols] for r in rows]

    return board


def assign_items_to_board(board):
    """
    Converts a numeric 9x9 Sudoku board into an item-based board.

    The function randomly selects 9 valid item groups (each group contains 9 unique-numbered items).
    It then maps numbers 1–9 to representative items from those groups.
    Finally, it replaces every number in the original board with its corresponding item.

    Args:
        board (list[list[int]]): A 9x9 matrix containing integers from 1 to 9.

    Returns:
        list[list[Item]]: A 9x9 matrix where each cell is an Item object instead of a number.
    """
    # Retrieve all valid item groups, each group_id maps to a list of 9 items
    valid_groups = get_valid_item_groups()

    # Randomly select 9 unique group_ids to represent numbers 1–9
    selected_group_ids = random.sample(list(valid_groups.keys()), 9)

    # Build a mapping: number 1–9 → representative item from each group
    number_to_item = build_number_to_item_mapping(selected_group_ids, valid_groups)

    # Replace each number in the board with the corresponding item
    item_board = [[number_to_item[num] for num in row] for row in board]
    return item_board


def get_valid_item_groups():
    """
    Loads all Item objects from the database and groups them by their group_id.

    Then filters these groups to find only the valid ones:
    - A valid group must contain exactly 9 items.
    - These 9 items must each have a unique number from 1 to 9.

    At least 9 such valid groups are required to proceed.
    If there are fewer than 9, a ValueError is raised.

    Returns:
        dict: A mapping {group_id: [Item, Item, ..., Item]} for all valid groups.
    """
    # Retrieve all Item objects from the database and convert the QuerySet to a list.
    all_items = list(Item.objects.all())

    # Initialize a dictionary with default value as an empty list.
    # This dictionary will map each group_id to the list of items belonging to it.
    group_map = defaultdict(list)

    # Iterate over every item in the list
    for item in all_items:
        # Check if the item has a group_id assigned.
        if item.group_id:
            # Append the item to the list of items under its group_id.
            group_map[item.group_id].append(item)

    # Create a new dictionary with only valid groups.
    # A valid group is one where the set of unique numbers for the items has exactly 9 elements.
    # This means that the group contains items with numbers 1 through 9.
    valid_groups = {
        gid: items
        for gid, items in group_map.items()
        if len(set(i.number for i in items)) == 9
    }
    # Check if there are at least 9 valid groups.
    # If not, raise an error indicating there are not enough valid group_ids.
    if len(valid_groups) < 9:
        raise ValueError("❌ Not enough valid group_ids with unique numbers 1–9.")

    # Return the dictionary of valid groups.
    return valid_groups


def build_number_to_item_mapping(selected_group_ids, group_map):
    """
    Creates a mapping from numbers 1–9 to Item objects using selected item groups.

    Each number is assigned an item with the same number from a different group.
    This ensures that no two numbers use items from the same group,
    which avoids duplicates by meaning (group_id) in the resulting board.

    Args:
        selected_group_ids (list[str]): List of 9 unique group_ids.
        group_map (dict): Mapping of group_id to list of Item objects.

    Returns:
        dict: A mapping {1: Item, 2: Item, ..., 9: Item}

    Raises:
        ValueError: If any group does not contain the expected number (1–9).
    """
    # Initialize empty mapping for number → item
    number_to_item = {}

    # Iterate over the selected group_ids and assign numbers 1–9
    for i, group_id in enumerate(selected_group_ids):
        items = group_map[group_id]

        # Look for an item in the group that has number == i + 1
        item = next((it for it in items if it.number == i + 1), None)

        # Raise an error if the expected number is missing in the group
        if not item:
            raise ValueError(f"❌ Group '{group_id}' does not contain item number {i + 1}")

        # Assign the item to the corresponding number
        number_to_item[i + 1] = item

    return number_to_item


def create_game_for_player(player, difficulty='easy'):
    """
    Creates a new Sudoku-based item game for the given player.

    - Generates a valid Sudoku number grid (1–9).
    - Selects 9 valid rooms, each representing a Sudoku block with unique item groups.
    - Creates a Game object and assigns room-to-block mappings.
    - Converts the numeric Sudoku into an item-based board using the selected rooms.
    - Fills the game with Cell objects based on the logic and saves the setup.

    Args:
        player (User): The player for whom the game is being created.
        difficulty (str): Game difficulty ('easy', 'medium', 'hard').

    Returns:
        Game: A fully initialized and solvable Game object, or None if unsolvable.
    """
    # Generate a full valid Sudoku grid with numbers 1–9
    board = generate_sudoku()

    # Select 9 valid Room objects to represent each Sudoku block
    # Each room must contain 9 unique items with distinct group_ids
    selected_rooms = select_valid_rooms()


    # Create a new Game instance with the selected rooms and difficulty
    game = Game.objects.create(
        player=player,
        difficulty=difficulty,
        block_rooms=[room.id for room in selected_rooms], # maps blocks 0–8 to Room IDs
        block_items={} # will be filled next
    )


    # Create a mapping of block index → 9 items from corresponding room
    block_items = {
        str(index): build_block_items(room)
        for index, room in enumerate(selected_rooms)
    }

    # Assign the item mapping to the game and save it
    game.block_items = block_items
    game.save()

    # Fill the board with Cell objects based on the Sudoku structure and item mapping
    fill_cells(game, board, block_items, difficulty)
    # Return the game only if the resulting board is solvable
    if is_sudoku_solvable(game):
        return game



def select_valid_rooms():
    """
    Selects 9 rooms from the database to be used as Sudoku blocks.

    Each selected room must contain exactly 9 items,
    and all items must have unique group_ids (no repetition of meaning).

    The rooms are shuffled before selection to ensure randomness in gameplay.

    Returns:
        list[Room]: A list of 9 Room objects with valid unique group_id items.

    Raises:
        ValueError: If fewer than 9 valid rooms are found.
    """
    # Load all rooms from the database and prefetch related items for efficiency
    rooms = list(Room.objects.prefetch_related('items').all())

    # Shuffle rooms to ensure random selection
    random.shuffle(rooms)

    selected = []
    # Iterate through shuffled rooms
    for room in rooms:
        # Collect all unique group_ids from the room's items
        group_ids = {item.group_id for item in room.items.all()}

        # Check if the room has exactly 9 unique group_ids
        if len(group_ids) == 9:
            selected.append(room)

        # If we have selected 9 valid rooms, return them
        if len(selected) == 9:
            return selected
    # If not enough valid rooms are found, raise an error
    raise ValueError("Cannot find 9 rooms with 9 unique group_ids.")


def build_block_items(room):
    """
    Builds a mapping from numbers 1–9 to item IDs from a given room.

    Ensures that:
    - Each number 1–9 is represented by exactly one item.
    - Each item comes from a unique group_id (no group is reused).
    - Items are selected only from the specified room.

    Args:
        room (Room): The Room object containing items to choose from.

    Returns:
        dict[int, int]: A mapping {1: item_id, 2: item_id, ..., 9: item_id}

    Raises:
        ValueError: If the room does not contain 9 unique group_ids,
                    or it is not possible to assign all 9 numbers.
    """

    # Group items from the room by their group_id
    group_map = defaultdict(list)
    for item in room.items.all():
        group_map[item.group_id].append(item)

    # The room must contain exactly 9 different group_ids
    if len(group_map) != 9:
        raise ValueError(f"Room '{room.name}' does not contain 9 unique group_ids.")

    # Initialize mapping number → item_id
    number_to_item = {}

    # Keep track of which group_ids have already been used
    used_group_ids = set()

    # Convert the group mapping to a list and shuffle it to randomize selection
    group_list = list(group_map.items())
    random.shuffle(group_list)

    # Try to assign each number 1–9 to an item from a unique group
    for number in range(1, 10):
        for group_id, items in group_list:
            if group_id in used_group_ids:
                continue
            # Look for an item in the group that has the matching number
            for item in items:
                if item.number == number:
                    number_to_item[number] = item.id
                    used_group_ids.add(group_id)
                    break
            # If number is assigned, break the outer loop as well
            if number in number_to_item:
                break
        else:
            raise ValueError(f"Cannot find item with number {number} in room '{room.name}'.")

    # Final sanity check: all numbers 1–9 must be assigned
    if len(number_to_item) != 9:
        raise ValueError(f"Room '{room.name}' is missing one or more numbers 1–9.")

    return number_to_item


def fill_cells(game, board, block_items, difficulty='easy'):
    """
    Creates 81 Cell objects for the given Game based on a Sudoku board and block-item mapping.

    Depending on the difficulty, a number of cells will be prefilled (visible to the player).
    The rest will be hidden and must be discovered during gameplay.

    Each cell is assigned:
    - its position (row, column),
    - the correct item (based on the number),
    - and optionally a prefilled item (if visible from the start).

    Args:
        game (Game): The Game instance to associate the cells with.
        board (list[list[int]]): A 9x9 grid of numbers 1–9 representing the solution.
        block_items (dict[str, dict[int, int]]): Mapping of block index to {number → item_id}.
        difficulty (str): Difficulty level ('easy', 'medium', 'hard').
    """
    # Set how many cells will be visible at the start, based on difficulty
    if difficulty == 'easy':
        visible_count = 36
    elif difficulty == 'medium':
        visible_count = 30
    elif difficulty == 'hard':
        visible_count = 24
    else:
        visible_count = 30  # default fallback

    # Randomly choose which of the 81 cells will be hidden
    hidden_cells = set(random.sample(range(81), 81 - visible_count))

    # Create Cell objects for each position in the grid
    for r in range(9):
        for c in range(9):
            number = board[r][c]

            # Determine which 3x3 block the cell belongs to
            grid_index = (r // 3) * 3 + (c // 3)

            # Get the correct item ID for this number in this block
            item_id = block_items[str(grid_index)][number]
            item = Item.objects.get(id=item_id)

            # Determine if the cell should be prefilled (visible at start)
            is_prefilled = (r * 9 + c) not in hidden_cells

            # Create and save the cell in the database
            Cell.objects.create(
                game=game,
                row=r,
                column=c,
                correct_item=item,
                selected_item=item if is_prefilled else None,
                prefilled=is_prefilled
            )

# DEBUG ONLY – not used in production.
# def print_sudoku_grid(game_id):
#     """
#     Debug helper: Prints the correct solution grid (numbers 1–9) for a given Game ID.
#
#     Loads the Game and its related Cell objects, reconstructs the 9x9 solution grid
#     from the correct_item of each cell, and prints it in a readable format.
#
#     Args:
#         game_id (int): ID of the Game to be printed.
#
#     Returns:
#         None
#     """
#     try:
#         # Attempt to load the Game object by ID
#         game = Game.objects.get(id=game_id)
#     except Game.DoesNotExist:
#         # If the game does not exist, print an error and exit
#         print(f"Game {game_id} does not exist.")
#         return
#
#     # Fetch all Cell objects related to this game
#     cells = Cell.objects.filter(game=game)
#     # Initialize empty 9x9 grid,
#     grid = [[0 for _ in range(9)] for _ in range(9)]
#
#     # Fill the grid with correct numbers from each cell's correct item
#     for cell in cells:
#         grid[cell.row][cell.column] = cell.correct_item.number
#
#     # Print the grid in a readable format
#     print(f"\n=== SUDOKU for Game {game_id} ===")
#     for row in grid:
#         print(" ".join(str(n) for n in row))
#     print("===============================\n")

def has_solution(grid):
    """
    Checks whether the given Sudoku grid has at least one valid solution.

    Uses a recursive backtracking algorithm to try filling all empty cells (represented by 0).
    If it finds a valid solution, it returns True. Otherwise, it returns False.

    Args:
        grid (list[list[int]]): A 9x9 Sudoku grid, where empty cells are 0.

    Returns:
        bool: True if a valid solution exists, False otherwise.
    """
    def is_safe(row, col, num):
        # Check if num is already in the same row or column
        for i in range(9):
            if grid[row][i] == num or grid[i][col] == num:
                return False
            # Check if num is already in the corresponding 3x3 block
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for r in range(3):
            for c in range(3):
                if grid[start_row + r][start_col + c] == num:
                    return False
        return True

    def solve():
        # Traverse the grid to find the first empty cell (0)
        for r in range(9):
            for c in range(9):
                if grid[r][c] == 0:
                    # Try placing numbers 1–9 in the empty cell
                    for num in range(1, 10):
                        if is_safe(r, c, num):
                            grid[r][c] = num # Tentatively place number
                            if solve(): # Recursively solve next cells
                                return True
                            grid[r][c] = 0  # Backtrack if needed
                    return False  # No valid number found → backtrack
        return True # All cells filled → valid solution found

    return solve()


def is_sudoku_solvable(game):
    """
    Checks whether the current state of the game board is solvable.

    Builds a numeric grid from the player's selected items (ignoring empty cells),
    then uses a backtracking Sudoku solver to verify that at least one valid solution exists.

    Args:
        game (Game): The game instance to check.

    Returns:
        bool: True if the Sudoku is solvable, False otherwise.
    """
    # Load all Cell objects for the given game
    cells = Cell.objects.filter(game=game)

    # Create a blank 9x9 grid (filled with 0 = empty)
    grid = [[0 for _ in range(9)] for _ in range(9)]

    # Fill in the grid with numbers from the player's selected items
    for cell in cells:
        if cell.selected_item:
            grid[cell.row][cell.column] = cell.selected_item.number

    # Use the backtracking solver to check if the grid has a valid solution
    return has_solution(grid)

def try_unlock_memory(game):
    """
    Tries to unlock a new memory for the player after finishing a game.

    Based on the game's difficulty, it loads the corresponding unlocked memory list,
    finds which memories are still locked, and randomly unlocks one of them (if any).

    The unlocked memory's order is saved to the player's story progress.

    Args:
        game (Game): The finished game instance used to determine difficulty and player.

    Returns:
        Memory | None: A newly unlocked Memory object, or None if all are already unlocked.
    """
    player = game.player
    difficulty = game.difficulty

    # Get or create the player's story progress object
    progress, _ = PlayerStoryProgress.objects.get_or_create(player=player)

    # Select the correct unlocked list based on game difficulty
    if difficulty == "easy":
        unlocked = progress.unlocked_easy
    elif difficulty == "medium":
        unlocked = progress.unlocked_medium
    else:
        unlocked = progress.unlocked_hard

    # Debug prints (for development only)
    # print(f"--- try_unlock_memory ---")
    # print(f"Player: {player.username}")
    # print(f"Difficulty: {difficulty}")
    # print(f"Already unlocked: {unlocked}")

    # Find all memories for this difficulty
    available_memories = Memory.objects.filter(difficulty=difficulty)
    locked_memories = [m for m in available_memories if m.order not in unlocked]

    # Debug prints (for development only)
    # print(f"Available: {available_memories.count()}")
    # print(f"Locked: {len(locked_memories)}")

    # If there are no locked memories left, return None
    if not locked_memories:
        return None

    # Randomly choose one locked memory to unlock
    new_memory = random.choice(locked_memories)

    # Append the new memory's order to the unlocked list and save
    if difficulty == "easy":
        progress.unlocked_easy.append(new_memory.order)
    elif difficulty == "medium":
        progress.unlocked_medium.append(new_memory.order)
    else:
        progress.unlocked_hard.append(new_memory.order)

    progress.save()
    return new_memory

def get_sequence_for_trigger(trigger, player, memory=None):
    """
    Determines which story sequence to play based on the player's state and the given trigger.

    Triggers:
        - "start": triggers the intro if the player has unlocked no memories at all.
        - "complete": triggers final sequences (easy_end, medium_end, hard_end),
                      or a memory sequence if a new memory was just unlocked.

    Args:
        trigger (str): The trigger type, e.g., "start" or "complete".
        player (User): The player whose progress should be evaluated.
        memory (Memory | None): The newly unlocked memory, if any.

    Returns:
        str | None: The name of the sequence to play, or None if no sequence should be triggered.
    """
    from gameplay.models import PlayerStoryProgress

    # Get or create progress object for the player
    progress, _ = PlayerStoryProgress.objects.get_or_create(player=player)

    # Handle the 'start' trigger → play intro only if player has no memories at all
    if trigger == "start":
        total = (
            len(progress.unlocked_easy)
            + len(progress.unlocked_medium)
            + len(progress.unlocked_hard)
        )
        if total == 0:
            return "intro"

    # Handle the 'complete' trigger → after player finishes a game
    if trigger == "complete":
        if len(progress.unlocked_easy) == 20:
            return "easy_end"
        if len(progress.unlocked_medium) == 20:
            return "medium_end"
        if len(progress.unlocked_hard) == 20:
            return "hard_end"
        # If memory was just unlocked, play its sequence
        if memory:
            return "memory"
    # No sequence triggered
    return None