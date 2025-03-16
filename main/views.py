from django.shortcuts import render, redirect
from gameplay.models import Game
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

@login_required
def home(request):
    """
    Main game page here player will be selecting modes for the game continuation or more options.
    """
    existing_game = Game.objects.filter(player=request.user, completed=False).first()

    return render(request, 'main/home.html', {'existing_game': existing_game})

def main_page(request):
    """
    Main page will serve as billboard and launching point of the game.
    This will redirect to the game menu if registered and if not to the register form.
    """
    return render(request, 'main/main_page.html')

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