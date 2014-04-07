#-*- coding: utf-8 -*-
"""
    inyoka.core.models
    ~~~~~~~~~~~~~~~~~~

    This module provides autoloading a certain core functions.

    :copyright: (c) 2012-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys
from django.db.models import loading
from django.utils.importlib import import_module

IS_PYPY = hasattr(sys, "pypy_version_info")
AUTOIMPORT_MODULES = ['macros', 'signals']


def register_special_modules():
    """Import special modules for every application.

    This enables to implement pluggable APIs where application can register
    addons to some core functionality.

    With this we are able to finally split application logic from core
    functionality and cleanup some fancy circular imports.

    This truely adds some overhead for the initial startup time of Inyoka but
    as Python caches imports the overhead is bearable.
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
                except ImportError as exc:
                    _ = str(exc)
                    exc_path = module_path if IS_PYPY else path
                    if _ != 'No module named %s' % exc_path:
                        raise

register_special_modules()
