from common.baseTests import createStates, createUsers, createSchools
from django.test import TestCase
from django.urls import reverse

from django.http import HttpRequest

from users.models import User

class Test_redirectsMiddleware_notStaff(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createSchools(cls)

    def setUp(self):
        self.login = self.client.login(request=HttpRequest(), username=self.email_user_state1_school1_mentor1, password=self.password)

    def testNoRedirect(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 200)

    def testPasswordChangeRedirect(self):
        self.user_state1_school1_mentor1.forcePasswordChange = True
        self.user_state1_school1_mentor1.save()

        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('password_change'))
