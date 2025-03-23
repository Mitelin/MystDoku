from django.db import models
from django.contrib.auth.models import User
import uuid

class Room(models.Model):
    """
    Model for Definition of thematic rooms for usage in different games.
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Item(models.Model):
    """
    Model for Thematic items:
    (1, fork)
    (2, knifes)
    (3, coolers)
    ...
    Belongs to unique rooms
    """
    name = models.CharField(max_length=100)
    number = models.IntegerField()  # Number 1–9
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='items')

    def __str__(self):
        return f"{self.name} ({self.number}) in {self.room.name}"

    class Meta:
        unique_together = ('name', 'number', 'room')


class Game(models.Model):
    """
    Model for Game instance
    This model links user (Player) id and game user creating.
    We are using id of user and game time of creation as additional identifier for future scoreboard
    We are setting up the user in a way that if he deletes his account his complete history will be removed.
    We are using UUID instead of int ID it simply looks better
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # ⚠️ Unique UUID instead of simple ID
    player = models.ForeignKey(User, on_delete=models.CASCADE)  # id of User
    created_at = models.DateTimeField(auto_now_add=True)  # Game time creation for future score tracking
    completed = models.BooleanField(default=False)  # Game status

    def __str__(self):
        return f"Game {self.id} - User: {self.player.username} - {'Completed' if self.completed else 'In progress'}"

    def is_completed(self):
        """
        Return True if the game is successfully completed.
        """
        return not Cell.objects.filter(grid__game=self, selected_item__isnull=True).exists() and \
               not Cell.objects.filter(grid__game=self).exclude(correct_item=models.F("selected_item")).exists()

class Cell(models.Model):
    """
    Model for Definition of cells and where they belong.
    This model store cells with their columns and rows and identification of their valid / invalid status.
    And this also store the player current selection.
    Using the selected item and correct item will enable validation of sudoku Game state and current selection state.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    row = models.IntegerField()  # Row (0-8) We are using 9 cells but computer naming start whit 0 so 0-8 but 9 total
    column = models.IntegerField()  # Column (0-8) We are using 9 cells but computer naming start whit 0 so 0-8 but 9 total
    correct_item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="correct_cells")  # Correct item belonging to right cell
    selected_item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, related_name="selected_cells")  # Player selected item

    def __str__(self):
        return f"Cell ({self.row}, {self.column})"

    def is_correct(self):
        """
        Will return true if the user selected the correct cell
        """
        return self.selected_item == self.correct_item

