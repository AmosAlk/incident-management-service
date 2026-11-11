# Threat Model

## Scope

This threat model covers the Incident Operations Service API, its local OIDC authentication integration, PostgreSQL persistence, multi-tenant authorisation model, and API throttling controls.

## Assets

The primary assets are:

- incident and comment data;
- organisation membership and role information;
- audit history;
- user identities;
- authentication tokens;
- database and application credentials;
- API availability and application resources.

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
| Authenticated user sends a large burst of API requests | Per-user burst throttling using DRF `UserRateThrottle` |
| Authenticated user consumes excessive API capacity over a longer period | Per-user sustained throttling |
| Authenticated user performs excessive state-changing requests | Separate write throttle for non-safe HTTP methods |
| Client exceeds an applicable API rate limit | DRF rejects the request with `429 Too Many Requests` and a `Retry-After` response header |
| Production accidentally runs with Django debug mode enabled | Application refuses to start when `DEBUG=True` in the production environment |
| Malicious or unexpected HTTP `Host` value | Explicit `ALLOWED_HOSTS` configuration is required in production |
| Authentication tokens or session data transmitted over plain HTTP | Production configuration redirects HTTP to HTTPS |
| Session or CSRF cookies transmitted over HTTP | Production configuration marks both cookies as secure |
| Browser later reconnects to the production service using HTTP | Production configuration enables HSTS |
| Application secrets committed to source control | Secrets are sourced from environment variables and local `.env` remains Git-ignored |
| Development identity-provider configuration used as production configuration | Keycloak `start-dev` is explicitly documented as development-only |
| Incorrect proxy trust permits forged HTTPS forwarding information | `SECURE_PROXY_SSL_HEADER` remains unset until a trusted reverse-proxy architecture is established |

## Residual Risks / Future Work

The following controls remain future work:

- production HTTPS and HSTS configuration;
- production Keycloak configuration rather than `start-dev`;
- infrastructure-level rate limiting and denial-of-service protection;
- distributed/shared throttle storage suitable for horizontally scaled deployments;
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
- access tokens are only trusted after cryptographic and claim validation;
- application-level throttling limits abusive request patterns but is not a substitute for infrastructure-level denial-of-service protection.