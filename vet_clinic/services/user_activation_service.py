from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from vet_clinic.services.email_service import send_activation_email

User = get_user_model()


def _get_uidb64(user):
    return urlsafe_base64_encode(force_bytes(user.pk))


def _get_token(user):
    return default_token_generator.make_token(user)


def _get_activation_link(user):
    uid = _get_uidb64(user)
    token = _get_token(user)
    path = reverse("vet_clinic:activate", kwargs={"uidb64": uid, "token": token})
    return f"{settings.SITE_URL.rstrip('/')}{path}"


def register_user(user) -> User:
    with transaction.atomic():
        user.is_active = False
        user.save()
        activation_link = _get_activation_link(user)
        send_activation_email(user, activation_link)
    return user


def activate_user(uidb64, token) -> bool:
    try:
        pk = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=pk)
    except TypeError, ValueError, OverflowError, User.DoesNotExist:
        user = None

    if user and default_token_generator.check_token(user, token):
        User.objects.filter(pk=user.pk).update(is_active=True)
        return True
    return False
