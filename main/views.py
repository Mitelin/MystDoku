from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def home_landing(request):
    """
    Main page will serve as billboard and launching point of the game.
    This will redirect to the game menu if registered and if not to the register form.
    """
    return render(request, 'main/home_landing.html')

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

def fallback_redirect(request, unused_path):
    return redirect('main_page')  # redirect to main page