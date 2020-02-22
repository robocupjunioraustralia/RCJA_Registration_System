import os
from django.core.management.base import BaseCommand
from users.models import User
from keyvaluestore.utils import get_value_or_default, set_key_value

class Command(BaseCommand):
    help = 'Detect and run first time setup for Heroku platforms'

    def handle(self, *args, **options):
        self.stdout.write('Running Heroku setup script')
        
        first_run = get_value_or_default('HEROKU_FIRST_RUN', 'yes')
        if first_run == 'yes':
            if not User.objects.filter(is_superuser=True).exists():
                # Set up the super user
                email = os.environ.get('DJANGO_SUPERUSER_EMAIL', None)
                password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', None)
                if email and password:
                    User.objects.create_superuser(email, password)
                    self.stdout.write(f'Created superuser {email}')
                else:
                    self.stdout.write('Missing superuser credentials. Skipping...')

            set_key_value('HEROKU_FIRST_RUN', 'no')
            self.stdout.write('Ran first time setup')
        else:
            self.stdout.write('Not first run. Skipping setup')
