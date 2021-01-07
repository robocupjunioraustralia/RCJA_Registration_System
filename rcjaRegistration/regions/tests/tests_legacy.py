from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, modify_settings
from django.urls import reverse
from django.test import Client
from django.http import HttpRequest
from django.core.exceptions import ValidationError

from regions.models import State, Region
from users.models import User
from coordination.models import Coordinator

import datetime

def commonSetUp(self):
    self.user1 = User.objects.create_user(email=self.email1, password=self.password)
    self.user2 = User.objects.create_user(email=self.email2, password=self.password)
    self.user3 = User.objects.create_user(email=self.email3, password=self.password)
    self.usersuper = User.objects.create_user(email=self.emailsuper, password=self.password, is_staff=True, is_superuser=True)

    self.state1 = State.objects.create(typeRegistration=True, name='Victoria', abbreviation='VIC')
    self.state2 = State.objects.create(typeRegistration=True, name='South Australia', abbreviation='SA')

class TestStateClean(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)

    def testValid(self):
        state2 = State(
            
            name='New South Wales',
            abbreviation='NSW',
        )

        self.assertEqual(state2.clean(), None)

    def testNameCaseInsensitive(self):
        state2 = State(
            
            name='VicToria',
            abbreviation='VIC1',
        )
        self.assertRaises(ValidationError, state2.clean)

    def testAbbreviationCaseInsensitive(self):
        state2 = State(
            
            name='Thing',
            abbreviation='vic',
        )
        self.assertRaises(ValidationError, state2.clean)

class TestStateMethods(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)

    def testGetState(self):
        self.assertEqual(self.state1, self.state1.getState())

    def testStr(self):
        self.assertEqual('Victoria', str(self.state1))

    def testSave_abbreviation(self):
        state2 = State(
            name='New South Wales',
            abbreviation='nsw',
        )

        self.assertEqual('nsw', state2.abbreviation)
        state2.save()
        self.assertEqual('NSW', state2.abbreviation)

    def testTypeGlobal_typeRegistration(self):
        self.state1.typeGlobal = True
        self.assertEqual(self.state1.typeGlobal, True)
        self.state1.save()
        self.assertEqual(self.state1.typeGlobal, False)

    def testTypeGlobal_notTypeRegistration(self):
        self.state1.typeGlobal = True
        self.state1.typeRegistration = False
        self.assertEqual(self.state1.typeGlobal, True)
        self.state1.save()
        self.assertEqual(self.state1.typeGlobal, True)

    def testTypeGlobal_otherGlobalState(self):
        self.state1.typeGlobal = True
        self.state1.typeRegistration = False
        self.state1.save()
        self.assertEqual(self.state1.typeGlobal, True)

        self.state2.typeGlobal = True
        self.state2.typeRegistration = False
        self.state2.save()
        self.assertEqual(self.state2.typeGlobal, True)
        self.state1.refresh_from_db()
        self.assertEqual(self.state1.typeGlobal, False)
