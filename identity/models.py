import uuid

from django.conf import settings
from django.db import models

# These are not necessarily the same person, so identity needs
# to be stronger. Both issuer and subject must be used in combination.
# Keycloak A
# sub = 123

# Keycloak B
# sub = 123


class ExternalIdentity(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Foreign key but stricter. Only ONE external identity per Django user.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="external_identity",
    )

    issuer = models.URLField(max_length=255)
    subject = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["issuer", "subject"],
                name="unique_oidc_identity",
            )
        ]

    def __str__(self) -> str:
        return f"{self.issuer} / {self.subject}"
