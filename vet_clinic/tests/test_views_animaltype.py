from django.urls import reverse

from vet_clinic.models import AnimalType
from vet_clinic.tests.test_base import RequireLoginTest, make_vet, messages_of


class AnimalTypeCreateViewTests(RequireLoginTest):
    url = reverse("vet_clinic:animal-type-create")

    def setUp(self):
        self.user = make_vet("user")

    def test_requires_login(self):
        self.assertRequiresLogin(self.url)
        self.assertRequiresLogin(self.url, method="post")

    def test_get_renders_form(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_post_creates_capitalized_type_and_redirects(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"name": "  hamster "})
        self.assertRedirects(
            response,
            reverse("vet_clinic:pet-create"),
            fetch_redirect_response=False,
        )
        self.assertTrue(AnimalType.objects.filter(name="Hamster").exists())
        self.assertIn("Animal type updated successfully.", messages_of(response))

    def test_exact_duplicate_rejected(self):
        AnimalType.objects.create(name="Dog")
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"name": "Dog"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.context["form"].errors)
        self.assertEqual(AnimalType.objects.count(), 1)

    def test_case_insensitive_duplicate_rejected(self):
        AnimalType.objects.create(name="Dog")
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"name": "dOG"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AnimalType.objects.count(), 1)

    def test_name_that_is_substring_of_existing_is_allowed(self):
        AnimalType.objects.create(name="Catfish")
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"name": "Cat"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AnimalType.objects.filter(name="Cat").exists())
