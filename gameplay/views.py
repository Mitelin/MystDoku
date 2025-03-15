from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .utils import create_game_for_player
from .models import Game, Grid, Cell, Item
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def start_new_game(request):
    """
    Create new game for logged user and redirect to its page
    """
    game = create_game_for_player(request.user)
    return redirect(f'/gameplay/{game.id}/')

@login_required
def game_view(request, game_id):
    """
    Render page for the game
    """
    game = get_object_or_404(Game, id=game_id, player=request.user)
    grids = Grid.objects.filter(game=game).order_by('index')
    cells = Cell.objects.filter(grid__game=game).order_by('grid__index', 'row', 'column')
    items = Item.objects.all()  # List of all available items

    # Adding the boolean for the cells (right/wrong answers) empty string if empty
    for cell in cells:
        cell.status = "correct" if cell.selected_item and cell.is_correct() \
            else "incorrect" if cell.selected_item else ""

    grid_borders = [2, 5]

    return render(request, 'gameplay/game.html', {
        'game': game,
        'grids': grids,
        'cells': cells,
        'items': items,  # Sending available items
        'grid_borders': grid_borders
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
            cell = get_object_or_404(Cell, id=cell_id, grid__game__player=request.user)
            print(f"DEBUG: Loaded Cell - {cell}")

            data = json.loads(request.body)  # Load JSON dat
            item_id = data.get("item_id", -1)  # Default value is -1 (deletion)

            if item_id == -1:
                print("DEBUG: Removing object from cell")
                cell.selected_item = None
            else:
                item = get_object_or_404(Item, id=item_id)
                print(f"DEBUG: Loaded item - {item}")
                cell.selected_item = item if cell.selected_item != item else None

            cell.save()

            game = cell.grid.game
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