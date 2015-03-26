# -*- coding: utf-8 -*-
"""
    inyoka.markup.signals
    ~~~~~~~~~~~~~~~~~~~

    Macro signals for Inyoka.

    :copyright: (c) 2012-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import django.dispatch

build_picture_node = django.dispatch.Signal(providing_args=[
    'context',
    'format'
])
