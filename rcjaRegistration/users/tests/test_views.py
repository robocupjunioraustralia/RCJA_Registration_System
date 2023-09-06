from common.baseTests import createStates, createUsers
from django.test import TestCase
from django.core.exceptions import ValidationError
from unittest.mock import patch, Mock
from django.urls import reverse
from django.test import Client
from django.http import HttpRequest

from users.models import User
from coordination.models import Coordinator
from events.models import Year

class Test_LoginRequired(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        cls.year = Year.objects.create(year=2021, displayEventsOnWebsite=True)

    def testsetCurrentAdminYear(self):
        response = self.client.get(reverse('users:setCurrentAdminYear', kwargs= {'year':self.year.year}))
        self.assertEqual(response.url, f"/accounts/login/?next=/user/setCurrentAdminYear/{self.year.year}")
        self.assertEqual(response.status_code, 302)

    def testsetCurrentAdminState(self):
        response = self.client.get(reverse('users:setCurrentAdminState', kwargs= {'stateID':self.state1.id}))
        self.assertEqual(response.url, f"/accounts/login/?next=/user/setCurrentAdminState/{self.state1.id}")
        self.assertEqual(response.status_code, 302)

class Test_StaffRequired(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        cls.year = Year.objects.create(year=2021, displayEventsOnWebsite=True)

    def setUp(self):
        self.login = self.client.login(request=HttpRequest(), username=self.email_user_notstaff, password=self.password)

    def testsetCurrentAdminYear(self):
        self.assertEqual(self.user_notstaff.currentlySelectedAdminYear, None)

        response = self.client.get(reverse('users:setCurrentAdminYear', kwargs= {'year':self.year.year}))
        self.assertEqual(response.status_code, 403)

        # Check no update to value
        self.user_notstaff.refresh_from_db()
        self.assertEqual(self.user_notstaff.currentlySelectedAdminYear, None)

    def testsetCurrentAdminState(self):
        self.assertEqual(self.user_notstaff.currentlySelectedAdminState, None)

        response = self.client.get(reverse('users:setCurrentAdminState', kwargs= {'stateID':self.state1.id}))
        self.assertEqual(response.status_code, 403)

        # Check no update to value
        self.user_notstaff.refresh_from_db()
        self.assertEqual(self.user_notstaff.currentlySelectedAdminState, None)

class Test_response_setCurrentAdminYear(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        cls.year = Year.objects.create(year=2021, displayEventsOnWebsite=True)

    def setUp(self):
        self.login = self.client.login(request=HttpRequest(), username=self.email_user_state1_fullcoordinator, password=self.password)

    def testSuccess(self):
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminYear, None)

        response = self.client.get(reverse('users:setCurrentAdminYear', kwargs= {'year':self.year.year}))
        self.assertEqual(response.status_code, 302)

        # Check updated
        self.user_state1_fullcoordinator.refresh_from_db()
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminYear, self.year)

    def testRedirectNoReferer(self):
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminYear, None)

        response = self.client.get(reverse('users:setCurrentAdminYear', kwargs= {'year':self.year.year}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/")

    def testRedirectReferer(self):
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminYear, None)

        response = self.client.get(reverse('users:setCurrentAdminYear', kwargs= {'year':self.year.year}), HTTP_REFERER='http://localhost/accounts/profile')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/accounts/profile")

    def testNotExist404(self):
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminYear, None)

        response = self.client.get(reverse('users:setCurrentAdminYear', kwargs= {'year':500}))
        self.assertEqual(response.status_code, 404)

        # Check no update to value
        self.user_state1_fullcoordinator.refresh_from_db()
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminState, None)

    def testNone404(self):
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminYear, None)

        response = self.client.get(reverse('users:setCurrentAdminYear', kwargs= {'year':0}))
        self.assertEqual(response.status_code, 404)

        # Check no update to value
        self.user_state1_fullcoordinator.refresh_from_db()
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminState, None)

class Test_response_setCurrentAdminState(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        cls.year = Year.objects.create(year=2021, displayEventsOnWebsite=True)

    def setUp(self):
        self.login = self.client.login(request=HttpRequest(), username=self.email_user_state1_fullcoordinator, password=self.password)

    def testSuccess(self):
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminState, None)

        response = self.client.get(reverse('users:setCurrentAdminState', kwargs= {'stateID':self.state1.id}))
        self.assertEqual(response.status_code, 302)

        # Check updated
        self.user_state1_fullcoordinator.refresh_from_db()
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminState, self.state1)

    def testRedirectNoReferer(self):
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminState, None)

        response = self.client.get(reverse('users:setCurrentAdminState', kwargs= {'stateID':self.state1.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/")

    def testRedirectReferer(self):
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminState, None)

        response = self.client.get(reverse('users:setCurrentAdminState', kwargs= {'stateID':self.state1.id}), HTTP_REFERER='http://localhost/accounts/profile')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/accounts/profile")

    def testNotExist404(self):
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminState, None)

        response = self.client.get(reverse('users:setCurrentAdminState', kwargs= {'stateID':500}))
        self.assertEqual(response.status_code, 404)

        # Check no update to value
        self.user_state1_fullcoordinator.refresh_from_db()
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminState, None)

    def testNoneSuccess(self):
        self.user_state1_fullcoordinator.currentlySelectedAdminState = self.state1
        self.user_state1_fullcoordinator.save()
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminState, self.state1)

        response = self.client.get(reverse('users:setCurrentAdminState', kwargs= {'stateID':0}))
        self.assertEqual(response.status_code, 302)

        # Check updated
        self.user_state1_fullcoordinator.refresh_from_db()
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminState, None)

    def testNoPemissionDenied(self):
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminState, None)

        response = self.client.get(reverse('users:setCurrentAdminState', kwargs= {'stateID': self.state2.id}))
        self.assertEqual(response.status_code, 403)

        # Check updated
        self.user_state1_fullcoordinator.refresh_from_db()
        self.assertEqual(self.user_state1_fullcoordinator.currentlySelectedAdminState, None)
