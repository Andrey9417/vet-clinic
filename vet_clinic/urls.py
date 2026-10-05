from django.urls import path

from vet_clinic.views import index, VeterinarianListView, VeterinarianDetailView, PetDetailView, PetListView, \
    ToggleAssignPet, MyPetListView, UpdateProfileView, PetCreateView, AnimalTypeCreateView, PetUpdateView, PetDeleteView

urlpatterns = [
    path("", index, name="index"),
    path("veterinarians/", VeterinarianListView.as_view(), name="vet-list"),
    path("veterinarians/<int:pk>/", VeterinarianDetailView.as_view(), name="vet-detail"),
    path("pets/", PetListView.as_view(), name="pet-list"),
    path("pets/mine/", MyPetListView.as_view(), name="my-patients"),
    path("pets/create/", PetCreateView.as_view(), name="pet-create"),
    path("pets/<int:pk>/", PetDetailView.as_view(), name="pet-detail"),
    path("pets/<int:pk>/update/", PetUpdateView.as_view(), name="pet-update"),
    path("pets/<int:pk>/delete/", PetDeleteView.as_view(), name="pet-delete"),
    path("pets/<int:pk>/toggle-assign/", ToggleAssignPet.as_view(), name="toggle-assign-pet"),
    path("profile/edit", UpdateProfileView.as_view(), name="update-profile"),
    path("animal-types/create/", AnimalTypeCreateView.as_view(), name="animal-type-create"),
]


app_name = "vet_clinic"