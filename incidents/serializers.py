from rest_framework import serializers

from incidents.models import Incident
from organisations.models import OrganisationMembership


# Could use Serializer instead of ModelSerializer but it requires
# you to manually describe every field. Model can infer them
# from the provided model in the meta class.
class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        # Tells the serializer that this describes the API
        # representation of the Incident model.
        model = Incident
        # COULD say fields = "__all__", but we want to be careful
        # and deliberate in what we expose in case something we
        # want hidden is added as a field in the model later.
        fields = [
            "id",
            "organisation",
            "title",
            "description",
            "severity",
            "status",
            "created_by",
            "assigned_to",
            "created_at",
            "updated_at",
        ]
        # To prevent mass assignment, clients can only modify fields
        # that they actually own.
        read_only_fields = [
            "id",
            "status",
            "created_by",
            "assigned_to",
            "created_at",
            "updated_at",
        ]


class IncidentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = [
            "id",
            "organisation",
            "title",
            "description",
            "severity",
            "status",
            "created_by",
            "assigned_to",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organisation",
            "created_by",
            "created_at",
            "updated_at",
        ]

    # DRF recognises methods with the name validate_<field_name>
    # so when a client sends eg "status" : "investigating",
    # DRF will confirm that "investigating" is valid TextChoices value
    # as determined by the model for incidents.
    # Value is attempted new status, self.instance.status is old status.
    def validate_status(self, value):
        # self.instance is the current object being updated.
        # Also prevents patching with the same value as the object
        # currently has.
        # Might be None if a creation somehow occured instead of an update.
        if self.instance is None or value == self.instance.status:
            # Return "ok" to DRM because there is nothing to validate
            # if there is no state change.
            return value

        # Dict of statuses to sets of statuses you are allowed to move to.
        allowed_transitions = {
            Incident.Status.OPEN: {
                Incident.Status.INVESTIGATING,
            },
            Incident.Status.INVESTIGATING: {
                Incident.Status.RESOLVED,
            },
            Incident.Status.RESOLVED: {
                Incident.Status.INVESTIGATING,
                Incident.Status.CLOSED,
            },
            Incident.Status.CLOSED: set(),
        }

        current_status = self.instance.status

        if value not in allowed_transitions[current_status]:
            raise serializers.ValidationError(
                f"Cannot change status from {current_status} to {value}."
            )

        return value

    def validate_assigned_to(self, value):
        if value is None:
            return value

        if self.instance is None:
            return value

        is_member = OrganisationMembership.objects.filter(
            organisation=self.instance.organisation,
            user=value,
        ).exists()

        if not is_member:
            raise serializers.ValidationError(
                "Assigned user must be a member of the incident's organisation."
            )

        return value
