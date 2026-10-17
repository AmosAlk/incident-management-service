import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from organisations.models import Organisation, OrganisationMembership


@pytest.mark.django_db
def test_administrator_can_add_member() -> None:
    administrator = User.objects.create_user(
        username="alice",
    )
    new_user = User.objects.create_user(
        username="bob",
    )

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=administrator,
        role=OrganisationMembership.Role.ADMINISTRATOR,
    )

    client = APIClient()
    client.force_authenticate(user=administrator)

    response = client.post(
        reverse(
            "organisations:membership-list-create",
            kwargs={"organisation_id": organisation.id},
        ),
        {
            "user": new_user.id,  # type: ignore[attr-defined]
            "role": OrganisationMembership.Role.ANALYST,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    membership = OrganisationMembership.objects.get(user=new_user)

    assert membership.organisation == organisation
    assert membership.role == OrganisationMembership.Role.ANALYST


@pytest.mark.django_db
def test_analyst_cannot_add_member() -> None:
    analyst = User.objects.create_user(
        username="alice",
    )
    new_user = User.objects.create_user(
        username="bob",
    )

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=analyst,
        role=OrganisationMembership.Role.ANALYST,
    )

    client = APIClient()
    client.force_authenticate(user=analyst)

    response = client.post(
        reverse(
            "organisations:membership-list-create",
            kwargs={"organisation_id": organisation.id},
        ),
        {
            "user": new_user.id,  # type: ignore[attr-defined]
            "role": OrganisationMembership.Role.VIEWER,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN

    assert not OrganisationMembership.objects.filter(user=new_user).exists()


@pytest.mark.django_db
def test_administrator_can_change_member_role() -> None:
    administrator = User.objects.create_user(
        username="alice",
    )
    user = User.objects.create_user(
        username="bob",
    )

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=administrator,
        role=OrganisationMembership.Role.ADMINISTRATOR,
    )

    membership = OrganisationMembership.objects.create(
        organisation=organisation,
        user=user,
        role=OrganisationMembership.Role.VIEWER,
    )

    client = APIClient()
    client.force_authenticate(user=administrator)

    response = client.patch(
        reverse(
            "organisations:membership-detail",
            kwargs={
                "organisation_id": organisation.id,
                "pk": membership.id,
            },
        ),
        {
            "role": OrganisationMembership.Role.ANALYST,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    membership.refresh_from_db()

    assert membership.role == OrganisationMembership.Role.ANALYST


@pytest.mark.django_db
def test_duplicate_membership_is_rejected() -> None:
    administrator = User.objects.create_user(
        username="alice",
    )
    user = User.objects.create_user(
        username="bob",
    )

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=administrator,
        role=OrganisationMembership.Role.ADMINISTRATOR,
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=user,
        role=OrganisationMembership.Role.VIEWER,
    )

    client = APIClient()
    client.force_authenticate(user=administrator)

    response = client.post(
        reverse(
            "organisations:membership-list-create",
            kwargs={"organisation_id": organisation.id},
        ),
        {
            "user": user.id,  # type: ignore[attr-defined]
            "role": OrganisationMembership.Role.ANALYST,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert (
        OrganisationMembership.objects.filter(
            organisation=organisation,
            user=user,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_last_administrator_cannot_be_demoted() -> None:
    administrator = User.objects.create_user(
        username="alice",
    )

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    membership = OrganisationMembership.objects.create(
        organisation=organisation,
        user=administrator,
        role=OrganisationMembership.Role.ADMINISTRATOR,
    )

    client = APIClient()
    client.force_authenticate(user=administrator)

    response = client.patch(
        reverse(
            "organisations:membership-detail",
            kwargs={
                "organisation_id": organisation.id,
                "pk": membership.id,
            },
        ),
        {
            "role": OrganisationMembership.Role.ANALYST,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    membership.refresh_from_db()

    assert membership.role == OrganisationMembership.Role.ADMINISTRATOR


@pytest.mark.django_db
def test_last_administrator_cannot_be_deleted() -> None:
    administrator = User.objects.create_user(
        username="alice",
    )

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    membership = OrganisationMembership.objects.create(
        organisation=organisation,
        user=administrator,
        role=OrganisationMembership.Role.ADMINISTRATOR,
    )

    client = APIClient()
    client.force_authenticate(user=administrator)

    response = client.delete(
        reverse(
            "organisations:membership-detail",
            kwargs={
                "organisation_id": organisation.id,
                "pk": membership.id,
            },
        )
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert OrganisationMembership.objects.filter(pk=membership.id).exists()


@pytest.mark.django_db
def test_administrator_cannot_modify_membership_from_another_organisation() -> None:
    alice = User.objects.create_user(
        username="alice",
    )
    bob = User.objects.create_user(
        username="bob",
    )

    acme = Organisation.objects.create(
        name="Acme Security AB",
    )
    northstar = Organisation.objects.create(
        name="Northstar Systems AB",
    )

    OrganisationMembership.objects.create(
        organisation=acme,
        user=alice,
        role=OrganisationMembership.Role.ADMINISTRATOR,
    )

    northstar_membership = OrganisationMembership.objects.create(
        organisation=northstar,
        user=bob,
        role=OrganisationMembership.Role.VIEWER,
    )

    client = APIClient()
    client.force_authenticate(user=alice)

    response = client.patch(
        reverse(
            "organisations:membership-detail",
            kwargs={
                "organisation_id": acme.id,
                "pk": northstar_membership.id,
            },
        ),
        {
            "role": OrganisationMembership.Role.ANALYST,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND

    northstar_membership.refresh_from_db()

    assert northstar_membership.role == OrganisationMembership.Role.VIEWER
