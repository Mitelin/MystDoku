from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .utils import create_game_for_player
from .models import Game, Grid, Cell, Item
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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
def place_item(request, cell_id, item_id):
    """Save item and place it in the grid"""
    if request.method == "POST":
        cell = get_object_or_404(Cell, id=cell_id, grid__game__player=request.user)
        item = get_object_or_404(Item, id=item_id)
        cell.selected_item = item
        cell.save()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)