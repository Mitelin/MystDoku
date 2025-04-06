from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .utils import create_game_for_player, get_sequence_for_trigger, try_unlock_memory
from .models import Game, Cell, Item, Room, Intro, Memory, DifficultyTransition, PlayerStoryProgress, SequenceFrame
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
import json


@login_required
def start_new_game(request):
    """
    Will remove all existing games and create new one with unique UUID.
    Now also supports difficulty from GET param (?difficulty=medium)
    """

    existing_games = Game.objects.filter(player=request.user, completed=False)
    if existing_games.exists():
        existing_games.delete()

    # 🔍 Zjistíme, jestli je to první hra hráče
    progress, _ = PlayerStoryProgress.objects.get_or_create(player=request.user)
    if not progress.unlocked_easy and not progress.unlocked_medium and not progress.unlocked_hard:
        request.session["play_intro"] = True

    difficulty = request.GET.get("difficulty", "easy").lower()
    if difficulty not in ["easy", "medium", "hard"]:
        difficulty = "easy"  # fallback

    game = create_game_for_player(request.user, difficulty=difficulty)
    return redirect('game_view', game_id=game.id)  # ✅ UUID instead of simple number ID


@login_required
def game_view(request, game_id, block_index=0):
    """
    Render page for the game – display full sudoku + selected 3×3 blocks.
    IM NEED TO BE SPLIT AND REFACTORED!!!
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

    used_numbers = set()
    for cell in selected_block:
        if cell.prefilled and cell.correct_item:
            used_numbers.add(cell.correct_item.number)
        elif cell.selected_item:
            used_numbers.add(cell.selected_item.number)
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
            block_item_names[int(number_str)] = {
                "group_id": item.group_id,
                "name": item.name,
            }

    neighbor_indexes = get_neighbors(block_index)
    neighbor_rooms = {}

    for direction, idx in neighbor_indexes.items():
        room_id = game.block_rooms[idx]
        room = Room.objects.get(id=room_id)
        neighbor_rooms[direction] = {
            "index": idx,
            "name": room.name,
        }

    return render(request, 'gameplay/game.html', {
        'game': game,
        "in_game": True,
        'cells': cells,
        'selected_block': selected_block,
        'items': items,
        "group_id": item.group_id,
        'neighbors': neighbor_rooms,
        'room_name': room.name,
        'block_index': block_index,
        'block_range': range(9),
        'item_names': item_names,
        'used_numbers': used_numbers,
        'block_item_names': block_item_names,
        'range9': range(9),
        'current_room': game.block_rooms[block_index],
        'room_links': [
            {'index': i, 'name': Room.objects.get(id=rid).name}
            for i, rid in enumerate(game.block_rooms)
        ],

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

                # 🔓 Odemkni memory hned po výhře
                new_memory = try_unlock_memory(game)
                if new_memory:
                    request.session["just_unlocked_order"] = new_memory.order
                print(f"DEBUG: Unlocked memory: {new_memory}")

                return JsonResponse({"status": "completed"})

                return JsonResponse({"status": "completed"})
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

def get_neighbors(index):
    neighbors = {}

    row = index // 3
    col = index % 3

    if row > 0:
        neighbors["up"] = (row - 1) * 3 + col
    if row < 2:
        neighbors["down"] = (row + 1) * 3 + col
    if col > 0:
        neighbors["left"] = row * 3 + (col - 1)
    if col < 2:
        neighbors["right"] = row * 3 + (col + 1)

    return neighbors


def load_image_map(sequence_name: str) -> dict[int, str]:
    frames = SequenceFrame.objects.filter(sequence=sequence_name).order_by("index")
    return {frame.index: frame.image for frame in frames}


def story_so_far(request):
    # intro sekvence
    intro = Intro.objects.order_by("order")
    intro_texts = list(intro.values_list("text", flat=True))
    intro_images = load_image_map("intro")

    # easy sekvence
    easy_memories = Memory.objects.filter(difficulty="easy").order_by("order")
    easy_texts = list(easy_memories.values_list("text", flat=True))

    try:
        easy_transition = DifficultyTransition.objects.get(difficulty="easy")
        easy_texts.append(easy_transition.text)
    except ObjectDoesNotExist:
        easy_texts.append("[CHYBÍ PŘECHOD EASY – story.json nebyl načten]")

    easy_images = load_image_map("easy_end")

    medium_memories = Memory.objects.filter(difficulty="medium").order_by("order")
    medium_texts = list(medium_memories.values_list("text", flat=True))

    try:
        medium_transition = DifficultyTransition.objects.get(difficulty="medium")
        medium_texts.append(medium_transition.text)
    except ObjectDoesNotExist:
        medium_texts.append("[CHYBÍ PŘECHOD medium – story.json nebyl načten]")

    medium_images = load_image_map("medium_end")

    # hard sekvence
    hard_memories = Memory.objects.filter(difficulty="hard").order_by("order")
    hard_texts = list(hard_memories.values_list("text", flat=True))

    try:
        hard_transition = DifficultyTransition.objects.get(difficulty="hard")
        hard_texts.append(hard_transition.text)
    except ObjectDoesNotExist:
        hard_texts.append("[CHYBÍ PŘECHOD HARD – story.json nebyl načten]")

    hard_images = load_image_map("hard_end")

    progress, _ = PlayerStoryProgress.objects.get_or_create(player=request.user)

    unlocked_easy = Memory.objects.filter(
        difficulty="easy", order__in=progress.unlocked_easy
    ).order_by("order")

    unlocked_medium = Memory.objects.filter(
        difficulty="medium", order__in=progress.unlocked_medium
    ).order_by("order")

    unlocked_hard = Memory.objects.filter(
        difficulty="hard", order__in=progress.unlocked_hard
    ).order_by("order")
    game = Game.objects.filter(player=request.user, completed=True).order_by("-created_at").first()
    just_unlocked = None
    order = request.session.pop("just_unlocked_order", None)
    if order is not None:
        # Zjistíme, jaké difficulty to je
        just_unlocked = Memory.objects.filter(order=order).first()
    if just_unlocked:
        memory = [
            just_unlocked.text,
            just_unlocked.transition or "[CHYBÍ TRANSITION]"
        ]
        memory_images = load_image_map("memory")
    else:
        memory = []
        memory_images = {}

    sequence_name = None

    # 🎯 EASY END – pokud právě získal 20. vzpomínku
    if just_unlocked and just_unlocked.difficulty == "easy" and len(unlocked_easy) == 20:
        sequence_name = "easy_end"

    # 🎯 MEDIUM END
    elif just_unlocked and just_unlocked.difficulty == "medium" and len(unlocked_medium) == 20:
        sequence_name = "medium_end"

    # 🎯 HARD END
    elif just_unlocked and just_unlocked.difficulty == "hard" and len(unlocked_hard) == 20:
        sequence_name = "hard_end"

    # 🧠 Pokud právě odemkl memory (ale nemá ještě 20)
    elif just_unlocked and (len(unlocked_easy) < 20 and len(unlocked_medium) < 20 and len(unlocked_hard) < 20):
        sequence_name = "memory"

    # 🆕 Pokud není splněna žádná podmínka, neprovádí se nic
    else:
        sequence_name = None

    sequences = {
        "intro": intro_texts,
        "easy_end": easy_texts,
        "medium_end": medium_texts,
        "hard_end": hard_texts,
        "memory": memory,
    }
    sequence_image_map = {
        "intro": intro_images,
        "easy_end": easy_images,
        "medium_end": medium_images,
        "hard_end": hard_images,
        "memory": memory_images,
    }

    return render(request, "gameplay/story_so_far.html", {
        "unlocked_easy": unlocked_easy,
        "unlocked_medium": unlocked_medium,
        "unlocked_hard": unlocked_hard,
        "sequence_name": sequence_name,
        "sequence_frames": sequences.get(sequence_name, []),
        "sequence_images": sequence_image_map.get(sequence_name, {}),
        "sequences": sequences,
        "sequence_image_map": sequence_image_map,
    })

@login_required
def auto_fill(request, game_id):
    game = get_object_or_404(Game, id=game_id, player=request.user)

    cells = Cell.objects.filter(game=game, prefilled=False)

    for cell in cells:
        cell.selected_item = cell.correct_item
        cell.save()

    return redirect("game_block", game_id=game.id, block_index=0)

@login_required
def reset_progress(request):
    PlayerStoryProgress.objects.filter(player=request.user).delete()
    return redirect("story_so_far")

@login_required
def debug_add_memory(request, difficulty):
    progress, _ = PlayerStoryProgress.objects.get_or_create(player=request.user)
    memory_qs = Memory.objects.filter(difficulty=difficulty).order_by("order")

    if difficulty == "easy":
        current = progress.unlocked_easy
    elif difficulty == "medium":
        current = progress.unlocked_medium
    elif difficulty == "hard":
        current = progress.unlocked_hard
    else:
        return redirect("game_selection")  # unknown difficulty fallback

    next_mem = memory_qs.exclude(order__in=current).first()
    if next_mem:
        if difficulty == "easy":
            progress.unlocked_easy.append(next_mem.order)
        elif difficulty == "medium":
            progress.unlocked_medium.append(next_mem.order)
        elif difficulty == "hard":
            progress.unlocked_hard.append(next_mem.order)
        progress.save()
        request.session["just_unlocked_order"] = next_mem.order  # spustíme přehrání

    return redirect("story_so_far")

