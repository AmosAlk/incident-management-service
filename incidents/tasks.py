import smtplib

from celery import shared_task
from celery.contrib.django.task import DjangoTask
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import F
from django.utils import timezone

from incidents.models import IncidentNotificationDelivery
from organisations.models import OrganisationMembership


def retry_delay(retries: int) -> int:
    return min(
        5 * (2**retries),
        60,
    )


@shared_task(
    bind=True,
    ignore_result=True,
    acks_late=True,
    max_retries=5,
    soft_time_limit=20,
    time_limit=30,
)
def notify_administrators_incident_created(
    self: DjangoTask,
    delivery_id: str,
) -> None:
    try:
        delivery = (
            IncidentNotificationDelivery.objects.select_related(
                "incident__organisation"
            ).get(pk=delivery_id)
        )
    except IncidentNotificationDelivery.DoesNotExist:
        return

    if delivery.status in {
        IncidentNotificationDelivery.Status.SENT,
        IncidentNotificationDelivery.Status.SKIPPED,
    }:
        return

    incident = delivery.incident

    recipients = list(
        OrganisationMembership.objects.filter(
            organisation=incident.organisation,
            role=OrganisationMembership.Role.ADMINISTRATOR,
        )
        .exclude(user__email="")
        .values_list(
            "user__email",
            flat=True,
        )
        .distinct()
    )

    if not recipients:
        delivery.status = (
            IncidentNotificationDelivery.Status.SKIPPED
        )
        delivery.last_error = ""
        delivery.save(
            update_fields=[
                "status",
                "last_error",
                "updated_at",
            ]
        )
        return

    IncidentNotificationDelivery.objects.filter(
        pk=delivery.pk
    ).update(
        attempts=F("attempts") + 1
    )

    delivery.refresh_from_db(
        fields=["attempts"]
    )

    try:
        send_mail(
            subject=f"New incident: {incident.title}",
            message=(
                f"A new {incident.severity} severity incident "
                f"has been created.\n\n"
                f"Title: {incident.title}\n"
                f"Incident ID: {incident.pk}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )

    except (
        OSError,
        smtplib.SMTPException,
        SoftTimeLimitExceeded,
    ) as exc:
        delivery.last_error = (
            f"{type(exc).__name__}: {exc}"
        )[:2000]

        delivery.save(
            update_fields=[
                "last_error",
                "updated_at",
            ]
        )

        raise self.retry(
            exc=exc,
            countdown=retry_delay(
                self.request.retries
            ),
        )

    delivery.status = (
        IncidentNotificationDelivery.Status.SENT
    )
    delivery.sent_at = timezone.now()
    delivery.last_error = ""

    delivery.save(
        update_fields=[
            "status",
            "sent_at",
            "last_error",
            "updated_at",
        ]
    )