# -*- coding: utf-8 -*-
from django.apps import AppConfig


class PortalAppConfig(AppConfig):
    name = 'inyoka.portal'
    verbose_name = 'Portal'

    css_generated = False

    def ready(self):
        """
        Will be executed once on startup

        see https://docs.djangoproject.com/en/1.8/ref/applications/#django.apps.AppConfig.ready
        """
        if not self.css_generated:
            from inyoka.portal.models import Linkmap
            Linkmap.objects.generate_css()
            self.css_generated = True
