from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .utils import create_game_for_player, get_sequence_for_trigger, try_unlock_memory
from .models import Game, Cell, Item, Room, Intro, Memory, DifficultyTransition, SequenceFrame, PlayerStoryProgress
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
import json
from django.apps import apps

@login_required
def start_new_game(request):
    """
    Will remove all existing games and create new one with unique UUID.
    Now also supports difficulty from GET param (?difficulty=medium)
    """
    # Remove all unfinished games for this player
    existing_games = Game.objects.filter(player=request.user, completed=False)
    if existing_games.exists():
        existing_games.delete()

    # Check if this is the player's very first game
    progress, _ = PlayerStoryProgress.objects.get_or_create(player=request.user)
    if not progress.unlocked_easy and not progress.unlocked_medium and not progress.unlocked_hard:
        request.session["play_intro"] = True

    # Read difficulty from query parameter (?difficulty=easy / medium / hard)
    difficulty = request.GET.get("difficulty", "easy").lower()
    if difficulty not in ["easy", "medium", "hard"]:
        difficulty = "easy"  # fallback

    # Create a new Game instance for the player using the selected difficulty
    game = create_game_for_player(request.user, difficulty=difficulty)

    # Redirect player to the game page (uses UUID for safety)
    return redirect('game_view', game_id=game.id)  # ✅ UUID instead of simple number ID


