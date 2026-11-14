# Threat Model

## Scope

This threat model covers the current incident-management service, including:

- the Django REST Framework API;
- PostgreSQL persistence;
- multi-tenant organisation isolation;
- organisation membership and role-based authorisation;
- audit logging;
- external OIDC authentication through Keycloak;
- JWT validation using issuer, audience, expiry, subject, and JWKS signature verification;
- API throttling and HTTP abuse controls;
- environment-specific security configuration;
- RabbitMQ as the Celery message broker;
- Celery background workers;
- asynchronous incident-created notifications;
- durable notification-delivery state stored in PostgreSQL.

The local Keycloak instance is a development identity provider and is not treated as a production-ready deployment.

The threat model currently focuses on the backend service and its directly connected infrastructure. Production deployment controls such as Kubernetes network policies, production secret stores, external TLS termination, monitoring, and backup infrastructure will be added later in the project.

---

## Assets

The primary assets that require protection are:

- incident data;
- comment data;
- organisation membership data;
- administrator, analyst, and viewer role assignments;
- audit events;
- external identity mappings;
- OIDC access tokens;
- PostgreSQL data;
- application secrets;
- database credentials;
- RabbitMQ credentials;
- queued task messages;
- notification-delivery state;
- service availability;
- application and infrastructure resources.

A compromise of these assets could result in:

- unauthorised access to another organisation's data;
- unauthorised modification of incidents;
- privilege escalation;
- impersonation of another user;
- loss or manipulation of audit evidence;
- duplicate or lost background work;
- disclosure of credentials or access tokens;
- service degradation or denial of service.

---

## Trust Boundaries

### Client → Keycloak

The client sends authentication requests to Keycloak.

Keycloak is responsible for authenticating the user and issuing OIDC tokens.

The application does not manage user passwords or issue authentication tokens itself.

---

### Client → Django API

The client sends bearer tokens and API requests to Django.

Django must not trust the token merely because the client supplied it.

The API validates the token signature and security claims before establishing an authenticated Django user.

The authenticated user must then pass application-level organisation membership and role checks.

---

### Django → Keycloak JWKS endpoint

Django retrieves public signing-key information from Keycloak's JWKS endpoint.

The public keys are used to verify JWT signatures.

The application must validate the expected issuer and audience in addition to the cryptographic signature.

---

### Django → PostgreSQL

Django reads and modifies application state in PostgreSQL.

The database contains security-sensitive state including:

- incidents;
- comments;
- organisation memberships;
- role assignments;
- audit events;
- external identity mappings;
- notification-delivery records.

Application validation is reinforced by database constraints where appropriate.

---

### Authenticated user → Other organisations

An authenticated user is not automatically authorised to access every organisation.

All organisation-specific resources must remain scoped to organisations in which the authenticated user has a valid `OrganisationMembership`.

Knowing or guessing another object's UUID must not grant access.

---

### Django → RabbitMQ

Django publishes Celery task messages to RabbitMQ after relevant database transactions commit.

RabbitMQ is trusted to route queued work to Celery workers.

Broker credentials must not be exposed to clients or committed to source control.

A successful database transaction does not by itself guarantee that RabbitMQ accepted the task if broker publication ultimately fails.

---

### RabbitMQ → Celery worker

RabbitMQ delivers queued task messages to Celery workers.

Workers must treat task execution as potentially repeatable because messages can be retried or redelivered.

Late acknowledgement is used for the notification task so work is not considered complete merely because a worker received it.

---

### Celery worker → PostgreSQL

Celery workers load notification-delivery and incident state from PostgreSQL.

Workers update durable delivery state such as:

- status;
- attempt count;
- last error;
- completion timestamp.

The worker must not rely solely on task-message contents when current database state can be loaded instead.

---

## Threats and Controls

