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

    self.state1 = State.objects.create(treasurer=self.user1, name='Victoria', abbreviation='VIC')
    self.state2 = State.objects.create(treasurer=self.user1, name='South Australia', abbreviation='SA')

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

class TestCoordinatorMethods(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
        self.coord1 = Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.user1.first_name = 'First'
        self.user1.last_name = 'Last'
        self.user1.save()
    
    def testGetState(self):
        self.assertEqual(self.coord1.getState(), self.state1)

    def testUserName(self):
        self.assertEqual(self.coord1.userName(), 'First Last')

    def testUserEmail(self):
        self.assertEqual(self.coord1.userEmail(), self.email1)

class TestCoordinatorAdmin(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
        self.coord1 = Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.coord2 = Coordinator.objects.create(user=self.user2, state=self.state2, permissions='full', position='Thing')

    def testCoordinatorListLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:coordination_coordinator_changelist'))
        self.assertEqual(response.status_code, 200)

    def testCoordinatorChangeLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:coordination_coordinator_change', args=(self.coord1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testCoordinatorListContent_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:coordination_coordinator_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.email1)
        self.assertContains(response, self.email2)

    def testCoordinatorDeleteLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:coordination_coordinator_delete', args=(self.coord1.id,)))
        self.assertEqual(response.status_code, 200)

    def testCoordinatorListNonStaff_denied(self):
        self.client.login(request=HttpRequest(), username=self.email3, password=self.password)
        response = self.client.get(reverse('admin:coordination_coordinator_changelist'))
        self.assertEqual(response.status_code, 302)

    def testCoordinatorListLoads_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:coordination_coordinator_changelist'))
        self.assertEqual(response.status_code, 200)

    def testCoordinatorListContent_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:coordination_coordinator_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.email1)
        self.assertNotContains(response, self.email2)

    def testCoordinatorChangeLoads_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:coordination_coordinator_change', args=(self.coord1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testCoordinatorChangeDenied_wrongState_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:coordination_coordinator_change', args=(self.coord2.id,)))
        self.assertEqual(response.status_code, 302)

    def testCoordinatorChangeDenied_viewPermission_coordinator(self):
        self.coord1.permissions = 'viewall'
        self.coord1.save()

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:coordination_coordinator_change', args=(self.coord1.id,)))
        self.assertEqual(response.status_code, 403)

    def testChangePostDenied_coordinator(self):
        self.coord1.permissions = 'viewall'
        self.coord1.save()

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'user': self.user3.id,
            'state': self.state1.id,
            'permissions': 'full',
            'position': 'Thing',
        }
        response = self.client.post(reverse('admin:coordination_coordinator_add'), data=payload)
        self.assertEqual(response.status_code, 403)

    # Coordinator FK filtering

    # State field
    def testStateFieldSucces_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        payload = {
            'user': self.user3.id,
            'state': self.state1.id,
            'permissions': 'full',
            'position': 'Thing',
        }
        response = self.client.post(reverse('admin:coordination_coordinator_add'), data=payload)
        self.assertEqual(response.status_code, 302)

    def testStateFieldSucces_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'user': self.user3.id,
            'state': self.state1.id,
            'permissions': 'full',
            'position': 'Thing',
        }
        response = self.client.post(reverse('admin:coordination_coordinator_add'), data=payload)
        self.assertEqual(response.status_code, 302)

    def testStateFieldDenied_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'user': self.user3.id,
            'state': self.state2.id,
            'permissions': 'full',
            'position': 'Thing',
        }
        response = self.client.post(reverse('admin:coordination_coordinator_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')
