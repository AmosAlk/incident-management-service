# Incident Operations Service - V1 Scope

## Purpose

Build a secure, multi-tenant service in which organisations can register, investigate and track operational or security incidents.

The project is intended to demonstrate production-oriented Python backend engineering, security engineering, testing, deployment, observability and operational recovery.

## Primary workflow

1. An authenticated analyst creates an incident.
2. The analyst assigns a severity and description.
3. Authorised users view and comment on the incident.
4. An analyst changes the incident status.
5. The system records important actions in an audit log.

## Roles

### Administrator

- Manages organisation members and roles.
- Can view and modify all incidents belonging to the organisation.
- Can perform administrative actions.

### Analyst

- Can create and update incidents.
- Can add comments and attachments.
- Cannot manage organisation membership or roles.

### Viewer

- Can view incidents belonging to the organisation.
- Cannot create, update or delete incidents.

## Core entities

- Organisation
- User
- OrganisationMembership
- Incident
- Comment
- Attachment
- AuditEvent

## Initial incident properties

- Title
- Description
- Severity
- Status
- Organisation
- Created by
- Assigned to
- Created timestamp
- Updated timestamp

## V1 acceptance criteria

- Users can authenticate.
- Users can only access data belonging to their organisation.
- Analysts can create and update incidents.
- Viewers have read-only access.
- Administrative actions require the administrator role.
- Important changes generate audit events.
- The API has automated tests and OpenAPI documentation.
- The service can run locally using Docker Compose.

## Non-goals for the first version

- Real-time chat
- Mobile application
- Complex frontend
- Multiple microservices
- Machine-learning incident classification
- Kubernetes before the local application works
- Custom password or token implementation
