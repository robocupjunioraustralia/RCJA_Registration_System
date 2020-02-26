from django.core.management.base import BaseCommand

from users.models import User
from regions.models import State, Region
from schools.models import School, SchoolAdministrator

from django.db.utils import IntegrityError

import csv

class Command(BaseCommand):
    help = 'Import users from csv'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str, help='Filename of csv to import')

    def handle(self, *args, **kwargs):
        filename = kwargs['filename']

        with open(filename,"r",1,'utf-8-sig') as csvFile:
            reader = csv.DictReader(csvFile)
            for row in reader:
                try:

                    # Create user
                    user = User.objects.create(
                        email=row['email'],
                        password=f"sha1$${row['password']}",
                        first_name=row['firstName'],
                        last_name=row['lastName'],
                        mobileNumber=row['mobileNumber'],
                        forcePasswordChange=True,
                        forceDetailsUpdate=True,
                    )

                    if row['schoolCode']:
                        # Get or create school
                        school, created = School.objects.get_or_create(abbreviation=row['schoolCode'], defaults={'name': row['schoolName'], 'forceSchoolDetailsUpdate': True})

                        # Create school admin
                        schoolAdmin = SchoolAdministrator.objects.create(school=school, user=user)

                except IntegrityError:
                    continue
