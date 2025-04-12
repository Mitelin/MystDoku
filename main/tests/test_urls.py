from django.test import SimpleTestCase
from django.urls import reverse, resolve
from main.views import home_landing, play_redirect, fallback_redirect

class MainURLTests(SimpleTestCase):
    # Test that the main page URL correctly resolves to the home_landing view
    def test_main_page_url_resolves(self):
        url = reverse('main_page')
        self.assertEqual(resolve(url).func, home_landing)

    # Test that the "play" URL correctly resolves to the play_redirect view
    def test_play_redirect_url_resolves(self):
        url = reverse('play_redirect')
        self.assertEqual(resolve(url).func, play_redirect)

    # Test that a non-existent URL triggers the fallback view (usually for 404 behavior)
    def test_fallback_redirect_url_resolves(self):
        match = resolve('/neexistujici/')
        self.assertEqual(match.func, fallback_redirect)
