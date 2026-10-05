import uuid

from django.conf import settings
from django.db import models

from organisations.models import Organisation


class Incident(models.Model):
    class Severity(models.TextChoices):
        # LOW in python, low in postgres, Low in human readable
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        INVESTIGATING = "investigating", "Investigating"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="incidents",
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        # Prevent deletion of a user that has created an incident. It does not make
        # sense to delete the incidents a user has created, they may be important.
        on_delete=models.PROTECT,
        related_name="created_incidents",
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        # A user assigned to an incident should be able to be deleted, so we just set
        # null to the assigned user. It is part of the workflow, and not important
        # history as such.
        on_delete=models.SET_NULL,
        # Allows null to be stored in the actual database.
        null=True,
        # Allows this part of the record to be empty, for django validation purposes.
        blank=True,
        related_name="assigned_incidents",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title


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
