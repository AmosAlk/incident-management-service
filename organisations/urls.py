from django.urls import path

from organisations.views import (
    OrganisationMembershipDetailView,
    OrganisationMembershipListCreateView,
)

app_name = "organisations"

urlpatterns = [
    path(
        "<uuid:organisation_id>/memberships/",
        OrganisationMembershipListCreateView.as_view(),
        name="membership-list-create",
    ),
    path(
        "<uuid:organisation_id>/memberships/<uuid:pk>/",
        OrganisationMembershipDetailView.as_view(),
        name="membership-detail",
    ),
]
