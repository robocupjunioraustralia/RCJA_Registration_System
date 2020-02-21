from django.apps import AppConfig


class UserprofilesConfig(AppConfig):
    name = 'userprofiles'
    verbose_name = 'Profiles'
    def ready(self):
        import userprofiles.signals
