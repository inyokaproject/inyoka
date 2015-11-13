# From http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html
from __future__ import absolute_import

import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inyoka.default_settings')

from django.conf import settings  # noqa

app = Celery('inyoka')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')

# Autodiscover does not work with django app objects at the moment (celery 3.1)
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
