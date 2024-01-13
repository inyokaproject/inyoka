from django.apps import AppConfig


class MarkupAppConfig(AppConfig):
    name = 'inyoka.markup'
    verbose_name = 'Markup'

    def ready(self):
        import inyoka.markup.macros
