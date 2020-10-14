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
        self.coordinator1 = Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
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

        self.coordinator1 = Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
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

    def testAdminBulkDelete(self):
        # Setup
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)

        self.coordinator1 = Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.assertTrue(self.user1.is_staff)
        self.assertFalse(self.user1.is_superuser)

        # Bulk delete coordinator
        payload = {
            'post': "yes",
            '_selected_action': self.coordinator1.id,
            'action': 'delete_selected'
        }

        response = self.client.post(reverse('admin:coordination_coordinator_changelist'), data=payload)
        self.user1.refresh_from_db()
        
        # Check delete success
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Coordinator.objects.exists())

        # Check permissions update
        self.assertFalse(self.user1.is_staff)
        self.assertFalse(self.user1.is_superuser)

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

    def testStringState(self):
        self.assertEqual(str(self.coord1), f'First Last: Victoria - Full')

    def testStringNoState(self):
        self.coord2 = Coordinator.objects.create(user=self.user1, permissions='full', position='Thing')
        self.assertEqual(str(self.coord2), f'First Last: Full')

    def testCleanNotDuplicate(self):
        self.coord2 = Coordinator(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        self.coord2.clean()

    def testCleanDuplicate(self):
        self.coord2 = Coordinator(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.assertRaises(ValidationError, self.coord2.clean)

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

    def testStateFieldBlankDenied_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'user': self.user3.id,
            'state': '',
            'permissions': 'full',
            'position': 'Thing',
        }
        response = self.client.post(reverse('admin:coordination_coordinator_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'This field is required.')
