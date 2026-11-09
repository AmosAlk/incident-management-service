# Threat Model

## Scope

This threat model covers the Incident Operations Service API, its local OIDC authentication integration, PostgreSQL persistence, and multi-tenant authorisation model.

## Assets

The primary assets are:

- incident and comment data;
- organisation membership and role information;
- audit history;
- user identities;
- authentication tokens;
- database and application credentials.

## Trust Boundaries

The main trust boundaries are:

1. Client → Keycloak
2. Client → Django API
3. Django API → Keycloak JWKS
4. Django API → PostgreSQL
5. Authenticated user → another organisation's resources

All client-provided values are considered untrusted until validated.

## Threats and Controls

| Threat | Existing control |
| --- | --- |
| Forged or modified access token | JWT signature verification using Keycloak public keys |
| Expired access token | `exp` validation |
| Token issued by an unexpected identity provider | `iss` validation |
| Valid token intended for another API | `aud` validation |
| External identity colliding with a local Django username | Explicit `ExternalIdentity` mapping using issuer + subject |
| User accesses another organisation's incident | Tenant-scoped querysets |
| User guesses another tenant's object UUID | Tenant-scoped retrieval returns 404 |
| Viewer modifies an incident | DRF role/object permissions |
| Analyst performs administrator-only membership operations | Administrator permission checks |
| Client impersonates incident creator/comment author | Actor fields are server controlled |
| Client mass-assigns protected incident fields | Serializer read-only fields |
| Client manufactures audit records | Audit API is read-only and events are server generated |
| Business change succeeds without matching audit event | Database transaction wraps mutation and audit creation |
| Organisation loses its final Administrator | Serializer/view validation prevents final Administrator removal/demotion |
| Secret committed to Git | Secrets are loaded from `.env`, which is Git-ignored |

## Residual Risks / Future Work

The following controls remain future work:

- production HTTPS and HSTS configuration;
- production Keycloak configuration rather than `start-dev`;
- rate limiting and resource-consumption protection;
- background-job security;
- database least-privilege configuration;
- production logging and monitoring;
- backup and restore testing;
- dependency and container vulnerability scanning;
- production secret management;
- deployment/network isolation;
- formal load and security testing.

## Security Principles

The service follows several recurring principles:

- authentication and authorisation are separate concerns;
- knowing an object identifier does not grant access to the object;
- tenant isolation is enforced when querying data, not merely in the user interface;
- client-controlled input must not control server-owned fields;
- database constraints provide a final line of defence against invalid state;
- security-critical multi-step writes should be atomic;
- access tokens are only trusted after cryptographic and claim validation.