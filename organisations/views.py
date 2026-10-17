from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from organisations.models import Organisation, OrganisationMembership
from organisations.permissions import IsOrganisationAdministrator
from organisations.serializers import (
    OrganisationMembershipCreateSerializer,
    OrganisationMembershipSerializer,
    OrganisationMembershipUpdateSerializer,
)


class OrganisationMembershipListCreateView(generics.ListCreateAPIView):
    permission_classes = [
        IsAuthenticated,
        IsOrganisationAdministrator,
    ]

    def get_organisation(self) -> Organisation:
        return get_object_or_404(
            Organisation,
            # As before, organisation_id is extracted from the path.
            pk=self.kwargs["organisation_id"],
        )

    def get_queryset(self):
        return OrganisationMembership.objects.filter(
            organisation_id=self.kwargs["organisation_id"],
        ).select_related(
            "organisation",
            "user",
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrganisationMembershipCreateSerializer

        return OrganisationMembershipSerializer

    def get_serializer_context(self):
        # dict() just to make pylance happy...
        # Organisation context is added here so that we can
        # check if a user already belongs to that organisation
        # in the serializer.
        context = dict(super().get_serializer_context())
        context["organisation"] = self.get_organisation()
        return context

    def perform_create(self, serializer):
        serializer.save(organisation=self.get_organisation())


class OrganisationMembershipDetailView(generics.RetrieveUpdateDestroyAPIView):
    # From docs: Used for read-write-delete endpoints to
    # represent a single model instance.
    serializer_class = OrganisationMembershipUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOrganisationAdministrator,
    ]
    http_method_names = [
        "get",
        "patch",
        "delete",
        "head",
        "options",
    ]

    def get_queryset(self):
        return OrganisationMembership.objects.filter(
            organisation_id=self.kwargs["organisation_id"],
        ).select_related(
            "organisation",
            "user",
        )

    def perform_destroy(self, instance):
        if instance.role == OrganisationMembership.Role.ADMINISTRATOR:
            administrator_count = OrganisationMembership.objects.filter(
                organisation=instance.organisation,
                role=(OrganisationMembership.Role.ADMINISTRATOR),
            ).count()

            if administrator_count <= 1:
                raise ValidationError(
                    "An organisation must have at least one administrator."
                )

        instance.delete()
