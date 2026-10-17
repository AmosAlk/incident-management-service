from rest_framework.permissions import BasePermission

from organisations.models import OrganisationMembership


class IsOrganisationAdministrator(BasePermission):
    # Automatically called by DRF. This permission is then included in a
    # view requiring Admin authorization.
    # Conceptually:
    #
    # permission = IsOrganisationAdministrator()
    # permission.has_permission(request, view)
    #
    # has_permission and not get_object_permission because there is no
    # relationship yet. So, the authorization is on the request itself,
    # not on an existing object.
    def has_permission(self, request, view) -> bool:
        organisation_id = view.kwargs.get("organisation_id")

        return OrganisationMembership.objects.filter(
            organisation_id=organisation_id,
            user=request.user,
            role=OrganisationMembership.Role.ADMINISTRATOR,
        ).exists()
