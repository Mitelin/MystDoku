from django.contrib import admin
from .models import Game, Cell, Item, Room

admin.site.register(Game)
admin.site.register(Item)
admin.site.register(Room)

@admin.register(Cell)
class CellAdmin(admin.ModelAdmin):
    list_display = ('id', 'game', 'row', 'column', 'selected_item', 'correct_item', 'prefilled')
    list_filter = ('game', 'prefilled')