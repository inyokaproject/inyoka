from django.apps import AppConfig


class WikiAppConfig(AppConfig):
    name = 'inyoka.wiki'
    verbose_name = 'Wiki'

    def ready(self):
        import inyoka.wiki.macros
        import inyoka.wiki.signals
