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
    self.user1 = User.objects.create_user(email=self.email1, password=self.password)
    self.user2 = User.objects.create_user(email=self.email2, password=self.password)

    self.state1 = State.objects.create(typeRegistration=True, name='Victoria', abbreviation='VIC')
    self.state2 = State.objects.create(typeRegistration=True, name='South Australia', abbreviation='SA')

    self.user3 = User.objects.create_user(email=self.email3, password=self.password, homeState=self.state1)
    self.usersuper = User.objects.create_user(email=self.emailsuper, password=self.password, is_staff=True, is_superuser=True)

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
        self.coordinator1 = Coordinator.objects.create(user=self.user1, state=self.state1, permissionLevel='full', position='Thing')
        self.assertEqual(self.user1.is_staff, True)
        self.assertEqual(self.user1.is_superuser, False)

        # test changing user field on coordinator
        self.coordinator1.user = self.user2
        self.coordinator1.save()
        self.user1.refresh_from_db()
        # Check user 1
        self.assertEqual(self.user1.is_staff, False)
        self.assertEqual(self.user1.is_superuser, False)

        # Check user 2
        self.assertEqual(self.user2.is_staff, True)
        self.assertEqual(self.user2.is_superuser, False)

    def testDelete(self):
        # Setup
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)

        self.coordinator1 = Coordinator.objects.create(user=self.user1, state=self.state1, permissionLevel='full', position='Thing')
        self.assertTrue(self.user1.is_staff)
        self.assertFalse(self.user1.is_superuser)

        # Delete
        self.coordinator1.delete()
        self.user1.refresh_from_db()
        
        # Check delete success
        self.assertFalse(Coordinator.objects.exists())

        # Check permissions update
        self.assertFalse(self.user1.is_staff)
        self.assertFalse(self.user1.is_superuser)

    def testAdminBulkDeleteFails(self):
        # Setup
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)

        self.coordinator1 = Coordinator.objects.create(user=self.user1, state=self.state1, permissionLevel='full', position='Thing')
        self.assertTrue(self.user1.is_staff)
        self.assertFalse(self.user1.is_superuser)
        numCoordinators = Coordinator.objects.count()

        # Bulk delete coordinator
        payload = {
            'post': "yes",
            '_selected_action': self.coordinator1.id,
            'action': 'delete_selected'
        }

        response = self.client.post(reverse('admin:coordination_coordinator_changelist'), data=payload)
        self.user1.refresh_from_db()

        # Check delete failure - bulk delete disabled
        self.assertEqual(response.status_code, 302)
        self.assertEqual(numCoordinators, Coordinator.objects.count())