| Threat | Current control |
|---|---|
| Forged access token | JWT signature is verified using Keycloak JWKS and the expected signing algorithm. |
| Expired access token | JWT `exp` is required and validated. |
| Token issued by the wrong identity provider | JWT `iss` is required and validated against the configured issuer. |
| Token intended for another service | JWT `aud` is required and validated against the API's configured audience. |
| Missing or malformed bearer token | OIDC authentication rejects invalid authentication input rather than treating it as an authenticated request. |
| Collision between local users and external identities | External users are mapped using the combination of OIDC issuer and subject rather than trusting usernames. |
| Concurrent first login for the same OIDC identity | External identity creation is protected by a database uniqueness constraint and transaction handling. |
| Cross-tenant incident access | Incident querysets are scoped through `OrganisationMembership`; inaccessible objects are hidden rather than returned across tenants. |
| Cross-tenant comment access | Parent incident lookup is tenant-scoped before comments are accessed. |
| Cross-tenant membership access | Membership-management endpoints are nested under and filtered by the organisation. |
| Viewer modifies an incident | Object/application permissions restrict modification to authorised roles. |
| Viewer creates a comment | Comment creation checks organisation membership and requires Administrator or Analyst role. |
| Unauthorised incident creation | `perform_create()` verifies that the authenticated user belongs to the submitted organisation and has an Administrator or Analyst role. |
| Privilege escalation through membership management | Membership-management endpoints require an organisation Administrator. |
| Removal or demotion of the final Administrator | Application validation prevents deleting or demoting the final Administrator of an organisation. |
| Mass assignment of protected incident fields | Server-controlled fields such as `created_by`, status, and assignment cannot be freely supplied by the client during creation. |
| Client forges audit information | Audit events are generated server-side rather than accepted from client input. |
| Incident saved without required audit event | Critical incident mutation and audit recording are wrapped in `transaction.atomic()`. |
| Comment saved without required audit event | Comment creation and audit recording are wrapped in `transaction.atomic()`. |
| Background task observes an uncommitted incident | Celery work is scheduled with `delay_on_commit()` so the task is published only after the database transaction commits. |
| Duplicate background-task execution sends repeated notifications | Notification delivery is persisted in PostgreSQL and completed `SENT` or `SKIPPED` deliveries are treated as no-ops when executed again. |
| Duplicate notification-delivery records | A database uniqueness constraint permits only one delivery for a given incident and notification kind. |
| Temporary email or network failure permanently loses notification work | Selected transient failures trigger bounded Celery retries with exponential backoff. |
| Retry storm against a failing external dependency | Retry delay increases exponentially and is capped; retry count is bounded. |
| Worker crashes before completing a task | Notification tasks use late acknowledgement so task completion is not acknowledged merely when execution begins. Worker-loss retry handling is also configured. |
| Task runs indefinitely | Celery soft and hard time limits bound execution time. |
| Background-task retry hides permanent programming errors | Retries are limited to selected transient exception types rather than every exception. |
| Notification state cannot be inspected after task execution | PostgreSQL stores delivery status, attempt count, last error, and completion time. |
| RabbitMQ temporarily unavailable when publishing | Celery producer publication retry is enabled with a bounded retry policy. |
| RabbitMQ remains unavailable after publication retries | The database retains a `PENDING` notification-delivery record so unfinished work remains detectable, although automatic republishing is not yet implemented. |
| Broker credentials disclosed | RabbitMQ credentials are provided through environment configuration and are excluded from source control. |
| Unsafe task serialisation | Celery task serialisation and accepted content are restricted to JSON. |
| Excessive API traffic | Authenticated users are subject to burst and sustained DRF throttles. |
| Excessive write traffic | Unsafe HTTP methods are additionally subject to a write-specific throttle. |
| Client exceeds configured API rate | DRF responds with `429 Too Many Requests` and may include `Retry-After`. |
| Application throttling assumed to provide DDoS protection | The documented design explicitly treats DRF throttling as application-level abuse protection rather than infrastructure-level DDoS mitigation. |
| Unexpected browser cross-origin access | No permissive CORS configuration has been added because the current service has no browser frontend requiring cross-origin API access. |
| Cross-site request forgery | Normal API authentication uses explicit bearer tokens rather than automatically attached authentication cookies; Django's CSRF middleware remains enabled for session-based surfaces such as Django administration. |
| Development debug information exposed in production | Environment-aware configuration prevents `DEBUG=True` when the application environment is production. |
| Production service accepts arbitrary host headers | Production configuration requires explicit `ALLOWED_HOSTS`. |
| Plain HTTP used in production | Production Django configuration enables HTTPS redirection. |
| Authentication/session cookies transmitted insecurely | Production configuration marks session and CSRF cookies as secure. |
| Browser downgrades from HTTPS after visiting secure site | Production configuration supports HTTP Strict Transport Security with configurable duration and optional subdomain/preload settings. |
| Reverse-proxy security assumptions configured incorrectly | `SECURE_PROXY_SSL_HEADER` is intentionally not configured until the trusted production reverse-proxy architecture is known. |
| Application secret committed to source control | `.env` is ignored and `.env.example` documents required configuration without containing real secrets. |

