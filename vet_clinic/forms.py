from django import forms
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


from vet_clinic.models import AnimalType, Pet

User = get_user_model()


class PetSearchForm(forms.Form):
    name = forms.CharField(
        max_length=50,
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Search by name..."}
        ),
    )
    animal_type = forms.ModelChoiceField(
        queryset=AnimalType.objects.all(),
        required=False,
        empty_label="All types",
        label="",
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class AnimalTypeCreateForm(forms.ModelForm):
    class Meta:
        model = AnimalType
        fields = ["name"]

    def clean_name(self):
        name = self.cleaned_data["name"].strip().capitalize()
        if AnimalType.objects.filter(name__icontains=name).exists():
            raise forms.ValidationError("This animal type already exists.")
        return name


class PetCreateForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = [
            "animal_type",
            "name",
            "birth_date",
            "owner_name",
            "owner_phone",
            "description",
            "veterinarians",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "description": forms.Textarea(attrs={"rows": 3}),
            "veterinarians": forms.CheckboxSelectMultiple,
        }

    def clean_birth_date(self):
        birth_date = self.cleaned_data["birth_date"]
        if birth_date > date.today():
            raise forms.ValidationError("Birth date cannot be in the future.")
        return birth_date


class UserRegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + (
            "email",
            "first_name",
            "last_name",
            "specialization",
            "years_of_experience",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__icontains=email).exists():
            raise forms.ValidationError("This email already exists.")
        return email
