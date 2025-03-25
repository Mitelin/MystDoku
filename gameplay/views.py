from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .utils import create_game_for_player
from .models import Game, Cell, Item, Room
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def start_new_game(request):
    """
    Will remove all existing games and create new one whit unique UUID
    Added debug messages for further changes current
    REMOVE # For DEBUG
    """
    existing_games = Game.objects.filter(player=request.user, completed=False)

    if existing_games.exists():
        # print(f"DEBUG: Deleting: {existing_games.count()} unfinished games of player: {request.user}")
        existing_games.delete()

    # print(f"DEBUG: Creating new game for player: {request.user}")
    game = create_game_for_player(request.user)
    return redirect('game_view', game_id=game.id)  # ✅ UUID instead of simple number ID




@login_required
def game_view(request, game_id, block_index=0):
    """
    Render page for the game – display full sudoku + selected 3×3 blocks.

    """
    game = get_object_or_404(Game, id=game_id, player=request.user)

    if not game:
        game = create_game_for_player(request.user)

    cells = list(Cell.objects.filter(game=game).order_by('row', 'column'))

    block_mapping = {
        0: [0, 1, 2, 9, 10, 11, 18, 19, 20],
        1: [3, 4, 5, 12, 13, 14, 21, 22, 23],
        2: [6, 7, 8, 15, 16, 17, 24, 25, 26],
        3: [27, 28, 29, 36, 37, 38, 45, 46, 47],
        4: [30, 31, 32, 39, 40, 41, 48, 49, 50],
        5: [33, 34, 35, 42, 43, 44, 51, 52, 53],
        6: [54, 55, 56, 63, 64, 65, 72, 73, 74],
        7: [57, 58, 59, 66, 67, 68, 75, 76, 77],
        8: [60, 61, 62, 69, 70, 71, 78, 79, 80],
    }

    selected_block = [cells[i] for i in block_mapping[block_index]]

    # part for getting id of rooms and translating it to our blocks.
    room_id = game.block_rooms[block_index]
    room = Room.objects.get(id=room_id)

    item_ids = list(game.block_items[str(block_index)].values())  # JSONField keys are strings
    items = list(Item.objects.filter(id__in=item_ids).order_by("number"))
    used_item_ids = Cell.objects.filter(game=game).values_list("correct_item", "selected_item")
    used_item_ids = set(filter(None, [item_id for pair in used_item_ids for item_id in pair]))

    item_names = {
        item.id: item.name
        for item in Item.objects.filter(id__in=used_item_ids)
    }
    block_item_names = {}
    block_map = game.block_items[str(block_index)]
    for number_str, item_id in block_map.items():
        item = Item.objects.filter(id=item_id).first()
        if item:
            block_item_names[int(number_str)] = item.name
    return render(request, 'gameplay/game.html', {
        'game': game,
        'cells': cells,
        'selected_block': selected_block,
        'items': items,
        'room_name': room.name,
        'block_index': block_index,
        'block_range': range(9),
        'item_names': item_names,
        'block_item_names': block_item_names,
    })

@csrf_exempt
@login_required
def place_item(request, cell_id):
    """
    DEBUG DIDNT WANT TO WORK....
    Save selected item to the cell or remove him if clicked
    """

    print(f"DEBUG: Received request - cell_id: {cell_id}")

    if request.method == "POST":
        try:
            cell_id = int(cell_id)
            cell = get_object_or_404(Cell, id=cell_id, game__player=request.user)
            print(f"DEBUG: Loaded Cell - {cell}")

            data = json.loads(request.body)
            number = data.get("number", -1)  # 1–9 ether or -1 = deletion

            if number == -1:
                print("DEBUG: Removing item from cell")
                cell.selected_item = None
            else:
                # will find correct item by its room.
                room = cell.correct_item.room
                item = Item.objects.filter(room=room, number=number).first()

                if item:
                    print(f"DEBUG: Loaded item by number {number} from room {room}")
                    cell.selected_item = item if cell.selected_item != item else None
                else:
                    print(f"DEBUG: Item with number {number} not found in room {room}")

            cell.save()

            game = cell.game
            if game.is_completed():
                print("DEBUG: Game is finished")
                game.completed = True
                game.save()
                return JsonResponse({"status": "completed"})

            return JsonResponse({"status": "success"})
        except Exception as e:
            print(f"DEBUG: Error {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    print("DEBUG: Invalid request method")
    return JsonResponse({"status": "error"}, status=400)

@login_required
def win_view(request):
    """
    Will render the win page
    """
    return render(request, 'gameplay/win.html')