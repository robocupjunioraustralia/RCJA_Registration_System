from common.baseTests import createStates, createUsers, createEvents
from django.http import HttpRequest
from django.urls import reverse
from django.test import TestCase


class TestDivisionActive(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createEvents(cls)

    def setUp(self):
        self.client.login(request=HttpRequest(), username=self.email_user_state1_super1, password=self.password)

    def test_filter_default(self):
        response = self.client.get(reverse('admin:events_division'))
        self.assertContains(response.content, "4 Divisions")

    def test_filter_inactive(self):
        response = self.client.get(reverse('admin:events_division?active=inactive'))
        self.assertContains(response.content, "1 Division")