@login_required
def game_view(request, game_id, block_index=0):
    """
    Renders the main game page.

    Displays the full Sudoku grid with all 81 cells,
    highlights the currently selected 3×3 block,
    and shows the associated room, its items, and neighboring rooms.

    This view is large and handles logic, layout and state prep —
    should be split into smaller helpers in the future.
    """

    # Load the current game for the logged-in user
    try:
        game = Game.objects.get(id=game_id, player=request.user)
    except Game.DoesNotExist:
        return redirect('main_page')

    # (fallback) Should never happen due to get_object_or_404
    if not game:
        game = create_game_for_player(request.user)

    # Load all 81 cells ordered by row & column
    cells = list(Cell.objects.filter(game=game).order_by('row', 'column'))

    # Map of 3x3 blocks to their cell indexes
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
    # Select the 9 cells from the requested block
    selected_block = [cells[i] for i in block_mapping[block_index]]

    # Track which numbers are already used in the selected block
    used_numbers = set()
    for cell in selected_block:
        if cell.prefilled and cell.correct_item:
            used_numbers.add(cell.correct_item.number)
        elif cell.selected_item:
            used_numbers.add(cell.selected_item.number)

    # Find the Room linked to this block
    room_id = game.block_rooms[block_index]
    room = Room.objects.get(id=room_id)

    # Load the items assigned to this block
    item_ids = list(game.block_items[str(block_index)].values())  # JSONField keys are strings
    items = list(Item.objects.filter(id__in=item_ids).order_by("number"))

    # Collect all item IDs that have been selected or are correct
    used_item_ids = Cell.objects.filter(game=game).values_list("correct_item", "selected_item")
    used_item_ids = set(filter(None, [item_id for pair in used_item_ids for item_id in pair]))

    # Build item name lookup by ID (for item hover tooltips)
    item_names = {
        item.id: item.name
        for item in Item.objects.filter(id__in=used_item_ids)
    }

    # Build number → item info map for selected block (used in rendering)
    block_item_names = {}
    block_map = game.block_items[str(block_index)]
    for number_str, item_id in block_map.items():
        item = Item.objects.filter(id=item_id).first()
        if item:
            block_item_names[int(number_str)] = {
                "group_id": item.group_id,
                "name": item.name,
            }

    # Get adjacent block indexes (up/down/left/right)
    neighbor_indexes = get_neighbors(block_index)
    neighbor_rooms = {}

    # Map neighboring block index to room name
    for direction, idx in neighbor_indexes.items():
        room_id = game.block_rooms[idx]
        room = Room.objects.get(id=room_id)
        neighbor_rooms[direction] = {
            "index": idx,
            "name": room.name,
        }

    # Render the template with all required data
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
    Handles AJAX POST request when player places or removes an item in a cell.

    - If number == -1 → item is removed from the cell
    - If number in 1–9 → item from same room is placed into the cell
    - If game becomes completed → unlocks memory, updates score, deletes game
    """
    # DEBUG not in production
    # print(f"DEBUG: Received request - cell_id: {cell_id}")

    # Only accept POST requests
    if request.method == "POST":
        try:
            # Validate and load the Cell
            cell_id = int(cell_id)
            cell = get_object_or_404(Cell, id=cell_id, game__player=request.user)
            # DEBUG not in production
            # print(f"DEBUG: Loaded Cell - {cell}")

            # Parse JSON body to get selected number (1–9 or -1)
            data = json.loads(request.body)
            number = data.get("number", -1) # -1 means "remove item"

            if number == -1:
                # Remove item from the cell
                # DEBUG not in production
                # print("DEBUG: Removing item from cell")
                cell.selected_item = None
            else:
                # Select item from the same room by number
                room = cell.correct_item.room
                item = Item.objects.filter(room=room, number=number).first()

                if item:
                    # DEBUG not in production
                    # print(f"DEBUG: Loaded item by number {number} from room {room}")
                    cell.selected_item = item if cell.selected_item != item else None
                else:
                    # DEBUG! remove pass for DEBUG!
                    # print(f"DEBUG: Item with number {number} not found in room {room}") #  remove pass for DEBUG
                    pass
            # Save updated cell
            cell.save()

            # Check if the game is now completed
            game = cell.game
            if game.is_completed():
                # DEBUG not in production
                # print("DEBUG: Game is finished")
                game.completed = True
                game.save()

                # Try unlocking a new memory (if possible)
                new_memory = try_unlock_memory(game)
                if new_memory:
                    request.session["just_unlocked_order"] = new_memory.order
                    # DEBUG not in production
                    # print(f"DEBUG: Unlocked memory: {new_memory}")

                # Update scoreboard before deleting the game
                from score.utils import update_score_for_game
                update_score_for_game(game)

                # Delete game after scoring and memory unlock
                game.delete()

                return JsonResponse({
                    "status": "completed",
                    "redirect_url": "/gameplay/story/"
                })


        except Exception as e:
            # DEBUG not in production
            # print(f"DEBUG: Error {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    # If not POST → return error
    # DEBUG not in production
    # print("DEBUG: Invalid request method")
    return JsonResponse({"status": "error"}, status=400)

def get_neighbors(index):
    """
    Given a block index (0–8), returns a dictionary of its neighboring block indexes.

    Block layout (3×3):
        0 1 2
        3 4 5
        6 7 8

    Neighbors are mapped as: 'up', 'down', 'left', 'right'.

    Args:
        index (int): Block index from 0 to 8.

    Returns:
        dict[str, int]: Dictionary with directions and corresponding neighbor indexes.
    """
    neighbors = {}

    # Convert 0–8 index to 2D coordinates (row, col)
    row = index // 3
    col = index % 3

    # Add neighbor above (if not in top row)
    if row > 0:
        neighbors["up"] = (row - 1) * 3 + col

    # Add neighbor below (if not in bottom row)
    if row < 2:
        neighbors["down"] = (row + 1) * 3 + col
    # Add neighbor to the left (if not in leftmost column)
    if col > 0:
        neighbors["left"] = row * 3 + (col - 1)

    # Add neighbor to the right (if not in rightmost column)
    if col < 2:
        neighbors["right"] = row * 3 + (col + 1)

    return neighbors


def load_image_map(sequence_name: str) -> dict[int, str]:
    """
    Loads an ordered mapping of frame indexes to image filenames
    for a given sequence.

    Used to display background images for narrative transitions.

    Args:
        sequence_name (str): Name of the sequence (e.g. 'intro', 'memory', 'hard_end').

    Returns:
        dict[int, str]: A dictionary {index: image_filename}.
    """
    # Load all frames for the given sequence, ordered by index
    frames = SequenceFrame.objects.filter(sequence=sequence_name).order_by("index")

    # Build a dictionary {index: image_filename} for easy access in templates
    return {frame.index: frame.image for frame in frames}

def story_so_far(request):
    """
    Renders the "Story So Far" page where the player can view their unlocked memories.

    The function:
    - Loads text and images for all sequences (intro, easy/medium/hard end, memory)
    - Tracks player progress (unlocked memories by difficulty)
    - Determines which sequence to play (just unlocked memory, or final transition)
    - Prepares both text and image frames for animated rendering
    """
    # --- Intro ---
    # Load intro texts and images for the sequence "intro"
    intro = Intro.objects.order_by("order")
    intro_texts = list(intro.values_list("text", flat=True))
    intro_images = load_image_map("intro")

    # --- Easy ---
    # Load texts for easy difficulty and the transition text for easy
    easy_memories = Memory.objects.filter(difficulty="easy").order_by("order")
    easy_texts = list(easy_memories.values_list("text", flat=True))
    try:
        # Fetch the transition text for easy difficulty
        easy_transition = DifficultyTransition.objects.get(difficulty="easy")
        easy_texts.append(easy_transition.text)
    except ObjectDoesNotExist:
        # If no transition found, add a placeholder text
        easy_texts.append("[[MISSING EASY TRANSITION – story.json not loaded]")
    easy_images = load_image_map("easy_end")

    # --- Medium ---
    # Load texts for medium difficulty and the transition text for medium
    medium_memories = Memory.objects.filter(difficulty="medium").order_by("order")
    medium_texts = list(medium_memories.values_list("text", flat=True))
    try:
        # Fetch the transition text for medium difficulty
        medium_transition = DifficultyTransition.objects.get(difficulty="medium")
        medium_texts.append(medium_transition.text)
    except ObjectDoesNotExist:
        # If no transition found, add a placeholder text
        medium_texts.append("[MISSING MEDIUM TRANSITION – story.json not loaded]")
    medium_images = load_image_map("medium_end")

    # --- Hard special case ---
    # Get the texts for all difficulties (easy, medium, and hard) to combine them later
    easy_only_texts = list(
        Memory.objects.filter(difficulty="easy").order_by("order").values_list("text", flat=True)
    )
    medium_only_texts = list(
        Memory.objects.filter(difficulty="medium").order_by("order").values_list("text", flat=True)
    )
    hard_only_texts = list(
        Memory.objects.filter(difficulty="hard").order_by("order").values_list("text", flat=True)
    )
    try:
        # Get the transition text for hard difficulty
        hard_transition = DifficultyTransition.objects.get(difficulty="hard")
        hard_only_texts.append(hard_transition.text)
    except ObjectDoesNotExist:
        # If no transition found, add a placeholder text
        hard_only_texts.append("[MISSING HARD TRANSITION – story.json not loaded]")

    # Combine texts from easy, medium, and hard difficulties for the final hard-end sequence
    final_hard_texts = easy_only_texts + medium_only_texts + hard_only_texts

    # --- Images ---
    # Load images for all difficulty levels (easy, medium, hard)
    easy_only_images = load_image_map("easy_end")
    medium_only_images = load_image_map("medium_end")
    hard_only_images = load_image_map("hard_end")

    # Combine images for final hard-end sequence
    final_hard_images = {}
    i = 0
    for j in range(20):
        if j in easy_only_images:
            final_hard_images[i] = easy_only_images[j]
            i += 1
    for j in range(20):
        if j in medium_only_images:
            final_hard_images[i] = medium_only_images[j]
            i += 1
    for j in range(len(hard_only_images)):
        final_hard_images[i] = hard_only_images[j]
        i += 1


    # --- Player progress ---
    # Get or create the player's story progress (unlocked memories)
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

    # --- Last game and just unlocked memory ---
    # Check for the last completed game and whether a new memory was unlocked
    game = Game.objects.filter(player=request.user, completed=True).order_by("-created_at").first()
    just_unlocked = None
    order = request.session.pop("just_unlocked_order", None)
    if order is not None:
        just_unlocked = Memory.objects.filter(order=order).first()

    # If a memory was just unlocked, set it for display
    if just_unlocked:
        memory = [
            just_unlocked.text,
            just_unlocked.transition or "[MISSING TRANSITION]"
        ]
        memory_images = load_image_map("memory")
    else:
        memory = []
        memory_images = {}

    # --- Choose sequence to play ---
    # Determine the correct sequence based on the player's progress and unlocked memories
    sequence_name = None
    if just_unlocked and just_unlocked.difficulty == "easy" and len(unlocked_easy) == 20:
        sequence_name = "easy_end"
    elif just_unlocked and just_unlocked.difficulty == "medium" and len(unlocked_medium) == 20:
        sequence_name = "medium_end"
    elif just_unlocked and just_unlocked.difficulty == "hard" and len(unlocked_hard) == 20:
        sequence_name = "hard_end"
    elif just_unlocked:
        difficulty = just_unlocked.difficulty
        unlocked_count = {
            "easy": len(unlocked_easy),
            "medium": len(unlocked_medium),
            "hard": len(unlocked_hard),
        }[difficulty]
        if unlocked_count == 20:
            sequence_name = f"{difficulty}_end"
        else:
            sequence_name = "memory"
    else:
        sequence_name = None

    # --- Output ---
    # Prepare context to pass to the template
    sequences = {
        "intro": intro_texts,
        "easy_end": easy_texts,
        "medium_end": medium_texts,
        "hard_end": final_hard_texts,
        "memory": memory,
    }
    sequence_image_map = {
        "intro": intro_images,
        "easy_end": easy_images,
        "medium_end": medium_images,
        "hard_end": final_hard_images,
        "memory": memory_images,
    }
    # Calculate total unlocked memories (easy + medium + hard)
    total_unlocked = (
        len(progress.unlocked_easy) +
        len(progress.unlocked_medium) +
        len(progress.unlocked_hard)
    )
    # Render the story page with all the context data
    return render(request, "gameplay/story_so_far.html", {
        "unlocked_easy": unlocked_easy,
        "unlocked_medium": unlocked_medium,
        "unlocked_hard": unlocked_hard,
        "sequence_name": sequence_name,
        "sequence_frames": sequences.get(sequence_name, []),
        "sequence_images": sequence_image_map.get(sequence_name, {}),
        "sequences": sequences,
        "sequence_image_map": sequence_image_map,
        "total_unlocked": total_unlocked,
    })

@login_required
def auto_fill(request, game_id):
    """
    DEBUG FUNCTION!
    Autofill all empty cells with their correct items.

    This is used to help players complete the Sudoku puzzle.
    Only cells that are not pre-filled are updated.

    After filling, the user is redirected to the first block.

    Args:
        request (HttpRequest): The HTTP request object.
        game_id (int): The ID of the game to be autofilled.

    Returns:
        HttpResponseRedirect: Redirects to the game block view.
    """
    # Load the game based on its ID and check if it's for the current player
    game = get_object_or_404(Game, id=game_id, player=request.user)

    # Find all cells in this game that are not prefilled
    cells = Cell.objects.filter(game=game, prefilled=False)
    # For each empty cell, assign the correct item to the cell
    for cell in cells:
        # Set the selected item to the correct item for this cell
        cell.selected_item = cell.correct_item
        cell.save() # Save the updated cell

    # Redirect the player to the first block (block_index=0)
    return redirect("game_block", game_id=game.id, block_index=0)


@login_required
def reset_progress(request):
    """
    Resets the player's progress, including:
    - Deletes all unlocked memories.
    - Resets player score and progress statistics.
    Redirects the player to the game selection page after resetting.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects to the game selection view.
    """
    # Dynamically import the PlayerStoryProgress model (needed for resetting)
    PlayerStoryProgress = apps.get_model('gameplay', 'PlayerStoryProgress')

    # Delete all unlocked memories and progress for the current player
    PlayerStoryProgress.objects.filter(player=request.user).delete()

    # Fetch the player's score object
    PlayerScore = apps.get_model('score', 'PlayerScore')

    # Reset all progress and stats related to the player’s score
    player_score = PlayerScore.objects.get(user=request.user)
    player_score.unlocked_memories = 0
    player_score.completed_easy = 0
    player_score.completed_medium = 0
    player_score.completed_hard = 0
    player_score.best_time_easy = None
    player_score.best_time_medium = None
    player_score.best_time_hard = None
    player_score.total_completed_games = 0
    # Save the reset player score to the database
    player_score.save()

    # Redirect the player to the game selection screen after resetting progress
    return redirect("game_selection")

@login_required
def debug_add_memory(request, difficulty):
    """
    DEBUG FUNCTION!
    For debugging purposes: Adds a memory to the player's progress based on the difficulty level.

    The function:
    - Adds the next unlocked memory from the specified difficulty (easy, medium, or hard).
    - Marks the memory as unlocked and sets it for playback.
    - Redirects to the "story_so_far" page to show the newly unlocked memory.

    Args:
        request (HttpRequest): The HTTP request object.
        difficulty (str): The difficulty level (easy, medium, hard).

    Returns:
        HttpResponseRedirect: Redirects to the "story_so_far" page.
    """
    # Get or create the PlayerStoryProgress for the current player
    progress, _ = PlayerStoryProgress.objects.get_or_create(player=request.user)
    # Get all memories for the specified difficulty, ordered by their 'order'
    memory_qs = Memory.objects.filter(difficulty=difficulty).order_by("order")

    # Determine which list of unlocked memories to update based on difficulty
    if difficulty == "easy":
        current = progress.unlocked_easy
    elif difficulty == "medium":
        current = progress.unlocked_medium
    elif difficulty == "hard":
        current = progress.unlocked_hard
    else:
        # Redirect to game selection if an unknown difficulty is provided
        return redirect("game_selection")  # unknown difficulty fallback


    # Find the next memory that hasn't been unlocked yet
    next_mem = memory_qs.exclude(order__in=current).first()
    # Add the next memory to the appropriate unlocked list based on difficulty
    if next_mem:
        if difficulty == "easy":
            progress.unlocked_easy.append(next_mem.order)
        elif difficulty == "medium":
            progress.unlocked_medium.append(next_mem.order)
        elif difficulty == "hard":
            progress.unlocked_hard.append(next_mem.order)
        # Save the player's updated progress
        progress.save()

        # Mark the just unlocked memory for playback (used in the "story_so_far" page)
        request.session["just_unlocked_order"] = next_mem.order
    # Redirect the player to the story page to view the newly unlocked memory
    return redirect("story_so_far")

@login_required
def game_selection(request):
    """
    The main page where the player selects options for continuing the game or starting a new one.

    - If no game is active and no memories are unlocked, the intro sequence is displayed.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered game selection page.
    """
    # Check if the player has an active game (not completed)
    existing_game = Game.objects.filter(player=request.user, completed=False).first()


    # --- Intro ---
    # Load intro texts and images for the first-time experience
    intro = Intro.objects.order_by("order")
    intro_texts = list(intro.values_list("text", flat=True))
    intro_images = load_image_map("intro")

    # --- Detect if player has any active game or unlocked memory ---
    # Check if player has an active game (not completed)
    has_active_game = existing_game is not None

    # Get or create the player's progress in terms of unlocked memories
    progress, _ = PlayerStoryProgress.objects.get_or_create(player=request.user)
    # Check if player has any unlocked memory (easy, medium, or hard)
    has_any_memory = (
        progress.unlocked_easy or
        progress.unlocked_medium or
        progress.unlocked_hard
    )
    # --- Intro condition ---
    # If there is no active game and no memories unlocked, the intro will be played
    play_intro = not has_active_game and not has_any_memory

    # Render the game section page with all the context data
    return render(request, 'gameplay/game_selection.html', {
        'progress': progress,  # For status
        'unlocked_easy': progress.unlocked_easy,
        'unlocked_medium': progress.unlocked_medium,
        'existing_game': existing_game,
        'play_intro': play_intro,
        'sequences': {
            'intro': intro_texts
        },
        'sequence_image_map': {
            'intro': intro_images
        }
    })

def manual_view(request):
    """
    Renders the game manual page. This page is typically used to explain the game mechanics and rules.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered manual page.
    """
    # Render the manual page
    # This page provides the game instructions or guidelines
    return render(request, "gameplay/manual.html")