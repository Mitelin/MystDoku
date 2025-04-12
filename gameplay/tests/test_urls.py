from django.test import SimpleTestCase
from django.urls import reverse, resolve
from gameplay import views


class GameplayURLTests(SimpleTestCase):
    # Test that the 'start_new_game' URL correctly maps to the start_new_game view
    def test_start_new_game_url(self):
        url = reverse('start_new_game')
        self.assertEqual(resolve(url).func, views.start_new_game)

    # Test that the 'game_view' URL with a UUID maps to the game_view view
    def test_game_view_url(self):
        fake_uuid = "123e4567-e89b-12d3-a456-426614174000"
        url = reverse('game_view', args=[fake_uuid])
        self.assertEqual(resolve(url).func, views.game_view)

    # Test that the 'game_block' URL with a UUID and block index also maps to game_view view
    def test_game_block_url(self):
        fake_uuid = "123e4567-e89b-12d3-a456-426614174000"
        url = reverse('game_block', args=[fake_uuid, 0])
        self.assertEqual(resolve(url).func, views.game_view)

    # Test that the 'place_item' URL with an item ID maps to the place_item view
    def test_place_item_url(self):
        url = reverse('place_item', args=[1])
        self.assertEqual(resolve(url).func, views.place_item)

    # Test that the 'story_so_far' URL maps to the story_so_far view
    def test_story_so_far_url(self):
        url = reverse('story_so_far')
        self.assertEqual(resolve(url).func, views.story_so_far)

    # Test that the 'auto_fill' URL with a UUID maps to the auto_fill view
    def test_auto_fill_url(self):
        fake_uuid = "123e4567-e89b-12d3-a456-426614174000"
        url = reverse('auto_fill', args=[fake_uuid])
        self.assertEqual(resolve(url).func, views.auto_fill)

    # Test that the 'reset_progress' URL maps to the reset_progress view
    def test_reset_progress_url(self):
        url = reverse('reset_progress')
        self.assertEqual(resolve(url).func, views.reset_progress)

    # Test that the 'debug_add_memory' URL with a difficulty level maps to the debug_add_memory view
    def test_debug_add_memory_url(self):
        url = reverse('debug_add_memory', args=['easy'])
        self.assertEqual(resolve(url).func, views.debug_add_memory)

    # Test that the 'game_selection' URL maps to the game_selection view
    def test_game_selection_url(self):
        url = reverse('game_selection')
        self.assertEqual(resolve(url).func, views.game_selection)

    # Test that the 'manual' URL maps to the manual_view view
    def test_manual_view_url(self):
        url = reverse('manual')
        self.assertEqual(resolve(url).func, views.manual_view)
