import random
from .models import Game, Cell, Item, Room
#from django.contrib.auth.models import User
from collections import defaultdict
from .models import Item

def generate_sudoku():
    """
    Function for creating valid sudoku 9x9 (matrix)
    Have 2 sub functions together creating functional board for sudoku
    Will shuffle rows and columns in a way that block keep together.
    Then it will shuffle individual blocks 3x3 randomly
    And finally it will create and return board grid.

    Thanks to this we will make allways random sudoku sequence.

    """
    base = 3
    side = base * base


    def pattern(r, c):
        """
        Function for generation of base pattern
        Will make valid sudoku 9x9 (matrix) but allways the same
        """
        return (base * (r % base) + r // base + c) % side


    def shuffle(s):
        """
        Function for shuffling sudoku 9x9 (matrix)
        Will take all elements (s) and randomly shuffle them.
        """
        return random.sample(s, len(s))

    rows = [g * base + r for g in shuffle(range(base)) for r in shuffle(range(base))]
    cols = [g * base + c for g in shuffle(range(base)) for c in shuffle(range(base))]
    nums = shuffle(range(1, side + 1))

    # Creation of board grid.
    board = [[nums[pattern(r, c)] for c in cols] for r in rows]

    return board


def assign_items_to_board(board):
    # Select 9 valid group_ids and map numbers 1–9 to representative items
    valid_groups = get_valid_item_groups()
    selected_group_ids = random.sample(list(valid_groups.keys()), 9)
    number_to_item = build_number_to_item_mapping(selected_group_ids, valid_groups)

    # Replace each number on the board with the corresponding item
    item_board = [[number_to_item[num] for num in row] for row in board]
    return item_board


def get_valid_item_groups():
    # Load all items and organize them by group_id
    all_items = list(Item.objects.all())
    group_map = defaultdict(list)

    for item in all_items:
        if item.group_id:
            group_map[item.group_id].append(item)

    # Only keep groups that contain exactly one item for each number 1–9
    valid_groups = {
        gid: items
        for gid, items in group_map.items()
        if len(set(i.number for i in items)) == 9
    }

    if len(valid_groups) < 9:
        raise ValueError("❌ Not enough valid group_ids with unique numbers 1–9.")

    return valid_groups


def build_number_to_item_mapping(selected_group_ids, group_map):
    # For each number 1–9, select an item with matching number from a different group
    number_to_item = {}

    for i, group_id in enumerate(selected_group_ids):
        items = group_map[group_id]
        item = next((it for it in items if it.number == i + 1), None)
        if not item:
            raise ValueError(f"❌ Group '{group_id}' does not contain item number {i + 1}")
        number_to_item[i + 1] = item

    return number_to_item


def create_game_for_player(player):
    # Generate Sudoku grid (with numbers 1–9)
    board = generate_sudoku()

    # Select 9 valid rooms (blocks) with unique group_ids inside
    selected_rooms = select_valid_rooms()

    # Create new game instance
    game = Game.objects.create(
        player=player,
        block_rooms=[room.id for room in selected_rooms],
        block_items={}
    )

    # Assign item mapping for each block based on room content
    block_items = {
        str(index): build_block_items(room)
        for index, room in enumerate(selected_rooms)
    }

    game.block_items = block_items
    game.save()

    # Fill the game board with Cells based on Sudoku logic
    fill_cells(game, board, block_items)
    return game


def select_valid_rooms():
    # Load and shuffle all rooms
    rooms = list(Room.objects.prefetch_related('items').all())
    random.shuffle(rooms)

    selected = []
    for room in rooms:
        group_ids = {item.group_id for item in room.items.all()}
        if len(group_ids) == 9:
            selected.append(room)
        if len(selected) == 9:
            return selected

    raise ValueError("❌ Nelze najít 9 místností s 9 unikátními group_id.")


def build_block_items(room):
    # Group items in the room by group_id
    group_map = defaultdict(list)
    for item in room.items.all():
        group_map[item.group_id].append(item)

    if len(group_map) != 9:
        raise ValueError(f"❌ Místnost '{room.name}' nemá 9 různých group_id.")

    # For each number 1–9, find an item with matching number from a different group_id
    number_to_item = {}
    used_group_ids = set()
    group_list = list(group_map.items())
    random.shuffle(group_list)

    for number in range(1, 10):
        for group_id, items in group_list:
            if group_id in used_group_ids:
                continue
            for item in items:
                if item.number == number:
                    number_to_item[number] = item.id
                    used_group_ids.add(group_id)
                    break
            if number in number_to_item:
                break
        else:
            raise ValueError(f"❌ Nelze najít item s číslem {number} v místnosti '{room.name}'.")

    if len(number_to_item) != 9:
        raise ValueError(f"❌ V místnosti '{room.name}' chybí některá čísla 1–9.")

    return number_to_item


def fill_cells(game, board, block_items):
    # Randomly choose 30 hidden cells (for difficulty)
    hidden_cells = set(random.sample(range(81), 30))

    for r in range(9):
        for c in range(9):
            number = board[r][c]
            grid_index = (r // 3) * 3 + (c // 3)
            item_id = block_items[str(grid_index)][number]
            item = Item.objects.get(id=item_id)

            is_prefilled = (r * 9 + c) not in hidden_cells

            # Create a Cell object with correct and optionally pre-filled selected item
            Cell.objects.create(
                game=game,
                row=r,
                column=c,
                correct_item=item,
                selected_item=item if is_prefilled else None,
                prefilled=is_prefilled
            )