### Throttling limitations

The current DRF throttles are application-level controls rather than infrastructure-level denial-of-service protection.

They rely on Django's configured cache and are primarily intended to limit authenticated API overuse.

A production deployment with multiple application instances will require an appropriate shared cache or external rate-limiting layer if throttle counters must be coordinated across instances.

Infrastructure controls such as a reverse proxy, load balancer, CDN, WAF, network limits, or platform-level rate limiting remain separate concerns.

---

## Background-Task Reliability Model

The incident-created notification workflow currently behaves approximately as follows:

```text
HTTP request
    |
    v
Django
    |
    v
transaction.atomic()
    |
    +-- Incident
    +-- AuditEvent
    +-- NotificationDelivery(PENDING)
    |
    v
COMMIT
    |
    v
Celery task publication
    |
    v
RabbitMQ
    |
    v
Celery worker
    |
    +-- already SENT or SKIPPED
    |       |
    |       +-- return without duplicate side effect
    |
    +-- delivery succeeds
    |       |
    |       +-- mark SENT
    |
    +-- transient failure
            |
            +-- record error
            +-- retry with backoff
```

The system does **not** claim exactly-once external notification delivery.

The intended model is closer to:

- at-least-once task execution;
- durable notification state;
- bounded retries;
- late acknowledgement;
- duplicate suppression after successful delivery has been recorded.

There remains a failure window in which an external email may successfully be sent but the worker may crash before PostgreSQL is updated to `SENT`.

A later execution could therefore send the external notification again.

Removing that failure window requires stronger support from the external provider, such as provider-level idempotency keys, or a more comprehensive delivery architecture.

---

## Residual Risks / Future Work

The following controls or improvements remain future work:

- production TLS termination and verification of HTTPS/HSTS behaviour in the deployed environment;
- production Keycloak configuration rather than development `start-dev` mode;
- infrastructure-level rate limiting, shared-cache throttling, and resource-consumption/load testing;
- database least-privilege configuration;
- production logging, monitoring, and alerting;
- PostgreSQL backup and tested restore procedures;
- dependency and container vulnerability scanning;
- production secret injection, storage, rotation, and access control;
- production deployment and network isolation;
- formal load and security testing;
- full transactional outbox or equivalent guaranteed task-publication mechanism when RabbitMQ remains unavailable after producer retries;
- provider-level idempotency for external notification delivery;
- dead-letter handling and operational alerting for permanently failed background tasks.

---

## Security Principles

The current implementation follows these principles:

- authentication and authorisation are separate concerns;
- Keycloak establishes external identity while the application controls organisation membership and application roles;
- every tenant-specific query must enforce organisation isolation;
- authenticated users are not trusted merely because they possess a valid token;
- client input must not control server-owned security fields;
- critical state changes and their audit events should succeed or fail together;
- database constraints provide a final layer of integrity protection;
- application throttling is abuse protection, not infrastructure-level DDoS protection;
- production security configuration must fail closed rather than silently enabling unsafe development behaviour;
- secrets belong in environment or secret-management systems rather than source control;
- background tasks must be designed under the assumption that execution can fail or occur more than once;
- retries should target transient failures and remain bounded;
- asynchronous work should have durable state when the application needs to reason about whether it completed;
- exactly-once external side effects should not be claimed without an architecture that can actually guarantee them.