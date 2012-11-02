#-*- coding: utf-8 -*-

import django.dispatch

build_picture_node = django.dispatch.Signal(providing_args=[
    'context',
    'format'
])