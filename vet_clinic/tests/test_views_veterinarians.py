from django.test import TestCase
from django.urls import reverse

from vet_clinic.models import AnimalType
from vet_clinic.tests.test_base import make_vet, Veterinarian, PASSWORD, RequireLoginTest, make_pet


class VeterinarianListViewTests(TestCase):
    url = reverse("vet_clinic:vet-list")

    def test_accessible_without_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_excludes_inactive_and_superusers(self):
        active = make_vet("active")
        make_vet("inactive", is_active=False)
        Veterinarian.objects.create_superuser(
            "admin", "admin@example.com", PASSWORD
        )
        response = self.client.get(self.url)
        self.assertEqual(list(response.context["vets"]), [active])

    def test_ordered_by_last_then_first_name(self):
        b = make_vet("b", last_name="Zed", first_name="Anna")
        c = make_vet("c", last_name="Adams", first_name="Zoe")
        a = make_vet("a", last_name="Adams", first_name="Bob")
        response = self.client.get(self.url)
        self.assertEqual(list(response.context["vets"]), [a, c, b])

    def test_pagination_three_per_page(self):
        for i in range(4):
            make_vet(f"vet{i}", last_name=f"L{i}")
        page1 = self.client.get(self.url)
        page2 = self.client.get(self.url, {"page": 2})
        self.assertTrue(page1.context["is_paginated"])
        self.assertEqual(len(page1.context["vets"]), 3)
        self.assertEqual(len(page2.context["vets"]), 1)


class VeterinarianDetailViewTests(RequireLoginTest):
    def setUp(self):
        self.user = make_vet("user")
        self.vet = make_vet("target")

    def test_requires_login(self):
        self.assertRequiresLogin(
            reverse("vet_clinic:vet-detail", args=[self.vet.pk])
        )

    def test_active_vet_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("vet_clinic:vet-detail", args=[self.vet.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["vet"], self.vet)

    def test_inactive_vet_returns_404(self):
        inactive = make_vet("gone", is_active=False)
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("vet_clinic:vet-detail", args=[inactive.pk])
        )
        self.assertEqual(response.status_code, 404)


class ToggleAssignPetTests(RequireLoginTest):
    def setUp(self):
        self.user = make_vet("user")
        self.pet = make_pet(AnimalType.objects.create(name="Cat"))
        self.url = reverse("vet_clinic:toggle-assign-pet", args=[self.pet.pk])

    def test_requires_login(self):
        self.assertRequiresLogin(self.url, method="post")
        self.assertEqual(self.pet.veterinarians.count(), 0)

    def test_get_not_allowed(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_assigns_when_not_assigned(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertRedirects(
            response,
            reverse("vet_clinic:pet-detail", args=[self.pet.pk]),
            fetch_redirect_response=False,
        )
        self.assertIn(self.user, self.pet.veterinarians.all())

    def test_unassigns_when_already_assigned(self):
        self.pet.veterinarians.add(self.user)
        self.client.force_login(self.user)
        self.client.post(self.url)
        self.assertNotIn(self.user, self.pet.veterinarians.all())

    def test_toggle_does_not_affect_other_vets(self):
        other = make_vet("other")
        self.pet.veterinarians.add(other)
        self.client.force_login(self.user)
        self.client.post(self.url)
        self.assertCountEqual(self.pet.veterinarians.all(), [other, self.user])

    def test_missing_pet_returns_404(self):
        self.client.raise_request_exception = False
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("vet_clinic:toggle-assign-pet", args=[9999])
        )
        self.assertEqual(response.status_code, 404)


class UpdateProfileViewTests(RequireLoginTest):
    url = reverse("vet_clinic:update-profile")

    def setUp(self):
        self.user = make_vet("user", first_name="Old", last_name="Name")
        self.other = make_vet("other", first_name="Other")

    def profile_data(self, **overrides):
        data = {
            "first_name": "New",
            "last_name": "Surname",
            "email": "new@example.com",
            "specialization": "Surgery",
            "years_of_experience": 7,
        }
        data.update(overrides)
        return data

    def test_requires_login(self):
        self.assertRequiresLogin(self.url)
        self.assertRequiresLogin(self.url, method="post")

    def test_get_uses_current_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["object"], self.user)

    def test_post_updates_current_user_and_redirects(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, self.profile_data())
        self.assertRedirects(
            response,
            reverse("vet_clinic:vet-detail", args=[self.user.pk]),
            fetch_redirect_response=False,
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "New")
        self.assertEqual(self.user.specialization, "Surgery")
        self.assertEqual(self.user.years_of_experience, 7)

    def test_other_users_are_not_modified(self):
        self.client.force_login(self.user)
        self.client.post(self.url, self.profile_data())
        self.other.refresh_from_db()
        self.assertEqual(self.other.first_name, "Other")

    def test_duplicate_email_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url, self.profile_data(email=self.other.email)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
