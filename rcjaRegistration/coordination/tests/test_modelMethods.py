from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, modify_settings
from django.urls import reverse
from django.test import Client
from django.http import HttpRequest
from django.core.exceptions import ValidationError

from coordination.models import Coordinator
from users.models import User
from regions.models import State, Region

# Create your tests here.

def commonSetUp(self):
    self.user1 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email1, password=self.password)
    self.user2 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email2, password=self.password)

    self.state1 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='Victoria', abbreviation='VIC')
    self.state2 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='South Australia', abbreviation='SA')

    self.user3 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email3, password=self.password, homeState=self.state1)
    self.usersuper = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.emailsuper, password=self.password, is_staff=True, is_superuser=True)

class TestCoordinatorMethods(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
        self.coord1 = Coordinator.objects.create(user=self.user1, state=self.state1, permissionLevel='full', position='Thing')
        self.user1.first_name = 'First'
        self.user1.last_name = 'Last'
        self.user1.save()
    
    def testGetState(self):
        self.assertEqual(self.coord1.getState(), self.state1)

    def testUserName(self):
        self.assertEqual(self.coord1.userName(), 'First Last')

    def testUserEmail(self):
        self.assertEqual(self.coord1.userEmail(), self.email1)

    def testStringState(self):
        self.assertEqual(str(self.coord1), f'First Last: Victoria - Full')

    def testStringNoState(self):
        self.coord2 = Coordinator.objects.create(user=self.user1, permissionLevel='full', position='Thing')
        self.assertEqual(str(self.coord2), f'First Last: Full')

    def testCleanNotDuplicate(self):
        self.coord2 = Coordinator(user=self.user1, state=self.state1, permissionLevel='viewall', position='Thing')
        self.coord2.clean()

    def testCleanDuplicate(self):
        self.coord2 = Coordinator(user=self.user1, state=self.state1, permissionLevel='full', position='Thing')
        self.assertRaises(ValidationError, self.coord2.clean)
