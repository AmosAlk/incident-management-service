from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(["GET"])
def health_check(_request: Request) -> Response:
    """Report that the HTTP application is running."""
    return Response({"status": "ok"})
