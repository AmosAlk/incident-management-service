from django.contrib import admin
from django.urls import include, path

from incidents.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/incidents/", include("incidents.urls")),
]
