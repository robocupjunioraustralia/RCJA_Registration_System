from django.apps import AppConfig


class CoordinationConfig(AppConfig):
    name = 'coordination'
    def ready(self):
        import coordination.signals
