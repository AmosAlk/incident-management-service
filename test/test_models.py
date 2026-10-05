import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from incidents.models import Incident
from organisations.models import Organisation, OrganisationMembership


# Says test intentionally wants db access. So an isolated test db is created.
@pytest.mark.django_db
def test_new_incident_is_open_by_default() -> None:
    user = get_user_model().objects.create_user(username="alice")
    organisation = Organisation.objects.create(name="Acme Security AB")

    incident = Incident.objects.create(
        organisation=organisation,
        title="Suspicious login",
        description="An unusual login was detected.",
        severity=Incident.Severity.HIGH,
        created_by=user,
    )

    assert incident.status == Incident.Status.OPEN


@pytest.mark.django_db
def test_user_cannot_have_duplicate_membership_in_organisation() -> None:
    user = get_user_model().objects.create_user(username="alice")
    organisation = Organisation.objects.create(name="Acme Security AB")

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=user,
        role=OrganisationMembership.Role.ANALYST,
    )

    with pytest.raises(IntegrityError):
        OrganisationMembership.objects.create(
            organisation=organisation,
            user=user,
            role=OrganisationMembership.Role.VIEWER,
        )
