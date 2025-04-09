from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField
import uuid

class Room(models.Model):
    """
    Model for definition of thematic rooms used in different games.
    Each room can be associated with several items.
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Item(models.Model):
    """
    Model for thematic items:
    (1, fork),
    (2, knives),
    (3, coolers),
    ...
    Belongs to a unique room.
    """
    name = models.CharField(max_length=100)  # Name of the item (e.g., fork, knife)
    number = models.IntegerField()   # Number representing the item (1-9)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='items') # Room to which the item belongs
    group_id = models.CharField(max_length=100) # Unique identifier for similar items (e.g., all forks share the same group_id)

    def __str__(self):
        return f"{self.name} ({self.number}) in {self.room.name}"

    class Meta:
        unique_together = ('name', 'number', 'room') # Ensures that there can't be duplicate items with the same name, number, and room

DIFFICULTY_CHOICES = [
    ('easy', 'Easy'),
    ('medium', 'Medium'),
    ('hard', 'Hard'),
]


class Game(models.Model):
    """
    Model for a game instance.

    This model links the user (Player) ID and the game that the user is creating.
    We are using the user ID and game creation time as additional identifiers for future scoreboards.
    We also set up the user so that if they delete their account, their entire game history will be removed.
    Instead of an int ID, we use UUID because it looks better.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # Unique UUID as the primary key
    player = models.ForeignKey(User, on_delete=models.CASCADE)   # ForeignKey to the User model
    created_at = models.DateTimeField(auto_now_add=True)   # Timestamp when the game is created
    completed = models.BooleanField(default=False)  # Game status (completed or in progress)
    block_rooms = JSONField(default=list)  # List of 9 Room IDs for the current game
    block_items = JSONField(default=dict)  # Mapping: block -> number -> item ID (mapping for blocks in sudoku)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy') # Difficulty level (easy, medium, hard)

    def __str__(self):
        return f"Game {self.id} - User: {self.player.username} - {'Completed' if self.completed else 'In progress'}"

    def is_completed(self):
        """
        Returns True if the game is successfully completed.
        This checks if all cells are filled correctly.
        """
        cells = Cell.objects.filter(game=self)

        for cell in cells:
            if not cell.selected_item or not cell.is_correct():
                return False

        return True


class Cell(models.Model):
    """
    Model for defining cells and where they belong.

    This model stores cells with their columns, rows, and identification of their valid/invalid status.
    It also stores the player's current selection.
    The selected item and correct item will enable validation of the sudoku game state and the current selection state.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE) # ForeignKey to the Game model
    row = models.IntegerField()  # Row index (0–8)
    column = models.IntegerField()  # Column index (0–8)
    correct_item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="correct_cells")   # The correct item for the sudoku cell
    selected_item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, related_name="selected_cells")  # The item selected by the player
    prefilled = models.BooleanField(default=False) # Whether the cell is prefilled (part of the puzzle or not)

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
    Model for representing introduction data (text) in a sequence.
    The texts are ordered by 'order' field for a step-by-step load during the game.

    This model stores the order in which the introduction texts should appear
    and the text content itself.
    """
    order = models.PositiveIntegerField(unique=True)  # The order in which texts should appear (1, 2, 3...)
    text = models.TextField()  # The text of the introduction

    class Meta:
        ordering = ['order']  # Ensure texts are ordered by 'order' field when queried

    # Read data for admin Intro 1 , 2 , 3
    def __str__(self):
        return f"Intro {self.order}"


class Memory(models.Model):
    """
    Model for representing each memory of the protagonist.
    Memories are split into 3 blocks, each representing different difficulty levels.
    Links memory difficulty and transition together.

    Each memory has a specific order and is associated with a transition text.
    """
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    # Difficulty of the memory (easy, medium, hard)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)

    # Order in which the memory should appear (unique for each memory)
    order = models.PositiveIntegerField(unique=True)

    # The content of the memory
    text = models.TextField()

    # Transition text that is shown when the memory is triggered
    transition = models.TextField()

    class Meta:
        ordering = ['order'] # Ensure memories are ordered by their 'order' field

    def __str__(self):
        return f"Memory {self.order} ({self.difficulty})"


class DifficultyTransition(models.Model):
    """
    Create difficulty transitions between difficulty levels.

    Each transition holds text that represents the narrative or dialogue
    that appears when the player moves from one difficulty level to another.
    """
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('end', 'End'),
    ]
    # Difficulty level to which this transition corresponds
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, unique=True)

    # The text shown during the transition
    text = models.TextField()

    def __str__(self):
        return f"Transition ({self.difficulty})"

class PlayerStoryProgress(models.Model):
    """
    Tracks the user's progress in unlocking memories for each difficulty level.

    This model stores which memories (easy, medium, hard) the player has unlocked.
    Each difficulty has its own list of unlocked memories.
    """
    player = models.OneToOneField(User, on_delete=models.CASCADE)  # One-to-one relationship with the player (User model)

    unlocked_easy = models.JSONField(default=list) # List of unlocked memories for 'easy' difficulty
    unlocked_medium = models.JSONField(default=list) # List of unlocked memories for 'medium' difficulty
    unlocked_hard = models.JSONField(default=list) # List of unlocked memories for 'hard' difficulty

    def __str__(self):
        return f"{self.player.username} memory progress"

class SequenceFrame(models.Model):
    """
    Model representing frames in an animated sequence.

    Each sequence contains multiple frames, each with an index and an associated image.
    This model stores the sequence name, index of the frame, and the image file associated with it.
    """
    sequence = models.CharField(max_length=50) # Name of the sequence (e.g., 'intro', 'memory'
    index = models.PositiveIntegerField() # Frame index (order of the frame in the sequence)
    image = models.CharField(max_length=100)  # Image filename or path for the frame

    class Meta:
        unique_together = ("sequence", "index") # Ensure unique sequence-index pairs
        ordering = ["sequence", "index"]  # Order frames by sequence name and index

    def __str__(self):
        # Return a readable string representation of the SequenceFrame instance
        # This will display "Frame {index} of {sequence}" when printed
        return f"Frame {self.index} of {self.sequence}"