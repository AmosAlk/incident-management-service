from rest_framework import serializers

from auditlog.models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "actor",
            "action",
            "resource_type",
            "resource_id",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields
