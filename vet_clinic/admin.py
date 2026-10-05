from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin

from vet_clinic.models import Veterinarian, AnimalType, Pet


@admin.register(Veterinarian)
class VeterinarianAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("specialization", "years_of_experience")
    fieldsets = UserAdmin.fieldsets + (
        (("Additional info", {"fields": ("specialization", "years_of_experience")}),)
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            (
                "Additional info",
                {
                    "fields": (
                        "first_name",
                        "last_name",
                        "specialization",
                        "years_of_experience"
                    )
                },
            ),
        )
    )


@admin.register(AnimalType)
class AnimalTypeAdmin(ModelAdmin):
    pass


@admin.register(Pet)
class PetAdmin(ModelAdmin):
    pass
