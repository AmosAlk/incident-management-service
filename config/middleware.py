import logging
import time
from collections.abc import Callable
from uuid import uuid4

from django.http import HttpRequest, HttpResponse

from config.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
)
from config.request_context import (
    reset_request_id,
    set_request_id,
)

logger = logging.getLogger("api.request")


def generate_request_id() -> str:
    return str(uuid4())


# Middleware sits between the client and the django view.
class RequestIDMiddleware:
    # Runs only when initialising the middleware.
    def __init__(
        self,
        # Confusing syntax. get_response is something callable which takes
        # argument types in [], so only HttpRequest, and returns a
        # HttpResponse.
        # The actual function which fits this interface is supplied by
        # Django. It takes the HttpRequest and passes it to whatever
        # comes next.
        get_response: Callable[
            [HttpRequest],
            HttpResponse,
        ],
    ) -> None:
        self.get_response = get_response

    # Runs every time the middleware is called on a request.
    def __call__(
        self,
        request: HttpRequest,
    ) -> HttpResponse:
        request_id = generate_request_id()

        token = set_request_id(request_id)

        request.request_id = request_id  # type: ignore

        started_at = time.perf_counter()

        # Here we try to process the request. Regardless of the
        # outcome, we then reset back to the token.
        try:
            response = self.get_response(request)

            duration_seconds = time.perf_counter() - started_at

            duration_ms = round(
                duration_seconds * 1000,
                2,
            )

            status = str(response.status_code)

            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                status=status,
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                status=status,
            ).observe(duration_seconds)

            response["X-Request-ID"] = request_id

            logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

            return response

        except Exception:
            duration_seconds = time.perf_counter() - started_at

            duration_ms = round(
                duration_seconds * 1000,
                2,
            )

            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                status="500",
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                status="500",
            ).observe(duration_seconds)

            logger.exception(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.path,
                    "duration_ms": duration_ms,
                },
            )

            raise

        finally:
            reset_request_id(token)
