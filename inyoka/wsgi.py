# -*- coding: utf-8 -*-
"""
    inyoka.wsgi
    ~~~~~~~~~~~

    A default WSGI handler to run Inyoka. If :data:`settings.DEBUG` is ``True``
    the application is a `debugged Werkzeug application
    <http://werkzeug.pocoo.org/docs/debug/>`_.

    :copyright: (c) 2008-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler

application = WSGIHandler()
if settings.DEBUG:
    from werkzeug.debug import DebuggedApplication
    application = DebuggedApplication(application, evalex=True)
