from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, modify_settings
from django.urls import reverse
from django.test import Client
from django.http import HttpRequest
from django.core.exceptions import ValidationError

from .models import State, Region
from users.models import User

import datetime

def commonSetUp(self):
    self.user1 = User.objects.create_user(email=self.email1, password=self.password)

    self.state1 = State.objects.create(treasurer=self.user1, name='Victoria', abbreviation='VIC')

class TestStateClean(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)


    def testValid(self):
        state2 = State(
            treasurer=self.user1,
            name='New South Wales',
            abbreviation='NSW',
        )

        self.assertEqual(state2.clean(), None)

    def testNameCaseInsensitive(self):
        state2 = State(
            treasurer=self.user1,
            name='VicToria',
            abbreviation='VIC1',
        )
        self.assertRaises(ValidationError, state2.clean)

    def testAbbreviationCaseInsensitive(self):
        state2 = State(
            treasurer=self.user1,
            name='Thing',
            abbreviation='vic',
        )
        self.assertRaises(ValidationError, state2.clean)

class TestStateMethods(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)

    def testGetState(self):
        self.assertEqual(self.state1, self.state1.getState())

    def testTreasurerName(self):
        self.assertEqual(self.user1.fullname_or_email(), self.state1.treasurerName())

    def testStr(self):
        self.assertEqual('Victoria', str(self.state1))

    def testSave(self):
        state2 = State(
            treasurer=self.user1,
            name='New South Wales',
            abbreviation='nsw',
        )

        self.assertEqual('nsw', state2.abbreviation)
        state2.save()
        self.assertEqual('NSW', state2.abbreviation)
