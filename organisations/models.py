import uuid

from django.conf import settings
from django.db import models


class Organisation(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class OrganisationMembership(models.Model):
    class Role(models.TextChoices):
        # administrator in Postgres, Administrator in "human readable",
        # ADMINISTRATOR in code
        ADMINISTRATOR = "administrator", "Administrator"
        ANALYST = "analyst", "Analyst"
        VIEWER = "viewer", "Viewer"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        # allows us to find all memberships, given an organisation eg
        # org.memberships.all()
        related_name="memberships",
    )

    user = models.ForeignKey(
        # Django allows for different user models so this just connects this field
        # to the model which is configured in this project.
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        # Same as before, myname.organisation_membership.all() lists all of
        # myname's org memberships.
        related_name="organisation_memberships",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                # A user can have at most one role per organisation.
                fields=["organisation", "user"],
                name="unique_user_per_organisation",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.organisation} ({self.role})"
