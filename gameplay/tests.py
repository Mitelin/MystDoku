from django.test import TestCase
from django.contrib.auth.models import User
from gameplay.models import Game, Grid, Cell, Item
from gameplay.utils import generate_sudoku, assign_items_to_board, create_game_for_player


class SudokuGenerationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Create testing data - 9 game items
        Using class method so we get same data for all test cases
        """

        items = [
            {"name": "Vidlička", "number": 1},
            {"name": "Nůž", "number": 2},
            {"name": "Talíř", "number": 3},
            {"name": "Hrnek", "number": 4},
            {"name": "Lžíce", "number": 5},
            {"name": "Toustovač", "number": 6},
            {"name": "Mikrovlnka", "number": 7},
            {"name": "Kuchyňský robot", "number": 8},
            {"name": "Pánev", "number": 9}
        ]
        for item in items:
            Item.objects.create(**item)

    def test_generate_valid_sudoku(self):
        """
        Checks if generated sudoku matrix is valid by sudoku rules
        """

        board = generate_sudoku()

        # check that every number we use in row is unique 1-9 no duplicates
        for row in board:
            self.assertEqual(len(set(row)), 9)

        # check that every number we use in column is unique 1-9 no duplicates
        for col in zip(*board):  # Transposition
            self.assertEqual(len(set(col)), 9)

    def test_assign_items_to_board(self):
        """
        Function to check if we can assign items to board correctly
        and every cell have item object assigned
        """
        board = generate_sudoku()
        item_board = assign_items_to_board(board)

        # Check is every cell have item object assigned
        for row in item_board:
            for item in row:
                self.assertIsInstance(item, Item)

    def test_create_game_for_player(self):
        """
        Will check if the game is generated and correctly saved to database
        """
        user = User.objects.create(username="testplayer")
        game = create_game_for_player(user)

        self.assertEqual(Game.objects.count(), 1)
        self.assertEqual(Grid.objects.filter(game=game).count(), 9)
        self.assertEqual(Cell.objects.filter(grid__game=game).count(), 81)
