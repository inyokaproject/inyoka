#-*- coding: utf-8 -*-
from django.conf import settings
from django.db.models import loading
from django.utils.importlib import import_module


AUTOIMPORT_MODULES = ['search', 'macros', 'signals']


def register_special_modules():
    """Import special modules for every application.

    This enables to implement pluggable APIs where application
    can register addons to some core functionality.

    With this we are able to finally split application logic
    from core functionality and cleanup some fancy circular imports.

    This truely adds some overhead for the initial startup time
    of Inyoka but as Python caches imports the overhead is bearable.
    """
    apps = loading.get_apps()
    for app in apps:
        name = app.__name__
        if name.startswith('inyoka.'):
            for path in AUTOIMPORT_MODULES:
                module_path = '%s.%s' % ('.'.join(name.split('.')[:2]),
                                         path)
                try:
                    import_module(module_path)
                except ImportError, exc:
                    _ = str(exc)
                    if _ != 'No module named %s' % path:
                        raise
                    pass

register_special_modules()
