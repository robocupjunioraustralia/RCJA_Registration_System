from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, modify_settings
from django.urls import reverse
from django.test import Client
from django.http import HttpRequest
from django.core.exceptions import ValidationError

from .models import Coordinator
from users.models import User
from regions.models import State, Region

# Create your tests here.

def commonSetUp(self):
    self.user1 = User.objects.create_user(email=self.email1, password=self.password)
    self.user2 = User.objects.create_user(email=self.email2, password=self.password)
    self.user3 = User.objects.create_user(email=self.email3, password=self.password)
    self.usersuper = User.objects.create_user(email=self.emailsuper, password=self.password, is_staff=True, is_superuser=True)

    self.state1 = State.objects.create(treasurer=self.user1, name='Victoria', abbreviation='VIC')
    self.state2 = State.objects.create(treasurer=self.user1, name='South Australia', abbreviation='SA')

class TestUpdateUserPermissions(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)

    def testCoordinatorUserChange(self):
        # Setup
        coordinator1 = Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.assertEqual(self.user1.is_staff, True)
        self.assertEqual(self.user1.is_superuser, False)

        # test changing user field on coordinator
        coordinator1.user = self.user2
        coordinator1.save()
        self.user1.refresh_from_db()
        # Check user 1
        self.assertEqual(self.user1.is_staff, False)
        self.assertEqual(self.user1.is_superuser, False)

        # Check user 2
        self.assertEqual(self.user2.is_staff, True)
        self.assertEqual(self.user2.is_superuser, False)

