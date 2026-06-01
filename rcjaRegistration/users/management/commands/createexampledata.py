from django.core.management.base import BaseCommand, CommandError

from common.baseTests import createStates, createUsers, createSchools, createEvents, createTeams, createWorkshopAttendees

from regions.models import State, Region
from users.models import User

class Command(BaseCommand):
    help = "Creates example data for development"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        createStates(self)
        createUsers(self)
        createSchools(self)
        createEvents(self)
        createTeams(self)
        createWorkshopAttendees(self)

        self.stdout.write(self.style.SUCCESS('Successfully created example data'))
