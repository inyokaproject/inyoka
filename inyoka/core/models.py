#-*- coding: utf-8 -*-

# register core signals here as app.models get imported
# by django on a proper point where we cannot mess up
# the django.conf setup anymore.

import inyoka.core.signals
