from django.apps import AppConfig


class ForumAppConfig(AppConfig):
    name = 'inyoka.forum'
    verbose_name = 'Forum'

    def ready(self):
        import inyoka.forum.macros
        import inyoka.forum.signals
