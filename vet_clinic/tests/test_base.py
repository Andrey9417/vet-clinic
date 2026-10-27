from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from vet_clinic.models import Pet

Veterinarian = get_user_model()

PASSWORD = "StrongPass123!x"


def make_vet(username="vet", **extra):
    extra.setdefault("email", f"{username}@example.com")
    password = extra.pop("password", PASSWORD)
    return Veterinarian.objects.create_user(
        username=username, password=password, **extra
    )


def make_pet(animal_type, name="Rex", **extra):
    extra.setdefault("birth_date", date(2020, 1, 1))
    extra.setdefault("owner_name", "Owner")
    extra.setdefault("owner_phone", "+10000000000")
    return Pet.objects.create(name=name, animal_type=animal_type, **extra)


def pet_create_update_form_data(animal_type, **overrides):
    data = {
        "animal_type": animal_type.pk,
        "name": "Buddy",
        "birth_date": "2021-05-01",
        "owner_name": "John Doe",
        "owner_phone": "+380501234567",
        "description": "Friendly",
    }
    data.update(overrides)
    return data


def messages_of(response):
    return [str(m) for m in get_messages(response.wsgi_request)]


class RequireLoginTest(TestCase):
    def assertRequiresLogin(self, url, method="get"):
        response = getattr(self.client, method)(url)
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={url}",
            fetch_redirect_response=False,
        )
