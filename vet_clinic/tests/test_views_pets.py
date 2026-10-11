from datetime import date, timedelta

from django.urls import reverse

from vet_clinic.models import AnimalType, Pet
from vet_clinic.tests.test_base import RequireLoginTest, make_vet, make_pet, pet_create_update_form_data, messages_of


class PetListViewTests(RequireLoginTest):
    url = reverse("vet_clinic:pet-list")

    def setUp(self):
        self.user = make_vet("user")
        self.cat = AnimalType.objects.create(name="Cat")
        self.dog = AnimalType.objects.create(name="Dog")
        self.client.force_login(self.user)

    def names(self, response):
        return [p.name for p in response.context["object_list"]]

    def test_requires_login(self):
        self.client.logout()
        self.assertRequiresLogin(self.url)

    def test_search_form_in_context(self):
        response = self.client.get(self.url)
        self.assertIn("search_form", response.context)

    def test_ordered_by_name(self):
        make_pet(self.cat, "Zed")
        make_pet(self.cat, "Alf")
        response = self.client.get(self.url)
        self.assertEqual(self.names(response), ["Alf", "Zed"])

    def test_filter_by_name_case_insensitive_partial(self):
        make_pet(self.cat, "Rex")
        make_pet(self.cat, "Rexie")
        make_pet(self.cat, "Bella")
        response = self.client.get(self.url, {"name": "REX"})
        self.assertEqual(self.names(response), ["Rex", "Rexie"])

    def test_filter_by_animal_type(self):
        make_pet(self.cat, "Tom")
        make_pet(self.dog, "Rex")
        response = self.client.get(self.url, {"animal_type": self.dog.pk})
        self.assertEqual(self.names(response), ["Rex"])

    def test_filter_by_name_and_type_combined(self):
        make_pet(self.cat, "Rex")
        make_pet(self.dog, "Rex")
        make_pet(self.dog, "Bella")
        response = self.client.get(
            self.url, {"name": "rex", "animal_type": self.dog.pk}
        )
        self.assertEqual(len(response.context["object_list"]), 1)
        self.assertEqual(
            response.context["object_list"][0].animal_type, self.dog
        )

    def test_invalid_animal_type_ignores_filter(self):
        make_pet(self.cat, "Tom")
        response = self.client.get(self.url, {"animal_type": 9999})
        self.assertEqual(self.names(response), ["Tom"])

    def test_pagination_thirteen_per_page(self):
        for i in range(11):
            make_pet(self.cat, f"Pet{i:02d}")
        page1 = self.client.get(self.url)
        page2 = self.client.get(self.url, {"page": 2})
        self.assertEqual(len(page1.context["object_list"]), 10)
        self.assertEqual(len(page2.context["object_list"]), 1)


class MyPetListViewTests(RequireLoginTest):
    url = reverse("vet_clinic:my-patients")

    def setUp(self):
        self.user = make_vet("user")
        self.other = make_vet("other")
        self.cat = AnimalType.objects.create(name="Cat")
        self.mine = make_pet(self.cat, "Mine")
        self.mine.veterinarians.add(self.user)
        self.theirs = make_pet(self.cat, "Theirs")
        self.theirs.veterinarians.add(self.other)
        self.unassigned = make_pet(self.cat, "Nobody")

    def test_requires_login(self):
        self.assertRequiresLogin(self.url)

    def test_shows_only_current_vets_pets(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(list(response.context["object_list"]), [self.mine])

    def test_sets_mine_flag(self):
        self.client.force_login(self.user)
        self.assertTrue(self.client.get(self.url).context["mine"])

    def test_regular_pet_list_has_no_mine_flag(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("vet_clinic:pet-list"))
        self.assertFalse(response.context.get("mine"))

    def test_search_still_applies(self):
        other_mine = make_pet(self.cat, "Other mine")
        other_mine.veterinarians.add(self.user)
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"name": "other"})
        self.assertEqual(list(response.context["object_list"]), [other_mine])


