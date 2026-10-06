from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views import generic

from vet_clinic.forms import (
    PetSearchForm,
    AnimalTypeCreateForm,
    PetCreateForm,
    UserRegisterForm,
)
from vet_clinic.models import Pet, AnimalType
from vet_clinic.services.user_activation_service import activate_user, register_user

Veterinarian = get_user_model()


def index(request):
    context = {
        "animal_types": AnimalType.objects.order_by("name"),
        "vets": Veterinarian.objects.filter(is_active=True).order_by(
            "-years_of_experience"
        )[:3],
    }
    return render(request, "vet_clinic/index.html", context)


class VeterinarianListView(generic.ListView):
    model = Veterinarian
    context_object_name = "vets"
    template_name = "vet_clinic/veterinarian_list.html"
    queryset = Veterinarian.objects.filter(is_active=True, is_superuser=False).order_by(
        "last_name", "first_name"
    )
    paginate_by = 3


class VeterinarianDetailView(LoginRequiredMixin, generic.DetailView):
    model = Veterinarian
    context_object_name = "vet"
    template_name = "vet_clinic/veterinarian_detail.html"
    queryset = Veterinarian.objects.filter(is_active=True).prefetch_related(
        "pets__animal_type"
    )


class PetListView(LoginRequiredMixin, generic.ListView):
    model = Pet
    paginate_by = 13

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = PetSearchForm(self.request.GET)
        return context

    def get_queryset(self):
        queryset = (
            Pet.objects.select_related("animal_type")
            .prefetch_related("veterinarians")
            .order_by("name")
        )
        search_form = PetSearchForm(self.request.GET)
        if search_form.is_valid():
            name = search_form.cleaned_data["name"]
            animal_type = search_form.cleaned_data["animal_type"]
            if name:
                queryset = queryset.filter(name__icontains=name)
            if animal_type:
                queryset = queryset.filter(animal_type_id=animal_type.id)
        return queryset


class MyPetListView(PetListView):
    def get_queryset(self):
        return super().get_queryset().filter(veterinarians__id=self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mine"] = True
        return context


class PetDetailView(LoginRequiredMixin, generic.DetailView):
    model = Pet
    queryset = Pet.objects.select_related("animal_type").prefetch_related(
        "veterinarians"
    )


class PetCreateView(LoginRequiredMixin, SuccessMessageMixin, generic.CreateView):
    form_class = PetCreateForm
    template_name = "vet_clinic/pet_form.html"
    success_message = "Pet created successfully."

    def get_success_url(self):
        return reverse("vet_clinic:pet-detail", args=[self.object.pk])


class PetUpdateView(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = Pet
    form_class = PetCreateForm
    template_name = "vet_clinic/pet_form.html"
    success_message = "Pet created successfully."

    def get_success_url(self):
        return reverse("vet_clinic:pet-detail", args=[self.object.pk])


class PetDeleteView(LoginRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    model = Pet
    success_message = "Pet deleted successfully."
    success_url = reverse_lazy("vet_clinic:pet-list")


class AnimalTypeCreateView(LoginRequiredMixin, SuccessMessageMixin, generic.CreateView):
    form_class = AnimalTypeCreateForm
    success_url = reverse_lazy("vet_clinic:pet-create")
    success_message = "Animal type updated successfully."
    template_name = "vet_clinic/animaltype_form.html"


class ToggleAssignPet(LoginRequiredMixin, generic.View):
    def post(self, request, *args, **kwargs):
        pet = Pet.objects.get(pk=kwargs["pk"])
        vet = request.user

        if vet in pet.veterinarians.all():
            pet.veterinarians.remove(vet)
        else:
            pet.veterinarians.add(vet)
        return redirect("vet_clinic:pet-detail", pk=pet.pk)


class UpdateProfileView(LoginRequiredMixin, generic.UpdateView):
    model = Veterinarian
    fields = [
        "first_name",
        "last_name",
        "email",
        "specialization",
        "years_of_experience",
    ]
    template_name = "vet_clinic/profile_update.html"

    def get_success_url(self):
        return reverse_lazy("vet_clinic:vet-detail", args=[self.request.user.pk])

    def get_object(self, queryset=None):
        return self.request.user


class UserRegisterView(generic.FormView):
    form_class = UserRegisterForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        user = form.save(commit=False)
        register_user(user)
        messages.success(
            self.request,
            "User created successfully",
        )
        return super().form_valid(form)


class ActivateUserView(generic.View):
    def get(self, request: HttpRequest, uidb64: str, token: str):
        if activate_user(uidb64, token):
            messages.success(request, "User successfully activated")
        else:
            messages.error(request, "Wrong or invalid token")
        return redirect("login")
