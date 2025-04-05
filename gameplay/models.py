from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField
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
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='items') # Ids of room
    group_id = models.CharField(max_length=100) # Unique identifier for similar items

    def __str__(self):
        return f"{self.name} ({self.number}) in {self.room.name}"

    class Meta:
        unique_together = ('name', 'number', 'room')

DIFFICULTY_CHOICES = [
    ('easy', 'Easy'),
    ('medium', 'Medium'),
    ('hard', 'Hard'),
]


class Game(models.Model):
    """
    Model for Game instance
    This model links user (Player) id and game that user creating.
    We are using id of user and game time of creation as additional identifier for future scoreboard
    We are setting up the user in a way that if he deletes his account his complete history will be removed.
    We are using UUID instead of int ID it simply looks better
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # ⚠️ Unique UUID instead of simple ID
    player = models.ForeignKey(User, on_delete=models.CASCADE)  # id of User
    created_at = models.DateTimeField(auto_now_add=True)  # Game time creation for future score tracking
    completed = models.BooleanField(default=False)  # Game status
    block_rooms = JSONField(default=list)  # List of 9 Room IDs for current game
    block_items = JSONField(default=dict)  # Dict: block -> number -> item ID
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')

    def __str__(self):
        return f"Game {self.id} - User: {self.player.username} - {'Completed' if self.completed else 'In progress'}"

    def is_completed(self):
        """
        Return True if the game is successfully completed.
        """
        cells = Cell.objects.filter(game=self)

        for cell in cells:
            if not cell.selected_item or not cell.is_correct():
                return False

        return True


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
    prefilled = models.BooleanField(default=False)

    def __str__(self):
        return f"Cell ({self.row}, {self.column})"

    def is_correct(self):
        """
        Will return true if the user selected the correct cell
        """
        return (
                self.selected_item is not None and
                self.correct_item is not None and
                self.selected_item.number == self.correct_item.number
        )

class Intro(models.Model):
    """
    Model for representing Introduction data.
    It selected in order for easy step by step load.
    """
    order = models.PositiveIntegerField(unique=True)
    text = models.TextField()

    class Meta:
        ordering = ['order']

    # Read data for admin Intro 1 , 2 , 3
    def __str__(self):
        return f"Intro {self.order}"


class Memory(models.Model):
    """
    Model for each memory from protagonist
    Its split to 3 blocks each representing different memory sets.
    Links memory difficulty and transition together
    """
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    order = models.PositiveIntegerField(unique=True)
    text = models.TextField()
    transition = models.TextField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Memory {self.order} ({self.difficulty})"


class DifficultyTransition(models.Model):
    """
    Create difficulty transitions between difficulty levels.
    """
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('end', 'End'),
    ]

    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, unique=True)
    text = models.TextField()

    def __str__(self):
        return f"Transition ({self.difficulty})"

class PlayerStoryProgress(models.Model):
    """
    Tracks user memory progress for each difficulty.
    """
    player = models.OneToOneField(User, on_delete=models.CASCADE)

    unlocked_easy = models.JSONField(default=list)
    unlocked_medium = models.JSONField(default=list)
    unlocked_hard = models.JSONField(default=list)

    def __str__(self):
        return f"{self.player.username} memory progress"