import uuid

from django.conf import settings
from django.db import models

from organisations.models import Organisation


class AuditEvent(models.Model):
    class Action(models.TextChoices):
        # First value used in Python, second value is used in the db, third
        # is a human readable lable.
        INCIDENT_CREATED = "incident.created", "Incident created"
        INCIDENT_STATUS_CHANGED = (
            "incident.status_changed",
            "Incident status changed",
        )
        COMMENT_CREATED = "comment.created", "Comment created"

    class ResourceType(models.TextChoices):
        INCIDENT = "incident", "Incident"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # For tenant-scoped retrieval. This needs to be concrete so that
    # members of other organisations cannot access audit logs that do
    # not belong to their organisation.
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        related_name="audit_events",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="audit_events",
    )

    action = models.CharField(
        max_length=64,
        choices=Action.choices,
    )

    resource_type = models.CharField(
        max_length=50,
        choices=ResourceType.choices,
    )

    # The resource it refers to, eg an incident.
    # But not a foreign key relationship because logs are
    # not necessarily about incidents.
    resource_id = models.UUIDField()

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # How they are ordered when queried, unless specified otherwise.
        ordering = ["created_at", "id"]
        # Since org, resource type, resource id will be a common database query,
        # postgres has an additional data structure to designed to find
        # matching rows much faster. Stored in a B tree.
        indexes = [
            models.Index(
                fields=[
                    "organisation",
                    "resource_type",
                    "resource_id",
                ],
                name="audit_resource_idx",
            )
        ]

    def __str__(self) -> str:
        return f"{self.action} by {self.actor}"
