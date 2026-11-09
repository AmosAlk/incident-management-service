import uuid

import jwt
from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError, PyJWTError
from rest_framework.authentication import (
    BaseAuthentication,
    get_authorization_header,
)
from rest_framework.exceptions import AuthenticationFailed

from identity.models import ExternalIdentity


class OIDCBearerAuthentication(BaseAuthentication):
    # Keycloak publishes its public signing keys through the JWKS endpoint.
    # We use those keys to verify that incoming access tokens were really
    # issued by Keycloak and have not been modified.
    jwks_client = PyJWKClient(settings.OIDC_JWKS_URL)

    def get_or_create_user(self, claims) -> User:
        issuer = claims["iss"]
        subject = claims["sub"]

        identity = (
            ExternalIdentity.objects.select_related("user")
            .filter(
                issuer=issuer,
                subject=subject,
            )
            .first()
        )

        if identity is not None:
            return identity.user

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=f"oidc_{uuid.uuid4().hex}",
                    email=claims.get("email", ""),
                    first_name=claims.get("given_name", ""),
                    last_name=claims.get("family_name", ""),
                )

                ExternalIdentity.objects.create(
                    user=user,
                    issuer=issuer,
                    subject=subject,
                )

                return user

        except IntegrityError:
            identity = ExternalIdentity.objects.select_related("user").get(
                issuer=issuer,
                subject=subject,
            )

            return identity.user

    def authenticate(self, request):
        # Expected header:
        # Authorization: Bearer <access-token>
        parts = get_authorization_header(request).split()

        # No Authorization header means this authentication class has
        # nothing to authenticate.
        if not parts:
            return None

        # Ignore other authentication schemes such as Basic auth.
        if parts[0].lower() != b"bearer":
            return None

        # A Bearer header must contain exactly:
        # ["Bearer", "<token>"]
        if len(parts) != 2:
            raise AuthenticationFailed("Invalid Authorization header.")

        # get_authorization_header() returns bytes, while PyJWT expects
        # the token as a normal Python string.
        try:
            token = parts[1].decode("ascii")
        except UnicodeDecodeError as exc:
            raise AuthenticationFailed("Invalid bearer token.") from exc

        try:
            # The JWT contains a key ID ("kid"). PyJWKClient uses it to
            # find the correct public key from Keycloak's JWKS endpoint.
            # Keycloak uses multiple private-public key pairs.
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Verify the token and return its claims.
            #
            # This checks:
            # - the cryptographic signature
            # - that RS256 was used
            # - that the token was issued by our Keycloak realm
            # - that it is intended for this API
            # - that it has not expired
            # - that the required claims are present
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.OIDC_AUDIENCE,
                issuer=settings.OIDC_ISSUER,
                options={
                    "require": [
                        "aud",
                        "exp",
                        "iat",
                        "iss",
                        "sub",
                    ]
                },
            )

        except (PyJWTError, PyJWKClientError) as exc:
            # Keep the response deliberately general. The client only needs
            # to know that the token cannot be accepted.
            raise AuthenticationFailed("Invalid or expired access token.") from exc

        user = self.get_or_create_user(claims)

        # DRF interprets this as:
        # request.user = user
        # request.auth = claims
        return user, claims

    def authenticate_header(self, request) -> str:
        # Used by DRF when returning an authentication challenge, e.g.
        # WWW-Authenticate: Bearer
        return "Bearer"
