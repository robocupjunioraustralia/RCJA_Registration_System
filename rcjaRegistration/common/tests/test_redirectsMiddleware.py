from common.baseTests import createStates, createUsers, createSchools
from django.test import TestCase
from django.urls import reverse

from django.http import HttpRequest

from users.models import User

class Base_Tests_redirectsMiddleware:
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createSchools(cls)

    def testNoRedirect(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 200)

    def testPasswordChangeRedirect(self):
        self.user.forcePasswordChange = True
        self.user.forceDetailsUpdate = True
        self.user.save()

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('password_change'))

    def testNoRedirectTermsAndConditions(self):
        self.user.forcePasswordChange = True
        self.user.forceDetailsUpdate = True
        self.user.save()

        response = self.client.get(reverse('users:termsAndConditions'))
        self.assertEqual(response.status_code, 200)

    def testUserDetailsUpdateRedirect(self):
        self.user.forceDetailsUpdate = True
        self.user.save()

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:details'))

class Test_redirectsMiddleware_notStaff(Base_Tests_redirectsMiddleware, TestCase):
    def setUp(self):
        self.login = self.client.login(request=HttpRequest(), username=self.email_user_state1_school1_mentor1, password=self.password)
        self.user = self.user_state1_school1_mentor1

    def testSchoolDetailsUpdateRedirect(self):
        self.user.currentlySelectedSchool.forceSchoolDetailsUpdate = True
        self.user.currentlySelectedSchool.save()

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('schools:details'))

    def testNoRedirectNoSchool(self):
        self.user.currentlySelectedSchool.forceSchoolDetailsUpdate = True
        self.user.currentlySelectedSchool.save()

        self.user.currentlySelectedSchool = None
        self.user.save()

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 200)
