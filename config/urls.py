from django.contrib import admin
from django.urls import include, path

from config.views import metrics_view
from incidents.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/incidents/", include("incidents.urls")),
    path(
        "api/organisations/",
        include("organisations.urls"),
    ),
    path("metrics/", metrics_view, name="metrics"),
]
