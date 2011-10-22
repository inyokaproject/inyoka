from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler

from werkzeug.debug import DebuggedApplication

application = WSGIHandler()
if settings.DEBUG:
    application = DebuggedApplication(application, evalex=True)
