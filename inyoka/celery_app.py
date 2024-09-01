# From http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html

import os

import celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inyoka.default_settings')

app = celery.Celery('inyoka')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover does not work with django app objects at the moment (celery 3.1)
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
