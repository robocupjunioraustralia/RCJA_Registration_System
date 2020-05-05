from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, modify_settings
from django.urls import reverse
from django.test import Client
from django.http import HttpRequest
from django.core.exceptions import ValidationError

from .models import State, Region
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

class TestStateAdmin(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)

    def testStateListLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:regions_state_changelist'))
        self.assertEqual(response.status_code, 200)

    def testStateChangeLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:regions_state_change', args=(self.state1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testStateListContent_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:regions_state_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Victoria')
        self.assertContains(response, 'South Australia')

    def testStateDeleteLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:regions_state_delete', args=(self.state1.id,)))
        self.assertEqual(response.status_code, 200)

    def testStateListNonStaff_denied(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:regions_state_changelist'))
        self.assertEqual(response.status_code, 302)

    def testStateListLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:regions_state_changelist'))
        self.assertEqual(response.status_code, 200)

    def testStateListContent_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:regions_state_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Victoria')
        self.assertNotContains(response, 'South Australia')

    def testStateChangeLoads_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:regions_state_change', args=(self.state1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testStateDeleteDenied_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:regions_state_delete', args=(self.state1.id,)))
        self.assertEqual(response.status_code, 403)

    def testStateAddDenied_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:regions_state_add'))
        self.assertEqual(response.status_code, 403)

    def testStateAddDenied_globalCoordinator(self):
        Coordinator.objects.create(user=self.user1, state=None, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:regions_state_add'))
        self.assertEqual(response.status_code, 403)

    def testStateChangeDenied_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:regions_state_change', args=(self.state2.id,)))
        self.assertEqual(response.status_code, 302)

    # Test inlines

    def testCorrectInlines_change_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:regions_state_change', args=(self.state1.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Coordinators")

    def testCorrectInlines_add_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:regions_state_add'))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, "Coordinators")

    def testCorrectInlines_change_fullCoordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:regions_state_change', args=(self.state1.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Coordinators")

    def testCorrectInlines_change_viewCoordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='viewall', position='Thing')
        Coordinator.objects.create(user=self.user1, state=self.state2, permissions='full', position='Thing')
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:regions_state_change', args=(self.state1.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, "Coordinators")

    # Test readonly fields on change page

    def testCorrectReadonlyFields_change_superuser_registration(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:regions_state_change', args=(self.state1.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, '<label>Registration:</label>')
        self.assertNotContains(response, '<input type="checkbox" name="typeRegistration"')

        self.assertContains(response, '<label>Global:</label>')
        self.assertNotContains(response, '<input type="checkbox" name="typeGlobal"')

        self.assertNotContains(response, '<label>Website:</label>')
        self.assertContains(response, '<input type="checkbox" name="typeWebsite"')

    def testCorrectReadonlyFields_change_superuser_notRegistration(self):
        self.state1.typeRegistration = False
        self.state1.save()

        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:regions_state_change', args=(self.state1.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, '<label>Registration:</label>')
        self.assertContains(response, '<input type="checkbox" name="typeRegistration"')

        self.assertNotContains(response, '<label>Global:</label>')
        self.assertContains(response, '<input type="checkbox" name="typeGlobal"')

        self.assertNotContains(response, '<label>Website:</label>')
        self.assertContains(response, '<input type="checkbox" name="typeWebsite"')

    def testCorrectReadonlyFields_change_coordinator(self):
        Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:regions_state_change', args=(self.state1.id,)))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, '<label>Registration:</label>')
        self.assertNotContains(response, '<input type="checkbox" name="typeRegistration"')

        self.assertContains(response, '<label>Global:</label>')
        self.assertNotContains(response, '<input type="checkbox" name="typeGlobal"')

        self.assertContains(response, '<label>Website:</label>')
        self.assertNotContains(response, '<input type="checkbox" name="typeWebsite"')
