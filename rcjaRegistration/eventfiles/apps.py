from django.apps import AppConfig


class EventfilesConfig(AppConfig):
    name = 'eventfiles'
    verbose_name= 'Event Files'
    def ready(self):
        import eventfiles.signals
