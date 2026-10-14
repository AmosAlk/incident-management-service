from auditlog.models import AuditEvent

# We do not want views throughout the program to repeatedly
# construct AuditEvents manually.


def record_audit_event(
    # All args passed by name.
    *,
    organisation,
    actor,
    action,
    resource_type,
    resource_id,
    metadata=None,
) -> AuditEvent:
    return AuditEvent.objects.create(
        organisation=organisation,
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=metadata or {},
    )
