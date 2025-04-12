from gameplay.models import Game

def existing_game(request):
    if request.user.is_authenticated:
        existing_game = Game.objects.filter(player=request.user, completed=False).first()
        return {'existing_game': existing_game}
    return {}