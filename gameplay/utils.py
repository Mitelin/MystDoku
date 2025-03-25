import random
from .models import Game, Cell, Item, Room
#from django.contrib.auth.models import User



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
    """
    Will add items to the game board randomly
    Shuffle game items so they are allways in different positions
    And create dictionary for those items
    """
    items = list(Item.objects.all())  # Load all possible items
    if len(items) < 9:
        raise ValueError("Error not enough items in database!")

    random.shuffle(items)  # Will shuffle order of items
    item_map = {i + 1: items[i] for i in range(9)}  # Will map numbers 1 - 9 to items

    # Replace numbers in matrix whit items
    item_board = [[item_map[num] for num in row] for row in board]

    return item_board

def create_game_for_player(player):
    """
    Function will create new gameboard and save it to the database
    """

    game = Game.objects.create(player=player)

    board = generate_sudoku()

    all_rooms = list(Room.objects.all())
    selected_rooms = random.sample(all_rooms, 9)
    block_rooms = [room.id for room in selected_rooms]
    block_items = {}

    for block_index, room in enumerate(selected_rooms):
        number_to_item = {}
        for number in range(1, 10):
            item = Item.objects.filter(room=room, number=number).order_by("?").first()
            number_to_item[number] = item.id
        block_items[block_index] = number_to_item

    game.block_rooms = block_rooms
    game.block_items = block_items
    game.save()

    hidden_cells = set(random.sample(range(81), 30))

    for r in range(9):
        for c in range(9):
            number = board[r][c]
            block_index = (r // 3) * 3 + (c // 3)
            item_id = block_items[block_index][number]
            correct_item = Item.objects.get(id=item_id)

            Cell.objects.create(
                game=game,
                row=r,
                column=c,
                correct_item=correct_item,
                selected_item=None if (r * 9 + c) in hidden_cells else correct_item
            )

    return game