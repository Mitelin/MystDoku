from django.test import SimpleTestCase
from django.urls import reverse, resolve
from gameplay import views


class GameplayURLTests(SimpleTestCase):
    def test_start_new_game_url(self):
        url = reverse('start_new_game')
        self.assertEqual(resolve(url).func, views.start_new_game)

    def test_game_view_url(self):
        fake_uuid = "123e4567-e89b-12d3-a456-426614174000"
        url = reverse('game_view', args=[fake_uuid])
        self.assertEqual(resolve(url).func, views.game_view)

    def test_game_block_url(self):
        fake_uuid = "123e4567-e89b-12d3-a456-426614174000"
        url = reverse('game_block', args=[fake_uuid, 0])
        self.assertEqual(resolve(url).func, views.game_view)

    def test_place_item_url(self):
        url = reverse('place_item', args=[1])
        self.assertEqual(resolve(url).func, views.place_item)

    def test_story_so_far_url(self):
        url = reverse('story_so_far')
        self.assertEqual(resolve(url).func, views.story_so_far)

    def test_auto_fill_url(self):
        fake_uuid = "123e4567-e89b-12d3-a456-426614174000"
        url = reverse('auto_fill', args=[fake_uuid])
        self.assertEqual(resolve(url).func, views.auto_fill)

    def test_reset_progress_url(self):
        url = reverse('reset_progress')
        self.assertEqual(resolve(url).func, views.reset_progress)

    def test_debug_add_memory_url(self):
        url = reverse('debug_add_memory', args=['easy'])
        self.assertEqual(resolve(url).func, views.debug_add_memory)

    def test_game_selection_url(self):
        url = reverse('game_selection')
        self.assertEqual(resolve(url).func, views.game_selection)

    def test_manual_view_url(self):
        url = reverse('manual')
        self.assertEqual(resolve(url).func, views.manual_view)