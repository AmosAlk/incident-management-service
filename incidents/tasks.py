from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from incidents.models import Incident
from organisations.models import OrganisationMembership


@shared_task(ignore_result=True)
def notify_administrators_incident_created(
    incident_id: str,
) -> None:
    incident = Incident.objects.select_related("organisation").get(pk=incident_id)

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
        return

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
