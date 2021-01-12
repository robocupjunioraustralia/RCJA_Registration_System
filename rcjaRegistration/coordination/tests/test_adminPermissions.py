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

    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

class TestCoordinatorAdmin(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
        self.coord1 = Coordinator.objects.create(user=self.user1, state=self.state1, permissionLevel='full', position='Thing')
        self.coord2 = Coordinator.objects.create(user=self.user2, state=self.state2, permissionLevel='full', position='Thing')

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
        self.coord1.permissionLevel = 'viewall'
        self.coord1.save()

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:coordination_coordinator_change', args=(self.coord1.id,)))
        self.assertEqual(response.status_code, 403)

    def testChangePostDenied_coordinator(self):
        self.coord1.permissionLevel = 'viewall'
        self.coord1.save()

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'user': self.user3.id,
            'state': self.state1.id,
            'permissionLevel': 'full',
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
            'permissionLevel': 'full',
            'position': 'Thing',
        }
        response = self.client.post(reverse('admin:coordination_coordinator_add'), data=payload)
        self.assertEqual(response.status_code, 302)

    def testStateFieldSucces_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'user': self.user3.id,
            'state': self.state1.id,
            'permissionLevel': 'full',
            'position': 'Thing',
        }
        response = self.client.post(reverse('admin:coordination_coordinator_add'), data=payload)
        self.assertEqual(response.status_code, 302)

    def testStateFieldDenied_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'user': self.user3.id,
            'state': self.state2.id,
            'permissionLevel': 'full',
            'position': 'Thing',
        }
        response = self.client.post(reverse('admin:coordination_coordinator_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

    def testStateFieldBlankDenied_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'user': self.user3.id,
            'state': '',
            'permissionLevel': 'full',
            'position': 'Thing',
        }
        response = self.client.post(reverse('admin:coordination_coordinator_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'This field is required.')
