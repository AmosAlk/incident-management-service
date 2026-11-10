from rest_framework.permissions import SAFE_METHODS
from rest_framework.throttling import UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    scope = "burst"


class SustainedRateThrottle(UserRateThrottle):
    scope = "sustained"


class WriteRateThrottle(UserRateThrottle):
    scope = "write"

    def allow_request(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True

        return super().allow_request(request, view)
