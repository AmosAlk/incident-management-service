# Security Configuration

## Environments

The service distinguishes between development and production using `DJANGO_ENVIRONMENT`.

Supported values are:

- `development`
- `production`

Unknown values cause application start-up to fail.

## Development

Development prioritises local usability while preserving the same authentication and authorisation architecture as production.

Typical development configuration includes:

- `DEBUG=True`
- HTTP on localhost
- local `.env` configuration
- Keycloak `start-dev`
- local PostgreSQL and Keycloak containers
- production HTTPS enforcement disabled

Development configuration must not be reused unchanged for an internet-facing deployment.

## Production

Production configuration requires:

- `DEBUG=False`
- explicit `ALLOWED_HOSTS`
- HTTPS enforcement
- secure session and CSRF cookies
- HSTS
- externally injected application/database secrets
- a production-configured identity provider
- production traffic controls and network boundaries

The application refuses to start if `DEBUG=True` while `DJANGO_ENVIRONMENT=production`.

## HTTPS

Production enables `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, and `CSRF_COOKIE_SECURE`.

HSTS is enabled with an initially conservative duration. `includeSubDomains` and preload are not enabled until the final production domain and TLS architecture are known.

`SECURE_PROXY_SSL_HEADER` must only be configured when the application is deployed behind a trusted reverse proxy that correctly strips and sets forwarding headers.

## Secrets

`.env` is a local-development convenience and is excluded from Git.

Production credentials should be supplied by the deployment environment or secret-management system rather than committed configuration files.

Examples of secret values include:

- Django secret key;
- PostgreSQL credentials;
- identity-provider administrative credentials.

OIDC issuer, audience, and public JWKS endpoint configuration are application configuration rather than secret credentials.

## Identity Provider

The local Keycloak container uses `start-dev` and exists only for development.

A production identity provider requires production-mode configuration, persistent storage, HTTPS, secure administrative credentials, controlled network exposure, backup procedures, and an explicit hostname/proxy configuration.

## Security Validation

Before production deployment:

1. Run the full automated test suite.
2. Run Django's normal system checks.
3. Run `manage.py check --deploy` using production configuration.
4. Review every remaining warning rather than suppressing checks mechanically.
5. Verify HTTPS, identity-provider connectivity, tenant isolation, authentication, authorisation, throttling, audit logging, secret injection, and backup/recovery behaviour in the deployed environment.