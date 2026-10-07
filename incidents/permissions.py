from rest_framework.permissions import SAFE_METHODS, BasePermission

from organisations.models import OrganisationMembership


class CanModifyIncident(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True

        return OrganisationMembership.objects.filter(
            organisation=obj.organisation,
            user=request.user,
            # Django ORM lookup syntax
            # Keep rows where role is one of the listed.
            role__in=[
                OrganisationMembership.Role.ADMINISTRATOR,
                OrganisationMembership.Role.ANALYST,
            ],
        ).exists()
