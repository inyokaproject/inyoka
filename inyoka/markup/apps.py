# -*- coding: utf-8 -*-
from django.apps import AppConfig


class MarkupAppConfig(AppConfig):
    name = 'inyoka.markup'
    verbose_name = 'Markup'

    def ready(self):
        import inyoka.markup.macros
