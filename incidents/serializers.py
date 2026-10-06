from rest_framework import serializers

from incidents.models import Incident


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
