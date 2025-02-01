from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, modify_settings
from django.urls import reverse
from django.test import Client
from django.http import HttpRequest
from django.core.exceptions import ValidationError

import datetime

from coordination.models import Coordinator
from users.models import User
from regions.models import State, Region
from association.models import AssociationMember

# Create your tests here.

def commonSetUp(self):
    self.user1 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email1, password=self.password)
    self.user1_association_member = AssociationMember.objects.create(user=self.user1, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), rulesAcceptedDate=datetime.datetime.now(), membershipStartDate=datetime.datetime.now())

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

    def test_clean_no_errors(self):
        try:
            self.coord1.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def test_clean_change_existing_coordinator_no_association_member(self):
        self.user1_association_member.delete()
        self.coord1.refresh_from_db()
        self.assertRaises(AssociationMember.DoesNotExist, lambda: self.coord1.user.associationmember)

        try:
            self.coord1.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def test_clean_change_existing_coordinator_no_rulesAcceptedDate(self):
        self.user1_association_member.rulesAcceptedDate = None
        self.user1_association_member.save()
        self.coord1.refresh_from_db()
        self.assertEqual(self.coord1.user.associationmember.rulesAcceptedDate, None)

        try:
            self.coord1.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def test_clean_add_new_coordinator_no_association_member(self):
        self.assertRaises(AssociationMember.DoesNotExist, lambda: self.user2.associationmember)

        self.coord2 = Coordinator(user=self.user2, state=self.state2, permissionLevel='full', position='Thing')
        self.assertRaisesMessage(ValidationError, 'User must be a member of the Association to be a coordinator', self.coord2.clean)

    def test_clean_add_new_coordinator_no_rulesAcceptedDate(self):
        self.user2_association_member = AssociationMember.objects.create(user=self.user2, birthday=(datetime.datetime.now() + datetime.timedelta(days=-20*365)).date(), membershipStartDate=datetime.datetime.now())

        self.coord2 = Coordinator(user=self.user2, state=self.state2, permissionLevel='full', position='Thing')
        self.assertRaisesMessage(ValidationError, 'User must accept Association rules before being a coordinator', self.coord2.clean)

    def testCleanNotDuplicate(self):
        self.coord2 = Coordinator(user=self.user1, state=self.state1, permissionLevel='viewall', position='Thing')
        try:
            self.coord2.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testCleanDuplicate(self):
        self.coord2 = Coordinator(user=self.user1, state=self.state1, permissionLevel='full', position='Thing')
        self.assertRaises(ValidationError, self.coord2.clean)
