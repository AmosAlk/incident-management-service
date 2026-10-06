from django.urls import path

from incidents.views import IncidentDetailView, IncidentListCreateView

app_name = "incidents"

urlpatterns = [
    path(
        "",
        # as_view creates a django-callable request handler from the class.
        IncidentListCreateView.as_view(),
        name="list-create",
    ),
    path(
        # Match ONLY a URL containing a valid UUID, and store the matched
        # value as "pk".
        "<uuid:pk>/",
        IncidentDetailView.as_view(),
        name="detail",
    ),
]
