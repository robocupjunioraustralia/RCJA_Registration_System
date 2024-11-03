from common.baseTests import createStates, createUsers, createEvents
from django.http import HttpRequest
from django.urls import reverse
from django.test import TestCase

class TestAdminCSVExport_Event(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createEvents(cls)

    def setUp(self):
        self.client.login(request=HttpRequest(), username=self.email_user_state1_super1, password=self.password)

    def test_export_as_csv_loads(self):
        response = self.client.post(reverse('admin:events_event_changelist'), {'action': 'export_as_csv', '_selected_action': [self.state1_openCompetition.pk]})
        self.assertEqual(response.status_code, 200)

    def test_export_as_csv_correctHeaders(self):
        response = self.client.post(reverse('admin:events_event_changelist'), {'action': 'export_as_csv', '_selected_action': [self.state1_openCompetition.pk]})
        self.assertContains(response, 'Name')
        self.assertContains(response, 'Event start date')

    def test_export_as_csv_correctValues(self):
        response = self.client.post(reverse('admin:events_event_changelist'), {'action': 'export_as_csv', '_selected_action': [self.state1_openCompetition.pk]})
        self.assertContains(response, 'State 1 Open Competition')
