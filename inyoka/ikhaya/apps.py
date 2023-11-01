from django.apps import AppConfig


class IkhayaAppConfig(AppConfig):
    name = 'inyoka.ikhaya'
    verbose_name = 'Ikhaya'

    def ready(self):
        import inyoka.ikhaya.macros
