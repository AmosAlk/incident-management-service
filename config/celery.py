import os

from celery import Celery
from celery.signals import worker_process_init

from config.telemetry import configure_tracing

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

app = Celery("config")

app.config_from_object(
    "django.conf:settings",
    namespace="CELERY",
)

app.autodiscover_tasks()


@worker_process_init.connect(weak=False)
def initialise_worker_tracing(
    **_kwargs,
) -> None:
    configure_tracing()
