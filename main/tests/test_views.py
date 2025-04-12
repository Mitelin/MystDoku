from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class MainViewsTests(TestCase):

    # Test that the home landing page renders successfully and uses the correct template
    def test_home_landing_renders_correct_template(self):
        response = self.client.get(reverse("main_page"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main/home_landing.html")

    # Test that an authenticated user visiting /play/ is redirected to the game selection page
    def test_play_redirect_authenticated_user(self):
        user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("play_redirect"))
        self.assertRedirects(response, reverse("game_selection"))

    # Test that an unauthenticated user visiting /play/ is redirected to the login page
    def test_play_redirect_unauthenticated_user(self):
        response = self.client.get(reverse("play_redirect"))
        self.assertRedirects(response, reverse("login"))

    # Test that a GET request to the registration page returns the form and correct template
    def test_register_get_request(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/register.html")

    # Test that a POST request with valid registration data creates a user and redirects to the game
    def test_register_post_valid_data_creates_user_and_redirects(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser",
            "password1": "TestPassword123",
            "password2": "TestPassword123"
        })
        self.assertRedirects(response, reverse("game_selection"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    # Test that accessing an unknown URL triggers the fallback and redirects to the main page
    def test_fallback_redirect_redirects_to_main_page(self):
        response = self.client.get("/some/unknown/url/")
        self.assertRedirects(response, reverse("main_page"))
