from common.baseTests import createStates, createUsers
from django.test import TestCase, override_settings
from django.urls import reverse

from django.http import HttpRequest

class Test_EnvironmentIndicator(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)

    def setUp(self):
        self.login = self.client.login(request=HttpRequest(), username=self.email_user_state1_school1_mentor1, password=self.password)

    def test_testingDisplayed(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertContains(response, 'TESTING')
    
    @override_settings(ENVIRONMENT='production')
    def test_noIndiactorInProduction(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertNotContains(response, 'TESTING')
