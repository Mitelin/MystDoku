from django.shortcuts import render, redirect
from gameplay.models import Game, PlayerStoryProgress, Intro
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def home_landing(request):
    """
    Main page will serve as billboard and launching point of the game.
    This will redirect to the game menu if registered and if not to the register form.
    """
    return render(request, 'main/home_landing.html')
@login_required
def game_selection(request):
    """
    Main game page here player will be selecting modes for the game continuation or more options.
    """
    existing_game = Game.objects.filter(player=request.user, completed=False).first()

    return render(request, 'main/game_selection.html', {'existing_game': existing_game})

def play_redirect(request):
    """
    Redirect script that sort players if they are registered or not
    """

    if request.user.is_authenticated:
        return redirect('game_selection')  # Logged and registered player goes to game page
    return redirect('login')  # Non logged/registered player goes to login page / registration

def register(request):
    """
    New user registration
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('game_selection')  # After registration user is followed to main game page
    else:
        form = UserCreationForm()

    return render(request, 'auth/register.html', {'form': form})



@login_required
def game_selection(request):
    # Načtení textů intro z databáze
    intro = Intro.objects.order_by("order")
    intro_texts = list(intro.values_list("text", flat=True))
    intro_images = {
        1: "Intro1.png",
        2: "Intro1.png",
        3: "Intro1.png",
        4: "Intro2.png",
        5: "Intro2.png",
        6: "Intro2.png",
        7: "Intro2.png",
        8: "Intro3.png",
        9: "Intro3.png",
    }

    has_active_game = Game.objects.filter(player=request.user, completed=False).exists()
    progress, _ = PlayerStoryProgress.objects.get_or_create(player=request.user)

    has_any_memory = (
        progress.unlocked_easy or
        progress.unlocked_medium or
        progress.unlocked_hard
    )

    play_intro = not has_active_game and not has_any_memory

    return render(request, 'main/game_selection.html', {
        'play_intro': play_intro,
        'intro_texts': intro_texts,
        'intro_images': intro_images,
        'sequences': {
            'intro': intro_texts
        },
        'sequence_image_map': {
            'intro': intro_images
        }
    })