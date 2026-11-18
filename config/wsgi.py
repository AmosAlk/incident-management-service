"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from config.telemetry import configure_tracing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

configure_tracing()

application = get_wsgi_application()
