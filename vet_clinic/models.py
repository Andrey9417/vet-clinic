from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models

class AnimalType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Veterinarian(AbstractUser):
    years_of_experience = models.IntegerField()
    specialization = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.username} ({self.first_name} {self.last_name})"

class Pet(models.Model):
    name = models.CharField(max_length=255)
    birth_date = models.DateField()
    description = models.TextField(blank=True, null=True)
    owner_name = models.CharField(max_length=255)
    owner_phone = models.CharField(max_length=20)
    animal_type = models.ForeignKey(AnimalType, on_delete=models.CASCADE, related_name="pets")
    veterinarians = models.ManyToManyField(get_user_model(), related_name="pets")

    def __str__(self):
        return f"{self.name} ({self.animal_type.name}, {self.get_age()})"

    def get_age(self):
        today = date.today()
        born = self.birth_date

        years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        if years >= 1:
            return f"{years} year{'s' if years != 1 else ''}"

        months = (today.year - born.year) * 12 + today.month - born.month - (today.day < born.day)
        if months >= 1:
            return f"{months} month{'s' if months != 1 else ''}"

        days = (today - born).days
        return f"{days} day{'s' if days != 1 else ''}"
