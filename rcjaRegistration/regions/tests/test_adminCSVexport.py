from common.baseTests import createStates, createUsers
from django.http import HttpRequest
from django.urls import reverse
from django.test import TestCase

class TestAdminCSVExport_State(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)

    def setUp(self):
        self.client.login(request=HttpRequest(), username=self.email_user_state1_super1, password=self.password)

    def test_export_as_csv_loads(self):
        response = self.client.post(reverse('admin:regions_state_changelist'), {'action': 'export_as_csv', '_selected_action': [1]})
        self.assertEqual(response.status_code, 200)

    def test_export_as_csv_correctHeaders(self):
        response = self.client.post(reverse('admin:regions_state_changelist'), {'action': 'export_as_csv', '_selected_action': [1]})
        self.assertContains(response, 'Name')
        self.assertContains(response, 'Abbreviation')
        self.assertContains(response, 'User registration')
        self.assertContains(response, 'Bank Account Name')

    def test_export_as_csv_correctValues(self):
        response = self.client.post(reverse('admin:regions_state_changelist'), {'action': 'export_as_csv', '_selected_action': [1]})
        self.assertContains(response, 'State 1')
        self.assertContains(response, 'ST1')
