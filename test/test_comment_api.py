import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from incidents.models import Comment, Incident
from organisations.models import Organisation, OrganisationMembership


@pytest.mark.django_db
def test_analyst_can_create_comment() -> None:
    user = get_user_model().objects.create_user(
        username="alice",
    )

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=user,
        role=OrganisationMembership.Role.ANALYST,
    )

    incident = Incident.objects.create(
        organisation=organisation,
        title="Suspicious login",
        description="An unusual login was detected.",
        severity=Incident.Severity.HIGH,
        created_by=user,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        reverse(
            "incidents:comment-list-create",
            kwargs={"incident_id": incident.id},
        ),
        {
            "body": "Reviewed the authentication logs.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    comment = Comment.objects.get()

    assert comment.incident == incident
    assert comment.author == user
    assert comment.body == "Reviewed the authentication logs."


@pytest.mark.django_db
def test_viewer_cannot_create_comment() -> None:
    viewer = get_user_model().objects.create_user(
        username="viewer",
    )

    creator = get_user_model().objects.create_user(
        username="creator",
    )

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=viewer,
        role=OrganisationMembership.Role.VIEWER,
    )

    incident = Incident.objects.create(
        organisation=organisation,
        title="Suspicious login",
        description="An unusual login was detected.",
        severity=Incident.Severity.HIGH,
        created_by=creator,
    )

    client = APIClient()
    client.force_authenticate(user=viewer)

    response = client.post(
        reverse(
            "incidents:comment-list-create",
            kwargs={"incident_id": incident.id},
        ),
        {
            "body": "I should not be allowed to add this.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_viewer_can_list_comments() -> None:
    viewer = get_user_model().objects.create_user(
        username="viewer",
    )

    author = get_user_model().objects.create_user(
        username="author",
    )

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=viewer,
        role=OrganisationMembership.Role.VIEWER,
    )

    incident = Incident.objects.create(
        organisation=organisation,
        title="Suspicious login",
        description="An unusual login was detected.",
        severity=Incident.Severity.HIGH,
        created_by=author,
    )

    comment = Comment.objects.create(
        incident=incident,
        author=author,
        body="Reviewed the authentication logs.",
    )

    client = APIClient()
    client.force_authenticate(user=viewer)

    response = client.get(
        reverse(
            "incidents:comment-list-create",
            kwargs={"incident_id": incident.id},
        )
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["id"] == str(comment.id)


@pytest.mark.django_db
def test_user_cannot_access_comments_for_another_organisation() -> None:
    alice = get_user_model().objects.create_user(
        username="alice",
    )

    bob = get_user_model().objects.create_user(
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
        role=OrganisationMembership.Role.ANALYST,
    )

    incident = Incident.objects.create(
        organisation=northstar,
        title="Northstar incident",
        description="Private Northstar data.",
        severity=Incident.Severity.HIGH,
        created_by=bob,
    )

    Comment.objects.create(
        incident=incident,
        author=bob,
        body="Private Northstar comment.",
    )

    client = APIClient()
    client.force_authenticate(user=alice)

    response = client.get(
        reverse(
            "incidents:comment-list-create",
            kwargs={"incident_id": incident.id},
        )
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_comment_author_is_authenticated_user() -> None:
    alice = get_user_model().objects.create_user(
        username="alice",
    )

    bob = get_user_model().objects.create_user(
        username="bob",
    )

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=alice,
        role=OrganisationMembership.Role.ANALYST,
    )

    incident = Incident.objects.create(
        organisation=organisation,
        title="Suspicious login",
        description="An unusual login was detected.",
        severity=Incident.Severity.HIGH,
        created_by=alice,
    )

    client = APIClient()
    client.force_authenticate(user=alice)

    response = client.post(
        reverse(
            "incidents:comment-list-create",
            kwargs={"incident_id": incident.id},
        ),
        {
            "body": "Reviewed the authentication logs.",
            "author": bob.id,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    comment = Comment.objects.get()

    assert comment.author == alice
    assert comment.author != bob
