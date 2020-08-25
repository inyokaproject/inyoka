# From http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html


import os

import celery
import raven
from django.conf import settings
from raven.contrib.celery import register_signal, register_logger_signal


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inyoka.default_settings')


class Celery(celery.Celery):

    def on_configure(self):
        if not hasattr(settings, 'RAVEN_CONFIG'):
            return

        client = raven.Client(settings.RAVEN_CONFIG['dsn'])

        # register a custom filter to filter out duplicate logs
        register_logger_signal(client)

        # hook into the Celery error handler
        register_signal(client)


app = Celery('inyoka')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover does not work with django app objects at the moment (celery 3.1)
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
