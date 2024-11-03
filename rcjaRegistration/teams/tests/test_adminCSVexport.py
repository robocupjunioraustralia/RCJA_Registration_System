from common.baseTests import createStates, createUsers, createSchools, createEvents, createTeams
from django.http import HttpRequest
from django.urls import reverse
from django.test import TestCase

from teams.models import Student

class TestAdminCSVExport_Team(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createSchools(cls)
        createEvents(cls)
        createTeams(cls)
        Student.objects.create(team=cls.state1_event1_team1, firstName="John", lastName="Smith", yearLevel=5, gender="other")

    def setUp(self):
        self.client.login(request=HttpRequest(), username=self.email_user_state1_super1, password=self.password)

    def test_export_as_csv_loads(self):
        response = self.client.post(reverse('admin:teams_team_changelist'), {'action': 'export_as_csv', '_selected_action': [1]})
        self.assertEqual(response.status_code, 200)

    def test_export_as_csv_correctHeaders(self):
        response = self.client.post(reverse('admin:teams_team_changelist'), {'action': 'export_as_csv', '_selected_action': [1]})
        self.assertContains(response, 'Name')
        self.assertContains(response, 'Event')
        self.assertContains(response, 'Division')
        self.assertContains(response, 'Creation date')
        self.assertContains(response, 'Last modified date')
        self.assertContains(response, 'Hardware platform')
        self.assertContains(response, 'Software platform')
        self.assertContains(response, 'Member 1 First Name')
        self.assertContains(response, 'Member 1 Last Name')
        self.assertContains(response, 'Member 1 Year Level')
        self.assertContains(response, 'Member 1 Gender')

    def test_export_as_csv_correctValues(self):
        response = self.client.post(reverse('admin:teams_team_changelist'), {'action': 'export_as_csv', '_selected_action': [1]})
        self.assertContains(response, 'Team 1')
        self.assertContains(response, 'State 1 Open Competition')
        self.assertContains(response, 'Division 3')
        self.assertContains(response, 'John')
        self.assertContains(response, 'Smith')
        self.assertContains(response, '5')
        self.assertContains(response, 'Other')
