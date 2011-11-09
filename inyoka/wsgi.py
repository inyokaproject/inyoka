from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler


application = WSGIHandler()
if settings.DEBUG:
    from werkzeug.debug import DebuggedApplication
    application = DebuggedApplication(application, evalex=True)
