#-*- coding: utf-8 -*-
from django.db.models.signals import class_prepared
from django.utils.importlib import import_module


AUTOIMPORT_MODULES = ['search']


def register_special_modules(sender, **kwargs):
    """Import special modules for every application.

    This enables to implement pluggable APIs where application
    can register addons to some core functionality.

    With this we are able to finally split application logic
    from core functionality and cleanup some fancy circular imports.

    This truely adds some overhead for the initial startup time
    of Inyoka but as Python caches imports the overhead is bearable.
    """
    module = sender.__module__
    if module.startswith('inyoka.'):
        for path in AUTOIMPORT_MODULES:
            try:
                import_module('.'.join(module.split('.')[:2]) + '.' + path)
            except ImportError:
                pass


class_prepared.connect(register_special_modules)
