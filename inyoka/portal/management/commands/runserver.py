from django.conf import settings
from django.core.management.commands.runserver import BaseRunserverCommand

from werkzeug.debug import DebuggedApplication

class Command(BaseRunserverCommand):

    def get_handler(self, *args, **options):
        """
        Returns the static files serving handler.
        """
        handler = super(Command, self).get_handler(*args, **options)
        if settings.DEBUG:
            enable_evalex = settings.DEBUG_PROPAGATE_EXCEPTIONS
            handler = DebuggedApplication(handler, evalex=enable_evalex)
        return handler

    def handle(self, addrport='', *args, **options):
        addrport = '8080' if not addrport else addrport
        return super(Command, self).handle(addrport, *args, **options)
