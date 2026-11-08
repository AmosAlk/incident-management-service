from unittest.mock import Mock, patch

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from jwt.exceptions import PyJWKClientError
from rest_framework import status
from rest_framework.test import APIClient

from identity.authentication import OIDCBearerAuthentication


@pytest.mark.django_db
def test_protected_endpoint_rejects_missing_token() -> None:
    client = APIClient()

    # No Authorization header is sent here.
    # OIDCBearerAuthentication therefore cannot authenticate a user,
    # and IsAuthenticated should reject the request.
    response = client.get(reverse("incidents:list-create"))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
# Replace jwt.decode() inside identity.authentication with a Mock.
# patch creates the Mock automatically and passes it into the test
# function. We choose to call that parameter "mock_decode".
@patch("identity.authentication.jwt.decode")
# Also replace the real signing-key lookup with a Mock.
# The name "mock_get_signing_key" below is just our own variable name;
# it does not have to exactly match "get_signing_key_from_jwt".
#
# Since this is the bottom/inner patch, its Mock becomes the FIRST
# parameter passed into the test function.
@patch.object(
    OIDCBearerAuthentication.jwks_client,
    "get_signing_key_from_jwt",
)
def test_valid_oidc_token_authenticates_user(
    mock_get_signing_key,
    mock_decode,
) -> None:
    # The real get_signing_key_from_jwt() returns an object that has
    # a .key attribute. Our authentication code later accesses:
    #
    #     signing_key.key
    #
    # So we make a fake object with the same shape.
    signing_key = Mock()
    signing_key.key = "public-key"

    # When authenticate() calls:
    #
    #     get_signing_key_from_jwt(token)
    #
    # return our fake signing-key object instead of contacting Keycloak.
    mock_get_signing_key.return_value = signing_key

    # jwt.decode() is also mocked, so no real cryptographic verification
    # happens in this test.
    #
    # We tell it to behave as if the token was valid and return the
    # claims that a real verified Keycloak token could contain.
    mock_decode.return_value = {
        "sub": "keycloak-user-123",
        "iss": settings.OIDC_ISSUER,
        "aud": settings.OIDC_AUDIENCE,
        "iat": 1_700_000_000,
        "exp": 4_102_444_800,
        "email": "alice@example.test",
        "given_name": "Alice",
        "family_name": "Example",
    }

    client = APIClient()

    # HTTP_AUTHORIZATION is how Django's test client adds the real HTTP
    # header:
    #
    #     Authorization: Bearer test-token
    #
    # "test-token" is not a real JWT. That is fine because the signing-key
    # lookup and jwt.decode() are mocked above.
    response = client.get(
        reverse("incidents:list-create"),
        HTTP_AUTHORIZATION="Bearer test-token",
    )

    # If authentication succeeded, request.user is now an authenticated
    # Django User, so the protected endpoint should allow the request.
    assert response.status_code == status.HTTP_200_OK

    # Everything below this point uses the real Django database.
    # authenticate() should have created a local User using the token's
    # "sub" claim as the username.
    user = User.objects.get(username="keycloak-user-123")

    assert user.email == "alice@example.test"

    # A Mock remembers how it was called.
    # This lets us check that our real authenticate() method called
    # jwt.decode() with the security settings we expect.
    decode_kwargs = mock_decode.call_args.kwargs

    assert decode_kwargs["algorithms"] == ["RS256"]
    assert decode_kwargs["audience"] == settings.OIDC_AUDIENCE
    assert decode_kwargs["issuer"] == settings.OIDC_ISSUER


@pytest.mark.django_db
# Again, replace the real signing-key lookup with a Mock.
# This test makes that lookup FAIL instead of returning a key.
@patch.object(
    OIDCBearerAuthentication.jwks_client,
    "get_signing_key_from_jwt",
)
def test_invalid_oidc_token_returns_401(
    mock_get_signing_key,
) -> None:
    # side_effect means:
    # "When this mocked method is called, raise this exception."
    #
    # This simulates a token whose signing key cannot be accepted/found.
    mock_get_signing_key.side_effect = PyJWKClientError("Unknown signing key")

    client = APIClient()

    response = client.get(
        reverse("incidents:list-create"),
        HTTP_AUTHORIZATION="Bearer invalid-token",
    )

    # OIDCBearerAuthentication catches PyJWKClientError and turns it
    # into an authentication failure, which DRF returns as 401.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