class PetDetailViewTests(RequireLoginTest):
    def setUp(self):
        self.user = make_vet("user")
        self.pet = make_pet(AnimalType.objects.create(name="Cat"))
        self.url = reverse("vet_clinic:pet-detail", args=[self.pet.pk])

    def test_requires_login(self):
        self.assertRequiresLogin(self.url)

    def test_returns_pet(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["pet"], self.pet)

    def test_missing_pet_returns_404(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("vet_clinic:pet-detail", args=[9999]))
        self.assertEqual(response.status_code, 404)


class PetCreateViewTests(RequireLoginTest):
    url = reverse("vet_clinic:pet-create")

    def setUp(self):
        self.user = make_vet("user")
        self.cat = AnimalType.objects.create(name="Cat")

    def test_requires_login_for_get_and_post(self):
        self.assertRequiresLogin(self.url)
        self.assertRequiresLogin(self.url, method="post")

    def test_get_renders_form(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_post_creates_pet_and_redirects(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url, pet_create_update_form_data(self.cat, veterinarians=[self.user.pk])
        )
        pet = Pet.objects.get(name="Buddy")
        self.assertRedirects(
            response,
            reverse("vet_clinic:pet-detail", args=[pet.pk]),
            fetch_redirect_response=False,
        )
        self.assertIn(self.user, pet.veterinarians.all())
        self.assertIn("Pet created successfully.", messages_of(response))

    def test_future_birth_date_is_rejected(self):
        self.client.force_login(self.user)
        future = (date.today() + timedelta(days=1)).isoformat()
        response = self.client.post(
            self.url, pet_create_update_form_data(self.cat, birth_date=future)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("birth_date", response.context["form"].errors)
        self.assertEqual(Pet.objects.count(), 0)

    def test_today_birth_date_is_accepted(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url, pet_create_update_form_data(self.cat, birth_date=date.today().isoformat())
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Pet.objects.count(), 1)

    def test_missing_required_fields_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Pet.objects.count(), 0)


class PetUpdateViewTests(RequireLoginTest):
    def setUp(self):
        self.user = make_vet("user")
        self.cat = AnimalType.objects.create(name="Cat")
        self.pet = make_pet(self.cat, "Old name")
        self.url = reverse("vet_clinic:pet-update", args=[self.pet.pk])

    def test_requires_login(self):
        self.assertRequiresLogin(self.url)
        self.assertRequiresLogin(self.url, method="post")

    def test_get_renders_form_with_instance(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].instance, self.pet)

    def test_valid_post_updates_and_redirects(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url, pet_create_update_form_data(self.cat, name="New name")
        )
        self.assertRedirects(
            response,
            reverse("vet_clinic:pet-detail", args=[self.pet.pk]),
            fetch_redirect_response=False,
        )
        self.pet.refresh_from_db()
        self.assertEqual(self.pet.name, "New name")

    def test_success_message_says_updated(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, pet_create_update_form_data(self.cat))
        self.assertIn("Pet updated successfully.", messages_of(response))

    def test_future_birth_date_rejected(self):
        self.client.force_login(self.user)
        future = (date.today() + timedelta(days=5)).isoformat()
        response = self.client.post(
            self.url, pet_create_update_form_data(self.cat, birth_date=future)
        )
        self.assertEqual(response.status_code, 200)
        self.pet.refresh_from_db()
        self.assertEqual(self.pet.name, "Old name")

    def test_missing_pet_returns_404(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("vet_clinic:pet-update", args=[9999]))
        self.assertEqual(response.status_code, 404)


class PetDeleteViewTests(RequireLoginTest):
    def setUp(self):
        self.user = make_vet("user")
        self.pet = make_pet(AnimalType.objects.create(name="Cat"))
        self.url = reverse("vet_clinic:pet-delete", args=[self.pet.pk])

    def test_requires_login(self):
        self.assertRequiresLogin(self.url)
        self.assertRequiresLogin(self.url, method="post")
        self.assertTrue(Pet.objects.filter(pk=self.pet.pk).exists())

    def test_get_shows_confirmation(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertTrue(Pet.objects.filter(pk=self.pet.pk).exists())

    def test_post_deletes_and_redirects(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertRedirects(
            response, reverse("vet_clinic:pet-list"), fetch_redirect_response=False
        )
        self.assertFalse(Pet.objects.filter(pk=self.pet.pk).exists())
        self.assertIn("Pet deleted successfully.", messages_of(response))
