from django.core.mail import EmailMessage
from django.template.loader import render_to_string

ACTIVATION_SUBJECT = "Activate your account to complete registration"


def send_activation_email(user, activation_link):
    context = {"username": user.username, "activation_link": activation_link}
    message = EmailMessage(
        subject=ACTIVATION_SUBJECT,
        body=render_to_string("emails/user_activation.html", context),
        to=[user.email],
    )
    message.content_subtype = "html"
    message.send()
