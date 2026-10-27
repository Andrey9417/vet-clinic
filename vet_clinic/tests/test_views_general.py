from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from vet_clinic.models import AnimalType
from vet_clinic.tests.test_base import make_vet, PASSWORD, Veterinarian, messages_of


class IndexViewTests(TestCase):
    def test_accessible_without_login(self):
        response = self.client.get(reverse("vet_clinic:index"))
        self.assertEqual(response.status_code, 200)

    def test_animal_types_ordered_by_name(self):
        for name in ["Rabbit", "Cat", "Dog"]:
            AnimalType.objects.create(name=name)
        response = self.client.get(reverse("vet_clinic:index"))
        names = [t.name for t in response.context["animal_types"]]
        self.assertEqual(names, ["Cat", "Dog", "Rabbit"])

    def test_vets_top_three_active_by_experience(self):
        make_vet("v1", years_of_experience=1)
        v2 = make_vet("v2", years_of_experience=20)
        v3 = make_vet("v3", years_of_experience=10)
        v4 = make_vet("v4", years_of_experience=15)
        make_vet("inactive", years_of_experience=50, is_active=False)

        response = self.client.get(reverse("vet_clinic:index"))
        self.assertEqual(list(response.context["vets"]), [v2, v4, v3])


class UserRegisterViewTests(TestCase):
    url = reverse("vet_clinic:register")

    def register_data(self, **overrides):
        data = {
            "username": "newvet",
            "email": "newvet@example.com",
            "first_name": "New",
            "last_name": "Vet",
            "specialization": "Dentistry",
            "years_of_experience": 3,
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        data.update(overrides)
        return data

    def test_accessible_without_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    @patch("vet_clinic.views.register_user")
    def test_valid_post_calls_service_and_redirects(self, mock_register):
        response = self.client.post(self.url, self.register_data())
        self.assertRedirects(
            response, reverse("login"), fetch_redirect_response=False
        )
        mock_register.assert_called_once()
        user = mock_register.call_args.args[0]
        self.assertIsInstance(user, Veterinarian)
        self.assertEqual(user.username, "newvet")
        self.assertEqual(user.email, "newvet@example.com")
        self.assertIn("User created successfully", messages_of(response))

    @patch("vet_clinic.views.register_user")
    def test_password_mismatch_does_not_register(self, mock_register):
        response = self.client.post(
            self.url, self.register_data(password2="different")
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        mock_register.assert_not_called()

    @patch("vet_clinic.views.register_user")
    def test_duplicate_email_case_insensitive_rejected(self, mock_register):
        make_vet("existing", email="taken@example.com")
        response = self.client.post(
            self.url, self.register_data(email="TAKEN@Example.com")
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        mock_register.assert_not_called()

    @patch("vet_clinic.views.register_user")
    def test_email_that_is_substring_of_existing_is_allowed(self, mock_register):
        make_vet("existing", email="john@example.com")
        response = self.client.post(
            self.url, self.register_data(email="hn@example.com")
        )
        self.assertEqual(response.status_code, 302)
        mock_register.assert_called_once()


class ActivateUserViewTests(TestCase):
    def url(self, uidb64="abc", token="tok-123"):
        return reverse("vet_clinic:activate", args=[uidb64, token])

    @patch("vet_clinic.views.activate_user", return_value=True)
    def test_success(self, mock_activate):
        response = self.client.get(self.url("uid", "token"))
        self.assertRedirects(
            response, reverse("login"), fetch_redirect_response=False
        )
        mock_activate.assert_called_once_with("uid", "token")
        self.assertIn("User successfully activated", messages_of(response))

    @patch("vet_clinic.views.activate_user", return_value=False)
    def test_failure(self, mock_activate):
        response = self.client.get(self.url())
        self.assertRedirects(
            response, reverse("login"), fetch_redirect_response=False
        )
        self.assertIn("Wrong or invalid token", messages_of(response))
